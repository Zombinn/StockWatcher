"""数据提供者工厂"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from src.config import get_config
from src.data_provider.base import BaseDataProvider

logger = logging.getLogger(__name__)

_providers: Dict[str, BaseDataProvider] = {}


def get_provider(name: str = "akshare") -> BaseDataProvider:
    """获取数据提供者实例（缓存）"""
    if name not in _providers:
        _providers[name] = _create_provider(name)
    return _providers[name]


def _create_provider(name: str) -> BaseDataProvider:
    config = get_config()

    if name == "akshare":
        from .akshare_fetcher import AkShareProvider
        return AkShareProvider()

    if name == "tushare":
        from .tushare_fetcher import TuShareProvider
        if config.tushare_token:
            return TuShareProvider(config.tushare_token)
        raise ValueError("未配置 TUSHARE_TOKEN")

    if name == "yfinance":
        from .yfinance_fetcher import YFinanceProvider
        return YFinanceProvider()

    if name == "tickflow":
        from .tickflow_fetcher import TickFlowProvider
        if config.tickflow_api_key:
            return TickFlowProvider(config.tickflow_api_key)
        raise ValueError("未配置 TICKFLOW_API_KEY")

    if name == "finnhub":
        from .finnhub_fetcher import FinnhubProvider
        if config.finnhub_api_key:
            return FinnhubProvider(config.finnhub_api_key)
        raise ValueError("未配置 FINNHUB_API_KEY")

    raise ValueError(f"未知数据提供者: {name}")


def get_provider_for_code(code: str) -> BaseDataProvider:
    """根据股票代码自动选择数据提供者"""
    code = code.strip().upper()
    config = get_config()

    # A 股: AkShare (首选) > Tushare > TickFlow
    if not code.endswith(".HK") and not code.endswith(".US"):
        if config.tushare_token:
            try:
                return get_provider("tushare")
            except Exception:
                pass
        return get_provider("akshare")

    # 港股/美股: YFinance (首选) > Finnhub
    if config.finnhub_api_key:
        try:
            return get_provider("finnhub")
        except Exception:
            pass
    return get_provider("yfinance")


def get_providers_for_codes(codes: List[str]) -> Dict[str, BaseDataProvider]:
    """批量获取股票对应的数据提供者"""
    result = {}
    for code in codes:
        result[code] = get_provider_for_code(code)
    return result
