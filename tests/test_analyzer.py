"""测试股票分析器"""
import pytest
import pandas as pd
import numpy as np
from src.stock_analyzer import StockAnalyzer, KLine


def _make_klines(count: int = 120, base_price: float = 50.0, trend: str = "up") -> list:
    """Generate kline data with deterministic patterns"""
    import math
    klines = []
    price = base_price
    for i in range(count):
        angle = i * 0.05
        if trend == "up":
            change = 0.3 + math.sin(angle) * 0.5
        elif trend == "down":
            change = -0.3 + math.sin(angle) * 0.5
        else:
            change = math.sin(angle) * 0.8
        price *= (1 + change / 100)
        klines.append(KLine(
            date=f"2024-{(i // 30) + 1:02d}-{(i % 28) + 1:02d}",
            open=float(price * 0.99),
            high=float(price * 1.02),
            low=float(price * 0.98),
            close=float(price),
            volume=float(3000000 + i * 10000),
            change_pct=float(change),
        ))
    return klines


def test_analyzer_returns_result():
    """测试分析器返回结构"""
    analyzer = StockAnalyzer()
    klines = _make_klines()
    result = analyzer.analyze(klines, name="测试股票")
    assert result.code == ""
    assert result.name == "测试股票"
    assert result.current_price > 0
    assert 0 <= result.score <= 100
    assert result.trend in ("多头上涨", "空头下跌", "震荡整理", "高位回调", "底部反弹")
    assert result.signal in ("买入", "卖出", "持有", "观望")
    assert result.indicators.ma5 > 0
    assert result.indicators.rsi_14 > 0


def test_analyzer_up_trend():
    """测试上涨趋势"""
    analyzer = StockAnalyzer()
    klines = _make_klines(trend="up")
    result = analyzer.analyze(klines)
    assert result.score >= 50  # 上涨趋势评分应该较高


def test_analyzer_down_trend():
    """测试下跌趋势"""
    analyzer = StockAnalyzer()
    klines = _make_klines(trend="down")
    result = analyzer.analyze(klines)
    assert result.score <= 70  # 下跌趋势评分应该较低


def test_analyzer_empty_klines():
    """测试空数据"""
    analyzer = StockAnalyzer()
    result = analyzer.analyze([])
    assert result.score == 0
    assert result.current_price == 0


def test_technical_indicators_rsi():
    """测试 RSI 计算"""
    analyzer = StockAnalyzer()
    prices = np.array([50, 51, 52, 53, 52, 51, 50, 49, 48, 49, 50, 51, 52, 53, 54])
    rsi = analyzer._calc_rsi(prices, 14)
    assert 0 <= rsi <= 100
