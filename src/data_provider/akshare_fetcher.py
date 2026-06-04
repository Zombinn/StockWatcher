"""AkShare 数据获取"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import akshare as ak
import pandas as pd

from .base import BaseDataProvider, KLine, StockInfo, StockPrice

logger = logging.getLogger(__name__)


class AkShareProvider(BaseDataProvider):
    """基于 AkShare 的数据提供者"""

    async def get_realtime_quote(self, code: str) -> Optional[StockPrice]:
        try:
            df = ak.stock_zh_a_spot_em()
            row = df[df["代码"] == code]
            if row.empty:
                return None
            r = row.iloc[0]
            return StockPrice(
                code=code,
                name=r.get("名称", ""),
                price=float(r.get("最新价", 0)),
                open=float(r.get("今开", 0)),
                high=float(r.get("最高", 0)),
                low=float(r.get("最低", 0)),
                pre_close=float(r.get("昨收", 0)),
                volume=float(r.get("成交量", 0)),
                amount=float(r.get("成交额", 0)),
                change_pct=float(r.get("涨跌幅", 0)),
                turnover_rate=float(r.get("换手率", 0)),
                volume_ratio=float(r.get("量比", 0)),
            )
        except Exception as e:
            logger.warning("AkShare 获取实时行情失败 %s: %s", code, e)
            return None

    async def get_kline(self, code: str, period: str = "daily", count: int = 120) -> List[KLine]:
        try:
            symbol = self._to_akshare_symbol(code)
            df = ak.stock_zh_a_hist(symbol=symbol, period=period, adjust="qfq")
            df = df.tail(count)
            results = []
            for _, r in df.iterrows():
                results.append(KLine(
                    date=str(r["日期"]),
                    open=float(r["开盘"]),
                    high=float(r["最高"]),
                    low=float(r["最低"]),
                    close=float(r["收盘"]),
                    volume=float(r["成交量"]),
                    amount=float(r["成交额"]),
                    change_pct=float(r.get("涨跌幅", 0)),
                ))
            return results
        except Exception as e:
            logger.warning("AkShare 获取 K 线失败 %s: %s", code, e)
            return []

    async def get_stock_info(self, code: str) -> Optional[StockInfo]:
        try:
            df = ak.stock_individual_info_em(symbol=code)
            info = {}
            for _, r in df.iterrows():
                info[r["item"]] = r["value"]
            return StockInfo(
                code=code,
                name=str(info.get("股票简称", "")),
                market=str(info.get("上市板块", "")),
                sector=str(info.get("行业", "")),
                market_cap=float(str(info.get("总市值", "0")).replace(",", "")),
            )
        except Exception as e:
            logger.warning("AkShare 获取股票信息失败 %s: %s", code, e)
            return None

    @staticmethod
    def _to_akshare_symbol(code: str) -> str:
        code = code.strip().upper()
        for prefix in ("SH", "SZ", "BJ"):
            if code.startswith(prefix):
                return code
        return code
