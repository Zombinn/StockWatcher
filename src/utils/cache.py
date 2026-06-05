"""极简内存 TTL 缓存（进程级，适用于慢接口结果短期复用）"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable, Optional

_store: dict[str, tuple[float, Any]] = {}
_locks: dict[str, asyncio.Lock] = {}


def get_cached(key: str, ttl: float) -> Optional[Any]:
    """命中且未过期则返回缓存值，否则返回 None"""
    item = _store.get(key)
    if item and (time.time() - item[0]) < ttl:
        return item[1]
    return None


def set_cached(key: str, value: Any) -> None:
    _store[key] = (time.time(), value)


async def cached_call(key: str, ttl: float, compute: Callable[[], Awaitable[Any]]) -> Any:
    """命中缓存则直接返回；否则在单飞锁内计算一次，避免并发重复执行慢任务"""
    hit = get_cached(key, ttl)
    if hit is not None:
        return hit
    lock = _locks.setdefault(key, asyncio.Lock())
    async with lock:
        hit = get_cached(key, ttl)  # 等锁期间可能已被其他请求填好
        if hit is not None:
            return hit
        result = await compute()
        set_cached(key, result)
        return result


def drop(key: str) -> None:
    """失效单个缓存键"""
    _store.pop(key, None)


def clear_cache() -> None:
    _store.clear()
