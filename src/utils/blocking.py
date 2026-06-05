"""阻塞调用统一调度到单一工作线程。

akshare 内部依赖 mini_racer（V8 引擎），V8 非线程安全：在多个线程并发初始化会
崩溃（FATAL: Check failed: !pool->IsInitialized()）。因此所有 akshare 等阻塞调用
都通过这个**单工作线程**执行——既不阻塞事件循环，又保证串行、只在一个线程里触碰 V8。
"""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, TypeVar

_T = TypeVar("_T")

# 必须是单线程（max_workers=1），不要改大，否则 mini_racer/V8 会并发初始化崩溃
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="blocking")


async def run_blocking(fn: Callable[..., _T], *args) -> _T:
    """在单一工作线程中执行同步函数并 await 结果"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, lambda: fn(*args))
