"""大盘复盘模块 - 市场情绪、板块轮动、北向资金"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from src.config import get_config

logger = logging.getLogger(__name__)

AKSHARE_MARKET_URL = "https://push2.eastmoney.com/api/qt/ulist.np/get"
AKSHARE_INDEX_MAP = {
    "上证指数": "1.000001",
    "深证成指": "0.399001",
    "创业板指": "0.399006",
    "科创50": "1.000688",
}


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
        """获取主要指数数据"""
        indices = []
        try:
            fields = "f2,f3,f4,f6,f15"
            secids = ",".join(AKSHARE_INDEX_MAP.values())
            async with httpx.AsyncClient(
    headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://quote.eastmoney.com/",
    },
    follow_redirects=True,
) as client:
                resp = await client.get(
                    AKSHARE_MARKET_URL,
                    params={"fltt": 2, "fields": fields, "secids": secids},
                    timeout=10,
                )
                data = resp.json()
                for item in data.get("data", {}).get("diff", []):
                    name_map = {v: k for k, v in AKSHARE_INDEX_MAP.items() if item.get("f12") in v}
                    name = next(iter(name_map.values()), item.get("f14", ""))
                    indices.append(IndexData(
                        name=name,
                        code=item.get("f12", ""),
                        price=float(item.get("f2", 0)),
                        change_pct=float(item.get("f3", 0)),
                        change_amount=float(item.get("f4", 0)),
                        volume=float(item.get("f6", 0)),
                        amount=float(item.get("f15", 0)),
                    ))
        except Exception as e:
            logger.warning("获取指数数据失败: %s", e)
        return indices

    async def fetch_market_overview(self) -> dict:
        """获取市场概览（涨跌家数）"""
        try:
            async with httpx.AsyncClient(
    headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://quote.eastmoney.com/",
    },
    follow_redirects=True,
) as client:
                resp = await client.get(
                    "https://push2.eastmoney.com/api/qt/ulist.np/get",
                    params={
                        "fltt": 2,
                        "fields": "f2,f3,f4,f12,f14",
                        "secids": "1.000001",
                        "mp": 1,
                    },
                    timeout=10,
                )
                data = resp.json()
                return data
        except Exception as e:
            logger.warning("获取市场概览失败: %s", e)
            return {}

    async def fetch_sectors(self, top: int = 10) -> tuple[List[SectorData], List[SectorData]]:
        """获取板块涨幅/跌幅排行"""
        top_sectors, fall_sectors = [], []
        try:
            async with httpx.AsyncClient(
    headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://quote.eastmoney.com/",
    },
    follow_redirects=True,
) as client:
                resp = await client.get(
                    "https://push2.eastmoney.com/api/qt/clist/get",
                    params={
                        "pn": 1,
                        "pz": top,
                        "fs": "m:90+t:3",
                        "fields": "f2,f3,f4,f12,f14,f104,f105",
                        "po": 1,  # 降序
                        "fid": "f3",
                    },
                    timeout=10,
                )
                data = resp.json()
                items = data.get("data", {}).get("diff", [])
                for item in items:
                    top_sectors.append(SectorData(
                        name=item.get("f14", ""),
                        change_pct=float(item.get("f3", 0)),
                        rise_count=int(item.get("f104", 0)),
                        fall_count=int(item.get("f105", 0)),
                    ))

                # 跌幅排行
                resp2 = await client.get(
                    "https://push2.eastmoney.com/api/qt/clist/get",
                    params={
                        "pn": 1,
                        "pz": top,
                        "fs": "m:90+t:3",
                        "fields": "f2,f3,f4,f12,f14,f104,f105",
                        "po": 0,
                        "fid": "f3",
                    },
                    timeout=10,
                )
                data2 = resp2.json()
                items2 = data2.get("data", {}).get("diff", [])
                for item in items2:
                    fall_sectors.append(SectorData(
                        name=item.get("f14", ""),
                        change_pct=float(item.get("f3", 0)),
                        rise_count=int(item.get("f104", 0)),
                        fall_count=int(item.get("f105", 0)),
                    ))
        except Exception as e:
            logger.warning("获取板块数据失败: %s", e)
        return top_sectors, fall_sectors

    async def fetch_northbound(self) -> Optional[NorthboundFlow]:
        """获取北向资金数据"""
        try:
            async with httpx.AsyncClient(
    headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://quote.eastmoney.com/",
    },
    follow_redirects=True,
) as client:
                resp = await client.get(
                    "https://push2.eastmoney.com/api/qt/kamt.kline/get",
                    params={"fields1": "f1,f2,f3,f4", "fields2": "f51,f52,f53,f54,f55"},
                    timeout=10,
                )
                data = resp.json()
                klines = data.get("data", {}).get("klines", [])
                if klines:
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
        result.top_sectors, result.fall_sectors = await self.fetch_sectors()
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
            logger.warning("LLM 大盘分析失败: %s", e)

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
