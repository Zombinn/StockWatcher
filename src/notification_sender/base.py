"""通知发送器基类"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseSender(ABC):
    """通知发送器抽象基类"""

    @abstractmethod
    async def send_text(self, message: str, title: str = "") -> bool:
        ...

    @abstractmethod
    async def send_markdown(self, content: str, title: str = "") -> bool:
        ...

    async def send(self, content: str, title: str = "", as_markdown: bool = False) -> bool:
        if as_markdown:
            return await self.send_markdown(content, title)
        return await self.send_text(content, title)
