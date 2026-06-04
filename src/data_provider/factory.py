"""数据提供者工厂 - 支持自动降级链"""
from __future__ import annotations

import logging
from typing import Dict, Optional

from src.data_provider.base import BaseDataProvider

logger = logging.getLogger(__name__)

_providers: Dict[str, BaseDataProvider] = {}


def _has_token(key: str) -> bool:
    """检查是否有有效 token（非空、非注释）"""
    from src.config import _get_env
    return _get_env(key) is not None


def get_provider(name: str = "akshare") -> BaseDataProvider:
    """获取数据提供者实例（缓存）"""
    if name not in _providers:
        _providers[name] = _create_provider(name)
    return _providers[name]


def _create_provider(name: str) -> BaseDataProvider:
    if name == "akshare":
        from .akshare_fetcher import AkShareProvider
        return AkShareProvider()

    if name == "efinance":
        from .efinance_fetcher import EfinanceProvider
        return EfinanceProvider()

    if name == "tushare":
        from .tushare_fetcher import TuShareProvider
        token = _has_token("TUSHARE_TOKEN")
        if not token:
            raise ValueError("未配置 TUSHARE_TOKEN 或配置无效")
        from src.config import get_config
        return TuShareProvider(get_config().tushare_token)

    if name == "yfinance":
        from .yfinance_fetcher import YFinanceProvider
        return YFinanceProvider()

    if name == "tickflow":
        from .tickflow_fetcher import TickFlowProvider
        if not _has_token("TICKFLOW_API_KEY"):
            raise ValueError("未配置 TICKFLOW_API_KEY")
        from src.config import get_config
        return TickFlowProvider(get_config().tickflow_api_key)

    if name == "finnhub":
        from .finnhub_fetcher import FinnhubProvider
        if not _has_token("FINNHUB_API_KEY"):
            raise ValueError("未配置 FINNHUB_API_KEY")
        from src.config import get_config
        return FinnhubProvider(get_config().finnhub_api_key)

    if name == "baostock":
        from .baostock_fetcher import BaostockProvider
        return BaostockProvider()

    if name == "pytdx":
        from .pytdx_fetcher import PytdxProvider
        return PytdxProvider()

    if name == "longbridge":
        from .longbridge_fetcher import LongbridgeProvider
        if not _has_token("LONGPORT_APP_KEY"):
            raise ValueError("未配置 LONGPORT_APP_KEY")
        return LongbridgeProvider()

    raise ValueError(f"未知数据提供者: {name}")


def get_provider_for_code(code: str) -> BaseDataProvider:
    """根据股票代码自动选择数据提供者，带自动降级"""
    code = code.strip().upper()

    # 智能判断市场:
    #   .HK 后缀 / 5位纯数字 = 港股 → YFinance
    #   .US 后缀 / 纯字母(≤5字符, 如TSLA,AAPL) = 美股 → YFinance > Finnhub
    #   其余（6位数字等）= A股 → AkShare > Tushare > TickFlow
    is_hk = code.endswith(".HK") or (code.isdigit() and len(code) == 5)
    is_us = code.endswith(".US") or (code.isalpha() and len(code) <= 5)

    if is_us or is_hk:
        # 港股/美股降级链: YFinance > Finnhub > Longbridge
        try:
            return get_provider("yfinance")
        except Exception as e:
            logger.debug("YFinance 不可用: %s", e)
        if _has_token("FINNHUB_API_KEY"):
            try:
                return get_provider("finnhub")
            except Exception as e:
                logger.debug("Finnhub 不可用: %s", e)
        if _has_token("LONGPORT_APP_KEY"):
            try:
                return get_provider("longbridge")
            except Exception as e:
                logger.debug("Longbridge 不可用: %s", e)
        return get_provider("yfinance")

    # A 股降级链: AkShare > Tushare > TickFlow
    try:
        return get_provider("akshare")
    except Exception as e:
        logger.debug("AkShare 不可用: %s", e)

    if _has_token("TUSHARE_TOKEN"):
        try:
            return get_provider("tushare")
        except Exception as e:
            logger.debug("Tushare 不可用: %s", e)

    if _has_token("TICKFLOW_API_KEY"):
        try:
            return get_provider("tickflow")
        except Exception as e:
            logger.debug("TickFlow 不可用: %s", e)

    # 无 token 的本地降级源: Baostock > Pytdx（需对应依赖已安装）
    for fallback in ("baostock", "pytdx"):
        try:
            return get_provider(fallback)
        except Exception as e:
            logger.debug("%s 不可用: %s", fallback, e)

    return get_provider("akshare")
