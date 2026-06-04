"""Telegram 通知"""
from __future__ import annotations

import logging

import httpx

from .base import BaseSender

logger = logging.getLogger(__name__)


class TelegramSender(BaseSender):
    """Telegram 机器人发送器"""

    def __init__(self, bot_token: str, chat_id: str):
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.chat_id = chat_id

    async def send_text(self, message: str, title: str = "") -> bool:
        try:
            text = f"*{title}*\n\n{message}" if title else message
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.api_url}/sendMessage",
                    json={"chat_id": self.chat_id, "text": text, "parse_mode": "Markdown"},
                    timeout=15,
                )
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error("Telegram 发送失败: %s", e)
            return False

    async def send_markdown(self, content: str, title: str = "") -> bool:
        return await self.send_text(content, title)
