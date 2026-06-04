# 🔌 数据源配置

StockWatcher 支持多个数据源，按自动降级链使用。数据源通过 `src/data_provider/factory.py` 管理。

## 数据源一览

| 数据源 | 市场 | 是否需要 Token | 默认优先级 |
|--------|------|---------------|-----------|
| AkShare | A 股 | 否 | 1（A 股首选） |
| YFinance | 港股/美股 | 否 | 1（港美股首选） |
| Tushare Pro | A 股 | 是（`TUSHARE_TOKEN`） | 2（A 股备用） |
| TickFlow | A 股 | 是（`TICKFLOW_API_KEY`） | 3（A 股备用） |
| Finnhub | 美股 | 是（`FINNHUB_API_KEY`） | 2（美股备用） |

## 自动降级链

### A 股

```
请求数据
  → AkShare（无 token，立刻返回）
    → 失败？Tushare（需 TUSHARE_TOKEN）
      → 失败？TickFlow（需 TICKFLOW_API_KEY）
        → 全部失败，返回空
```

### 港股 / 美股

```
请求数据
  → YFinance（无 token，立刻返回）
    → 失败？Finnhub（需 FINNHUB_API_KEY）
      → 全部失败，返回空
```

## 详细配置

### AkShare（A 股首选，无需 Token）

默认可用，不要求任何配置。内置：
- 反爬策略：随机 User-Agent、请求间隔 >= 0.5s
- 备用接口：东方财富 → 新浪财经自动降级

### YFinance（港股/美股首选，无需 Token）

默认可用，不要求任何配置。代码格式：
- 港股：`00700.HK`
- 美股：`AAPL.US` 或 `AAPL`

### Tushare Pro

在 `.env` 中配置：
```
TUSHARE_TOKEN=你的TushareToken
```
从 [tushare.pro](https://tushare.pro) 注册获取。

### TickFlow

```
TICKFLOW_API_KEY=你的TickFlowKey
```
从 [tickflow.org](https://tickflow.org) 注册获取。

### Finnhub（美股）

```
FINNHUB_API_KEY=你的FinnhubKey
```
从 [finnhub.io](https://finnhub.io) 注册获取（免费 tier 60 calls/min）。

## 扩展示例

### 在境外运行

如你身处海外，AkShare 的东财 API 可能因 DNS 不可用而失败，系统会自动降级到新浪备用接口。也可配置 USE_PROXY=true 使用代理。

### 使用 Tushare 替代 AkShare

配置 `TUSHARE_TOKEN` 即可。Tushare 在降级链中优先级高于 TickFlow，低于 AkShare。
