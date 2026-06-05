"""AkShare 数据获取（A股首选数据源，无需 token）"""
from __future__ import annotations

import logging
import random
import time
from datetime import datetime, timedelta
from typing import List, Optional

import akshare as ak
import pandas as pd

from .base import BaseDataProvider, KLine, StockInfo, StockPrice
from src.utils.blocking import run_blocking

logger = logging.getLogger(__name__)

# 新浪 A 股全市场快照缓存（避免每只股票各拉一次全表）
_SINA_SNAPSHOT: dict = {"ts": 0.0, "df": None}


def _sina_spot_snapshot():
    """返回新浪 A 股全市场快照（30s 缓存）"""
    now = time.time()
    if _SINA_SNAPSHOT["df"] is not None and now - _SINA_SNAPSHOT["ts"] < 30:
        return _SINA_SNAPSHOT["df"]
    df = ak.stock_zh_a_spot()
    _SINA_SNAPSHOT["df"] = df
    _SINA_SNAPSHOT["ts"] = now
    return df


class AkShareProvider(BaseDataProvider):
    """基于 AkShare 的数据提供者（A 股，无需 token）"""

    def __init__(self):
        self._last_call = 0.0
        self._rate_limit_sec = 0.5
        self._timeout = 15

    def _rate_limit(self):
        """AkShare 反爬限制：每次调用间隔至少 0.5s"""
        elapsed = time.time() - self._last_call
        if elapsed < self._rate_limit_sec:
            time.sleep(self._rate_limit_sec - elapsed)
        self._last_call = time.time()

    @staticmethod
    def _ua_rotate():
        """随机 User-Agent 降低被封概率"""
        uas = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        ]
        try:
            ak.set_headers({"User-Agent": random.choice(uas)})
        except Exception:
            pass

    @staticmethod
    def _clean_code(code: str) -> str:
        """清理代码格式为 AkShare 所需格式：纯数字"""
        code = code.strip().upper()
        for prefix in ("SH", "SZ", "BJ", "SH.", "SZ.", "BJ."):
            code = code.replace(prefix, "")
        return code

    async def get_realtime_quote(self, code: str) -> Optional[StockPrice]:
        """获取实时行情（同步调用放入线程，避免阻塞事件循环）"""
        return await run_blocking(self._get_realtime_quote_sync, code)

    def _get_realtime_quote_sync(self, code: str) -> Optional[StockPrice]:
        """获取实时行情（新浪快照，带缓存）"""
        clean = self._clean_code(code)
        return self._sina_quote(code, clean)

    def _sina_quote(self, code: str, clean: str) -> Optional[StockPrice]:
        """新浪实时行情降级（东方财富不可达时使用，带 30s 快照缓存）"""
        try:
            df = _sina_spot_snapshot()
            if df is None or df.empty:
                return None
            row = df[df["代码"].str.endswith(clean)]
            if row.empty:
                return None
            r = row.iloc[0]
            return StockPrice(
                code=code,
                name=str(r.get("名称", "")),
                price=float(r.get("最新价", 0) or 0),
                open=float(r.get("今开", 0) or 0),
                high=float(r.get("最高", 0) or 0),
                low=float(r.get("最低", 0) or 0),
                pre_close=float(r.get("昨收", 0) or 0),
                volume=float(r.get("成交量", 0) or 0),
                amount=float(r.get("成交额", 0) or 0),
                change_pct=float(r.get("涨跌幅", 0) or 0),
            )
        except Exception as e:
            logger.warning("AkShare(新浪) 实时行情失败 %s: %s", code, e)
            return None

    async def get_kline(self, code: str, period: str = "daily", count: int = 120) -> List[KLine]:
        """获取 K 线数据（同步调用放入线程，避免阻塞事件循环）"""
        return await run_blocking(self._get_kline_sync, code, period, count)

    def _get_kline_sync(self, code: str, period: str = "daily", count: int = 120) -> List[KLine]:
        """获取 K 线数据（新浪接口，东方财富已禁用 — 网络不可达）"""
        return self._fallback_kline_sina(code, count)

    def _fallback_kline_sina(self, code: str, count: int = 120) -> List[KLine]:
        """备用 K 线数据（新浪接口）"""
        try:
            self._rate_limit()
            clean = self._clean_code(code)
            prefix = "sh" if clean.startswith("6") else "sz"
            df = ak.stock_zh_a_daily(symbol=f"{prefix}{clean}")
            if df is None or df.empty:
                return []
            df = df.tail(count)
            results = []
            for _, r in df.iterrows():
                results.append(KLine(
                    code=code,
                    date=str(r["date"]),
                    open=float(r["open"]),
                    high=float(r["high"]),
                    low=float(r["low"]),
                    close=float(r["close"]),
                    volume=float(r["volume"]),
                ))
            return results
        except Exception as e:
            logger.warning("AkShare(新浪) K 线也失败 %s: %s", code, e)
            return []

    async def get_stock_info(self, code: str) -> Optional[StockInfo]:
        """获取股票信息（同步调用放入线程，避免阻塞事件循环）"""
        return await run_blocking(self._get_stock_info_sync, code)

    def _get_stock_info_sync(self, code: str) -> Optional[StockInfo]:
        try:
            self._rate_limit()
            self._ua_rotate()
            clean = self._clean_code(code)
            # 从新浪快照获取股票信息（避免触发 libmini_racer）
            df = _sina_spot_snapshot()
            if df is not None and not df.empty:
                # 新浪代码形如 sz300750/sh600000，需按后缀匹配纯数字代码
                row = df[df["代码"].str.endswith(clean)]
                if not row.empty:
                    r = row.iloc[0]
                    return StockInfo(
                        code=code,
                        name=str(r.get("名称", "")),
                        market=str(r.get("交易所", "")),
                    )
            return StockInfo(code=code, name="")
        except Exception as e:
            logger.warning("AkShare 股票信息失败 %s: %s", code, e)
            return None
