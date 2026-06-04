"""StockWatcher FastAPI 服务"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from src.config import setup_env, get_config

setup_env()

from src.logging_config import setup_logging

config = get_config()
setup_logging(log_prefix="api", log_dir=config.log_dir)
logger = logging.getLogger(__name__)


_agent = None

def get_agent():
    global _agent
    if _agent is None:
        from src.agent.executor import StockAgent
        _agent = StockAgent()
    return _agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("StockWatcher API 启动")
    yield
    logger.info("StockWatcher API 关闭")


app = FastAPI(title="StockWatcher API", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


# ====== 静态文件 & SPA 路由 ======
web_dist = os.path.join(os.path.dirname(__file__), "web", "dist")
index_html_path = os.path.join(web_dist, "index.html")
assets_dir = os.path.join(web_dist, "assets")

SPA_HTML: str | None = None
if os.path.isfile(index_html_path):
    with open(index_html_path, encoding="utf-8") as f:
        SPA_HTML = f.read()
    logger.info("React 前端已挂载: %s", web_dist)
    # 挂载 /assets/ 静态文件
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.get("/web")
@app.get("/web/{full_path:path}")
async def serve_spa(full_path: str = ""):
    """SPA 前端页面 — 支持任意前端路由"""
    if SPA_HTML:
        return HTMLResponse(SPA_HTML)
    return {"error": "前端未构建，请执行 cd web && npm run build"}


# ====== 基础 ======
@app.get("/")
async def root():
    if SPA_HTML:
        return HTMLResponse(SPA_HTML)
    return {"service": "StockWatcher", "version": "2.0.0", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


# ====== 技术分析 ======
@app.get("/api/v1/analyze")
async def analyze():
    from src.services.analysis_service import AnalysisService
    from src.formatters import format_analysis_report, format_short_notification
    service = AnalysisService(config)
    results = await service.full_analysis()
    report = format_analysis_report(results)
    summaries = {}
    for code, result in results.items():
        summaries[code] = format_short_notification(result)
    return {"success": True, "count": len(results), "report": report, "summaries": summaries}


@app.get("/api/v1/stocks/{code}")
async def analyze_stock(code: str):
    from src.services.analysis_service import AnalysisService
    service = AnalysisService(config)
    result = await service.analyze_single(code)
    if not result:
        raise HTTPException(404, f"无法分析 {code}")
    return {
        "success": True,
        "data": {
            "code": result.code, "name": result.name,
            "price": result.current_price, "change_pct": result.change_pct,
            "score": result.score, "trend": result.trend,
            "signal": result.signal, "risk": result.risk_level,
            "suggestion": result.suggestion,
            "support": result.support, "resistance": result.resistance,
            "indicators": {
                k: getattr(result.indicators, k, 0)
                for k in ("ma5", "ma10", "ma20", "macd", "macd_hist", "rsi_14", "boll_up", "boll_low")
            },
        },
    }



# ====== 智能搜索推荐 ======
@app.get("/api/v1/search/recommend")
async def search_recommend(market: str = "cn", limit: int = 6):
    """根据市场返回推荐股票列表"""
    recommendations = {
        "cn": [
            {"code": "600519", "name": "贵州茅台", "market": "cn"},
            {"code": "000001", "name": "平安银行", "market": "cn"},
            {"code": "000858", "name": "五粮液", "market": "cn"},
            {"code": "600036", "name": "招商银行", "market": "cn"},
            {"code": "601318", "name": "中国平安", "market": "cn"},
            {"code": "300750", "name": "宁德时代", "market": "cn"},
            {"code": "002594", "name": "比亚迪", "market": "cn"},
            {"code": "600276", "name": "恒瑞医药", "market": "cn"},
        ],
        "hk": [
            {"code": "0700.HK", "name": "腾讯控股", "market": "hk"},
            {"code": "9988.HK", "name": "阿里巴巴", "market": "hk"},
            {"code": "0999.HK", "name": "网易", "market": "hk"},
            {"code": "9618.HK", "name": "京东集团", "market": "hk"},
            {"code": "03690.HK", "name": "美团", "market": "hk"},
            {"code": "1810.HK", "name": "小米集团", "market": "hk"},
        ],
        "us": [
            {"code": "AAPL", "name": "Apple", "market": "us"},
            {"code": "TSLA", "name": "Tesla", "market": "us"},
            {"code": "MSFT", "name": "Microsoft", "market": "us"},
            {"code": "AMZN", "name": "Amazon", "market": "us"},
            {"code": "GOOGL", "name": "Alphabet", "market": "us"},
            {"code": "NVDA", "name": "NVIDIA", "market": "us"},
            {"code": "META", "name": "Meta", "market": "us"},
            {"code": "AMD", "name": "AMD", "market": "us"},
        ],
    }
    items = recommendations.get(market, recommendations["cn"])
    return {"success": True, "data": items[:limit]}


@app.get("/api/v1/search/suggest")
async def search_suggest(q: str = "", market: str = "cn", limit: int = 8):
    """智能搜索建议 — 支持代码/名称模糊匹配"""
    from src.services.analysis_service import AnalysisService
    query = q.strip().upper()
    if not query:
        return await search_recommend(market, limit)

    # Known stock map for quick lookup
    STOCK_MAP = {
        # A 股
        "600519": ("600519", "贵州茅台", "cn"),
        "000001": ("000001", "平安银行", "cn"), "000858": ("000858", "五粮液", "cn"),
        "600036": ("600036", "招商银行", "cn"), "601318": ("601318", "中国平安", "cn"),
        "300750": ("300750", "宁德时代", "cn"), "002594": ("002594", "比亚迪", "cn"),
        "600276": ("600276", "恒瑞医药", "cn"), "000333": ("000333", "美的集团", "cn"),
        "002415": ("002415", "海康威视", "cn"), "601012": ("601012", "隆基绿能", "cn"),
        "600887": ("600887", "伊利股份", "cn"),
        # 港股
        "0700.HK": ("0700.HK", "腾讯控股", "hk"), "9988.HK": ("9988.HK", "阿里巴巴", "hk"),
        "0999.HK": ("0999.HK", "网易", "hk"), "03690.HK": ("03690.HK", "美团", "hk"),
        "1810.HK": ("1810.HK", "小米集团", "hk"),
        # 美股
        "AAPL": ("AAPL", "Apple", "us"), "TSLA": ("TSLA", "Tesla", "us"),
        "MSFT": ("MSFT", "Microsoft", "us"), "AMZN": ("AMZN", "Amazon", "us"),
        "GOOGL": ("GOOGL", "Alphabet", "us"), "NVDA": ("NVDA", "NVIDIA", "us"),
        "META": ("META", "Meta", "us"), "AMD": ("AMD", "AMD", "us"),
    }

    results = []
    for code, (c, name, m) in STOCK_MAP.items():
        if market != "all" and m != market:
            continue
        if query in code or query in name.upper():
            results.append({"code": c, "name": name, "market": m})
        if len(results) >= limit:
            break

    # If no local match, try canonical stock code normalization
    if not results:
        # Try to get info from provider
        pass

    return {"success": True, "data": results}


# ====== LLM 解读 ======
@app.get("/api/v1/analyze/llm/{code}")
async def analyze_with_llm(code: str):
    from src.services.analysis_service import AnalysisService
    from src.llm.interpreter import LLMInterpreter
    service = AnalysisService(config)
    result = await service.analyze_single(code)
    if not result:
        raise HTTPException(404, f"无法分析 {code}")
    interpreter = LLMInterpreter()
    llm_result = await interpreter.interpret_technical(result)
    return {
        "success": True,
        "technical": result.__dict__,
        "llm_analysis": llm_result.__dict__ if llm_result else None,
    }


# ====== 大盘复盘 ======
@app.get("/api/v1/market/review")
async def market_review():
    from src.core.market_review import MarketReviewer
    reviewer = MarketReviewer()
    result = await reviewer.review()
    return {
        "success": True,
        "indices": [i.__dict__ for i in result.indices],
        "top_sectors": [s.__dict__ for s in result.top_sectors[:5]],
        "fall_sectors": [s.__dict__ for s in result.fall_sectors[:5]],
        "northbound": result.northbound.__dict__ if result.northbound else None,
        "market_summary": result.market_summary,
        "llm_analysis": result.llm_analysis,
        "timestamp": result.timestamp,
    }


# ====== 持仓管理 ======
@app.get("/api/v1/portfolio")
async def get_portfolio():
    from src.services.portfolio_service import PortfolioService
    service = PortfolioService()
    portfolio = await service.get_portfolio()
    return {
        "success": True,
        "data": {
            "total_cost": portfolio.total_cost,
            "total_market_value": portfolio.total_market_value,
            "total_profit": portfolio.total_profit,
            "total_profit_pct": portfolio.total_profit_pct,
            "risk_score": portfolio.risk_score,
            "suggestion": portfolio.suggestion,
            "positions": [
                {
                    "code": p.code, "name": p.name, "market": p.market,
                    "quantity": p.quantity, "cost_price": p.cost_price,
                    "current_price": p.current_price,
                    "market_value": p.market_value,
                    "profit": p.profit_amount, "profit_pct": p.profit_pct,
                    "weight": (p.market_value / portfolio.total_market_value * 100) if portfolio.total_market_value > 0 else 0,
                }
                for p in portfolio.positions
            ],
        },
    }


@app.post("/api/v1/portfolio/positions")
async def add_position(code: str = Query(...), quantity: int = Query(...), cost_price: float = Query(...), name: str = "", market: str = ""):
    from src.services.portfolio_service import PortfolioService
    service = PortfolioService()
    service.add_position(code, quantity, cost_price, name, market)
    return {"success": True, "message": f"已添加 {code} 持仓"}


@app.delete("/api/v1/portfolio/positions/{code}")
async def remove_position(code: str, quantity: Optional[int] = Query(None)):
    from src.services.portfolio_service import PortfolioService
    service = PortfolioService()
    service.remove_position(code, quantity)
    return {"success": True, "message": f"已更新 {code} 持仓"}


# ====== 告警 ======
@app.get("/api/v1/alerts")
async def get_alerts():
    from src.services.alert_service import AlertEngine
    engine = AlertEngine()
    rules = engine.get_rules()
    events = engine.get_recent_events(10)
    stats = engine.get_stats()
    return {
        "success": True,
        "rules": [r.__dict__ for r in rules],
        "events": [e.__dict__ for e in events],
        "stats": stats,
    }


@app.post("/api/v1/alerts/rules")
async def add_alert(code: str = Query(...), rule_type: str = Query(...), threshold: float = Query(...), name: str = ""):
    from src.services.alert_service import AlertEngine
    engine = AlertEngine()
    rule_id = engine.add_rule(code, rule_type, threshold, name)
    return {"success": True, "rule_id": rule_id}


@app.delete("/api/v1/alerts/rules/{rule_id}")
async def remove_alert(rule_id: str):
    from src.services.alert_service import AlertEngine
    engine = AlertEngine()
    ok = engine.remove_rule(rule_id)
    return {"success": ok}


@app.post("/api/v1/alerts/check")
async def check_alerts():
    from src.services.alert_service import AlertEngine
    engine = AlertEngine()
    events = await engine.check()
    return {"success": True, "triggered": len(events), "events": [e.__dict__ for e in events]}


# ====== Agent 问股 ======
@app.get("/api/v1/agent/strategies")
async def list_strategies():
    agent = get_agent()
    return {"success": True, "strategies": agent.get_strategies()}


@app.post("/api/v1/agent/session")
async def create_agent_session(code: str = Query(...), name: str = ""):
    agent = get_agent()
    session_id = await agent.create_session(code, name)
    return {"success": True, "session_id": session_id}


@app.post("/api/v1/agent/chat")
async def agent_chat(session_id: str = Query(...), message: str = Query(...), strategy: str = ""):
    agent = get_agent()
    response = await agent.chat(session_id, message, strategy)
    return {"success": True, "response": response}


# ====== 回测 ======
@app.get("/api/v1/backtest")
async def backtest(code: str = Query(...), strategy: str = Query("ma_cross"), start_date: str = "", end_date: str = ""):
    from src.core.backtest_engine import BacktestEngine
    engine = BacktestEngine()
    result = await engine.run(code, strategy, start_date, end_date)
    return {
        "success": True,
        "data": {
            "code": result.code, "initial_capital": result.initial_capital,
            "final_value": result.final_value, "total_return": result.total_return,
            "total_return_pct": result.total_return_pct,
            "annual_return": result.annual_return, "max_drawdown": result.max_drawdown,
            "win_rate": result.win_rate, "total_trades": result.total_trades,
            "sharpe_ratio": result.sharpe_ratio,
            "start_date": result.start_date, "end_date": result.end_date,
            "trades": [t.__dict__ for t in result.trades[-20:]],
        },
    }


# ====== 配置管理 ======
@app.get("/api/v1/config/sections")
async def get_config_sections():
    from src.services.config_service import ConfigManager
    sections = ConfigManager.get_sections()
    return {"success": True, "sections": sections}


@app.get("/api/v1/config/values")
async def get_config_values():
    from src.services.config_service import ConfigManager
    values = ConfigManager.get_all()
    status = ConfigManager.get_env_file_status()
    return {"success": True, "values": values, "status": status}


@app.post("/api/v1/config/update")
async def update_config(updates: dict):
    from src.services.config_service import ConfigManager
    result = ConfigManager.update(updates.get("updates", {}))
    result["success"] = True
    return result


@app.post("/api/v1/config/reset")
async def reset_config():
    from src.services.config_service import ConfigManager
    return ConfigManager.reset_to_default()


def start_server(cfg=None) -> None:
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    logger.info("启动 StockWatcher API: http://%s:%d", host, port)
    uvicorn.run("server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    start_server()
