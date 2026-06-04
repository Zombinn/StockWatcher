"""飞书机器人通知"""
from __future__ import annotations

import json
import logging

import httpx

from .base import BaseSender

logger = logging.getLogger(__name__)


class FeiShuSender(BaseSender):
    """飞书机器人发送器"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send_text(self, message: str, title: str = "") -> bool:
        try:
            payload = {"msg_type": "text", "content": {"text": message}}
            async with httpx.AsyncClient() as client:
                resp = await client.post(self.webhook_url, json=payload, timeout=15)
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error("飞书发送失败: %s", e)
            return False

    async def send_markdown(self, content: str, title: str = "") -> bool:
        try:
            payload = {
                "msg_type": "post",
                "content": {"post": {"zh_cn": {"title": title or "StockWatcher 分析报告", "content": [[{"tag": "markdown", "text": content}]]}}},
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(self.webhook_url, json=payload, timeout=15)
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error("飞书发送 Markdown 失败: %s", e)
            return False
