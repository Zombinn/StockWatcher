# 📊 StockWatcher - 股票智能分析系统

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

基于 AI 的多市场（A 股/港股/美股）股票智能分析系统。提供技术分析、AI 解读、大盘复盘、量化选股、持仓管理、告警引擎、回测、Agent 问股、形态识别、板块热力图、经济日历等能力，支持 Web 仪表盘和多渠道推送。

## ✨ 功能特性

### 📈 技术分析
- **指标全面** — MA5/10/20/60/120、RSI(6/14)、MACD、KDJ、BOLL、ATR、乖离率
- **综合评分** — 0-100 分，基于趋势+量能+指标加权
- **买卖信号** — 基于多指标综合判断，输出信号+操作建议
- **支撑/压力位** — 自动计算关键价位
- **形态识别** — 头肩顶/底、双顶/底、三角形、旗形、楔形等7种K线形态自动检测

### 🤖 AI 解读
- **LLM 解读** — 接入 DeepSeek / OpenAI / 通义千问 等模型解读技术指标
- **大盘 AI 分析** — 自动生成市场概况、板块轮动、资金流向分析
- **中转站支持** — 兼容任意 OpenAI 兼容 API（Anspire 等网关）

### 🔬 TimesFM 时序预测
- **本地部署** — Google TimesFM 2.5（200M 稠密模型），~880MB，本地运行无需 API
- **价格预测** — 基于历史 K 线预测未来 7/14/30 天走势，含置信区间
- **K 线图** — 近 60/120/250 天可切换，Canvas 手绘，鼠标跟随显示 OHLC + 成交量 + 涨跌幅

### 📊 大盘复盘
- **指数行情** — A 股（上证/深证/创业板/科创50/沪深300）、港股（恒生指数 via Yahoo）、美股（道琼斯/纳斯达克/标普500 via Yahoo）
- **市场切换** — A 股 / 港股 / 美股独立切换，指数和板块数据随市场联动
- **板块轮动** — A 股领涨/领跌板块排行（新浪源），港股美股暂无板块数据
- **板块热力图** — Grid 布局展示前 30 个板块涨跌幅，白色底色 + 红绿边框表示幅度
- **经济日历** — 美联储决议/非农/CPI/GDP 等关键事件，时间线排列，可按重要性筛选，点击查看详情弹窗

### 🎯 量化选股（AlphaSift）
- **多策略** — 强势突破 / 放量异动 / 超跌反弹 / 蓝筹精选 / 成长精选
- **多市场** — A 股 / 港股 / 美股独立策略
- **详情抽屉** — 点击候选股查看 K 线（多周期 60/120/250 天 + 鼠标跟随）、形态识别（含新手说明）、财报日历（实际 EPS）、价格预测（TimesFM）
- **批量操作** — 多选加入自选

### 💼 持仓管理
- **组合概览** — 总市值、总收益、风险评分、市场分布
- **持仓明细** — 市场/代码/名称/数量/成本/现价/市值/盈亏
- **市场筛选** — 按 A/港股/美股过滤
- **批量导入** — CSV/粘贴导入持仓，自动解析
- **自选股** — 独立自选列表，一键加入/移除
- **股票详情** — 点击股票行打开 K 线+预测+评分详情

### 🔔 告警引擎
- **价格告警** — 上穿/下穿触发
- **涨跌幅告警** — 日内涨跌幅监控
- **成交量告警** — 量能异常检测
- **冷却机制** — 避免重复推送

### 💬 Agent 问股
- **多轮对话** — 基于会话的股票分析对话
- **策略分析** — 多策略分析框架
- **侧边栏面板** — 半圆按钮展开/收起，拖拽调节宽度

### 📉 回测引擎
- **4 种策略** — 均线金叉 / MACD / RSI / 布林带
- **完整指标** — 总收益、胜率、最大回撤、夏普比率、交易次数
- **策略说明** — 内置策略说明弹窗

### 🌐 前端仪表盘
- **React + Ant Design** — 单页应用，8 个功能页面
- **首页** — 市场选择 + 搜索分析 + 报告预览 + 大盘概览
- **分析页** — 技术指标 + LLM 解读
- **大盘页** — 指数/板块/北向资金
- **配置中心** — 在线编辑 .env 配置，保存即生效
- **水印背景** — 全屏品牌水印
- **主题色动效** — Loading 文字主题色呼吸动画

### 📬 多通道推送
| 渠道 | 配置项 | 说明 |
|------|--------|------|
| 企业微信 | `WECHAT_WEBHOOK_URL` | 群机器人 |
| 飞书 | `FEISHU_WEBHOOK_URL` | 群机器人 |
| Telegram | `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` | Bot 私信 |
| Discord | `DISCORD_WEBHOOK_URL` | 频道 Webhook |
| Slack | `SLACK_WEBHOOK_URL` | 频道 Webhook |
| 邮件 | `SMTP_*` + `EMAIL_TO` | SMTP 发送 |

### ⏰ 定时任务
- 每日指定时间自动执行全量分析 + 推送
- `--serve` 模式下自动集成定时任务
- 支持启动时立即执行一次

### 📡 数据源
| 市场 | 数据源（降级链） | 是否需要 Token |
|------|-----------------|---------------|
| A 股 | AkShare（新浪） → Tushare | 新浪无需，Tushare 需申请 |
| 港股 | YFinance → Finnhub | 均无需 |
| 美股 | YFinance → Finnhub | YFinance 无需，Finnhub 需申请 |

## 🚀 快速开始

### 前置要求
- Python 3.10+
- Node.js 18+（仅前端开发需要）

### 安装与运行

```bash
# 1. 克隆
git clone https://github.com/Zombinn/StockWatcher.git
cd StockWatcher

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，至少设置 STOCK_LIST（自选股列表）

# 4. 单次运行（分析 + 推送）
python main.py

# 5. 启动 Web 服务
python main.py --serve
# 访问 http://localhost:8000
```

### 前端开发模式

```bash
cd web
npm install
npm run dev
# 访问 http://localhost:3000（API 自动代理到 :8000）
```

## 🖥️ 页面概览

| 页面 | 路由 | 功能 |
|------|------|------|
| **首页** | `/` | 市场选择 + 搜索分析 + 报告预览 + 大盘概览 + 推荐股票 |
| **选股** | `/screening` | 多市场策略选股 + 个股详情（K 线/预测/评分） |
| **分析** | `/analysis` | 全量自选股技术分析 + LLM 解读 |
| **大盘** | `/market` | 指数行情 + 板块排行 + 北向资金 |
| **持仓** | `/portfolio` | 持仓管理 + 自选股 + 盈亏跟踪 |
| **告警** | `/alerts` | 告警规则管理与事件 |
| **回测** | `/backtest` | 策略回测 + 策略说明 |
| **配置** | `/config` | 在线编辑 .env 配置 + 测试触发分析 |

## 🔌 API 概览（36 个端点）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/analyze` | 全量自选股分析 |
| POST | `/api/v1/analyze/trigger` | 手动触发全量分析 + 推送 |
| GET | `/api/v1/stocks/{code}` | 单只股票技术分析 |
| GET | `/api/v1/stocks/{code}/kline` | K 线数据 |
| GET | `/api/v1/stocks/{code}/forecast` | TimesFM 价格预测 |
| GET | `/api/v1/stocks/{code}/news` | 个股新闻 |
| GET | `/api/v1/analyze/llm/{code}` | AI 解读 |
| GET | `/api/v1/screen` | 智能选股 |
| GET | `/api/v1/search/suggest` | 搜索建议 |
| GET | `/api/v1/search/recommend` | 市场推荐 |
| GET | `/api/v1/market/review?market=cn` | 大盘复盘（支持 cn/hk/us 市场切换） |
| GET | `/api/v1/market/trading-day` | 交易日判断 |
| GET | `/api/v1/portfolio` | 持仓管理 |
| GET/POST | `/api/v1/watchlist` | 自选股管理 |
| POST | `/api/v1/agent/chat` | Agent 问股（多轮对话） |
| GET | `/api/v1/backtest` | 回测 |
| POST | `/api/v1/backtest/report` | 生成回测报告（Markdown/HTML） |
| POST | `/api/v1/backtest/report/save` | 保存回测报告到报告列表 |
| GET | `/api/v1/stocks/{code}/patterns` | 形态识别 |
| GET | `/api/v1/stocks/{code}/earnings` | 财报日历 |
| GET | `/api/v1/market/economic-calendar` | 经济日历 |
| GET | `/api/v1/reports` | 报告列表（分页） |
| GET | `/api/v1/reports/{rid}` | 报告详情 |
| DELETE | `/api/v1/reports/{rid}` | 删除报告 |
| POST | `/api/v1/reports/delete` | 批量删除报告 |
| GET/POST | `/api/v1/config/*` | 配置管理 |

## 📁 项目结构

```
StockWatcher/
├── main.py                    # CLI 入口
├── server.py                  # FastAPI 服务（36 个 API）
├── src/
│   ├── config.py              # 配置管理
│   ├── stock_analyzer.py      # 技术分析引擎
│   ├── formatters.py          # 报告格式化
│   ├── scheduler.py           # 定时调度
│   ├── data_provider/         # 数据源（5 个适配器 + 工厂）
│   ├── llm/                   # LLM 集成（客户端 + 解读 + TimesFM 预测）
│   ├── notification_sender/   # 推送适配器（6 个渠道）
│   ├── core/                  # 核心业务（大盘复盘 + 回测引擎）
│   ├── services/              # 业务服务层（6 个服务）
│   ├── agent/                 # Agent 问股引擎
│   └── utils/                 # 工具函数
├── web/                       # React 前端
│   └── src/
│       ├── pages/             # 8 个功能页面
│       ├── components/        # 5 个可复用组件
│       ├── api/               # API 客户端
│       └── types/             # TypeScript 类型
├── tests/                     # 7 个测试文件
├── .env.example               # 配置模板
└── docs/                      # 文档
```

## 🔧 配置管理

所有配置通过 `.env` 文件管理（详见 `.env.example`），也支持在 Web 仪表盘的 **配置** 页面在线编辑保存。

关键配置项：

| 配置 | 说明 | 默认值 |
|------|------|--------|
| `STOCK_LIST` | 自选股列表（逗号分隔） | 必填 |
| `SCHEDULE_TIME` | 定时分析时间 | `09:30` |
| `SCHEDULE_ENABLED` | 启用定时任务 | `false` |
| `LLM_RELAY_ENABLED` | 启用 LLM 中转站 | `false` |
| `OPENAI_API_KEY` | DeepSeek/OpenAI API Key | — |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | — |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID | — |

## 📊 大盘复盘

```bash
python main.py --market-review
```

## ⏰ 定时任务

```bash
# .env 中配置后
python main.py --schedule
# 或（自动集成定时任务）
python main.py --serve
```

## 📖 文档

| 文档 | 说明 |
|------|------|
| `docs/DATA_SOURCE.md` | 数据源配置 |
| `docs/CONFIG.md` | 完整配置项 |
| `docs/DEPLOY.md` | 部署指南 |
| `docs/API.md` | API 文档 |
| `docs/ARCHITECTURE.md` | 架构说明 |

## 📄 License

MIT
