"""股票技术分析器"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from src.data_provider.base import KLine

logger = logging.getLogger(__name__)


@dataclass
class TechnicalIndicators:
    """技术指标"""
    ma5: float = 0.0
    ma10: float = 0.0
    ma20: float = 0.0
    ma60: float = 0.0
    ma120: float = 0.0
    volume_ma5: float = 0.0
    volume_ma10: float = 0.0
    rsi_6: float = 0.0
    rsi_14: float = 0.0
    macd: float = 0.0
    macd_signal: float = 0.0
    macd_hist: float = 0.0
    kdj_k: float = 0.0
    kdj_d: float = 0.0
    kdj_j: float = 0.0
    boll_up: float = 0.0
    boll_mid: float = 0.0
    boll_low: float = 0.0
    atr: float = 0.0
    bias_5: float = 0.0  # 乖离率5
    bias_10: float = 0.0


@dataclass
class AnalysisResult:
    """分析结果"""
    code: str
    name: str = ""
    current_price: float = 0.0
    change_pct: float = 0.0
    indicators: TechnicalIndicators = field(default_factory=TechnicalIndicators)
    trend: str = ""  # 趋势判断
    signal: str = ""  # 信号
    score: float = 0.0  # 综合评分 0-100
    risk_level: str = ""  # 风险等级
    support: float = 0.0  # 支撑位
    resistance: float = 0.0  # 压力位
    suggestion: str = ""  # 操作建议
    reasons: List[str] = field(default_factory=list)  # 理由


class StockAnalyzer:
    """股票技术分析器"""

    def analyze(self, klines: List[KLine], name: str = "") -> AnalysisResult:
        """分析单只股票"""
        if not klines:
            return AnalysisResult(code="", name=name)

        df = self._kline_to_df(klines)
        code = klines[-1].code if klines else ""
        indicators = self._compute_indicators(df)
        current_price = float(df["close"].iloc[-1])
        change_pct = float(df["change_pct"].iloc[-1]) if "change_pct" in df.columns else 0.0

        trend = self._judge_trend(df, indicators)
        signal = self._judge_signal(df, indicators, trend)
        score = self._compute_score(df, indicators, trend)
        risk = self._judge_risk(indicators, score)
        support, resistance = self._find_support_resistance(df, indicators)
        suggestion = self._generate_suggestion(signal, score, risk)
        reasons = self._generate_reasons(df, indicators, trend, signal)

        return AnalysisResult(
            code=code,
            name=name,
            current_price=current_price,
            change_pct=change_pct,
            indicators=indicators,
            trend=trend,
            signal=signal,
            score=score,
            risk_level=risk,
            support=support,
            resistance=resistance,
            suggestion=suggestion,
            reasons=reasons,
        )

    def _kline_to_df(self, klines: List[KLine]) -> pd.DataFrame:
        data = {
            "close": [k.close for k in klines],
            "high": [k.high for k in klines],
            "low": [k.low for k in klines],
            "open": [k.open for k in klines],
            "volume": [k.volume for k in klines],
            "amount": [k.amount for k in klines],
            "change_pct": [k.change_pct for k in klines],
        }
        return pd.DataFrame(data)

    def _compute_indicators(self, df: pd.DataFrame) -> TechnicalIndicators:
        ind = TechnicalIndicators()
        closes = df["close"].values
        highs = df["high"].values
        lows = df["low"].values
        volumes = df["volume"].values
        n = len(closes)

        if n >= 5:
            ind.ma5 = float(np.mean(closes[-5:]))
            ind.volume_ma5 = float(np.mean(volumes[-5:]))
        if n >= 10:
            ind.ma10 = float(np.mean(closes[-10:]))
            ind.volume_ma10 = float(np.mean(volumes[-10:]))
        if n >= 20:
            ind.ma20 = float(np.mean(closes[-20:]))
        if n >= 60:
            ind.ma60 = float(np.mean(closes[-60:]))
        if n >= 120:
            ind.ma120 = float(np.mean(closes[-120:]))

        # RSI
        if n >= 15:
            ind.rsi_6 = self._calc_rsi(closes, 6)
            ind.rsi_14 = self._calc_rsi(closes, 14)

        # MACD
        ema12 = self._ema(closes, 12)
        ema26 = self._ema(closes, 26)
        diffs = [e12 - e26 for e12, e26 in zip(ema12, ema26)]
        dea = self._ema(diffs, 9) if len(diffs) >= 9 else diffs
        ind.macd = diffs[-1] if diffs else 0
        ind.macd_signal = dea[-1] if dea else 0
        ind.macd_hist = ind.macd - ind.macd_signal

        # KDJ
        if n >= 9:
            rsv = (closes[-1] - np.min(lows[-9:])) / (np.max(highs[-9:]) - np.min(lows[-9:])) * 100
            ind.kdj_k = float(50 * 2 / 3 + rsv * 1 / 3)
            ind.kdj_d = float(50 * 2 / 3 + ind.kdj_k * 1 / 3)
            ind.kdj_j = float(3 * ind.kdj_k - 2 * ind.kdj_d)

        # BOLL
        if n >= 20:
            mid = np.mean(closes[-20:])
            std = np.std(closes[-20:])
            ind.boll_mid = float(mid)
            ind.boll_up = float(mid + 2 * std)
            ind.boll_low = float(mid - 2 * std)

        # ATR
        if n >= 14:
            tr_values = []
            for i in range(1, 14):
                tr = max(highs[-i] - lows[-i], abs(highs[-i] - closes[-i - 1]), abs(lows[-i] - closes[-i - 1]))
                tr_values.append(tr)
            ind.atr = float(np.mean(tr_values))

        # 乖离率
        if ind.ma5 > 0:
            ind.bias_5 = (closes[-1] - ind.ma5) / ind.ma5 * 100
        if ind.ma10 > 0:
            ind.bias_10 = (closes[-1] - ind.ma10) / ind.ma10 * 100

        return ind

    def _calc_rsi(self, prices: np.ndarray, period: int) -> float:
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains[-period:]) if len(gains) >= period else 0
        avg_loss = np.mean(losses[-period:]) if len(losses) >= period and np.mean(losses[-period:]) > 0 else 1e-10
        rs = avg_gain / avg_loss
        return float(100 - (100 / (1 + rs)))

    def _ema(self, data: List[float], period: int) -> List[float]:
        if len(data) == 0:
            return []
        result = [data[0]]
        multiplier = 2 / (period + 1)
        for val in data[1:]:
            result.append((val - result[-1]) * multiplier + result[-1])
        return result

    def _judge_trend(self, df: pd.DataFrame, ind: TechnicalIndicators) -> str:
        """判断趋势"""
        close = df["close"].values[-1]
        # 多头排列：MA5 > MA10 > MA20
        if ind.ma5 > ind.ma10 > ind.ma20 and close > ind.ma5:
            return "多头上涨"
        # 空头排列：MA5 < MA10 < MA20
        if ind.ma5 < ind.ma10 < ind.ma20 and close < ind.ma5:
            return "空头下跌"
        # 震荡
        if ind.ma5 > ind.ma20 and close < ind.ma5:
            return "高位回调"
        if ind.ma5 < ind.ma20 and close > ind.ma5:
            return "底部反弹"
        return "震荡整理"

    def _judge_signal(self, df: pd.DataFrame, ind: TechnicalIndicators, trend: str) -> str:
        """判断买卖信号"""
        signals = []

        # MACD 金叉/死叉
        if ind.macd_hist > 0 and abs(ind.macd_hist) > 0.1:
            signals.append("MACD多头")
        elif ind.macd_hist < 0 and abs(ind.macd_hist) > 0.1:
            signals.append("MACD空头")

        # KDJ
        if ind.kdj_k > 80 and ind.kdj_d > 80:
            signals.append("KDJ超买")
        elif ind.kdj_k < 20 and ind.kdj_d < 20:
            signals.append("KDJ超卖")

        # RSI
        if ind.rsi_14 > 70:
            signals.append("RSI超买")
        elif ind.rsi_14 < 30:
            signals.append("RSI超卖")

        # 乖离率
        if ind.bias_5 > 5:
            signals.append("偏离过大")
        elif ind.bias_5 < -5:
            signals.append("偏离过负")

        # 综合判断
        buy_count = sum(1 for s in signals if "超卖" in s or "多头" in s or "过负" in s)
        sell_count = sum(1 for s in signals if "超买" in s or "空头" in s or "过大" in s)

        if buy_count >= 2:
            return "买入"
        if sell_count >= 2:
            return "卖出"
        if "多头" in trend:
            return "持有"
        return "观望"

    def _compute_score(self, df: pd.DataFrame, ind: TechnicalIndicators, trend: str) -> float:
        """综合评分 0-100"""
        score = 50.0

        # 趋势加分
        if "多头" in trend:
            score += 15
        elif "空头" in trend:
            score -= 15

        # RSI 评分
        if 40 <= ind.rsi_14 <= 60:
            score += 5
        elif ind.rsi_14 < 30:
            score += 10  # 超卖反弹机会
        elif ind.rsi_14 > 70:
            score -= 10

        # MACD
        if ind.macd_hist > 0:
            score += 5
        else:
            score -= 5

        # 均线排列
        if ind.ma5 > ind.ma10 > ind.ma20:
            score += 10
        elif ind.ma5 < ind.ma10 < ind.ma20:
            score -= 10

        # 量能
        if ind.volume_ma5 > 0 and ind.volume_ma5 >= ind.volume_ma10 * 1.2:
            score += 5
        elif ind.volume_ma5 > 0 and ind.volume_ma5 <= ind.volume_ma10 * 0.8:
            score -= 5

        return max(0, min(100, score))

    def _judge_risk(self, ind: TechnicalIndicators, score: float) -> str:
        if score >= 75:
            return "低风险"
        if score >= 50:
            return "中等风险"
        return "高风险"

    def _find_support_resistance(self, df: pd.DataFrame, ind: TechnicalIndicators) -> Tuple[float, float]:
        close = df["close"].values[-1]
        support = min(ind.ma5, ind.ma10, ind.ma20) if ind.ma20 > 0 else close * 0.95
        resistance = max(ind.ma5, ind.ma10, ind.ma20) if ind.ma20 > 0 else close * 1.05
        return float(support), float(resistance)

    def _generate_suggestion(self, signal: str, score: float, risk: str) -> str:
        if signal == "买入" and score >= 60:
            return "建议买入"
        if signal == "卖出" or score < 30:
            return "建议卖出"
        if signal == "持有":
            return "建议持有"
        return "建议观望"

    def _generate_reasons(self, df: pd.DataFrame, ind: TechnicalIndicators, trend: str, signal: str) -> List[str]:
        reasons = []
        reasons.append(f"趋势: {trend}")
        reasons.append(f"信号: {signal}")
        reasons.append(f"MA5={ind.ma5:.2f} MA10={ind.ma10:.2f} MA20={ind.ma20:.2f}")
        reasons.append(f"RSI14={ind.rsi_14:.1f} MACD={ind.macd:.2f}")
        reasons.append(f"KDJ=({ind.kdj_k:.1f},{ind.kdj_d:.1f},{ind.kdj_j:.1f})")
        reasons.append(f"乖离率(5)={ind.bias_5:.2f}%")
        return reasons
