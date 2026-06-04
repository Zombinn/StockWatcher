"""AkShare 数据获取（A股首选数据源，无需 token）"""
from __future__ import annotations

import asyncio
import logging
import random
import time
from datetime import datetime, timedelta
from typing import List, Optional

import akshare as ak
import pandas as pd

from .base import BaseDataProvider, KLine, StockInfo, StockPrice

logger = logging.getLogger(__name__)


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
        return await asyncio.to_thread(self._get_realtime_quote_sync, code)

    def _get_realtime_quote_sync(self, code: str) -> Optional[StockPrice]:
        """获取实时行情（通过东方财富接口）"""
        try:
            self._rate_limit()
            self._ua_rotate()
            clean = self._clean_code(code)
            df = ak.stock_zh_a_spot_em()
            if df is None or df.empty:
                return None
            row = df[df["代码"] == clean]
            if row.empty:
                return None
            r = row.iloc[0]
            return StockPrice(
                code=code,
                name=str(r.get("名称", "")),
                price=float(r.get("最新价", 0)),
                open=float(r.get("今开", 0)),
                high=float(r.get("最高", 0)),
                low=float(r.get("最低", 0)),
                pre_close=float(r.get("昨收", 0)),
                volume=float(r.get("成交量", 0)),
                amount=float(r.get("成交额", 0)),
                change_pct=float(r.get("涨跌幅", 0)),
                turnover_rate=float(r.get("换手率", 0)),
                volume_ratio=float(r.get("量比", 0)),
            )
        except Exception as e:
            logger.warning("AkShare 实时行情失败 %s: %s", code, e)
            return None

    async def get_kline(self, code: str, period: str = "daily", count: int = 120) -> List[KLine]:
        """获取 K 线数据（同步调用放入线程，避免阻塞事件循环）"""
        return await asyncio.to_thread(self._get_kline_sync, code, period, count)

    def _get_kline_sync(self, code: str, period: str = "daily", count: int = 120) -> List[KLine]:
        """获取 K 线数据（东方财富 stock_zh_a_hist，失败降级到新浪）"""
        try:
            self._rate_limit()
            self._ua_rotate()
            clean = self._clean_code(code)

            end = datetime.now()
            start = end - timedelta(days=count * 2)  # 多取一些，过滤非交易日

            df = ak.stock_zh_a_hist(
                symbol=clean,
                period=period,
                start_date=start.strftime("%Y%m%d"),
                end_date=end.strftime("%Y%m%d"),
                adjust="qfq",
            )

            if df is None or df.empty:
                logger.debug("AkShare(EM) K 线为空 %s，尝试新浪接口", code)
                return self._fallback_kline_sina(code, count)

            df = df.tail(count)
            results = []
            for _, r in df.iterrows():
                results.append(KLine(
                    code=code,
                    date=str(r["日期"]),
                    open=float(r["开盘"]),
                    high=float(r["最高"]),
                    low=float(r["最低"]),
                    close=float(r["收盘"]),
                    volume=float(r["成交量"]),
                    amount=float(r["成交额"]) if "成交额" in r else 0.0,
                    change_pct=float(r["涨跌幅"]) if "涨跌幅" in r else 0.0,
                ))
            return results

        except Exception as e:
            logger.warning("AkShare(EM) K 线失败 %s: %s，尝试新浪接口", code, e)
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
        return await asyncio.to_thread(self._get_stock_info_sync, code)

    def _get_stock_info_sync(self, code: str) -> Optional[StockInfo]:
        try:
            self._rate_limit()
            self._ua_rotate()
            clean = self._clean_code(code)
            df = ak.stock_individual_info_em(symbol=clean)
            info = {}
            for _, r in df.iterrows():
                info[r["item"]] = r["value"]
            return StockInfo(
                code=code,
                name=str(info.get("股票简称", "")),
                market=str(info.get("上市板块", "")),
                sector=str(info.get("行业", "")),
                market_cap=float(str(info.get("总市值", "0")).replace(",", "")),
            )
        except Exception as e:
            logger.warning("AkShare 股票信息失败 %s: %s", code, e)
            return None
