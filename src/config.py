"""配置管理 - 从 .env 加载配置并提供全局访问"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import dotenv_values, load_dotenv


def _is_valid(value: Optional[str]) -> bool:
    """判断配置值是否有效（非空、非注释占位符）"""
    if not value:
        return False
    value = value.strip()
    if not value:
        return False
    if value.startswith("#"):
        return False
    if value.startswith("//"):
        return False
    return True


def setup_env() -> None:
    """加载 .env 文件到环境变量"""
    # 关闭 akshare 内部 tqdm 进度条（"Please wait for a moment" 刷屏）
    os.environ.setdefault("TQDM_DISABLE", "1")
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)


@dataclass
class Config:
    """全局配置"""

    # 自选股
    stock_list: List[str] = field(default_factory=lambda: _parse_stock_list())

    # LLM
    ansipre_api_keys: List[str] = field(default_factory=lambda: _split_env("ANSPIRE_API_KEYS"))
    gemini_api_key: Optional[str] = field(default_factory=lambda: _get_env("GEMINI_API_KEY"))
    openai_api_key: Optional[str] = field(default_factory=lambda: _get_env("OPENAI_API_KEY"))
    openai_base_url: Optional[str] = field(default_factory=lambda: _get_env("OPENAI_BASE_URL"))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "Doubao-Seed-2.0-lite"))
    llm_timeout_sec: int = field(default_factory=lambda: int(os.getenv("LLM_TIMEOUT_SEC", "60")))

    # 数据源
    tushare_token: Optional[str] = field(default_factory=lambda: _get_env("TUSHARE_TOKEN"))
    tickflow_api_key: Optional[str] = field(default_factory=lambda: _get_env("TICKFLOW_API_KEY"))
    finnhub_api_key: Optional[str] = field(default_factory=lambda: _get_env("FINNHUB_API_KEY"))

    # 通知
    wechat_webhook_url: Optional[str] = field(default_factory=lambda: _get_env("WECHAT_WEBHOOK_URL"))
    feishu_webhook_url: Optional[str] = field(default_factory=lambda: _get_env("FEISHU_WEBHOOK_URL"))
    telegram_bot_token: Optional[str] = field(default_factory=lambda: _get_env("TELEGRAM_BOT_TOKEN"))
    telegram_chat_id: Optional[str] = field(default_factory=lambda: _get_env("TELEGRAM_CHAT_ID"))
    discord_webhook_url: Optional[str] = field(default_factory=lambda: _get_env("DISCORD_WEBHOOK_URL"))
    slack_webhook_url: Optional[str] = field(default_factory=lambda: _get_env("SLACK_WEBHOOK_URL"))
    smtp_server: Optional[str] = field(default_factory=lambda: _get_env("SMTP_SERVER"))
    smtp_port: int = field(default_factory=lambda: int(os.getenv("SMTP_PORT", "587")))
    smtp_user: Optional[str] = field(default_factory=lambda: _get_env("SMTP_USER"))
    smtp_password: Optional[str] = field(default_factory=lambda: _get_env("SMTP_PASSWORD"))
    email_to: Optional[str] = field(default_factory=lambda: _get_env("EMAIL_TO"))

    # 定时任务
    schedule_time: str = field(default_factory=lambda: os.getenv("SCHEDULE_TIME", "09:30"))
    schedule_enabled: bool = field(default_factory=lambda: os.getenv("SCHEDULE_ENABLED", "false").lower() == "true")
    run_immediately: bool = field(default_factory=lambda: os.getenv("RUN_IMMEDIATELY", "true").lower() == "true")

    # 代理
    use_proxy: bool = field(default_factory=lambda: os.getenv("USE_PROXY", "false").lower() == "true")
    proxy_host: str = field(default_factory=lambda: os.getenv("PROXY_HOST", "127.0.0.1"))
    proxy_port: str = field(default_factory=lambda: os.getenv("PROXY_PORT", "10809"))

    # 日志
    log_dir: str = field(default_factory=lambda: os.getenv("LOG_DIR", "logs"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())

    def proxy_url(self) -> Optional[str]:
        if self.use_proxy:
            return f"http://{self.proxy_host}:{self.proxy_port}"
        return None


_global_config: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置单例"""
    global _global_config
    if _global_config is None:
        setup_env()
        _global_config = Config()
    return _global_config


def reload_config() -> Config:
    """重新加载配置"""
    global _global_config
    setup_env()
    _global_config = Config()
    return _global_config


def _get_env(key: str) -> Optional[str]:
    """获取环境变量，过滤掉注释占位符"""
    val = os.getenv(key)
    if _is_valid(val):
        return val.strip()
    return None


def _parse_stock_list() -> List[str]:
    raw = os.getenv("STOCK_LIST", "")
    return [s.strip() for s in raw.split(",") if s.strip()]


def _split_env(key: str) -> List[str]:
    raw = os.getenv(key, "")
    vals = [s.strip() for s in raw.split(",") if s.strip()]
    return [v for v in vals if _is_valid(v)]
