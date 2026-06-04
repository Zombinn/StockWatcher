"""股票数据服务"""
from __future__ import annotations

import logging
from typing import List, Optional

from src.config import Config
from src.data_provider.base import KLine, StockInfo, StockPrice, canonical_stock_code
from src.data_provider.factory import get_provider_for_code

logger = logging.getLogger(__name__)


class StockService:
    """股票数据服务"""

    def __init__(self, config: Config):
        self.config = config

    async def get_realtime_quote(self, code: str) -> Optional[StockPrice]:
        provider = get_provider_for_code(code)
        return await provider.get_realtime_quote(canonical_stock_code(code))

    async def get_kline_history(self, code: str, count: int = 120) -> List[KLine]:
        provider = get_provider_for_code(code)
        return await provider.get_kline(canonical_stock_code(code), count=count)

    async def get_stock_info(self, code: str) -> Optional[StockInfo]:
        provider = get_provider_for_code(code)
        return await provider.get_stock_info(canonical_stock_code(code))
