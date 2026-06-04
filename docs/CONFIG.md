# 🔧 配置说明

所有配置通过 `.env` 文件管理，也支持在 Web 仪表盘的 ⚙ 配置页面在线编辑保存。

## 配置加载顺序

1. 加载 `.env` 文件（项目根目录）
2. 若 `.env` 不存在，加载 `.env.example`
3. 环境变量覆盖 `.env` 中的值

## 配置项完整列表

### 自选股与定时任务

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `STOCK_LIST` | 自选股代码，逗号分隔 | `600519,300750,002594` |
| `SCHEDULE_TIME` | 定时分析时间 (HH:MM) | `09:30` |
| `SCHEDULE_ENABLED` | 启用定时任务 | `false` |
| `RUN_IMMEDIATELY` | 定时模式下启动时立即执行 | `true` |

### LLM / AI 模型

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `ANSPIRE_API_KEYS` | Anspire API Key（支持多个逗号分隔） | - |
| `GEMINI_API_KEY` | Google Gemini API Key | - |
| `OPENAI_API_KEY` | OpenAI 兼容 API Key | - |
| `OPENAI_BASE_URL` | OpenAI 兼容 API 地址 | - |
| `OPENAI_MODEL` | 模型名称 | `gpt-4o-mini` |
| `LLM_MODEL` | Anspire 默认模型 | `Doubao-Seed-2.0-lite` |
| `LLM_TIMEOUT_SEC` | LLM 请求超时秒数 | `60` |

### 数据源

| 配置项 | 说明 |
|--------|------|
| `TUSHARE_TOKEN` | Tushare Pro Token |
| `TICKFLOW_API_KEY` | TickFlow API Key |
| `FINNHUB_API_KEY` | Finnhub API Key（美股） |

### 通知渠道

| 配置项 | 说明 |
|--------|------|
| `WECHAT_WEBHOOK_URL` | 企业微信机器人 Webhook |
| `FEISHU_WEBHOOK_URL` | 飞书机器人 Webhook |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID |
| `DISCORD_WEBHOOK_URL` | Discord Webhook |
| `SLACK_WEBHOOK_URL` | Slack Webhook |
| `SMTP_SERVER` | SMTP 服务器地址 |
| `SMTP_PORT` | SMTP 端口 |
| `SMTP_USER` | SMTP 用户名 |
| `SMTP_PASSWORD` | SMTP 密码 |
| `EMAIL_TO` | 接收邮箱 |

### 代理

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `USE_PROXY` | 是否启用代理 | `false` |
| `PROXY_HOST` | 代理主机 | `127.0.0.1` |
| `PROXY_PORT` | 代理端口 | `10809` |

### 日志

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `LOG_DIR` | 日志目录 | `logs` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

### 数据文件

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `PORTFOLIO_FILE` | 持仓数据文件 | `data/portfolio.json` |
| `ALERT_FILE` | 告警数据文件 | `data/alerts.json` |
