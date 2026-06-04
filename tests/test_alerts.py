"""测试告警引擎"""
from src.services.alert_service import AlertEngine, AlertRule, AlertEvent


def test_alert_rule_creation():
    """测试告警规则创建"""
    engine = AlertEngine()
    rule_id = engine.add_rule("600519", "price_above", 200.0, "茅台")
    assert rule_id is not None

    rules = engine.get_rules("600519")
    assert len(rules) > 0
    assert rules[0].code == "600519"
    assert rules[0].rule_type == "price_above"
    assert rules[0].threshold == 200.0

    # 清理
    engine.remove_rule(rule_id)
    assert len(engine.get_rules("600519")) == 0


def test_alert_rule_dataclass():
    """测试告警数据结构"""
    rule = AlertRule(id="test_1", code="000001", rule_type="change_pct", threshold=5.0)
    assert rule.code == "000001"
    assert rule.enabled is True
    assert rule.cooldown_minutes == 60

    event = AlertEvent(rule_id="test_1", code="000001", name="平安", rule_type="change_pct", message="测试", current_value=6.0, threshold=5.0)
    assert event.notified is False
    assert "测试" in event.message


def test_alert_stats():
    """测试告警统计"""
    engine = AlertEngine()
    stats = engine.get_stats()
    assert "total_rules" in stats
    assert "enabled_rules" in stats
    assert "total_events" in stats
