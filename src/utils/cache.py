"""极简内存 TTL 缓存（进程级，适用于慢接口结果短期复用）"""
from __future__ import annotations

import time
from typing import Any, Optional

_store: dict[str, tuple[float, Any]] = {}


def get_cached(key: str, ttl: float) -> Optional[Any]:
    """命中且未过期则返回缓存值，否则返回 None"""
    item = _store.get(key)
    if item and (time.time() - item[0]) < ttl:
        return item[1]
    return None


def set_cached(key: str, value: Any) -> None:
    _store[key] = (time.time(), value)


def drop(key: str) -> None:
    """失效单个缓存键"""
    _store.pop(key, None)


def clear_cache() -> None:
    _store.clear()
