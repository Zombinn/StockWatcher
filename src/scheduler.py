"""定时任务调度"""
from __future__ import annotations

import logging
import signal
import sys
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

import schedule

logger = logging.getLogger(__name__)


def _normalize_time(t: str) -> str:
    """标准化时间格式为 HH:MM"""
    t = t.strip()
    if ":" in t:
        return t
    if len(t) == 4 and t.isdigit():
        return f"{t[:2]}:{t[2:]}"
    return t

class Scheduler:
    """定时任务调度器"""

    def __init__(self):
        self._running = False
        self._jobs: List[Dict[str, Any]] = []

    def add_job(
        self,
        task: Callable,
        schedule_time: str = "09:30",
        run_immediately: bool = True,
        name: str = "",
    ) -> None:
        """添加定时任务"""
        self._jobs.append({
            "task": task,
            "time": schedule_time,
            "run_immediately": run_immediately,
            "name": name or f"task_{len(self._jobs)}",
        })
        if run_immediately:
            logger.info("立即执行 [%s]...", name or "task")
            try:
                task()
            except Exception as e:
                logger.error("立即执行 [%s] 失败: %s", name or "task", e)

    def _wrap_task(self, job_dict):
        """包装任务函数，添加日志"""
        original = job_dict["task"]
        def _wrapped():
            logger.info("调度器触发任务: %s", job_dict["name"])
            try:
                original()
                logger.info("调度器任务完成: %s", job_dict["name"])
            except Exception as e:
                logger.error("调度器任务失败: %s, %s", job_dict["name"], e)
        return _wrapped

    def start(self) -> None:
        """启动调度器"""
        for job in self._jobs:
            schedule.every().day.at(_normalize_time(job["time"])).do(self._wrap_task(job))
            logger.info("定时任务 [%s] 已设置: 每天 %s 执行", job["name"], job["time"])

        self._running = True
        logger.info("调度器已启动，等待定时任务...")

        # 信号只能在主线程注册；后台线程运行时跳过
        if threading.current_thread() is threading.main_thread():
            def _shutdown(signum, frame):
                logger.info("收到退出信号，调度器关闭")
                self._running = False
                sys.exit(0)

            signal.signal(signal.SIGINT, _shutdown)
            signal.signal(signal.SIGTERM, _shutdown)

        _log_timer = 0
        while self._running:
            try:
                schedule.run_pending()

                _log_timer += 1
                time.sleep(1)
            except Exception as e:
                logger.error("调度器循环异常: %s", e)
                time.sleep(5)
