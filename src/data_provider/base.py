"""数据提供者基类"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class StockPrice:
    """实时行情"""
    code: str
    name: str = ""
    price: float = 0.0
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    pre_close: float = 0.0
    volume: float = 0.0
    amount: float = 0.0
    change_pct: float = 0.0
    turnover_rate: float = 0.0
    volume_ratio: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class KLine:
    """K 线数据"""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float = 0.0
    change_pct: float = 0.0
    code: str = ""


@dataclass
class StockInfo:
    """股票信息"""
    code: str
    name: str
    market: str = ""
    sector: str = ""
    market_cap: float = 0.0
    pe: float = 0.0
    pb: float = 0.0


def canonical_stock_code(code: str) -> str:
    """规范化股票代码"""
    code = code.strip().upper()
    if code.startswith(("SH", "SZ", "BJ")):
        return code
    if code.startswith("6"):
        return f"SH{code}"
    if code.startswith(("0", "3")):
        return f"SZ{code}"
    return code


class BaseDataProvider(ABC):
    """数据提供者抽象基类"""

    @abstractmethod
    async def get_realtime_quote(self, code: str) -> Optional[StockPrice]:
        ...

    @abstractmethod
    async def get_kline(self, code: str, period: str = "daily", count: int = 120) -> List[KLine]:
        ...

    @abstractmethod
    async def get_stock_info(self, code: str) -> Optional[StockInfo]:
        ...

    async def get_multi_kline(self, codes: List[str], period: str = "daily", count: int = 120) -> Dict[str, List[KLine]]:
        result = {}
        for code in codes:
            if data := await self.get_kline(code, period, count):
                result[code] = data
        return result
