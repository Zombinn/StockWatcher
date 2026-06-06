"""配置管理服务 - WebUI 上读写所有配置"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import reload_config

logger = logging.getLogger(__name__)

ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"
ENV_EXAMPLE = Path(__file__).resolve().parent.parent.parent / ".env.example"


@dataclass
class ConfigField:
    """配置字段定义"""
    key: str
    label: str
    type: str = "string"  # string, number, boolean, password, multiline, select
    default: Any = ""
    description: str = ""
    placeholder: str = ""
    options: List[str] = field(default_factory=list)  # for select type
    section: str = "general"
    subsection: str = ""
    required: bool = False
    secret: bool = False  # 敏感字段，前端不回显完整值


# ===== 所有可配置字段定义 =====
ALL_FIELDS: List[ConfigField] = [
    # ---- 自选股 ----
    ConfigField("STOCK_LIST", "自选股列表", "multiline", "600519,300750,002594",
                "逗号分隔的股票代码，支持 A/H/US", section="stocks", required=True),
    ConfigField("SCHEDULE_TIME", "定时分析时间", "string", "09:30",
                "每天自动分析的执行时间 (HH:MM)", section="stocks"),
    ConfigField("SCHEDULE_ENABLED", "启用定时任务", "boolean", "false",
                "开启后每天按设定时间自动执行分析", section="stocks"),
    ConfigField("RUN_IMMEDIATELY", "启动时立即运行", "boolean", "true",
                "定时任务模式下，启动时先执行一次", section="stocks"),

    # ---- LLM / AI：中转站 ----
    ConfigField("LLM_RELAY_ENABLED", "启用中转站", "boolean", "false",
                "开启后优先使用中转站配置调用 LLM", section="llm", subsection="relay"),
    ConfigField("LLM_RELAY_PROVIDER", "中转站类型", "select", "custom",
                "选择内置中转站或自定义 OpenAI 兼容网关", section="llm", subsection="relay", options=["custom", "anspire"]),
    ConfigField("LLM_RELAY_API_KEY", "中转站 API Key", "password", "",
                "当前启用的中转站 API Key", section="llm", subsection="relay"),
    ConfigField("LLM_RELAY_API_KEYS", "中转站备用 Keys", "password", "",
                "可选，多个 Key 用逗号分隔；未填写单 Key 时使用第一个", section="llm", subsection="relay"),
    ConfigField("LLM_RELAY_BASE_URL", "中转站 Base URL", "string", "",
                "OpenAI 兼容网关地址，例如 http://host:port/v1；不要包含 /chat/completions", section="llm", subsection="relay"),
    ConfigField("LLM_RELAY_MODEL", "中转站模型", "string", "",
                "中转站模型名称，例如 gpt-5.5", section="llm", subsection="relay"),
    ConfigField("LLM_RELAY_TIMEOUT_SEC", "中转站超时(秒)", "number", "60",
                "中转站单次请求超时时间", section="llm", subsection="relay"),
    ConfigField("ANSPIRE_API_KEYS", "Anspire Legacy Keys", "password", "",
                "旧版 Anspire 网关 API Key，逗号分隔支持多个；建议迁移到中转站配置", section="llm", subsection="relay"),

    # ---- LLM / AI：非中转站 ----
    ConfigField("OPENAI_API_KEY", "OpenAI API Key", "password", "",
                "OpenAI 兼容 API Key（支持 DeepSeek/通义千问等）", section="llm", subsection="direct"),
    ConfigField("OPENAI_BASE_URL", "OpenAI Base URL", "string", "",
                "例如 https://api.openai.com/v1", section="llm", subsection="direct", placeholder="https://api.openai.com/v1"),
    ConfigField("OPENAI_MODEL", "OpenAI 模型", "string", "gpt-4o-mini",
                "使用的模型名称", section="llm", subsection="direct"),
    ConfigField("LLM_MODEL", "LLM 模型", "string", "Doubao-Seed-2.0-lite",
                "默认 LLM 模型名称", section="llm", subsection="direct"),
    ConfigField("LLM_TIMEOUT_SEC", "LLM 超时(秒)", "number", "60",
                "单次 LLM 请求超时时间", section="llm", subsection="direct"),

    # ---- 数据源 ----
    ConfigField("TUSHARE_TOKEN", "Tushare Token", "password", "",
                "Tushare Pro API Token", section="data"),
    ConfigField("TICKFLOW_API_KEY", "TickFlow API Key", "password", "",
                "TickFlow 数据源 API Key", section="data"),
    ConfigField("FINNHUB_API_KEY", "Finnhub API Key", "password", "",
                "Finnhub 美股数据源 API Key", section="data"),

    # ---- 通知 ----
    ConfigField("WECHAT_WEBHOOK_URL", "企业微信 Webhook", "password", "",
                "企业微信机器人 Webhook URL", section="notify"),
    ConfigField("FEISHU_WEBHOOK_URL", "飞书 Webhook", "password", "",
                "飞书机器人 Webhook URL", section="notify"),
    ConfigField("TELEGRAM_BOT_TOKEN", "Telegram Bot Token", "password", "",
                "Telegram 机器人 Token", section="notify"),
    ConfigField("TELEGRAM_CHAT_ID", "Telegram Chat ID", "password", "",
                "Telegram 接收消息的 Chat ID", section="notify"),
    ConfigField("DISCORD_WEBHOOK_URL", "Discord Webhook", "password", "",
                "Discord Webhook URL", section="notify"),
    ConfigField("SLACK_WEBHOOK_URL", "Slack Webhook", "password", "",
                "Slack Webhook URL", section="notify"),

    # ---- 代理 ----
    ConfigField("USE_PROXY", "启用代理", "boolean", "false",
                "是否通过代理访问网络", section="proxy"),
    ConfigField("PROXY_HOST", "代理主机", "string", "127.0.0.1",
                "代理服务器地址", section="proxy"),
    ConfigField("PROXY_PORT", "代理端口", "number", "10809",
                "代理服务器端口", section="proxy"),

    # ---- 日志 ----
    # ---- 邮件通知 (SMTP) ----
    ConfigField("SMTP_SERVER", "SMTP 服务器", "string", "", "SMTP 服务器地址", section="notify"),
    ConfigField("SMTP_PORT", "SMTP 端口", "number", "587", "SMTP 端口号", section="notify"),
    ConfigField("SMTP_USER", "SMTP 用户名", "password", "", "邮箱登录用户名", section="notify"),
    ConfigField("SMTP_PASSWORD", "SMTP 密码", "password", "", "邮箱密码或授权码", section="notify"),
    ConfigField("EMAIL_TO", "接收邮箱", "password", "", "接收分析报告的邮箱地址", section="notify"),

    # ---- 其他 ----
    ConfigField("PORTFOLIO_FILE", "持仓数据文件", "string", "data/portfolio.json", "持仓数据持久化路径", section="log"),
    ConfigField("ALERT_FILE", "告警数据文件", "string", "data/alerts.json", "告警规则和事件持久化路径", section="log"),


    ConfigField("LOG_DIR", "日志目录", "string", "logs",
                "日志和报告文件的存储路径", section="log"),
    ConfigField("LOG_LEVEL", "日志级别", "select", "INFO",
                "日志输出级别", section="log", options=["DEBUG", "INFO", "WARNING", "ERROR"]),
]


class ConfigManager:
    """配置管理器 - 读取写入 .env 文件"""

    @staticmethod
    def get_sections() -> List[Dict[str, Any]]:
        """获取所有配置分组及字段"""
        sections: Dict[str, dict] = {}
        for field in ALL_FIELDS:
            sec = field.section
            if sec not in sections:
                labels = {
                    "stocks": "📋 自选股与定时任务",
                    "llm": "🤖 LLM / AI 模型",
                    "data": "🔌 数据源",
                    "notify": "📬 通知渠道",
                    "proxy": "🔒 代理设置",
                    "log": "📝 日志",
                }
                sections[sec] = {"key": sec, "label": labels.get(sec, sec), "fields": []}
                if sec == "llm":
                    sections[sec]["subsections"] = [
                        {"key": "relay", "label": "中转站"},
                        {"key": "direct", "label": "非中转站"},
                    ]
            sections[sec]["fields"].append(field.__dict__)
        return list(sections.values())

    @staticmethod
    def get_all() -> Dict[str, str]:
        """读取当前所有配置值"""
        values = {}
        env_path = ENV_FILE if ENV_FILE.exists() else ENV_EXAMPLE
        if not env_path.exists():
            return values

        content = env_path.read_text(encoding="utf-8")
        for field in ALL_FIELDS:
            # 从 environ 获取（优先）或从 .env 文件解析
            env_val = os.getenv(field.key)
            if env_val is not None:
                values[field.key] = env_val
            else:
                # 从 .env 文件解析
                match = re.search(
                    rf"^{re.escape(field.key)}\s*=\s*(.*?)\s*$",
                    content,
                    re.MULTILINE,
                )
                if match:
                    values[field.key] = match.group(1).strip().strip('"').strip("'")
                else:
                    values[field.key] = field.default

            # 敏感字段脱敏
            if field.secret and values[field.key]:
                v = values[field.key]
                if len(v) > 8:
                    values[field.key] = v[:4] + "****" + v[-4:]
                else:
                    values[field.key] = "****"

        return values

    @staticmethod
    def update(updates: Dict[str, str]) -> Dict[str, Any]:
        """更新配置（写入 .env 文件）"""
        results = {"updated": [], "errors": [], "restart_required": False}

        # 读取当前 .env 内容
        env_path = ENV_FILE
        if not env_path.exists():
            env_path.parent.mkdir(parents=True, exist_ok=True)
            env_path.write_text("", encoding="utf-8")

        content = env_path.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=True) if content else []
        existing_keys = set()

        # 处理已有配置行
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") or "=" not in stripped:
                new_lines.append(line)
                continue

            key = stripped.split("=", 1)[0].strip()
            existing_keys.add(key)

            if key in updates:
                new_lines.append(f"{key}={updates[key]}\n")
                results["updated"].append(key)
            else:
                new_lines.append(line)

        # 追加新配置
        for key, value in updates.items():
            if key not in existing_keys:
                # 找到对应字段的注释
                field_obj = next((f for f in ALL_FIELDS if f.key == key), None)
                if field_obj and field_obj.description:
                    new_lines.append(f"\n# {field_obj.description}\n")
                new_lines.append(f"{key}={value}\n")
                results["updated"].append(key)

        env_path.write_text("".join(new_lines), encoding="utf-8")

        # 同步更新进程环境变量：load_dotenv(override=False) 不会覆盖已存在的 os.environ，
        # 否则保存后读到的仍是启动时的旧值（表现为「自选股被重置」）
        for key, value in updates.items():
            os.environ[key] = value

        # 重新加载配置
        reload_config()

        # 检查是否需要重启服务才能生效
        restart_keys = {"STOCK_LIST", "SCHEDULE_TIME", "SCHEDULE_ENABLED", "LOG_DIR", "LOG_LEVEL"}
        for key in updates:
            if key in restart_keys:
                results["restart_required"] = True
                break

        if not results["errors"]:
            results["message"] = f"已更新 {len(results['updated'])} 项配置"
            if results["restart_required"]:
                results["message"] += "，部分配置需重启服务生效"

        return results

    @staticmethod
    def reset_to_default() -> Dict[str, Any]:
        """重置为默认配置（从 .env.example 恢复）"""
        if not ENV_EXAMPLE.exists():
            return {"success": False, "message": "找不到 .env.example 模板文件"}

        example_content = ENV_EXAMPLE.read_text(encoding="utf-8")
        ENV_FILE.write_text(example_content, encoding="utf-8")
        reload_config()
        return {"success": True, "message": "已重置为默认配置"}

    @staticmethod
    def get_env_file_status() -> Dict[str, Any]:
        """获取 .env 文件状态"""
        exists = ENV_FILE.exists()
        if exists:
            size = ENV_FILE.stat().st_size
            modified = ENV_FILE.stat().st_mtime
        else:
            size = 0
            modified = 0
        return {
            "exists": exists,
            "path": str(ENV_FILE),
            "size": size,
            "modified": modified,
            "configurable_fields": len(ALL_FIELDS),
        }
