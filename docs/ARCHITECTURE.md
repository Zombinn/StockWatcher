# 🏗️ 架构说明

## 整体架构

```
┌─────────────────────────────────────────────────────┐
│                    Web 前端                           │
│           React + Ant Design (web/dist/)              │
└───────────────┬─────────────────────────────────────┘
                │ HTTP (Vite proxy / FastAPI static)
┌───────────────▼─────────────────────────────────────┐
│                  FastAPI 服务                          │
│           server.py (19+ REST API endpoints)           │
└───────┬───────────────┬───────────────┬─────────────┘
        │               │               │
┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼──────────┐
│  业务服务层   │ │  核心业务   │ │  外部集成        │
│ services/    │ │ core/      │ │ llm/            │
│ - analysis   │ │ - market   │ │ agent/          │
│ - portfolio  │ │ - backtest │ │ notification_   │
│ - alert      │ │            │ │ sender/         │
│ - config     │ │            │ │                 │
└───────┬──────┘ └────────────┘ └─────────────────┘
        │
┌───────▼─────────────────────────────────────────────┐
│                 数据源层                               │
│         data_provider/ (factory + fetcher)            │
│  AkShare → Tushare → TickFlow → YFinance → Finnhub   │
└─────────────────────────────────────────────────────┘
```

## 数据流

### 分析流程

```
用户请求 → AnalysisService
  → StockService.get_kline_history()
    → DataProviderFactory.get_provider_for_code()
      → AkShareProvider.get_kline() / YFinanceProvider.get_kline()
  → StockAnalyzer.analyze()
    → 计算 MA/MACD/RSI/KDJ/BOLL → 趋势判断 → 评分 → 信号
  → (可选) LLMInterpreter.interpret_technical()
  → formatters.format_analysis_report()
  → 推送通知 / 返回 API 响应
```

### 数据源选择逻辑

```
get_provider_for_code(code)
  ├─ A 股（不以 .HK/.US 结尾）
  │   ├─ AkShare（无需要求）→ 成功则返回
  │   ├─ Tushare（需 TUSHARE_TOKEN）→ 成功则返回
  │   └─ TickFlow（需 TICKFLOW_API_KEY）
  └─ 港股/美股
      ├─ YFinance → 成功则返回
      └─ Finnhub（需 FINNHUB_API_KEY）
```

## 模块设计原则

- **数据源适配器模式**: `BaseDataProvider` 定义统一接口，各 fetcher 实现
- **通知器策略模式**: `BaseSender` 定义统一接口，各 sender 实现 + factory
- **依赖注入**: 各 service 通过 `Config` 获取配置，不直接读环境变量
- **异步并发**: `asyncio` + `Semaphore(5)` 控制分析并发
- **SPA 架构**: React 前端独立构建，FastAPI 在生产模式提供静态文件
