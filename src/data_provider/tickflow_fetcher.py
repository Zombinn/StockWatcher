"""TickFlow 数据获取"""
from __future__ import annotations

import logging
from typing import List, Optional

import httpx

from .base import BaseDataProvider, KLine, StockInfo, StockPrice

logger = logging.getLogger(__name__)

TICKFLOW_BASE = "https://api.tickflow.org/v1"


class TickFlowProvider(BaseDataProvider):
    """基于 TickFlow API 的数据提供者"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._http = httpx.AsyncClient(base_url=TICKFLOW_BASE, timeout=15)

    async def get_realtime_quote(self, code: str) -> Optional[StockPrice]:
        try:
            resp = await self._http.get(
                "/quote",
                params={"code": code, "market": "A"},
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            data = resp.json()
            d = data.get("data", {})
            return StockPrice(
                code=code, name=d.get("name", ""),
                price=float(d.get("price", 0)),
                open=float(d.get("open", 0)),
                high=float(d.get("high", 0)),
                low=float(d.get("low", 0)),
                close=float(d.get("close", 0)),
                volume=float(d.get("volume", 0)),
                amount=float(d.get("amount", 0)),
                change_pct=float(d.get("change_pct", 0)),
            )
        except Exception as e:
            logger.warning("TickFlow 获取行情失败 %s: %s", code, e)
            return None

    async def get_kline(self, code: str, period: str = "daily", count: int = 120) -> List[KLine]:
        try:
            resp = await self._http.get(
                "/kline",
                params={"code": code, "period": period, "count": count},
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            data = resp.json()
            results = []
            for item in data.get("data", []):
                results.append(KLine(
                    code=code, date=item.get("date", ""),
                    open=float(item.get("open", 0)),
                    high=float(item.get("high", 0)),
                    low=float(item.get("low", 0)),
                    close=float(item.get("close", 0)),
                    volume=float(item.get("volume", 0)),
                    amount=float(item.get("amount", 0)),
                    change_pct=float(item.get("change_pct", 0)),
                ))
            return results
        except Exception as e:
            logger.warning("TickFlow 获取 K 线失败 %s: %s", code, e)
            return []

    async def get_stock_info(self, code: str) -> Optional[StockInfo]:
        try:
            resp = await self._http.get(
                "/stock/info",
                params={"code": code},
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            data = resp.json()
            d = data.get("data", {})
            return StockInfo(
                code=code, name=d.get("name", ""),
                sector=d.get("industry", ""),
                market_cap=float(d.get("market_cap", 0)),
                pe=float(d.get("pe", 0)),
                pb=float(d.get("pb", 0)),
            )
        except Exception as e:
            logger.warning("TickFlow 获取股票信息失败 %s: %s", code, e)
            return None
