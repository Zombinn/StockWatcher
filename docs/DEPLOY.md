# 🚀 部署指南

## 本地部署

### 前置要求

```bash
# Python 3.10+
python --version

# 推荐使用虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### 步骤

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置
cp .env.example .env
# 编辑 .env

# 3. 运行
python main.py              # 单次分析
python main.py --serve      # API 服务 + Web
python main.py --schedule   # 定时任务
```

### 后台运行

```bash
# Linux/Mac 使用 nohup
nohup python main.py --serve > stockwatcher.log 2>&1 &

# 或使用 screen
screen -S stockwatcher
python main.py --serve
# Ctrl+A D 分离
```

## 生产部署

### systemd 服务（Linux）

```ini
# /etc/systemd/system/stockwatcher.service
[Unit]
Description=StockWatcher API
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/StockWatcher
ExecStart=/path/to/venv/bin/python main.py --serve
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable stockwatcher
sudo systemctl start stockwatcher
```

### Nginx 反向代理（可选）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 前端构建

```bash
cd web
npm install
npm run build    # 输出到 web/dist/
```

构建后 FastAPI 自动提供静态文件，无需额外配置。

## 数据持久化

以下目录建议备份：

- `data/` — 持仓、告警数据
- `.env` — 配置

`logs/` 和 `reports/` 由 .gitignore 排除。
