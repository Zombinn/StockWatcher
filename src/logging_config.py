"""日志配置"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(
    log_prefix: str = "stockwatcher",
    debug: bool = False,
    log_dir: Optional[str] = None,
) -> None:
    """配置日志系统"""
    level = logging.DEBUG if debug else logging.INFO
    root = logging.getLogger()
    root.setLevel(level)

    # Clear existing handlers
    root.handlers.clear()

    # Console handler
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(level)
    console.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    root.addHandler(console)

    # File handler
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_handler = logging.FileHandler(
            log_path / f"{log_prefix}_{timestamp}.log",
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"
        ))
        root.addHandler(file_handler)
