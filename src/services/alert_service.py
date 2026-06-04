"""告警引擎 - 价格/指标触发告警"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src.config import get_config
from src.services.stock_service import StockService

logger = logging.getLogger(__name__)

ALERT_FILE = "data/alerts.json"


@dataclass
class AlertRule:
    """告警规则"""
    id: str = ""
    code: str = ""
    name: str = ""
    rule_type: str = ""  # price_above, price_below, change_pct, volume, rsi, macd
    threshold: float = 0.0
    enabled: bool = True
    last_triggered: Optional[str] = None
    cooldown_minutes: int = 60
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AlertEvent:
    """告警事件"""
    rule_id: str
    code: str
    name: str
    rule_type: str
    message: str
    current_value: float
    threshold: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notified: bool = False


class AlertEngine:
    """告警引擎"""

    def __init__(self):
        self.config = get_config()
        self.stock_service = StockService(self.config)
        self._rules: List[AlertRule] = []
        self._events: List[AlertEvent] = []
        self._load()

    def _load(self) -> None:
        path = Path(ALERT_FILE)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self._rules = [AlertRule(**r) for r in data.get("rules", [])]
                self._events = [AlertEvent(**e) for e in data.get("events", [])]
                logger.info("加载告警规则: %d 条, 事件: %d 条", len(self._rules), len(self._events))
            except Exception as e:
                logger.warning("加载告警文件失败: %s", e)

    def _save(self) -> None:
        path = Path(ALERT_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "rules": [r.__dict__ for r in self._rules],
            "events": [e.__dict__ for e in self._events],
            "updated_at": datetime.now().isoformat(),
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_rule(self, code: str, rule_type: str, threshold: float, name: str = "") -> str:
        """添加告警规则"""
        rule = AlertRule(
            id=f"{code}_{rule_type}_{datetime.now().timestamp():.0f}",
            code=code, name=name,
            rule_type=rule_type, threshold=threshold,
        )
        self._rules.append(rule)
        self._save()
        logger.info("添加告警规则: %s %s %s > %s", code, rule_type, threshold)
        return rule.id

    def remove_rule(self, rule_id: str) -> bool:
        """删除告警规则"""
        for r in self._rules:
            if r.id == rule_id:
                self._rules.remove(r)
                self._save()
                return True
        return False

    def get_rules(self, code: Optional[str] = None) -> List[AlertRule]:
        """获取告警规则列表"""
        if code:
            return [r for r in self._rules if r.code == code and r.enabled]
        return [r for r in self._rules if r.enabled]

    async def check(self, on_trigger: Optional[Callable[[AlertEvent], None]] = None) -> List[AlertEvent]:
        """检查所有规则并触发告警"""
        triggered = []
        now = datetime.now()

        for rule in self.get_rules():
            try:
                # 冷却检查
                if rule.last_triggered:
                    last = datetime.fromisoformat(rule.last_triggered)
                    elapsed = (now - last).total_seconds() / 60
                    if elapsed < rule.cooldown_minutes:
                        continue

                quote = await self.stock_service.get_realtime_quote(rule.code)
                if not quote:
                    continue

                triggered_flag, current_val, msg = self._evaluate(rule, quote)
                if triggered_flag:
                    event = AlertEvent(
                        rule_id=rule.id, code=rule.code,
                        name=rule.name or quote.name,
                        rule_type=rule.rule_type,
                        message=msg,
                        current_value=current_val,
                        threshold=rule.threshold,
                    )
                    self._events.append(event)
                    triggered.append(event)
                    rule.last_triggered = now.isoformat()

                    if on_trigger:
                        on_trigger(event)

            except Exception as e:
                logger.warning("检查告警规则 %s 失败: %s", rule.id, e)

        if triggered:
            self._save()

        return triggered

    def _evaluate(self, rule: AlertRule, quote) -> tuple[bool, float, str]:
        """评估单条规则"""
        value_map = {
            "price_above": ("价格上穿", quote.price, rule.threshold),
            "price_below": ("价格下穿", quote.price, rule.threshold),
            "change_pct": ("涨跌幅", abs(quote.change_pct), rule.threshold),
            "volume": ("成交量", quote.volume / 1e4, rule.threshold),  # 万股
        }

        label, current, threshold = value_map.get(rule.rule_type, ("", 0.0, 0.0))
        triggered = False

        if rule.rule_type == "price_above" and current >= threshold:
            triggered = True
        elif rule.rule_type == "price_below" and current <= threshold:
            triggered = True
        elif rule.rule_type == "change_pct" and current >= threshold:
            triggered = True
        elif rule.rule_type == "volume" and current >= threshold:
            triggered = True

        msg = f"[{rule.name or rule.code}] {label}触发: 当前{current:.2f} 阈值{threshold:.2f}" if triggered else ""
        return triggered, current, msg

    def get_recent_events(self, limit: int = 20) -> List[AlertEvent]:
        """获取最近告警事件"""
        events = sorted(self._events, key=lambda e: e.timestamp, reverse=True)
        return events[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """获取告警统计"""
        return {
            "total_rules": len(self._rules),
            "enabled_rules": len([r for r in self._rules if r.enabled]),
            "total_events": len(self._events),
            "recent_events": len([e for e in self._events if not e.notified]),
        }
