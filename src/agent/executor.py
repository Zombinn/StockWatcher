"""Agent 执行器 - 多轮对话策略分析"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.llm.client import LLMClient, create_llm_client
from src.services.analysis_service import AnalysisService
from src.services.stock_service import StockService
from src.stock_analyzer import AnalysisResult

logger = logging.getLogger(__name__)

# 策略定义
STRATEGIES = {
    "均线": "基于 MA5/MA10/MA20 多头排列分析趋势",
    "缠论": "分析笔、段、中枢的缠论技术形态",
    "波浪": "基于艾略特波浪理论的浪型识别",
    "趋势": "判断上升/下降/震荡趋势及持续性",
    "热点": "分析所属板块热度和资金关注度",
    "事件": "基于近期公告、新闻的事件驱动分析",
    "成长": "分析营收、利润增长的成长性评估",
    "预期": "基于市场预期的估值分析",
    "技术": "综合 MACD/RSI/KDJ/BOLL 技术指标",
    "资金": "分析主力资金流向和筹码分布",
}

_AGENT_SYSTEM_PROMPT = """你是一位资深股票投资顾问。请根据用户的问题和提供的技术数据，给出专业的分析和建议。

分析风格：
- 专业、客观、条理清晰
- 既看到机会也提示风险
- 给出具体的操作建议而非模糊说辞
- 使用中文回复

你可以分析的维度：技术指标、趋势形态、量价关系、市场情绪、基本面、资金面。

回复格式：请用 Markdown 格式回复，包含明确的分析结论。"""


@dataclass
class AgentMessage:
    """智能体对话消息"""
    role: str  # user / assistant / system
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentSession:
    """智能体对话会话"""
    session_id: str
    stock_code: str = ""
    stock_name: str = ""
    messages: List[AgentMessage] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class StockAgent:
    """股票分析智能体"""

    def __init__(self):
        self.llm_client = create_llm_client()
        self.analysis_service = AnalysisService()
        self.stock_service = StockService(self.analysis_service.config)
        self._sessions: Dict[str, AgentSession] = {}

    async def create_session(self, code: str, name: str = "") -> str:
        """创建新的分析会话"""
        session_id = f"agent_{code}_{datetime.now().timestamp():.0f}"

        # 获取基础分析数据作为上下文
        result = await self.analysis_service.analyze_single(code)
        info = await self.stock_service.get_stock_info(code)
        name = name or (info.name if info else code)

        context = {}
        if result:
            ind = result.indicators
            context["analysis"] = {
                "price": result.current_price,
                "change": result.change_pct,
                "trend": result.trend,
                "signal": result.signal,
                "score": result.score,
                "indicators": {
                    "ma5": ind.ma5, "ma10": ind.ma10, "ma20": ind.ma20,
                    "macd_hist": ind.macd_hist, "rsi_14": ind.rsi_14,
                    "kdj_k": ind.kdj_k, "kdj_d": ind.kdj_d, "kdj_j": ind.kdj_j,
                    "boll_up": ind.boll_up, "boll_low": ind.boll_low,
                    "bias_5": ind.bias_5,
                },
                "support": result.support,
                "resistance": result.resistance,
            }

        session = AgentSession(
            session_id=session_id,
            stock_code=code,
            stock_name=name,
            context=context,
        )
        self._sessions[session_id] = session
        return session_id

    async def chat(self, session_id: str, message: str, strategy: str = "") -> str:
        """发送消息并获取回复"""
        session = self._sessions.get(session_id)
        if not session:
            return "会话不存在，请先创建分析会话。"

        session.messages.append(AgentMessage(role="user", content=message))
        session.updated_at = datetime.now().isoformat()

        if not self.llm_client:
            return self._fallback_reply(session, message, strategy)

        # 构建上下文
        context_text = self._build_context(session, strategy)
        system_prompt = _AGENT_SYSTEM_PROMPT + "\n\n## 当前股票数据\n" + context_text

        messages = [{"role": "system", "content": system_prompt}]
        for msg in session.messages[-10:]:  # 最近 10 轮
            messages.append({"role": msg.role, "content": msg.content})

        try:
            response = await self.llm_client.chat(messages, temperature=0.3)
            session.messages.append(AgentMessage(role="assistant", content=response))
            return response
        except Exception as e:
            logger.error("Agent 回答失败: %s", e)
            return self._fallback_reply(session, message, strategy)

    def _build_context(self, session: AgentSession, strategy: str = "") -> str:
        """构建策略上下文"""
        ctx = session.context
        analysis = ctx.get("analysis", {})
        ind = analysis.get("indicators", {})
        lines = [
            f"股票: {session.stock_name} ({session.stock_code})",
            f"当前价格: {analysis.get('price', 'N/A')}",
            f"涨跌幅: {analysis.get('change', 'N/A'):+.2f}%" if analysis.get('change') else "",
            f"趋势: {analysis.get('trend', '未知')}",
            f"信号: {analysis.get('signal', '未知')}",
            f"综合评分: {analysis.get('score', 'N/A')}/100",
            "",
            "技术指标:",
            f"MA5={ind.get('ma5', 'N/A')} MA10={ind.get('ma10', 'N/A')} MA20={ind.get('ma20', 'N/A')}",
            f"MACD柱={ind.get('macd_hist', 'N/A')}",
            f"RSI14={ind.get('rsi_14', 'N/A')}",
            f"KDJ=({ind.get('kdj_k', 'N/A')},{ind.get('kdj_d', 'N/A')},{ind.get('kdj_j', 'N/A')})",
            f"BOLL上轨={ind.get('boll_up', 'N/A')} 下轨={ind.get('boll_low', 'N/A')}",
            f"乖离率={ind.get('bias_5', 'N/A')}%",
            f"支撑={analysis.get('support', 'N/A')} 压力={analysis.get('resistance', 'N/A')}",
        ]

        if strategy and strategy in STRATEGIES:
            lines.append(f"\n分析策略: {strategy} - {STRATEGIES[strategy]}")

        return "\n".join(lines)

    def _fallback_reply(self, session: AgentSession, message: str, strategy: str = "") -> str:
        """无 LLM 时的模板化回复"""
        ctx = session.context.get("analysis", {})
        ind = ctx.get("indicators", {})
        price = ctx.get("price", "N/A")
        trend = ctx.get("trend", "未知")
        signal = ctx.get("signal", "未知")
        score = ctx.get("score", "N/A")

        score_level = "高" if isinstance(score, (int, float)) and score >= 70 else "中" if isinstance(score, (int, float)) and score >= 40 else "低"
        rsi = ind.get("rsi_14", 50)
        rsi_note = "超买区" if rsi >= 70 else "超卖区" if rsi <= 30 else "中性区域"
        macd = ind.get("macd_hist", 0)
        macd_note = "多头动能" if macd > 0 else "空头动能"

        lines = [
            f"## 📊 {session.stock_name} ({session.stock_code}) 分析",
            "",
            f"**当前价格**: {price}",
            f"**趋势**: {trend}",
            f"**技术信号**: {signal}",
            f"**综合评分**: {score}/100（{score_level}）",
            "",
            "### 关键指标",
            f"- RSI(14) = {rsi}（{rsi_note}）",
            f"- MACD柱 = {macd}（{macd_note}）",
            f"- MA5 = {ind.get('ma5', 'N/A')} / MA10 = {ind.get('ma10', 'N/A')} / MA20 = {ind.get('ma20', 'N/A')}",
            f"- KDJ = ({ind.get('kdj_k', 'N/A')}, {ind.get('kdj_d', 'N/A')}, {ind.get('kdj_j', 'N/A')})",
            f"- BOLL 上轨 = {ind.get('boll_up', 'N/A')} / 下轨 = {ind.get('boll_low', 'N/A')}",
            f"- 支撑位 = {ctx.get('support', 'N/A')} / 压力位 = {ctx.get('resistance', 'N/A')}",
            "",
            "### 建议",
            "> 以上为技术面数据分析。如需更深入的 LLM 解读，请在 `.env` 中配置 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL`。",
        ]
        return "\n".join(lines)

    def get_session(self, session_id: str) -> Optional[AgentSession]:
        return self._sessions.get(session_id)

    def get_strategies(self) -> Dict[str, str]:
        return dict(STRATEGIES)
