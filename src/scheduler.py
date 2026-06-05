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

    def start(self) -> None:
        """启动调度器"""
        for job in self._jobs:
            schedule.every().day.at(job["time"]).do(job["task"])
            logger.info("定时任务 [%s] 已设置: 每天 %s 执行", job["name"], job["time"])

            if job["run_immediately"]:
                logger.info("立即执行 [%s]...", job["name"])
                try:
                    job["task"]()
                except Exception as e:
                    logger.error("立即执行 [%s] 失败: %s", job["name"], e)

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

        while self._running:
            schedule.run_pending()
            time.sleep(1)
