# 📊 StockWatcher - 股票智能分析系统

基于 AI 与技术的 A 股/港股/美股自选股智能分析系统。

## 功能

- **多数据源**: AkShare（A 股）、YFinance（港股/美股）
- **技术分析**: MA、MACD、RSI、KDJ、BOLL、ATR、乖离率
- **综合评分**: 0-100 分，含趋势判断、买卖信号、风险等级
- **多通道推送**: 企业微信、飞书、Telegram、Discord、Slack
- **Web 仪表盘**: 浏览器可视化分析报告
- **定时任务**: 每日自动分析 + 推送
- **API 服务**: FastAPI 提供 RESTful 接口

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 STOCK_LIST 和至少一个 LLM/通知渠道

# 3. 运行分析
python main.py

# 4. 启动 API 服务
python main.py --serve
# 访问 http://localhost:8000/web
```

## 项目结构

```
StockWatcher/
├── main.py                  # 主入口
├── server.py                # FastAPI 服务
├── webui.py                 # Web 前端
├── src/
│   ├── config.py            # 配置管理
│   ├── stock_analyzer.py    # 技术分析引擎
│   ├── formatters.py        # 报告格式化
│   ├── data_provider/       # 数据源适配
│   ├── notification_sender/ # 通知推送
│   └── services/            # 业务服务
└── tests/
```

## 配置说明

详见 `.env.example`。

## TODO

- [ ] LLM 分析集成（AI 解读）
- [ ] 大盘复盘模块
- [ ] 持仓管理
- [ ] 告警系统
- [ ] Agent 问股
- [ ] 回测引擎
- [ ] 更多数据源（Tushare、TickFlow）
- [ ] Docker 部署
- [ ] GitHub Actions 自动化

## License

MIT
