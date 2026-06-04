"""LLM 分析解读器 - AI 解读技术指标和新闻"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.llm.client import LLMClient, create_llm_client
from src.stock_analyzer import AnalysisResult

logger = logging.getLogger(__name__)

_LLM_ANALYSIS_SYSTEM_PROMPT = """你是一位专业的股票技术分析师。请根据以下技术指标数据，给出专业的分析解读。

请用中文回复，以 JSON 格式输出以下字段：
- summary: 一句话核心结论
- trend_analysis: 趋势分析（50-100字）
- technical_insight: 技术指标解读（50-100字）
- risk_warning: 风险提示
- operation_advice: 操作建议（含仓位建议）
- score_adjustment: 基于你的专业判断，对原始评分的调整值（-20 到 +20）
- key_levels: 关键价位，包含 support（支撑位）和 resistance（压力位）

只输出 JSON，不要包含其他文字。"""

_NEWS_ANALYSIS_PROMPT = """你是一位财经新闻分析师。请根据以下股票相关新闻，分析其对股价的潜在影响。

请用中文回复，以 JSON 格式输出以下字段：
- sentiment: 情绪（positive/negative/neutral）
- impact_score: 影响评分 1-10
- key_points: 关键信息点列表
- summary: 综合分析（30-50字）

只输出 JSON。"""

_MARKET_REVIEW_PROMPT = """你是一位市场分析师。请根据以下市场数据，撰写大盘复盘报告。

请用中文回复，以 JSON 格式输出：
- summary: 市场概况（50-80字）
- market_phase: 市场阶段（上涨/下跌/震荡/调整）
- sector_rotation: 板块轮动分析（30-50字）
- capital_flow: 资金流向分析
- risk_level: 风险等级（low/medium/high）
- outlook: 后市展望（30-50字）

只输出 JSON。"""


@dataclass
class LLMAnalysis:
    """LLM 分析结果"""
    summary: str = ""
    trend_analysis: str = ""
    technical_insight: str = ""
    risk_warning: str = ""
    operation_advice: str = ""
    score_adjustment: float = 0.0
    key_levels: Dict[str, float] = field(default_factory=dict)


class LLMInterpreter:
    """LLM 分析解读器"""

    def __init__(self, client: Optional[LLMClient] = None):
        self.client = client or create_llm_client()

    async def interpret_technical(self, result: AnalysisResult) -> Optional[LLMAnalysis]:
        """AI 解读技术指标"""
        if not self.client:
            logger.warning("LLM 客户端未配置，跳过 AI 解读")
            return None

        indicators = result.indicators
        tech_data = (
            f"股票: {result.name}({result.code})\n"
            f"价格: {result.current_price:.2f}\n"
            f"涨跌: {result.change_pct:+.2f}%\n"
            f"趋势: {result.trend}\n"
            f"信号: {result.signal}\n"
            f"评分: {result.score:.0f}/100\n"
            f"MA5={indicators.ma5:.2f}, MA10={indicators.ma10:.2f}, MA20={indicators.ma20:.2f}\n"
            f"MACD={indicators.macd:.2f}, Hist={indicators.macd_hist:.2f}\n"
            f"RSI6={indicators.rsi_6:.1f}, RSI14={indicators.rsi_14:.1f}\n"
            f"KDJ=({indicators.kdj_k:.1f},{indicators.kdj_d:.1f},{indicators.kdj_j:.1f})\n"
            f"BOLL UP={indicators.boll_up:.2f} MID={indicators.boll_mid:.2f} LOW={indicators.boll_low:.2f}\n"
            f"BIAS5={indicators.bias_5:.2f}%\n"
            f"ATR={indicators.atr:.2f}\n"
            f"支撑={result.support:.2f} 压力={result.resistance:.2f}"
        )

        try:
            response = await self.client.chat([
                {"role": "system", "content": _LLM_ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": tech_data},
            ])
            return self._parse_llm_response(response)
        except Exception as e:
            logger.error("LLM 技术解读失败: %s", e)
            return None

    async def analyze_news(self, news_text: str) -> Optional[Dict[str, Any]]:
        """AI 分析新闻情绪"""
        if not self.client:
            return None

        try:
            response = await self.client.chat([
                {"role": "system", "content": _NEWS_ANALYSIS_PROMPT},
                {"role": "user", "content": news_text[:3000]},
            ])
            return json.loads(response)
        except Exception as e:
            logger.error("新闻分析失败: %s", e)
            return None

    async def analyze_market(self, market_data: str) -> Optional[Dict[str, Any]]:
        """AI 分析大盘"""
        if not self.client:
            return None

        try:
            response = await self.client.chat([
                {"role": "system", "content": _MARKET_REVIEW_PROMPT},
                {"role": "user", "content": market_data[:3000]},
            ])
            return json.loads(response)
        except Exception as e:
            logger.error("大盘分析失败: %s", e)
            return None

    def _parse_llm_response(self, response: str) -> Optional[LLMAnalysis]:
        """解析 LLM JSON 响应"""
        try:
            # 尝试提取 JSON
            start = response.find("{")
            end = response.rfind("}")
            if start >= 0 and end > start:
                json_str = response[start:end + 1]
                data = json.loads(json_str)
            else:
                data = json.loads(response)

            kl = data.get("key_levels", {})
            return LLMAnalysis(
                summary=data.get("summary", ""),
                trend_analysis=data.get("trend_analysis", ""),
                technical_insight=data.get("technical_insight", ""),
                risk_warning=data.get("risk_warning", ""),
                operation_advice=data.get("operation_advice", ""),
                score_adjustment=float(data.get("score_adjustment", 0)),
                key_levels={
                    "support": float(kl.get("support", 0)),
                    "resistance": float(kl.get("resistance", 0)),
                },
            )
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            logger.warning("LLM 响应解析失败: %s\n响应: %s", e, response[:200])
            return None
