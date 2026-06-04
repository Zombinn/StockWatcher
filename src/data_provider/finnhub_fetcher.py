"""Finnhub 数据获取（美股）"""
from __future__ import annotations

import logging
from typing import List, Optional

import httpx

from .base import BaseDataProvider, KLine, StockInfo, StockPrice

logger = logging.getLogger(__name__)

FINNHUB_BASE = "https://finnhub.io/api/v1"


class FinnhubProvider(BaseDataProvider):
    """基于 Finnhub API 的数据提供者"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_realtime_quote(self, code: str) -> Optional[StockPrice]:
        try:
            symbol = code.replace(".US", "").strip()
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{FINNHUB_BASE}/quote",
                    params={"symbol": symbol, "token": self.api_key},
                    timeout=10,
                )
                data = resp.json()
                if not data or data.get("c", 0) == 0:
                    return None
                return StockPrice(
                    code=code,
                    price=float(data.get("c", 0)),
                    open=float(data.get("o", 0)),
                    high=float(data.get("h", 0)),
                    low=float(data.get("l", 0)),
                    pre_close=float(data.get("pc", 0)),
                    change_pct=float(data.get("dp", 0)),
                )
        except Exception as e:
            logger.warning("Finnhub 获取行情失败 %s: %s", code, e)
            return None

    async def get_kline(self, code: str, period: str = "daily", count: int = 120) -> List[KLine]:
        try:
            symbol = code.replace(".US", "").strip()
            resolution = {"daily": "D", "weekly": "W", "monthly": "M"}.get(period, "D")
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{FINNHUB_BASE}/stock/candle",
                    params={
                        "symbol": symbol, "resolution": resolution,
                        "count": count, "token": self.api_key,
                    },
                    timeout=10,
                )
                data = resp.json()
                if data.get("s") != "ok":
                    return []
                results = []
                for i in range(len(data.get("t", []))):
                    results.append(KLine(
                        code=code,
                        date=str(data["t"][i]),
                        open=float(data["o"][i]),
                        high=float(data["h"][i]),
                        low=float(data["l"][i]),
                        close=float(data["c"][i]),
                        volume=float(data["v"][i]),
                    ))
                return results
        except Exception as e:
            logger.warning("Finnhub 获取 K 线失败 %s: %s", code, e)
            return []

    async def get_stock_info(self, code: str) -> Optional[StockInfo]:
        try:
            symbol = code.replace(".US", "").strip()
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{FINNHUB_BASE}/stock/profile2",
                    params={"symbol": symbol, "token": self.api_key},
                    timeout=10,
                )
                data = resp.json()
                if not data:
                    return None
                return StockInfo(
                    code=code, name=data.get("name", ""),
                    sector=data.get("finnhubIndustry", ""),
                    market_cap=float(data.get("marketCapitalization", 0) or 0) * 1e6,
                )
        except Exception as e:
            logger.warning("Finnhub 获取股票信息失败 %s: %s", code, e)
            return None
