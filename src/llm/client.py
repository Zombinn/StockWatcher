"""LLM API 客户端"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from src.config import get_config

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """LLM 客户端基类"""

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "",
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        ...

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "",
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        ...


class OpenAICompatibleClient(LLMClient):
    """OpenAI 兼容 API 客户端"""

    def __init__(self, api_key: str, base_url: str, model: str, timeout: int = 120):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._http = httpx.AsyncClient(timeout=timeout)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "",
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            resp = await self._http.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error("LLM API 请求失败: %s", e)
            raise

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "",
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json=payload,
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                delta = chunk["choices"][0].get("delta", {})
                                if content := delta.get("content"):
                                    yield content
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error("LLM Stream 请求失败: %s", e)
            raise


def create_llm_client() -> Optional[LLMClient]:
    """根据配置创建 LLM 客户端"""
    config = get_config()

    # 中转站 / 网关优先（开启后覆盖非中转站配置）
    if getattr(config, "llm_relay_enabled", False):
        relay_keys = []
        if config.llm_relay_api_key:
            relay_keys.append(config.llm_relay_api_key)
        relay_keys.extend(config.llm_relay_api_keys)
        relay_keys.extend(config.ansipre_api_keys)
        key = relay_keys[0] if relay_keys else None
        base_url = config.llm_relay_base_url
        if not base_url and config.llm_relay_provider == "anspire":
            base_url = "https://open-gateway.anspire.cn/v6"
        model = config.llm_relay_model or config.llm_model
        if key and base_url and model:
            logger.info("创建 LLM 中转站客户端: provider=%s, base=%s, model=%s", config.llm_relay_provider, base_url, model)
            return OpenAICompatibleClient(key, base_url, model, timeout=config.llm_relay_timeout_sec)
        logger.warning("已启用 LLM 中转站，但 key/base_url/model 配置不完整，尝试非中转站配置")

    # OpenAI-compatible 优先
    if config.openai_api_key and config.openai_base_url:
        model = config.openai_model or config.llm_model
        logger.info("创建 OpenAI 兼容客户端: %s, model=%s", config.openai_base_url, model)
        return OpenAICompatibleClient(config.openai_api_key, config.openai_base_url, model, timeout=config.llm_timeout_sec)

    # Anspire legacy
    if config.ansipre_api_keys:
        key = config.ansipre_api_keys[0]
        base_url = "https://open-gateway.anspire.cn/v6"
        model = config.llm_model
        logger.info("创建 Anspire 客户端, model=%s", model)
        return OpenAICompatibleClient(key, base_url, model, timeout=config.llm_timeout_sec)

    logger.warning("未配置 LLM API Key，无法创建 LLM 客户端")
    return None
