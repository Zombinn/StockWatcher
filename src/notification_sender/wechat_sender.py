"""企业微信机器人通知"""
from __future__ import annotations

import json
import logging

import httpx

from .base import BaseSender

logger = logging.getLogger(__name__)


class WeChatSender(BaseSender):
    """企业微信机器人发送器"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send_text(self, message: str, title: str = "") -> bool:
        try:
            payload = {"msgtype": "text", "text": {"content": message}}
            async with httpx.AsyncClient() as client:
                resp = await client.post(self.webhook_url, json=payload, timeout=15)
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error("企业微信发送失败: %s", e)
            return False

    async def send_markdown(self, content: str, title: str = "") -> bool:
        try:
            payload = {"msgtype": "markdown", "markdown": {"content": content}}
            async with httpx.AsyncClient() as client:
                resp = await client.post(self.webhook_url, json=payload, timeout=15)
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error("企业微信发送 Markdown 失败: %s", e)
            return False
