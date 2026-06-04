"""Longbridge（长桥）数据获取（A 股/港股/美股，需 pip install longport 及 API 凭证）

凭证通过环境变量提供（longport SDK 自动读取）：
  LONGPORT_APP_KEY / LONGPORT_APP_SECRET / LONGPORT_ACCESS_TOKEN
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from .base import BaseDataProvider, KLine, StockInfo, StockPrice

logger = logging.getLogger(__name__)


class LongbridgeProvider(BaseDataProvider):
    """基于 Longbridge OpenAPI 的数据提供者"""

    def __init__(self):
        from longport.openapi import Config, QuoteContext  # 缺少依赖/凭证时由工厂捕获

        self._ctx = QuoteContext(Config.from_env())

    @staticmethod
    def _symbol(code: str) -> str:
        """转换为 longport 代码格式：700.HK / AAPL.US / 600519.SH"""
        c = code.strip().upper()
        if c.endswith(".HK") or c.endswith(".US"):
            return c
        if c.isdigit():
            if len(c) == 5:  # 港股
                return f"{c}.HK"
            return f"{c}.SH" if c.startswith("6") else f"{c}.SZ"
        return f"{c}.US"  # 纯字母按美股

    async def get_realtime_quote(self, code: str) -> Optional[StockPrice]:
        try:
            quotes = self._ctx.quote([self._symbol(code)])
            if not quotes:
                return None
            q = quotes[0]
            last = float(q.last_done)
            prev = float(q.prev_close)
            change_pct = ((last - prev) / prev * 100) if prev else 0.0
            return StockPrice(
                code=code, price=last, open=float(q.open),
                high=float(q.high), low=float(q.low), close=last,
                pre_close=prev, volume=float(q.volume), amount=float(q.turnover),
                change_pct=round(change_pct, 2),
            )
        except Exception as e:
            logger.warning("Longbridge 实时行情失败 %s: %s", code, e)
            return None

    async def get_kline(self, code: str, period: str = "daily", count: int = 120) -> List[KLine]:
        try:
            from longport.openapi import AdjustType, Period

            period_map = {"daily": Period.Day, "weekly": Period.Week, "monthly": Period.Month}
            bars = self._ctx.candlesticks(
                self._symbol(code),
                period_map.get(period, Period.Day),
                min(count, 1000),
                AdjustType.ForwardAdjust,
            )
            return [
                KLine(
                    code=code,
                    date=b.timestamp.strftime("%Y-%m-%d"),
                    open=float(b.open), high=float(b.high), low=float(b.low),
                    close=float(b.close), volume=float(b.volume), amount=float(b.turnover),
                )
                for b in bars
            ]
        except Exception as e:
            logger.warning("Longbridge K 线失败 %s: %s", code, e)
            return []

    async def get_stock_info(self, code: str) -> Optional[StockInfo]:
        try:
            infos = self._ctx.static_info([self._symbol(code)])
            if not infos:
                return None
            i = infos[0]
            return StockInfo(code=code, name=getattr(i, "name_cn", "") or getattr(i, "name_en", ""))
        except Exception as e:
            logger.warning("Longbridge 股票信息失败 %s: %s", code, e)
            return None
