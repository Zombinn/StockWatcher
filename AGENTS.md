# StockWatcher - AI 协作规则

## 项目结构

StockWatcher/
├── main.py              # 主入口
├── server.py            # FastAPI 服务
├── webui.py             # Web 前端路由
├── src/
│   ├── config.py        # 配置管理
│   ├── enums.py         # 枚举定义
│   ├── logging_config.py# 日志配置
│   ├── stock_analyzer.py# 技术分析引擎
│   ├── formatters.py    # 报告格式化
│   ├── scheduler.py     # 定时调度
│   ├── data_provider/   # 数据源层（AkShare, YFinance, Tushare...）
│   ├── notification_sender/ # 通知推送
│   └── services/        # 业务逻辑服务
├── data_provider/       # 兼容引用
├── tests/               # 测试
└── api/                 # API schemas (future)

## 规则

- 遵循现有目录边界，不新增平行实现
- 不改动未明确要求的模块行为
- commit message 使用英文
- 不写死密钥、路径
