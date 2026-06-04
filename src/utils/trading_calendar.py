"""A 股交易日 / 节假日识别（基于 AkShare 交易日历，带缓存）"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import List, Optional

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _trade_dates() -> frozenset[str]:
    """获取 A 股全部交易日集合（YYYY-MM-DD），失败返回空集合"""
    try:
        import akshare as ak

        df = ak.tool_trade_date_hist_sina()
        return frozenset(str(d) for d in df["trade_date"].tolist())
    except Exception as e:  # 网络/依赖不可用时降级
        logger.warning("交易日历获取失败，降级为周末判断: %s", e)
        return frozenset()


def _to_date(d: Optional[date | str]) -> date:
    if d is None:
        return date.today()
    if isinstance(d, str):
        return datetime.strptime(d, "%Y-%m-%d").date()
    return d


def is_trading_day(d: Optional[date | str] = None) -> bool:
    """判断是否为交易日。交易日历不可用时退化为「非周末」判断。"""
    day = _to_date(d)
    dates = _trade_dates()
    if dates:
        return day.strftime("%Y-%m-%d") in dates
    return day.weekday() < 5


def next_trading_day(d: Optional[date | str] = None) -> date:
    """返回给定日期之后的下一个交易日"""
    day = _to_date(d) + timedelta(days=1)
    for _ in range(30):
        if is_trading_day(day):
            return day
        day += timedelta(days=1)
    return day


def prev_trading_day(d: Optional[date | str] = None) -> date:
    """返回给定日期之前的上一个交易日"""
    day = _to_date(d) - timedelta(days=1)
    for _ in range(30):
        if is_trading_day(day):
            return day
        day -= timedelta(days=1)
    return day


def recent_trading_days(n: int = 5, end: Optional[date | str] = None) -> List[str]:
    """返回最近 n 个交易日（含 end 当天若为交易日），升序"""
    day = _to_date(end)
    out: List[str] = []
    for _ in range(n * 4):
        if is_trading_day(day):
            out.append(day.strftime("%Y-%m-%d"))
            if len(out) >= n:
                break
        day -= timedelta(days=1)
    return list(reversed(out))
