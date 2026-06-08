"""大盘复盘模块 - 市场情绪、板块轮动、北向资金"""
from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from src.config import get_config

logger = logging.getLogger(__name__)
from src.utils.blocking import run_blocking

AKSHARE_INDEX_MAP = {
    "上证指数": "1.000001",
    "深证成指": "0.399001",
    "创业板指": "0.399006",
    "科创50": "1.000688",
}

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]


def _headers() -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": "https://quote.eastmoney.com/",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }


def _http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        headers=_headers(),
        follow_redirects=True,
        timeout=6.0,
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
    )


async def _fetch_json(url: str, params: dict, retries: int = 1) -> Optional[dict]:
    """带双域名 fallback + 重试的 JSON 请求（快速失败，避免单接口拖垮整体）"""
    import asyncio
    for host in ("push2.eastmoney.com", "push2delay.eastmoney.com"):
        for attempt in range(retries):
            try:
                full_url = url.replace("push2.eastmoney.com", host)
                async with _http_client() as client:
                    resp = await client.get(full_url, params=params)
                    if resp.status_code == 200:
                        return await resp.json()
                    logger.debug("%s returned status %d, trying fallback", host, resp.status_code)
            except Exception as e:
                logger.debug("请求 %s (第%d次) 失败: %s", host, attempt + 1, e)
                if attempt < retries - 1:
                    await asyncio.sleep(1.0)
    return None


@dataclass
class IndexData:
    """指数数据"""
    name: str
    code: str
    price: float = 0.0
    change_pct: float = 0.0
    change_amount: float = 0.0
    volume: float = 0.0
    amount: float = 0.0


@dataclass
class SectorData:
    """板块数据"""
    name: str
    change_pct: float = 0.0
    rise_count: int = 0
    fall_count: int = 0
    leader_stock: str = ""


@dataclass
class NorthboundFlow:
    """北向资金"""
    sh_net: float = 0.0  # 沪股通净流入(亿)
    sz_net: float = 0.0  # 深股通净流入(亿)
    total_net: float = 0.0
    date: str = ""


@dataclass
class MarketReviewResult:
    """大盘复盘结果"""
    indices: List[IndexData] = field(default_factory=list)
    top_sectors: List[SectorData] = field(default_factory=list)
    fall_sectors: List[SectorData] = field(default_factory=list)
    northbound: Optional[NorthboundFlow] = None
    rise_count: int = 0
    fall_count: int = 0
    limit_up: int = 0
    limit_down: int = 0
    market_summary: str = ""
    llm_analysis: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))


class MarketReviewer:
    """大盘复盘器"""

    def __init__(self):
        self.config = get_config()

    async def fetch_indices(self) -> List[IndexData]:
        """获取主要指数数据（新浪源，东方财富已禁用 — 网络不可达）"""
        return await self._fetch_indices_sina()

    async def _fetch_indices_sina(self) -> List[IndexData]:
        """新浪指数源（东方财富不可达时降级，不依赖 eastmoney）"""
        def _run() -> List[IndexData]:
            try:
                import akshare as ak
                df = ak.stock_zh_index_spot_sina()
            except Exception as e:
                logger.warning("新浪指数获取失败: %s", e)
                return []
            order = ["上证指数", "深证成指", "创业板指", "科创50", "沪深300"]
            want = set(order)
            seen: dict = {}
            for _, r in df[df["名称"].isin(want)].iterrows():
                name = str(r["名称"])
                if name in seen:
                    continue
                try:
                    seen[name] = IndexData(
                        name=name, code=str(r["代码"]),
                        price=float(r["最新价"]), change_pct=float(r["涨跌幅"]),
                        change_amount=float(r.get("涨跌额", 0) or 0),
                    )
                except (ValueError, KeyError):
                    continue
            return [seen[n] for n in order if n in seen]

        return await run_blocking(_run)

    async def fetch_sectors(self, top: int = 10) -> tuple[List[SectorData], List[SectorData]]:
        """获取板块涨幅/跌幅排行"""
        top_sectors, fall_sectors = [], []
        try:
            params = {
                "pn": 1, "pz": top,
                "fs": "m:90+t:3",
                "fields": "f2,f3,f4,f12,f14,f104,f105",
                "fid": "f3",
            }
            # 涨幅排行 (po=1 降序)
            params["po"] = 1
            data = await _fetch_json("https://push2.eastmoney.com/api/qt/clist/get", params.copy())
            if data and isinstance(data, dict) and "data" in data and data["data"]:
                items = data["data"].get("diff", [])
                if isinstance(items, list):
                    for item in items:
                        top_sectors.append(SectorData(
                            name=item.get("f14", ""),
                            change_pct=float(item.get("f3", 0)),
                            rise_count=int(item.get("f104", 0)),
                            fall_count=int(item.get("f105", 0)),
                        ))

            # 跌幅排行 (po=0 升序)
            params["po"] = 0
            data = await _fetch_json("https://push2.eastmoney.com/api/qt/clist/get", params.copy())
            if data and isinstance(data, dict) and "data" in data and data["data"]:
                items = data["data"].get("diff", [])
                if isinstance(items, list):
                    for item in items:
                        fall_sectors.append(SectorData(
                            name=item.get("f14", ""),
                            change_pct=float(item.get("f3", 0)),
                            rise_count=int(item.get("f104", 0)),
                            fall_count=int(item.get("f105", 0)),
                        ))
        except Exception as e:
            logger.warning("获取板块数据失败: %s", e)
        if not top_sectors and not fall_sectors:
            logger.info("东方财富板块为空，降级到新浪源")
            top_sectors, fall_sectors = await self._fetch_sectors_sina(top)
        return top_sectors, fall_sectors

    async def _fetch_sectors_sina(self, top: int = 10) -> tuple[List[SectorData], List[SectorData]]:
        """新浪行业板块源（东方财富不可达时降级）"""
        def _pct(v) -> float:
            try:
                return float(str(v).replace("%", "").strip())
            except (ValueError, TypeError):
                return 0.0

        def _run() -> tuple[List[SectorData], List[SectorData]]:
            try:
                import akshare as ak
                df = ak.stock_sector_spot()
            except Exception as e:
                logger.warning("新浪板块获取失败: %s", e)
                return [], []
            rows = [(str(r["板块"]), _pct(r["涨跌幅"])) for _, r in df.iterrows()]
            rows.sort(key=lambda x: x[1], reverse=True)
            top_s = [SectorData(name=n, change_pct=c) for n, c in rows[:top]]
            fall_s = [SectorData(name=n, change_pct=c) for n, c in rows[-top:][::-1]]
            return top_s, fall_s

        return await run_blocking(_run)

    async def fetch_northbound(self) -> Optional[NorthboundFlow]:
        """获取北向资金数据"""
        try:
            data = await _fetch_json(
                "https://push2.eastmoney.com/api/qt/kamt.kline/get",
                {"fields1": "f1,f2,f3,f4", "fields2": "f51,f52,f53,f54,f55"},
            )
            if data and isinstance(data, dict) and "data" in data and data["data"]:
                klines = data["data"].get("klines", [])
                if klines and len(klines) > 0:
                    latest = klines[-1].split(",")
                    sh_net = float(latest[1]) if len(latest) > 1 else 0.0
                    sz_net = float(latest[2]) if len(latest) > 2 else 0.0
                    return NorthboundFlow(
                        sh_net=sh_net,
                        sz_net=sz_net,
                        total_net=sh_net + sz_net,
                        date=latest[0] if len(latest) > 0 else "",
                    )
        except Exception as e:
            logger.warning("获取北向资金失败: %s", e)
        return None

    async def review(self) -> MarketReviewResult:
        """执行大盘复盘"""
        result = MarketReviewResult()
        result.indices = await self.fetch_indices()
        result.top_sectors, result.fall_sectors = await self.fetch_sectors(top=50)
        result.northbound = await self.fetch_northbound()

        # 生成摘要
        result.market_summary = self._generate_summary(result)

        # LLM 深度分析
        try:
            from src.llm.interpreter import LLMInterpreter
            interpreter = LLMInterpreter()
            market_text = self._format_for_llm(result)
            llm_result = await interpreter.analyze_market(market_text)
            if llm_result:
                result.llm_analysis = llm_result
        except Exception as e:
            logger.debug("LLM 大盘分析不可用: %s", e)

        return result

    def _generate_summary(self, result: MarketReviewResult) -> str:
        """生成市场摘要"""
        lines = ["**主要指数**: "]
        for idx in result.indices:
            emoji = "🟢" if idx.change_pct >= 0 else "🔴"
            lines.append(f"  {emoji} {idx.name}: {idx.price:.2f} ({idx.change_pct:+.2f}%)")

        if result.northbound:
            nf = result.northbound
            emoji = "🟢" if nf.total_net >= 0 else "🔴"
            lines.append(f"\n**北向资金**: {emoji} 沪股通 {nf.sh_net:+.2f}亿 / 深股通 {nf.sz_net:+.2f}亿 / 合计 {nf.total_net:+.2f}亿")

        if result.top_sectors:
            lines.append("\n**领涨板块**: ")
            for s in result.top_sectors[:5]:
                lines.append(f"  🟢 {s.name}: {s.change_pct:+.2f}%")
        if result.fall_sectors:
            lines.append("\n**领跌板块**: ")
            for s in result.fall_sectors[:5]:
                lines.append(f"  🔴 {s.name}: {s.change_pct:+.2f}%")

        return "\n".join(lines)

    def _format_for_llm(self, result: MarketReviewResult) -> str:
        """格式化数据供 LLM 分析"""
        lines = ["## 大盘数据\n"]
        lines.append("### 指数")
        for idx in result.indices:
            lines.append(f"- {idx.name}: {idx.price:.2f} ({idx.change_pct:+.2f}%)")
        lines.append("\n### 北向资金")
        if result.northbound:
            nf = result.northbound
            lines.append(f"- 合计: {nf.total_net:+.2f}亿")
        lines.append("\n### 板块")
        if result.top_sectors:
            lines.append("领涨:")
            for s in result.top_sectors[:5]:
                lines.append(f"- {s.name}: {s.change_pct:+.2f}%")
        if result.fall_sectors:
            lines.append("领跌:")
            for s in result.fall_sectors[:5]:
                lines.append(f"- {s.name}: {s.change_pct:+.2f}%")
        return "\n".join(lines)
