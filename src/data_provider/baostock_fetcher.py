"""Baostock 数据获取（A 股，无需 token，需 pip install baostock）"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from .base import BaseDataProvider, KLine, StockInfo, StockPrice

logger = logging.getLogger(__name__)

_PERIOD_MAP = {"daily": "d", "weekly": "w", "monthly": "m"}


class BaostockProvider(BaseDataProvider):
    """基于 Baostock 的数据提供者（A 股）"""

    def __init__(self):
        import baostock as bs  # 缺少依赖时由工厂捕获并降级

        self._bs = bs

    @staticmethod
    def _bs_code(code: str) -> str:
        """转换为 baostock 代码格式：sh.600000 / sz.000001"""
        clean = code.strip().upper()
        for p in ("SH", "SZ", "BJ", "."):
            clean = clean.replace(p, "")
        prefix = "sh" if clean.startswith("6") else "sz"
        return f"{prefix}.{clean}"

    def _with_session(self, fn):
        """baostock 需要 login/logout 包裹每次会话"""
        lg = self._bs.login()
        if lg.error_code != "0":
            logger.warning("Baostock 登录失败: %s", lg.error_msg)
            return None
        try:
            return fn()
        finally:
            self._bs.logout()

    async def get_kline(self, code: str, period: str = "daily", count: int = 120) -> List[KLine]:
        def _run() -> List[KLine]:
            end = datetime.now()
            start = end - timedelta(days=count * 2)
            rs = self._bs.query_history_k_data_plus(
                self._bs_code(code),
                "date,open,high,low,close,volume,amount,pctChg",
                start_date=start.strftime("%Y-%m-%d"),
                end_date=end.strftime("%Y-%m-%d"),
                frequency=_PERIOD_MAP.get(period, "d"),
                adjustflag="2",  # 前复权
            )
            rows: List[KLine] = []
            while rs.error_code == "0" and rs.next():
                d = rs.get_row_data()
                try:
                    rows.append(KLine(
                        code=code, date=d[0],
                        open=float(d[1] or 0), high=float(d[2] or 0),
                        low=float(d[3] or 0), close=float(d[4] or 0),
                        volume=float(d[5] or 0), amount=float(d[6] or 0),
                        change_pct=float(d[7] or 0),
                    ))
                except (ValueError, IndexError):
                    continue
            return rows[-count:]

        try:
            return self._with_session(_run) or []
        except Exception as e:
            logger.warning("Baostock K 线失败 %s: %s", code, e)
            return []

    async def get_realtime_quote(self, code: str) -> Optional[StockPrice]:
        """Baostock 无实时接口，用最近一根日 K 近似"""
        klines = await self.get_kline(code, count=2)
        if not klines:
            return None
        last = klines[-1]
        return StockPrice(
            code=code, price=last.close, open=last.open,
            high=last.high, low=last.low, close=last.close,
            pre_close=klines[-2].close if len(klines) > 1 else last.open,
            volume=last.volume, amount=last.amount, change_pct=last.change_pct,
            timestamp=datetime.now(),
        )

    async def get_stock_info(self, code: str) -> Optional[StockInfo]:
        def _run() -> Optional[StockInfo]:
            rs = self._bs.query_stock_basic(code=self._bs_code(code))
            if rs.error_code == "0" and rs.next():
                d = rs.get_row_data()
                return StockInfo(code=code, name=d[1] if len(d) > 1 else "")
            return None

        try:
            return self._with_session(_run)
        except Exception as e:
            logger.warning("Baostock 股票信息失败 %s: %s", code, e)
            return None
