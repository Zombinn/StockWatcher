"""Tushare 数据获取"""
from __future__ import annotations

import logging
from typing import List, Optional

import tushare as ts

from .base import BaseDataProvider, KLine, StockInfo, StockPrice

logger = logging.getLogger(__name__)


class TuShareProvider(BaseDataProvider):
    """基于 Tushare Pro 的数据提供者"""

    def __init__(self, token: str):
        ts.set_token(token)
        self.pro = ts.pro_api()

    def _normalize_code(self, code: str) -> str:
        code = code.strip().upper()
        for prefix in ("SH", "SZ", "BJ"):
            code = code.replace(prefix, "")
        # Tushare 需要补齐 6 位
        return code.zfill(6)

    async def get_realtime_quote(self, code: str) -> Optional[StockPrice]:
        try:
            norm = self._normalize_code(code)
            df = self.pro.daily(ts_code=f"{norm}", start_date="", end_date="")
            if df.empty:
                return None
            latest = df.iloc[-1]
            return StockPrice(
                code=code,
                price=float(latest.get("close", 0)),
                open=float(latest.get("open", 0)),
                high=float(latest.get("high", 0)),
                low=float(latest.get("low", 0)),
                close=float(latest.get("close", 0)),
                pre_close=float(latest.get("pre_close", 0)),
                volume=float(latest.get("vol", 0) * 100),  # 手 → 股
                amount=float(latest.get("amount", 0) * 1000),  # 千元 → 元
                change_pct=float(latest.get("pct_chg", 0)),
            )
        except Exception as e:
            logger.warning("Tushare 获取行情失败 %s: %s", code, e)
            return None

    async def get_kline(self, code: str, period: str = "daily", count: int = 120) -> List[KLine]:
        try:
            norm = self._normalize_code(code)
            df = self.pro.daily(ts_code=norm, start_date="")
            df = df.head(count)
            results = []
            for _, r in df.iterrows():
                results.append(KLine(
                    code=code, date=str(r.get("trade_date", "")),
                    open=float(r.get("open", 0)),
                    high=float(r.get("high", 0)),
                    low=float(r.get("low", 0)),
                    close=float(r.get("close", 0)),
                    volume=float(r.get("vol", 0) * 100),
                    amount=float(r.get("amount", 0) * 1000),
                    change_pct=float(r.get("pct_chg", 0)),
                ))
            return results
        except Exception as e:
            logger.warning("Tushare 获取 K 线失败 %s: %s", code, e)
            return []

    async def get_stock_info(self, code: str) -> Optional[StockInfo]:
        try:
            norm = self._normalize_code(code)
            df = self.pro.stock_basic(ts_code=norm)
            if df.empty:
                return None
            r = df.iloc[0]
            return StockInfo(
                code=code, name=r.get("name", ""),
                market=r.get("market", ""),
                sector=r.get("industry", ""),
                market_cap=float(r.get("total_mv", 0) or 0) * 1e4,
                pe=float(r.get("pe", 0) or 0),
                pb=float(r.get("pb", 0) or 0),
            )
        except Exception as e:
            logger.warning("Tushare 获取股票信息失败 %s: %s", code, e)
            return None
