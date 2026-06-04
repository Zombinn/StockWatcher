"""Pytdx 数据获取（A 股，通达信行情，无需 token，需 pip install pytdx）"""
from __future__ import annotations

import logging
from typing import List, Optional

from .base import BaseDataProvider, KLine, StockInfo, StockPrice

logger = logging.getLogger(__name__)

# 通达信行情服务器（公开节点）
_SERVERS = [("119.147.212.81", 7709), ("60.12.136.250", 7709), ("218.108.98.244", 7709)]
# K 线类别：4=日线 5=周线 6=月线
_PERIOD_MAP = {"daily": 4, "weekly": 5, "monthly": 6}


class PytdxProvider(BaseDataProvider):
    """基于 Pytdx 的数据提供者（A 股）"""

    def __init__(self):
        from pytdx.hq import TdxHq_API  # 缺少依赖时由工厂捕获并降级

        self._api = TdxHq_API(heartbeat=True)

    @staticmethod
    def _market_code(code: str) -> tuple[int, str]:
        """返回 (market, code)；market: 1=上证 0=深证"""
        clean = code.strip().upper()
        for p in ("SH", "SZ", "BJ", "."):
            clean = clean.replace(p, "")
        market = 1 if clean.startswith("6") else 0
        return market, clean

    def _connect(self):
        for host, port in _SERVERS:
            try:
                if self._api.connect(host, port):
                    return True
            except Exception:
                continue
        return False

    async def get_kline(self, code: str, period: str = "daily", count: int = 120) -> List[KLine]:
        market, c = self._market_code(code)
        try:
            if not self._connect():
                return []
            try:
                category = _PERIOD_MAP.get(period, 4)
                bars = self._api.get_security_bars(category, market, c, 0, min(count, 800))
            finally:
                self._api.disconnect()
            if not bars:
                return []
            return [
                KLine(
                    code=code,
                    date=str(b.get("datetime", ""))[:10],
                    open=float(b.get("open", 0)), high=float(b.get("high", 0)),
                    low=float(b.get("low", 0)), close=float(b.get("close", 0)),
                    volume=float(b.get("vol", 0)), amount=float(b.get("amount", 0)),
                )
                for b in bars
            ]
        except Exception as e:
            logger.warning("Pytdx K 线失败 %s: %s", code, e)
            return []

    async def get_realtime_quote(self, code: str) -> Optional[StockPrice]:
        market, c = self._market_code(code)
        try:
            if not self._connect():
                return None
            try:
                quotes = self._api.get_security_quotes([(market, c)])
            finally:
                self._api.disconnect()
            if not quotes:
                return None
            q = quotes[0]
            pre_close = float(q.get("last_close", 0))
            price = float(q.get("price", 0))
            change_pct = ((price - pre_close) / pre_close * 100) if pre_close else 0.0
            return StockPrice(
                code=code, price=price, open=float(q.get("open", 0)),
                high=float(q.get("high", 0)), low=float(q.get("low", 0)),
                close=price, pre_close=pre_close,
                volume=float(q.get("vol", 0)), amount=float(q.get("amount", 0)),
                change_pct=round(change_pct, 2),
            )
        except Exception as e:
            logger.warning("Pytdx 实时行情失败 %s: %s", code, e)
            return None

    async def get_stock_info(self, code: str) -> Optional[StockInfo]:
        # 通达信行情接口不提供基础信息，返回最小信息
        return StockInfo(code=code, name="")
