"""报告格式化"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List

from src.stock_analyzer import AnalysisResult

logger = logging.getLogger(__name__)


def format_analysis_report(results: Dict[str, AnalysisResult], market_summary: str = "") -> str:
    """格式化分析报告为 Markdown"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# 📊 StockWatcher 智能分析报告",
        f"**生成时间**: {now}",
        "",
    ]

    if market_summary:
        lines.extend(["## 📈 大盘概况", market_summary, ""])

    lines.extend(["## 📋 个股分析", ""])

    for code, result in results.items():
        lines.extend(_format_single_stock(result))
        lines.append("")

    lines.append("---")
    lines.append("*免责声明：以上分析仅供参考，不构成投资建议*")
    return "\n".join(lines)


def _format_single_stock(result: AnalysisResult) -> List[str]:
    """格式化单只股票"""
    lines = [
        f"### {result.name} ({result.code})",
        f"**价格**: {result.current_price:.2f} | **涨跌**: {result.change_pct:+.2f}%",
        f"**评分**: {result.score:.0f}/100 | **趋势**: {result.trend} | **信号**: {result.signal}",
        f"**风险**: {result.risk_level} | **建议**: {result.suggestion}",
        "",
        "#### 技术指标",
        f"- MA: MA5={result.indicators.ma5:.2f} MA10={result.indicators.ma10:.2f} MA20={result.indicators.ma20:.2f}",
        f"- MACD: {result.indicators.macd:.2f} (Signal={result.indicators.macd_signal:.2f}, Hist={result.indicators.macd_hist:.2f})",
        f"- RSI: RSI6={result.indicators.rsi_6:.1f} RSI14={result.indicators.rsi_14:.1f}",
        f"- KDJ: K={result.indicators.kdj_k:.1f} D={result.indicators.kdj_d:.1f} J={result.indicators.kdj_j:.1f}",
        f"- BOLL: UP={result.indicators.boll_up:.2f} MID={result.indicators.boll_mid:.2f} LOW={result.indicators.boll_low:.2f}",
        f"- 乖离率: BIAS5={result.indicators.bias_5:.2f}% BIAS10={result.indicators.bias_10:.2f}%",
        f"- 支撑: {result.support:.2f} | 压力: {result.resistance:.2f}",
        "",
        "#### 分析理由",
    ]
    for reason in result.reasons:
        lines.append(f"- {reason}")
    return lines


def format_short_notification(result: AnalysisResult) -> str:
    """格式化简短推送通知"""
    emoji = {"买入": "🟢", "卖出": "🔴", "持有": "🟡", "观望": "⚪"}
    signal_emoji = emoji.get(result.signal, "⚪")
    return (
        f"{signal_emoji} {result.name}({result.code})\n"
        f"价格: {result.current_price:.2f} | 涨跌: {result.change_pct:+.2f}%\n"
        f"评分: {result.score:.0f}/100 | 趋势: {result.trend}\n"
        f"建议: {result.suggestion} | 风险: {result.risk_level}\n"
        f"支撑: {result.support:.2f} | 压力: {result.resistance:.2f}"
    )
