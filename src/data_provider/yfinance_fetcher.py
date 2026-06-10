"""YFinance 数据获取（港股/美股）"""
from __future__ import annotations

import logging
from typing import List, Optional

import yfinance as yf
import pandas as pd

from .base import BaseDataProvider, KLine, StockInfo, StockPrice

logger = logging.getLogger(__name__)


class YFinanceProvider(BaseDataProvider):
    """基于 YFinance 的数据提供者"""

    def _resolve_ticker(self, code: str) -> str:
        code = code.strip().upper()
        if code.endswith(".HK"):
            return code
        if code.endswith(".US"):
            return code[:-3]
        return code

    async def get_realtime_quote(self, code: str) -> Optional[StockPrice]:
        try:
            ticker = yf.Ticker(self._resolve_ticker(code))
            info = ticker.info or {}
            return StockPrice(
                code=code,
                name=info.get("longName", info.get("shortName", "")),
                price=float(info.get("currentPrice", info.get("regularMarketPrice", 0))),
                open=float(info.get("regularMarketOpen", 0)),
                high=float(info.get("regularMarketDayHigh", 0)),
                low=float(info.get("regularMarketDayLow", 0)),
                pre_close=float(info.get("regularMarketPreviousClose", 0)),
                volume=float(info.get("regularMarketVolume", 0)),
                change_pct=float(info.get("regularMarketChangePercent", 0)),
            )
        except Exception as e:
            logger.warning("YFinance 获取行情失败 %s: %s", code, e)
            return None

    async def get_kline(self, code: str, period: str = "daily", count: int = 120) -> List[KLine]:
        try:
            ticker = yf.Ticker(self._resolve_ticker(code))
            df = ticker.history(period="6mo", auto_adjust=False, repair=True)
            df = df.tail(count)
            results = []
            for date, r in df.iterrows():
                results.append(KLine(
                    code=code,
                    date=str(date.date()),
                    open=float(r["Open"]),
                    high=float(r["High"]),
                    low=float(r["Low"]),
                    close=float(r["Close"]),
                    volume=float(r["Volume"]),
                ))
            return results
        except Exception as e:
            logger.warning("YFinance 获取 K 线失败 %s: %s", code, e)
            return []

    async def get_stock_info(self, code: str) -> Optional[StockInfo]:
        try:
            ticker = yf.Ticker(self._resolve_ticker(code))
            info = ticker.info or {}
            return StockInfo(
                code=code,
                name=info.get("longName", info.get("shortName", "")),
                sector=info.get("sector", ""),
                market_cap=float(info.get("marketCap", 0) or 0),
                pe=float(info.get("trailingPE", 0) or 0),
                pb=float(info.get("priceToBook", 0) or 0),
            )
        except Exception as e:
            logger.warning("YFinance 获取股票信息失败 %s: %s", code, e)
            return None
