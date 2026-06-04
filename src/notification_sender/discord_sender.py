"""Discord 通知"""
from __future__ import annotations

import logging

import httpx

from .base import BaseSender

logger = logging.getLogger(__name__)


class DiscordSender(BaseSender):
    """Discord Webhook 发送器"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send_text(self, message: str, title: str = "") -> bool:
        try:
            payload = {"content": message}
            async with httpx.AsyncClient() as client:
                resp = await client.post(self.webhook_url, json=payload, timeout=15)
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error("Discord 发送失败: %s", e)
            return False

    async def send_markdown(self, content: str, title: str = "") -> bool:
        return await self.send_text(content)
