# 🌐 API 接口文档

启动服务后访问 `http://localhost:8000/docs` 查看交互式 Swagger 文档。

## 基础

### `GET /`

服务信息。

### `GET /health`

健康检查。

## 分析

### `GET /api/v1/analyze`

执行全量分析，返回所有自选股的分析报告。

**响应示例：**
```json
{
  "success": true,
  "count": 3,
  "report": "# 📊 StockWatcher 智能分析报告\n...",
  "summaries": {
    "600519": "🟢 贵州茅台(600519)\n价格: 1500.00 | 涨跌: +2.5%..."
  }
}
```

### `GET /api/v1/stocks/{code}`

分析单只股票。

### `GET /api/v1/analyze/llm/{code}`

AI 解读单只股票技术指标。

## 大盘

### `GET /api/v1/market/review`

大盘复盘：指数行情、板块轮动、北向资金。

## 持仓

### `GET /api/v1/portfolio`

获取持仓概览（市值、盈亏、风险评分、仓位建议）。

### `POST /api/v1/portfolio/positions`

添加持仓。

**参数：** `code`, `quantity`, `cost_price`, `name`(可选)

### `DELETE /api/v1/portfolio/positions/{code}`

删除/减仓。可选参数 `quantity`。

## 告警

### `GET /api/v1/alerts`

获取告警规则和最近事件。

### `POST /api/v1/alerts/rules`

添加告警规则。

**参数：** `code`, `rule_type`(price_above/price_below/change_pct/volume), `threshold`

### `DELETE /api/v1/alerts/rules/{rule_id}`

删除告警规则。

### `POST /api/v1/alerts/check`

检查所有规则并触发告警。

## Agent 问股

### `GET /api/v1/agent/strategies`

获取所有分析策略列表。

### `POST /api/v1/agent/session`

创建问股会话。

**参数：** `code`, `name`(可选)

### `POST /api/v1/agent/chat`

发送消息并获取 AI 回复。

**参数：** `session_id`, `message`, `strategy`(可选)

## 回测

### `GET /api/v1/backtest`

执行策略回测。

**参数：** `code`, `strategy`(ma_cross/macd/rsi/bollinger), `start_date`(可选), `end_date`(可选)

## 配置管理

### `GET /api/v1/config/sections`

获取配置分组和字段定义。

### `GET /api/v1/config/values`

获取当前配置值（敏感字段脱敏）。

### `POST /api/v1/config/update`

批量更新配置。

**请求体：** `{"updates": {"STOCK_LIST": "600519,300750", ...}}`

### `POST /api/v1/config/reset`

重置为 .env.example 默认值。
