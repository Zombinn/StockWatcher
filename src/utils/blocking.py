"""阻塞调用统一调度到单一工作线程。

mini_racer (V8) 根本问题：V8 在每个线程里都需要独立初始化，且不能并发初始化。
唯一安全方案：所有 akshare 调用都在**同一个线程**里顺序执行。
性能保障：单线程顺序执行虽然不并发，但每次调用后结果都被 TTL 缓存，重复访问秒回。
"""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, TypeVar

_T = TypeVar("_T")

# 单线程执行器——这是防止 V8 崩溃的关键，不要改大 max_workers
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="akshare_worker")


async def run_blocking(fn: Callable[..., _T], *args) -> _T:
    """在专用单工作线程中执行同步函数并 await 结果（不阻塞事件循环）"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, lambda: fn(*args))


# warmup_akshare 保留为空操作，避免已有调用方报错
def warmup_akshare() -> None:
    pass
