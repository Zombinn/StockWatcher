"""测试回测引擎"""
import pytest
from src.core.backtest_engine import BacktestEngine, TradeRecord, BacktestResult


def test_backtest_result_dataclass():
    """测试回测结果结构"""
    r = BacktestResult(code="600519")
    assert r.code == "600519"
    assert r.initial_capital == 100000.0
    assert r.final_value == 100000.0
    assert r.total_return == 0.0
    assert r.total_trades == 0


def test_trade_record():
    """测试交易记录"""
    t = TradeRecord(date="2024-01-01", action="buy", price=150.0, shares=100, amount=15000.0, reason="测试")
    assert t.action == "buy"
    assert t.price == 150.0
    assert t.shares == 100


def test_backtest_strategies_exist():
    """测试回测引擎支持策略列表"""
    engine = BacktestEngine()
    assert hasattr(engine, "_strategy_ma_cross")
    assert hasattr(engine, "_strategy_macd")
    assert hasattr(engine, "_strategy_rsi")
    assert hasattr(engine, "_strategy_bollinger")
