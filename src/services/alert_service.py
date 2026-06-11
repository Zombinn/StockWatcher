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
    """告警规则（单股票一条记录，四个维度字段）"""
    id: str = ""
    code: str = ""
    name: str = ""
    price_above: Optional[float] = None
    price_below: Optional[float] = None
    change_pct: Optional[float] = None
    volume: Optional[float] = None
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

    def set_rule_dimension(self, code: str, rule_type: str, threshold: float, name: str = "") -> str:
        """设置股票某个维度的告警阈值（upsert，单股票一条记录）"""
        existing = next((r for r in self._rules if r.code == code), None)
        if existing:
            setattr(existing, rule_type, threshold)
            existing.name = name or existing.name
            logger.info("更新 %s %s=%s", code, rule_type, threshold)
        else:
            rule = AlertRule(id=code, code=code, name=name or code)
            setattr(rule, rule_type, threshold)
            self._rules.append(rule)
            logger.info("添加 %s %s=%s", code, rule_type, threshold)
        self._save()
        return code

    def remove_rule(self, rule_id: str) -> bool:
        """删除告警规则（按 code 删除整条记录）"""
        for r in list(self._rules):
            if r.code == rule_id or r.id == rule_id:
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

                triggered_flag, current_val, msg, trigger_type, trigger_threshold = self._evaluate(rule, quote)
                if triggered_flag:
                    event = AlertEvent(
                        rule_id=rule.id, code=rule.code,
                        name=rule.name or quote.name,
                        rule_type=trigger_type,
                        message=msg,
                        current_value=current_val,
                        threshold=trigger_threshold,
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

    def _evaluate(self, rule: AlertRule, quote) -> tuple[bool, float, str, str, float]:
        """评估规则所有维度"""
        checks = [
            ("price_above", "价格上穿", quote.price, rule.price_above, lambda c, t: c >= t),
            ("price_below", "价格下穿", quote.price, rule.price_below, lambda c, t: c <= t),
            ("change_pct", "涨跌幅", abs(quote.change_pct), rule.change_pct, lambda c, t: c >= t),
            ("volume", "成交量(万手)", quote.volume / 1e4, rule.volume, lambda c, t: c >= t),
        ]
        for rtype, label, current, threshold, cond in checks:
            if threshold is not None and cond(current, threshold):
                msg = f"[{rule.name or rule.code}] {label}触发: 当前{current:.2f} 阈值{threshold:.2f}"
                return True, current, msg, rtype, threshold
        return False, 0.0, "", "", 0.0

    def get_recent_events(self, limit: int = 20) -> List[AlertEvent]:
        """获取最近告警事件"""
        events = sorted(self._events, key=lambda e: e.timestamp, reverse=True)
        return events[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """获取告警统计"""
        return {
            "total_rules": len(set(r.code for r in self._rules)),
            "enabled_rules": len([r for r in self._rules if r.enabled]),
            "total_events": len(self._events),
            "recent_events": len([e for e in self._events if not e.notified]),
        }
