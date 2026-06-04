"""持仓管理 - 组合盈亏、仓位建议"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.config import get_config
from src.services.stock_service import StockService

logger = logging.getLogger(__name__)

PORTFOLIO_FILE = "data/portfolio.json"


@dataclass
class Position:
    """持仓"""
    code: str
    name: str = ""
    quantity: int = 0  # 持股数量
    cost_price: float = 0.0  # 成本价
    current_price: float = 0.0
    market_value: float = 0.0  # 市值
    profit_pct: float = 0.0  # 收益率
    profit_amount: float = 0.0  # 盈亏金额
    weight: float = 0.0  # 仓位权重 %
    sector: str = ""


@dataclass
class Portfolio:
    """投资组合"""
    positions: List[Position] = field(default_factory=list)
    total_cost: float = 0.0
    total_market_value: float = 0.0
    total_profit: float = 0.0
    total_profit_pct: float = 0.0
    sector_allocation: Dict[str, float] = field(default_factory=dict)
    risk_score: float = 0.0  # 0-100
    suggestion: str = ""
    updated_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))


class PortfolioService:
    """持仓管理服务"""

    def __init__(self):
        self.config = get_config()
        self.stock_service = StockService(self.config)
        self._positions: Dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        """从文件加载持仓"""
        path = Path(PORTFOLIO_FILE)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self._positions = data.get("positions", {})
                logger.info("加载持仓数据: %d 只股票", len(self._positions))
            except Exception as e:
                logger.warning("加载持仓文件失败: %s", e)

    def save(self) -> None:
        """保存持仓到文件"""
        path = Path(PORTFOLIO_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {"positions": self._positions, "updated_at": datetime.now().isoformat()}
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("持仓已保存")

    def add_position(self, code: str, quantity: int, cost_price: float, name: str = "") -> None:
        """添加或更新持仓"""
        if code in self._positions:
            existing = self._positions[code]
            total_qty = existing["quantity"] + quantity
            existing["cost_price"] = (existing["cost_price"] * existing["quantity"] + cost_price * quantity) / total_qty
            existing["quantity"] = total_qty
        else:
            self._positions[code] = {
                "code": code, "name": name,
                "quantity": quantity, "cost_price": cost_price,
            }
        self.save()

    def remove_position(self, code: str, quantity: Optional[int] = None) -> None:
        """减仓或清仓"""
        if code not in self._positions:
            return
        if quantity is None or quantity >= self._positions[code]["quantity"]:
            del self._positions[code]
        else:
            self._positions[code]["quantity"] -= quantity
        self.save()

    async def get_portfolio(self) -> Portfolio:
        """获取当前持仓状态"""
        portfolio = Portfolio()
        total_value = 0.0
        total_cost = 0.0

        for code, pos in self._positions.items():
            try:
                quote = await self.stock_service.get_realtime_quote(code)
                info = await self.stock_service.get_stock_info(code)
                current_price = quote.price if quote else pos["cost_price"]
                name = info.name if info else pos.get("name", code)
            except Exception:
                current_price = pos["cost_price"]
                name = pos.get("name", code)

            quantity = pos["quantity"]
            cost = pos["cost_price"]
            market_value = current_price * quantity
            cost_total = cost * quantity
            profit_amount = market_value - cost_total
            profit_pct = ((current_price - cost) / cost * 100) if cost > 0 else 0.0

            position = Position(
                code=code, name=name,
                quantity=quantity, cost_price=cost,
                current_price=current_price,
                market_value=market_value,
                profit_pct=profit_pct,
                profit_amount=profit_amount,
            )
            portfolio.positions.append(position)
            total_value += market_value
            total_cost += cost_total

        # 计算权重
        for p in portfolio.positions:
            p.weight = (p.market_value / total_value * 100) if total_value > 0 else 0.0

        # 汇总
        portfolio.total_cost = total_cost
        portfolio.total_market_value = total_value
        portfolio.total_profit = total_value - total_cost
        portfolio.total_profit_pct = ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0.0

        # 行业分布
        for p in portfolio.positions:
            portfolio.sector_allocation[p.sector or "未知"] = (
                portfolio.sector_allocation.get(p.sector or "未知", 0) + p.weight
            )

        # 风险评估 + 建议
        portfolio.risk_score = self._calc_risk(portfolio)
        portfolio.suggestion = self._generate_suggestion(portfolio)

        return portfolio

    def _calc_risk(self, portfolio: Portfolio) -> float:
        """计算组合风险 0-100"""
        score = 0.0
        n = len(portfolio.positions)

        # 集中度风险: 单只 > 30% 权重
        max_weight = max((p.weight for p in portfolio.positions), default=0)
        if max_weight > 30:
            score += 30
        elif max_weight > 20:
            score += 15

        # 数量风险
        if n <= 2:
            score += 20
        elif n <= 4:
            score += 10

        # 盈亏风险
        if portfolio.total_profit_pct < -10:
            score += 30
        elif portfolio.total_profit_pct < -5:
            score += 15

        # 行业集中度
        sectors = len(portfolio.sector_allocation)
        if sectors <= 2:
            score += 20
        elif sectors <= 4:
            score += 10

        return min(100, score)

    def _generate_suggestion(self, portfolio: Portfolio) -> str:
        """生成仓位建议"""
        suggestions = []
        n = len(portfolio.positions)
        max_weight = max((p.weight for p in portfolio.positions), default=0)

        if n <= 3:
            suggestions.append("持仓集中度较高，建议适当分散至 5-8 只股票")
        if max_weight > 30:
            suggestions.append(f"单只权重 {max_weight:.0f}%，建议单只不超过 20%")
        if portfolio.total_profit_pct < -5:
            suggestions.append("组合出现亏损，建议审视止损策略")
        if portfolio.total_profit_pct > 20:
            suggestions.append("组合收益较好，可考虑部分止盈")
        if portfolio.risk_score > 60:
            suggestions.append("风险偏高，建议降低仓位或增加防御性配置")

        return "；".join(suggestions) if suggestions else "组合配置合理，继续持有"
