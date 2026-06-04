"""测试新增功能：策略、邮件、导入、交易日历"""
import tempfile

import src.services.portfolio_service as ps
from src.agent.executor import STRATEGIES
from src.notification_sender.email_sender import EmailSender
from src.utils import trading_calendar as tc


def test_agent_strategies_count():
    """对齐参考项目：15 个内置策略"""
    assert len(STRATEGIES) == 15
    for key in ("威科夫", "期望重估", "龙头", "量价", "风控"):
        assert key in STRATEGIES


def test_email_sender_recipients_parsed():
    """EMAIL_TO 支持逗号分隔多收件人"""
    s = EmailSender("smtp.x.com", 587, "u@x.com", "pw", "a@x.com, b@x.com")
    assert s.recipients == ["a@x.com", "b@x.com"]


def test_email_sender_factory_gated(monkeypatch):
    """SMTP 配置齐全时邮件渠道才注册"""
    from src.config import Config
    from src.notification_sender.factory import create_senders

    cfg = Config()
    cfg.smtp_server = "smtp.x.com"
    cfg.smtp_user = "u@x.com"
    cfg.smtp_password = "pw"
    cfg.email_to = "a@x.com"
    senders = create_senders(cfg)
    assert "email" in senders


def test_import_positions_parser():
    """批量导入：表头/空行/垃圾行静默跳过，多分隔符兼容"""
    tmp = tempfile.mktemp(suffix=".json")
    ps.PORTFOLIO_FILE = tmp
    svc = ps.PortfolioService()
    text = (
        "code,quantity,cost_price,name\n"
        "600519,100,1700.5,贵州茅台\n"
        "000001\t200\t11.2\n"
        "AAPL 50 180.3 Apple\n"
        "说明：这是一行无关文本\n"
        "\n"
    )
    result = svc.import_positions(text)
    assert result["imported"] == 3
    assert result["errors"] == []
    assert set(svc._positions.keys()) == {"600519", "000001", "AAPL"}


def test_trading_calendar_weekend_fallback(monkeypatch):
    """交易日历不可用时退化为非周末判断"""
    monkeypatch.setattr(tc, "_trade_dates", lambda: frozenset())
    assert tc.is_trading_day("2026-06-06") is False  # 周六
    assert tc.is_trading_day("2026-06-08") is True   # 周一
    assert str(tc.next_trading_day("2026-06-06")) == "2026-06-08"
