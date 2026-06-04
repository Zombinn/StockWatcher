# 📊 StockWatcher - 股票智能分析系统

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

基于 AI 与大数据的 A 股/港股/美股自选股智能分析系统。提供技术分析、AI 解读、大盘复盘、持仓管理、告警、回测、Agent 问股等能力，支持 Web 仪表盘和多渠道推送。

## ✨ 功能特性

| 能力 | 覆盖内容 |
|------|---------|
| 技术分析 | MA/MACD/RSI/KDJ/BOLL/ATR/乖离率，综合评分 0-100，买卖信号 |
| AI 解读 | 接入 LLM（OpenAI/DeepSeek/通义千问）解读技术指标和市场 |
| 大盘复盘 | 指数行情、板块轮动、北向资金，LLM 自动分析 |
| 多数据源 | AkShare（A 股，无 token）、YFinance（港股/美股） |
| 持仓管理 | 实时市值、组合盈亏、行业分布、集中度风险评分、仓位建议 |
| 告警引擎 | 价格上穿/下穿、涨跌幅、成交量触发，冷却机制 |
| Agent 问股 | 多轮对话，10 种内置分析策略（均线/缠论/波浪/趋势/热点等） |
| 回测引擎 | 均线金叉/MACD/RSI/布林带策略，含胜率/夏普/最大回撤 |
| Web 仪表盘 | React + Ant Design 暗色主题，6 大功能页面 + 配置管理中心 |
| 多通道推送 | 企业微信、飞书、Telegram、Discord、Slack |
| 定时任务 | 每日指定时间自动分析推送 |
| API 服务 | FastAPI 提供完整 RESTful 接口 |

## 🚀 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+（仅前端开发需要）
- pip 安装依赖

### 安装与运行

```bash
# 1. 克隆
git clone https://github.com/Zombinn/StockWatcher.git
cd StockWatcher

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，至少设置 STOCK_LIST

# 4. 运行分析
python main.py

# 5. 启动 Web 服务
python main.py --serve
# 访问 http://localhost:8000
```

### 前端开发模式（可选）

```bash
cd web
npm install
npm run dev
# 访问 http://localhost:3000（API 自动代理到 :8000）
```

## 📁 项目结构

```
StockWatcher/
├── main.py                    # 主入口（单次/定时/服务/回测/问股）
├── server.py                  # FastAPI 服务（25+ REST API）
├── src/
│   ├── config.py              # 配置管理（dataclass + .env）
│   ├── enums.py               # 枚举定义
│   ├── stock_analyzer.py      # 技术分析引擎
│   ├── formatters.py          # 报告格式化（Markdown）
│   ├── scheduler.py           # 定时调度
│   ├── data_provider/         # 数据源适配器
│   │   ├── base.py            # 抽象基类 + dataclass
│   │   ├── akshare_fetcher.py # AkShare（A 股，无 token）
│   │   ├── yfinance_fetcher.py# YFinance（港股/美股）
│   │   ├── tushare_fetcher.py # Tushare Pro（需 token）
│   │   ├── tickflow_fetcher.py# TickFlow（需 token）
│   │   ├── finnhub_fetcher.py # Finnhub（美股，需 token）
│   │   └── factory.py         # 工厂 + 自动降级链
│   ├── llm/                   # LLM 集成
│   │   ├── client.py          # API 客户端（OpenAI 兼容）
│   │   └── interpreter.py     # 技术/新闻/大盘解读
│   ├── notification_sender/   # 推送适配器
│   │   ├── wechat_sender.py
│   │   ├── feishu_sender.py
│   │   ├── telegram_sender.py
│   │   ├── discord_sender.py
│   │   └── slack_sender.py
│   ├── core/
│   │   ├── market_review.py   # 大盘复盘
│   │   └── backtest_engine.py # 回测引擎
│   ├── services/
│   │   ├── analysis_service.py# 分析协调
│   │   ├── stock_service.py   # 股票数据服务
│   │   ├── portfolio_service.py# 持仓管理
│   │   ├── alert_service.py   # 告警引擎
│   │   └── config_service.py  # 配置管理
│   └── agent/
│       └── executor.py        # Agent 问股引擎
├── web/                       # React + Ant Design 前端
│   ├── src/
│   │   ├── pages/             # 7 个功能页面
│   │   ├── api/               # API 客户端
│   │   └── types/             # TypeScript 类型
│   └── vite.config.ts
├── tests/                     # 16 个测试用例
├── .env.example               # 配置模板
└── docs/                      # 文档
```

## 🔌 数据源配置

数据源通过 `factory.py` 的自动降级链获取数据：

### A 股降级链

```
AkShare（无 token，首选）→ Tushare（需 TUSHARE_TOKEN）→ TickFlow（需 TICKFLOW_API_KEY）
```

### 港股/美股降级链

```
YFinance（无 token，首选）→ Finnhub（需 FINNHUB_API_KEY）
```

你无需关心具体使用哪个数据源，系统会自动按优先级尝试，失败自动降级。

详细配置见 [docs/DATA_SOURCE.md](docs/DATA_SOURCE.md)。

## 🔧 配置管理

所有配置通过 `.env` 文件管理（详见 `.env.example`），也支持在 Web 仪表盘的 **⚙ 配置** 页面在线编辑保存。

## 🌐 API 文档

启动服务后访问 `http://localhost:8000/docs` 查看 Swagger 文档。

### 核心端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/analyze | 执行全量分析 |
| GET | /api/v1/market/review | 大盘复盘 |
| GET | /api/v1/portfolio | 持仓概览 |
| GET | /api/v1/alerts | 告警规则与事件 |
| POST | /api/v1/alerts/rules | 添加告警规则 |
| POST | /api/v1/agent/chat | Agent 问股 |
| GET | /api/v1/backtest | 策略回测 |
| GET/POST | /api/v1/config/* | 配置管理 |

## 📊 大盘复盘

大盘复盘指数、板块和北向资金。

```bash
python main.py --market-review
```

## ⏰ 定时任务

```bash
# 在 .env 中设置 SCHEDULE_TIME=09:30 SCHEDULE_ENABLED=true
python main.py --schedule
```

## 📖 文档索引

| 文档 | 说明 |
|------|------|
| [docs/DATA_SOURCE.md](docs/DATA_SOURCE.md) | 数据源配置与优先级 |
| [docs/CONFIG.md](docs/CONFIG.md) | 完整配置项说明 |
| [docs/DEPLOY.md](docs/DEPLOY.md) | 部署指南 |
| [docs/API.md](docs/API.md) | API 接口文档 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 架构说明 |

## 🤝 贡献

欢迎提交 Issue 和 PR。代码规范详见 [AGENTS.md](AGENTS.md)。

## 📄 License

MIT
