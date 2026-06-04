"""通知发送器工厂"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from src.config import Config
from src.enums import NotifyChannel

logger = logging.getLogger(__name__)

_senders: Dict[str, "BaseSender"] = {}


def create_senders(config: Config) -> Dict[str, "BaseSender"]:
    """根据配置创建所有可用的通知发送器"""
    from .base import BaseSender
    from .wechat_sender import WeChatSender
    from .feishu_sender import FeiShuSender
    from .telegram_sender import TelegramSender
    from .discord_sender import DiscordSender

    senders: Dict[str, BaseSender] = {}

    if config.wechat_webhook_url:
        senders["wechat"] = WeChatSender(config.wechat_webhook_url)
        logger.info("✅ 企业微信通知已配置")

    if config.feishu_webhook_url:
        senders["feishu"] = FeiShuSender(config.feishu_webhook_url)
        logger.info("✅ 飞书通知已配置")

    if config.telegram_bot_token and config.telegram_chat_id:
        senders["telegram"] = TelegramSender(config.telegram_bot_token, config.telegram_chat_id)
        logger.info("✅ Telegram 通知已配置")

    if config.discord_webhook_url:
        senders["discord"] = DiscordSender(config.discord_webhook_url)
        logger.info("✅ Discord 通知已配置")

    if config.slack_webhook_url:
        from .slack_sender import SlackSender
        senders["slack"] = SlackSender(config.slack_webhook_url)
        logger.info("✅ Slack 通知已配置")

    if config.smtp_server and config.smtp_user and config.smtp_password and config.email_to:
        from .email_sender import EmailSender
        senders["email"] = EmailSender(
            config.smtp_server, config.smtp_port,
            config.smtp_user, config.smtp_password, config.email_to,
        )
        logger.info("✅ 邮件通知已配置")

    return senders


def get_senders(config: Optional[Config] = None) -> Dict[str, "BaseSender"]:
    """获取所有通知发送器"""
    if not _senders:
        from src.config import get_config
        cfg = config or get_config()
        _senders.update(create_senders(cfg))
    return _senders


async def send_to_all(content: str, title: str = "", as_markdown: bool = False) -> Dict[str, bool]:
    """发送通知到所有渠道"""
    senders = get_senders()
    results = {}
    for name, sender in senders.items():
        results[name] = await sender.send(content, title, as_markdown)
    return results
