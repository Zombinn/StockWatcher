"""StockWatcher FastAPI 服务"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.config import setup_env, get_config

setup_env()

from src.logging_config import setup_logging
from webui import router as webui_router

config = get_config()
setup_logging(log_prefix="api", log_dir=config.log_dir)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("StockWatcher API 启动")
    yield
    logger.info("StockWatcher API 关闭")


app = FastAPI(title="StockWatcher API", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(webui_router)


# ====== 基础 ======
@app.get("/")
async def root():
    return {"service": "StockWatcher", "version": "2.0.0", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "ok"}


# ====== 分析 ======
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
                "ma5": result.indicators.ma5, "ma10": result.indicators.ma10,
                "ma20": result.indicators.ma20, "macd": result.indicators.macd,
                "macd_hist": result.indicators.macd_hist,
                "rsi_14": result.indicators.rsi_14,
                "boll_up": result.indicators.boll_up, "boll_low": result.indicators.boll_low,
            },
        },
    }


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
    return {"success": True, "technical": result.__dict__, "llm_analysis": llm_result.__dict__ if llm_result else None}


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
                {"code": p.code, "name": p.name, "quantity": p.quantity,
                 "cost_price": p.cost_price, "current_price": p.current_price,
                 "market_value": p.market_value, "profit_pct": p.profit_pct,
                 "profit_amount": p.profit_amount, "weight": p.weight}
                for p in portfolio.positions
            ],
        },
    }

@app.post("/api/v1/portfolio/positions")
async def add_position(code: str=Query(...), quantity: int=Query(...), cost_price: float=Query(...), name: str=""):
    from src.services.portfolio_service import PortfolioService
    service = PortfolioService()
    service.add_position(code, quantity, cost_price, name)
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
    return {"success": True, "rules": [r.__dict__ for r in rules], "events": [e.__dict__ for e in events], "stats": stats}

@app.post("/api/v1/alerts/rules")
async def add_alert(code: str=Query(...), rule_type: str=Query(...), threshold: float=Query(...), name: str=""):
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
    from src.agent.executor import StockAgent
    agent = StockAgent()
    return {"success": True, "strategies": agent.get_strategies()}

@app.post("/api/v1/agent/session")
async def create_agent_session(code: str=Query(...), name: str=""):
    from src.agent.executor import StockAgent
    agent = StockAgent()
    session_id = await agent.create_session(code, name)
    return {"success": True, "session_id": session_id}

@app.post("/api/v1/agent/chat")
async def agent_chat(session_id: str=Query(...), message: str=Query(...), strategy: str=""):
    from src.agent.executor import StockAgent
    agent = StockAgent()
    response = await agent.chat(session_id, message, strategy)
    return {"success": True, "response": response}


# ====== 回测 ======
@app.get("/api/v1/backtest")
async def backtest(code: str=Query(...), strategy: str=Query("ma_cross"), start_date: str="", end_date: str=""):
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
    """获取所有可配置字段的分组"""
    from src.services.config_service import ConfigManager
    sections = ConfigManager.get_sections()
    return {"success": True, "sections": sections}

@app.get("/api/v1/config/values")
async def get_config_values():
    """获取当前所有配置值（敏感字段脱敏）"""
    from src.services.config_service import ConfigManager
    values = ConfigManager.get_all()
    status = ConfigManager.get_env_file_status()
    return {"success": True, "values": values, "status": status}

@app.post("/api/v1/config/update")
async def update_config(updates: dict):
    """批量更新配置"""
    from src.services.config_service import ConfigManager
    result = ConfigManager.update(updates.get("updates", {}))
    result["success"] = True
    return result

@app.post("/api/v1/config/reset")
async def reset_config():
    """重置为默认配置"""
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
