"""选股服务 — 对候选股票池拉行情+技术分析，返回真实结果"""
from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

from src.services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)

# 候选股票池（各市场常用标的，覆盖多个策略）
_POOL: dict[str, list[tuple[str, str]]] = {
    "hk": [
        ("0700.HK", "腾讯控股"), ("9988.HK", "阿里巴巴"), ("9618.HK", "京东集团"),
        ("03690.HK", "美团"),    ("1810.HK", "小米集团"), ("0939.HK", "建设银行"),
        ("0941.HK", "中国移动"), ("2318.HK", "中国平安"), ("0005.HK", "汇丰控股"),
        ("0388.HK", "香港交易所"),("9999.HK", "网易"),    ("2382.HK", "舜宇光学"),
        ("0175.HK", "吉利汽车"), ("1211.HK", "比亚迪股份"),("6690.HK", "海尔智家"),
    ],
    "us": [
        ("AAPL",  "Apple"),    ("MSFT",  "Microsoft"), ("NVDA",  "NVIDIA"),
        ("AMZN",  "Amazon"),   ("GOOGL", "Alphabet"),  ("META",  "Meta"),
        ("TSLA",  "Tesla"),    ("AMD",   "AMD"),        ("AVGO",  "Broadcom"),
        ("TSM",   "台积电"),    ("ORCL",  "Oracle"),    ("CRM",   "Salesforce"),
        ("NFLX",  "Netflix"),  ("UBER",  "Uber"),       ("COIN",  "Coinbase"),
    ],
}

# A 股：从 watchlist.json + 自选股种子兜底
_CN_SEED = [
    ("600519", "贵州茅台"), ("300750", "宁德时代"), ("000001", "平安银行"),
    ("600036", "招商银行"), ("601318", "中国平安"), ("002594", "比亚迪"),
    ("600276", "恒瑞医药"), ("300308", "中际旭创"), ("002415", "海康威视"),
    ("601012", "隆基绿能"), ("000333", "美的集团"), ("600887", "伊利股份"),
]


def _sort_key(item: dict, strategy: str) -> float:
    if strategy == "top_gainers":
        return item.get("change_pct") or 0
    if strategy == "oversold_reversal":
        return -(item.get("change_pct") or 0)   # 跌得最多的在前
    if strategy == "blue_chip":
        return item.get("score") or 0
    if strategy == "growth":
        return item.get("score") or 0
    return item.get("score") or 0


async def screen(market: str, strategy: str = "top_gainers", limit: int = 12) -> list[dict]:
    """对股票池做真实行情 + 技术分析，按策略排序返回"""
    if market == "cn":
        # A 股：合并 watchlist + 种子
        try:
            from src.services.watchlist_service import WatchlistService
            codes = WatchlistService().get_codes()
            pool = [(c, c) for c in codes if not c.endswith((".HK", ".US")) and not c.isalpha()]
        except Exception:
            pool = []
        for code, name in _CN_SEED:
            if not any(p[0] == code for p in pool):
                pool.append((code, name))
    else:
        pool = _POOL.get(market, [])

    if not pool:
        return []

    sem = asyncio.Semaphore(3)   # 并发度保守一些
    service = AnalysisService()

    stock_service = service.stock_service

    async def _analyze_one(code: str, fallback_name: str) -> Optional[dict]:
        async with sem:
            try:
                result = await service.analyze_single(code)
                if not result:
                    return None
                # analyze_single gets price/change from kline; supplement with realtime quote
                # (yfinance kline may return nan for recently-closed markets)
                import math
                if not result.current_price or not math.isfinite(result.current_price):
                    quote = await stock_service.get_realtime_quote(code)
                    if quote and quote.price:
                        result.current_price = quote.price
                        result.change_pct = quote.change_pct
                def _f(v):
                    """JSON-safe float (replace nan/inf with 0)"""
                    import math
                    return 0.0 if (v is None or (isinstance(v, float) and not math.isfinite(v))) else round(v, 4)

                return {
                    "code": code,
                    "name": result.name or fallback_name,
                    "price": _f(result.current_price),
                    "change_pct": _f(result.change_pct),
                    "score": _f(result.score),
                    "signal": result.signal,
                    "trend": result.trend,
                    "risk": result.risk_level,
                    "support": _f(result.support),
                    "resistance": _f(result.resistance),
                    "reason": _reason(result, strategy),
                }
            except Exception as e:
                logger.warning("选股分析失败 %s: %s", code, e)
                return None

    tasks = [_analyze_one(code, name) for code, name in pool]
    raw = [r for r in await asyncio.gather(*tasks) if r]

    raw.sort(key=lambda r: _sort_key(r, strategy), reverse=(strategy != "oversold_reversal"))
    return raw[:limit]


def _reason(result, strategy: str) -> str:
    ind = result.indicators
    if strategy == "top_gainers":
        return f"涨跌 {result.change_pct:+.2f}%，{result.trend}，评分 {result.score:.0f}"
    if strategy == "oversold_reversal":
        return f"RSI14={ind.rsi_14:.1f}（{'超卖' if ind.rsi_14 < 35 else '偏低'}），乖离率 {ind.bias_5:.2f}%"
    if strategy in ("blue_chip", "growth"):
        return f"综合评分 {result.score:.0f}，趋势「{result.trend}」，信号「{result.signal}」"
    return f"{result.trend}，信号「{result.signal}」"
