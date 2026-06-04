"""测试持仓管理"""
import json
import tempfile
from pathlib import Path

import pytest

from src.services.portfolio_service import PortfolioService, Portfolio, Position


def test_portfolio_dataclass():
    """测试持仓数据结构"""
    p = Portfolio()
    assert p.total_cost == 0
    assert p.total_market_value == 0
    assert p.total_profit == 0
    assert p.risk_score == 0.0

    pos = Position(code="600519", name="贵州茅台", quantity=100, cost_price=150.0)
    assert pos.code == "600519"
    assert pos.market_value == 0  # 尚未计算


def test_portfolio_risk_calculation():
    """测试风险评分"""
    service = PortfolioService()
    portfolio = Portfolio()

    # 单只股票 + 集中度高 = 高风险
    portfolio.positions = [
        Position(code="600519", name="A", quantity=100, cost_price=10, current_price=12, weight=50),
    ]
    risk = service._calc_risk(portfolio)
    assert risk > 50

    # 多只分散 = 低风险
    portfolio.positions = [
        Position(code="600519", name="A", quantity=100, cost_price=10, current_price=12, weight=15),
        Position(code="000001", name="B", quantity=200, cost_price=8, current_price=9, weight=15),
        Position(code="300750", name="C", quantity=300, cost_price=20, current_price=22, weight=20),
        Position(code="002594", name="D", quantity=400, cost_price=30, current_price=32, weight=20),
        Position(code="601318", name="E", quantity=500, cost_price=40, current_price=42, weight=15),
        Position(code="000858", name="F", quantity=600, cost_price=50, current_price=52, weight=15),
    ]
    risk2 = service._calc_risk(portfolio)
    assert risk2 < risk
