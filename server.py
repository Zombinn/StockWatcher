"""StockWatcher FastAPI 服务"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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

WEB_BUILT = os.path.isfile(index_html_path)
if WEB_BUILT:
    logger.info("React 前端已挂载: %s", web_dist)
    # 挂载 /assets/ 静态文件
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


def _spa_response():
    """每次请求实时读取 index.html，前端重新构建后无需重启服务即可生效"""
    # 禁用缓存，避免浏览器命中已失效的旧 bundle 哈希
    return FileResponse(index_html_path, headers={"Cache-Control": "no-cache"})


@app.get("/web")
@app.get("/web/{full_path:path}")
async def serve_spa(full_path: str = ""):
    """SPA 前端页面 — 支持任意前端路由"""
    if WEB_BUILT:
        return _spa_response()
    return {"error": "前端未构建，请执行 cd web && npm run build"}


# ====== 基础 ======
@app.get("/")
async def root():
    if WEB_BUILT:
        return _spa_response()
    return {"service": "StockWatcher", "version": "2.0.0", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


# ====== 技术分析 ======
@app.get("/api/v1/analyze")
async def analyze():
    from src.utils.cache import cached_call

    async def _compute():
        from src.services.analysis_service import AnalysisService
        from src.formatters import format_analysis_report, format_short_notification
        service = AnalysisService(config)
        results = await service.full_analysis()
        report = format_analysis_report(results)
        summaries = {}
        stocks = []
        for code, r in results.items():
            summaries[code] = format_short_notification(r)
            stocks.append({
                "code": code, "name": r.name, "price": r.current_price,
                "change_pct": r.change_pct, "score": r.score, "trend": r.trend,
                "signal": r.signal, "risk": r.risk_level, "suggestion": r.suggestion,
                "support": r.support, "resistance": r.resistance,
            })
        stocks.sort(key=lambda s: s["score"], reverse=True)
        return {"success": True, "count": len(results), "stocks": stocks, "report": report, "summaries": summaries}

    return await cached_call("analyze", 300, _compute)


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




# ====== 选股筛选 ======
@app.get("/api/v1/screen")
async def screen_stocks(market: str = "cn", strategy: str = "top_gainers", limit: int = 12):
    """真实行情 + 技术分析选股（非静态列表）"""
    from src.services.screening_service import screen
    results = await screen(market, strategy, limit)
    return {"success": True, "count": len(results), "data": results}


# ====== 手动触发分析 ======
@app.post("/api/v1/analyze/trigger")
async def trigger_analysis():
    """手动触发全量分析（用于测试）"""
    import asyncio
    logger.info("手动触发全量分析")
    
    async def _run():
        from src.services.analysis_service import AnalysisService
        from src.formatters import format_analysis_report, format_short_notification
        from src.notification_sender.factory import send_to_all
        service = AnalysisService(config)
        results = await service.full_analysis()
        if not results:
            logger.warning("分析结果为空")
            return
        report = format_analysis_report(results)
        summary_lines = ["📊 StockWatcher 分析简报\n"]
        for code, result in results.items():
            summary_lines.append(format_short_notification(result))
            summary_lines.append("")
        await send_to_all("\n".join(summary_lines), title="StockWatcher 手动触发分析")
        logger.info("手动分析完成，已推送通知")
    
    asyncio.create_task(_run())
    return {"success": True, "message": "分析任务已启动，完成后将通过通知推送"}


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
    """智能搜索建议 — 支持代码/名称/拼音(全拼+首字母)模糊匹配"""
    if not q.strip():
        return await search_recommend(market, limit)
    from src.services.stock_search import search_stocks
    results = search_stocks(q, market, limit)
    return {"success": True, "data": results}


# ====== 个股新闻 ======
@app.get("/api/v1/stocks/{code}/news")
async def stock_news(code: str, limit: int = 10):
    """获取个股相关新闻/资讯"""
    from src.data_provider.news_fetcher import get_stock_news
    items = await get_stock_news(code, limit)
    return {"success": True, "count": len(items), "data": [i.__dict__ for i in items]}


# ====== 交易日历 ======
@app.get("/api/v1/market/trading-day")
async def trading_day(date: str = ""):
    """交易日/节假日判断（不传 date 默认今天）"""
    from src.utils import trading_calendar as tc
    d = date or None
    return {
        "success": True,
        "date": date or str(__import__("datetime").date.today()),
        "is_trading_day": tc.is_trading_day(d),
        "next_trading_day": str(tc.next_trading_day(d)),
        "prev_trading_day": str(tc.prev_trading_day(d)),
        "recent_trading_days": tc.recent_trading_days(5, d),
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
    return {
        "success": True,
        "technical": result.__dict__,
        "llm_analysis": llm_result.__dict__ if llm_result else None,
    }


# ====== 大盘复盘 ======
@app.get("/api/v1/market/review")
async def market_review():
    from src.utils.cache import cached_call

    async def _compute():
        from src.core.market_review import MarketReviewer
        result = await MarketReviewer().review()
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

    return await cached_call("market_review", 300, _compute)


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


@app.post("/api/v1/portfolio/import")
async def import_positions(payload: dict):
    """批量导入持仓 — 支持 CSV/Excel/剪贴板粘贴的文本（每行: 代码,数量,成本价[,名称]）"""
    from src.services.portfolio_service import PortfolioService
    text = (payload or {}).get("text", "")
    if not text.strip():
        raise HTTPException(400, "导入内容为空")
    service = PortfolioService()
    result = service.import_positions(text)
    result["success"] = True
    return result


# ====== 代码下拉（自选 + 持仓去重） ======
@app.get("/api/v1/symbols")
async def get_symbols():
    """自选股 + 持仓去重后的股票代码，供输入框下拉选择（仅读文件，快速）"""
    from src.services.watchlist_service import WatchlistService
    from src.services.portfolio_service import PortfolioService, _detect_market
    merged: dict = {}
    for code in WatchlistService().get_codes():
        cu = code.strip().upper()
        if cu:
            merged[cu] = {"code": cu, "name": "", "market": _detect_market(cu), "source": "watchlist"}
    for code, pos in PortfolioService()._positions.items():
        cu = code.strip().upper()
        name = pos.get("name") or ""
        if cu in merged:
            if name:
                merged[cu]["name"] = name
            merged[cu]["source"] = "both"
        else:
            merged[cu] = {"code": cu, "name": name, "market": pos.get("market") or _detect_market(cu), "source": "portfolio"}
    return {"success": True, "count": len(merged), "data": list(merged.values())}


# ====== 自选股 ======
@app.get("/api/v1/watchlist")
async def get_watchlist():
    from src.utils.cache import cached_call

    async def _compute():
        from src.services.watchlist_service import WatchlistService
        quotes = await WatchlistService().get_quotes()
        return {"success": True, "count": len(quotes), "data": quotes}

    return await cached_call("watchlist", 60, _compute)


@app.post("/api/v1/watchlist")
async def add_watchlist(code: str = Query(...)):
    from src.services.watchlist_service import WatchlistService
    from src.utils.cache import drop
    service = WatchlistService()
    added = service.add(code)
    drop("analyze"); drop("watchlist")  # 自选股变更后让分析/自选缓存失效
    return {"success": True, "added": added, "codes": service.get_codes()}


@app.delete("/api/v1/watchlist/{code}")
async def remove_watchlist(code: str):
    from src.services.watchlist_service import WatchlistService
    from src.utils.cache import drop
    service = WatchlistService()
    removed = service.remove(code)
    drop("analyze"); drop("watchlist")
    return {"success": True, "removed": removed, "codes": service.get_codes()}


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
