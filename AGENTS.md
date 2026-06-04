# StockWatcher - AI 协作规则

## 项目定位

股票智能分析系统，覆盖 A 股、港股、美股。

## 目录边界

```
StockWatcher/
├── main.py                  # CLI 入口
├── server.py                # FastAPI 服务
├── src/
│   ├── config.py            # 配置管理
│   ├── stock_analyzer.py    # 技术分析引擎
│   ├── formatters.py        # 报告格式化
│   ├── scheduler.py         # 定时调度
│   ├── data_provider/       # 数据源（base + fetcher + factory）
│   ├── notification_sender/ # 通知推送（base + sender + factory）
│   ├── llm/                 # LLM 集成（client + interpreter）
│   ├── core/                # 核心业务（market_review + backtest）
│   ├── services/            # 业务服务层
│   └── agent/               # Agent 问股
├── web/                     # React + Ant Design 前端
├── tests/                   # 测试
└── docs/                    # 文档
```

## 规则

- 后端逻辑放 `src/` 下对应子目录，不新增目录层次
- 前端改动在 `web/src/pages/`，API 调用在 `web/src/api/index.ts`
- 数据源新增在 `src/data_provider/` + 注册到 `factory.py`
- 通知渠道新增在 `src/notification_sender/` + 注册到 `factory.py`
- `.env.example` 同步更新新增配置项
- 不写死密钥、路径、端口、模型名
- commit message 使用英文
