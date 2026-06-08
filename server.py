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
    # TimesFM 在后台线程预加载，不阻塞服务启动
    import asyncio as _aio
    async def _warmup_timesfm():
        try:
            from src.utils.blocking import run_blocking
            from src.llm.timesfm_forecaster import _load_model
            await run_blocking(_load_model)
            logger.info("TimesFM 模型预加载完成")
        except Exception as e:
            logger.warning("TimesFM 预加载失败（不影响其他功能）: %s", e)
    _aio.create_task(_warmup_timesfm())
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
import asyncio as _asyncio
_analyze_task: Optional[_asyncio.Task] = None


async def _run_analysis_background() -> None:
    """在后台执行分析并填充缓存，不阻塞请求"""
    global _analyze_task
    from src.utils.cache import get_cached, set_cached
    from src.services.analysis_service import AnalysisService
    from src.formatters import format_analysis_report, format_short_notification
    try:
        service = AnalysisService(config)
        results = await service.full_analysis()
        report = format_analysis_report(results)
        summaries, stocks = {}, []
        import math

        def _safe(v):
            return 0.0 if (isinstance(v, float) and not math.isfinite(v)) else v

        for code, r in results.items():
            summaries[code] = format_short_notification(r)
            stocks.append({
                "code": code, "name": r.name or code,
                "price": _safe(r.current_price), "change_pct": _safe(r.change_pct),
                "score": _safe(r.score), "trend": r.trend,
                "signal": r.signal, "risk": r.risk_level, "suggestion": r.suggestion,
                "support": _safe(r.support), "resistance": _safe(r.resistance),
            })
        stocks.sort(key=lambda s: s["score"], reverse=True)
        from src.services.report_service import get_report_service
        from src.utils.cache import set_cached
        set_cached("analyze", {"success": True, "count": len(results), "stocks": stocks,
                                "report": report, "summaries": summaries})
        try:
            get_report_service().save_current_analysis({"success": True, "count": len(results), "stocks": stocks, "report": report, "summaries": summaries}, report)
        except Exception as _re:
            logger.warning("保存报告失败: %s", _re)
        logger.info("后台分析完成，%d 只股票", len(results))
    except Exception as e:
        logger.error("后台分析失败: %s", e)
    finally:
        _analyze_task = None


@app.get("/api/v1/analyze")
async def analyze():
    global _analyze_task
    from src.utils.cache import get_cached
    cached = get_cached("analyze", ttl=300)
    if cached is not None:
        return cached  # 命中缓存，立即返回

    # 缓存未命中：启动后台任务，立即返回 loading 状态
    if _analyze_task is None or _analyze_task.done():
        _analyze_task = _asyncio.create_task(_run_analysis_background())
        logger.info("已触发后台分析任务")
    return {"success": True, "loading": True, "count": 0, "stocks": [], "report": "", "summaries": {}}


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
        from src.services.report_service import get_report_service
        from src.notification_sender.factory import send_to_all
        service = AnalysisService(config)
        results = await service.full_analysis()
        if not results:
            logger.warning("分析结果为空")
            return
        report = format_analysis_report(results)
        
        # 自动保存报告
        try:
            from src.utils.cache import get_cached
            cached = get_cached("analyze", ttl=300)
            if cached:
                get_report_service().save_current_analysis(cached, report)
        except Exception as e:
            logger.warning("保存报告失败: %s", e)
        
        # TimesFM 预测
        forecasts = {}
        try:
            from src.llm.timesfm_forecaster import forecast as tfm_forecast
            from src.services.stock_service import StockService
            logger.info("开始获取 TimesFM 预测...")
            stock_service = StockService(config)
            for code in results:
                try:
                    klines = await stock_service.get_kline_history(code, count=60)
                    if klines:
                        fc = await tfm_forecast(klines, horizon=5)
                        if fc and fc.forecast:
                            forecasts[code] = fc
                except Exception as e:
                    logger.warning("TimesFM 预测失败 %s: %s", code, e)
        except Exception as e:
            logger.warning("TimesFM 模块异常: %s", e)
        
        from src.formatters import SIGNAL_LEGEND
        summary_lines = [f"📊 StockWatcher 分析简报\n{SIGNAL_LEGEND}\n"]
        for code, result in results.items():
            line = format_short_notification(result)
            fc = forecasts.get(code)
            if fc and fc.forecast:
                dates_fmt = "/".join(d[-5:] for d in fc.dates[:5])
                vals_fmt = " ".join(f"{v:.1f}" for v in fc.forecast[:5])
                line += f"\n📈 TimesFM预测: {dates_fmt} → {vals_fmt}"
            summary_lines.append(line)
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



# ====== K 线数据 ======
@app.get("/api/v1/stocks/{code:str}/kline")
async def stock_kline(code: str, count: int = 60, period: str = "daily"):
    """获取股票 K 线数据（支持日/周/月）"""
    from src.services.stock_service import StockService
    stock_service = StockService(config)
    klines = await stock_service.get_kline_history(code, count=count)
    if not klines:
        raise HTTPException(404, f"无法获取 {code} 的 K 线数据")
    
    items = []
    for k in klines:
        items.append({
            "date": k.date,
            "open": k.open,
            "high": k.high,
            "low": k.low,
            "close": k.close,
            "volume": k.volume,
            "amount": k.amount,
            "change_pct": k.change_pct,
        })
    return {"success": True, "code": code, "count": len(items), "items": items}


# ====== 形态识别 ======
@app.get("/api/v1/stocks/{code:str}/patterns")
async def stock_patterns(code: str):
    """识别 K 线形态"""
    from src.services.stock_service import StockService
    from src.stock_analyzer import PatternRecognizer
    stock_service = StockService(config)
    klines = await stock_service.get_kline_history(code, count=120)
    if not klines:
        raise HTTPException(404, f"无法获取 {code} 的 K 线数据")
    recognizer = PatternRecognizer()
    patterns = recognizer.analyze(klines)
    return {"success": True, "code": code, "patterns": [p.__dict__ for p in patterns]}


# ====== 财报日历 ======
@app.get("/api/v1/stocks/{code:str}/earnings")
async def stock_earnings(code: str):
    """获取财报日历（近 4 个季度）"""
    import akshare as ak
    import pandas as pd
    import re
    
    # 提取纯数字代码
    code_num = re.sub(r'[^0-9]', '', code)
    sh_code = f"sh{code_num}" if code.startswith(("SH", "sh", "6")) else f"sz{code_num}"
    
    try:
        df = ak.stock_financial_report_sina(stock=sh_code, symbol="利润表")
        if df is not None and not df.empty and "基本每股收益" in df.columns and "公告日期" in df.columns:
            df = df.sort_values("报告日", ascending=False).head(4)
            earnings = []
            for _, row in df.iterrows():
                report_date = str(row.get("报告日", ""))
                if len(report_date) >= 7:
                    quarter_num = (int(report_date[4:6]) - 1) // 3 + 1
                    q_label = f"{report_date[:4]}Q{quarter_num}"
                else:
                    q_label = report_date
                eps = row.get("基本每股收益")
                eps_val = float(eps) if pd.notna(eps) and eps else None
                notice = row.get("公告日期", "")
                notice_str = str(notice)[:10] if pd.notna(notice) else ""
                earnings.append({
                    "quarter": q_label,
                    "date": notice_str or report_date[:10],
                    "actual_eps": eps_val,
                })
            return {"success": True, "code": code, "earnings": earnings}
    except Exception as e:
        logger.warning("获取 %s 财报失败: %s", code, e)
    
    # 降级：返回季度标签
    import datetime
    today = datetime.date.today()
    quarters = []
    for i in range(4):
        q_num = (today.month - 1) // 3 - i
        year = today.year + (q_num - 1) // 4 if q_num <= 0 else today.year
        q = (q_num - 1) % 4 + 1 if q_num > 0 else (q_num % 4 + 4) % 4 + 1
        quarters.append({
            "quarter": f"{year}Q{q}",
            "date": f"{year}-{(q*3):02d}-15",
            "actual_eps": None,
        })
    return {"success": True, "code": code, "earnings": list(reversed(quarters))}


# ====== TimesFM 价格预测 ======
@app.get("/api/v1/stocks/{code:str}/forecast")
async def stock_forecast(code: str, horizon: int = 14):
    """TimesFM 时间序列预测：基于历史 K 线预测未来 horizon 个交易日价格"""
    from src.utils.cache import get_cached, set_cached
    cache_key = f"forecast_{code}_{horizon}"
    cached = get_cached(cache_key, ttl=3600)   # 预测结果缓存 1 小时
    if cached:
        return cached

    from src.services.stock_service import StockService
    from src.llm.timesfm_forecaster import forecast as tfm_forecast
    stock_service = StockService(config)
    klines = await stock_service.get_kline_history(code, count=min(horizon * 8, 512))
    if not klines:
        raise HTTPException(404, f"无法获取 {code} 的行情数据")

    result = await tfm_forecast(klines, horizon=horizon)
    if not result:
        raise HTTPException(503, "TimesFM 预测失败（数据不足或模型未就绪）")

    payload = {
        "success": True, "code": code, "horizon": horizon,
        "model": result.model,
        "last_date": result.last_date, "last_price": result.last_price,
        "dates": result.dates,
        "forecast": result.forecast,
        "lower_90": result.lower_90, "upper_90": result.upper_90,
        "lower_80": result.lower_80, "upper_80": result.upper_80,
    }
    set_cached(cache_key, payload)
    return payload


# ====== 个股新闻 ======
@app.get("/api/v1/stocks/{code:str}/news")
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
            "all_sectors": [s.__dict__ for s in result.top_sectors] + [s.__dict__ for s in result.fall_sectors],
            "northbound": result.northbound.__dict__ if result.northbound else None,
            "market_summary": result.market_summary,
            "llm_analysis": result.llm_analysis,
            "timestamp": result.timestamp,
        }

    return await cached_call("market_review", 300, _compute)


# ====== 经济日历 ======
@app.get("/api/v1/market/economic-calendar")
async def economic_calendar(days: int = 90):
    from src.core.economic_calendar import fetch_economic_calendar
    events = await fetch_economic_calendar(days)
    return {"success": True, "events": events}


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


# ====== 回测报告 ======
@app.post("/api/v1/backtest/report")
async def backtest_report(payload: dict):
    from src.core.backtest_engine import BacktestEngine
    code = payload.get("code", "")
    strategy = payload.get("strategy", "ma_cross")
    start_date = payload.get("start_date", "")
    end_date = payload.get("end_date", "")
    fmt = payload.get("format", "markdown")
    engine = BacktestEngine()
    result = await engine.run(code, strategy, start_date, end_date)
    is_pos = result.total_return_pct >= 0
    md = f"# {'📈' if is_pos else '📉'} {result.code} Backtest Report\n\n"
    md += f"**Strategy**: {strategy}  **Period**: {result.start_date} ~ {result.end_date}\n\n"
    md += "## Performance\n\n| Metric | Value |\n|--------|-------|\n"
    md += f"| Initial Capital | {result.initial_capital:,.2f} |\n"
    md += f"| Final Value | {result.final_value:,.2f} |\n"
    md += f"| Total Return | {result.total_return_pct:+.2f}% |\n"
    md += f"| Annual Return | {(result.annual_return or 0) * 100:+.2f}% |\n"
    md += f"| Max Drawdown | {result.max_drawdown:.2f}% |\n"
    md += f"| Win Rate | {result.win_rate:.2f}% |\n"
    md += f"| Sharpe Ratio | {result.sharpe_ratio:.2f} |\n"
    md += f"| Total Trades | {result.total_trades} |\n\n"
    md += "## Trades\n\n"
    if result.trades:
        for t in result.trades[-30:]:
            act = "BUY" if t.action == "buy" else "SELL"
            md += f"- `{t.date}` **{act}** @ {t.price:.2f} x {t.shares} = {t.amount:,.2f} -- {t.reason}\n"
    else:
        md += "No trades generated.\n"
    if fmt == "html":
        html = "<html><body><pre>" + md.replace("\n", "<br>") + "</pre></body></html>"
        return {"success": True, "content": html, "format": "html"}
    return {"success": True, "content": md, "format": "markdown"}


@app.post("/api/v1/backtest/report/save")
async def backtest_report_save(payload: dict):
    from src.services.report_service import get_report_service
    code = payload.get("code", "")
    content = payload.get("content", "")
    fmt = payload.get("format", "markdown")
    service = get_report_service()
    rid = service.save(
        title=f"Backtest Report {code}",
        summary=content[:200],
        stock_count=1,
        details={"code": code, "backtest_report": content, "format": fmt},
    )
    return {"success": True, "report_id": rid}


# ====== 报告管理 ======
@app.get("/api/v1/reports")
async def list_reports(page: int = 1, page_size: int = 10):
    from src.services.report_service import get_report_service
    service = get_report_service()
    items, total = service.list(page, page_size)
    return {"success": True, "items": items, "total": total, "page": page, "page_size": page_size}


@app.get("/api/v1/reports/{rid}")
async def get_report(rid: str):
    from src.services.report_service import get_report_service
    service = get_report_service()
    record = service.get(rid)
    if not record:
        from fastapi import HTTPException
        raise HTTPException(404, "报告不存在")
    return {"success": True, "data": record}


@app.delete("/api/v1/reports/{rid}")
async def delete_report(rid: str):
    from src.services.report_service import get_report_service
    service = get_report_service()
    ok = service.delete(rid)
    return {"success": ok, "message": "已删除" if ok else "报告不存在"}


@app.post("/api/v1/reports/delete")
async def delete_reports_batch(payload: dict):
    from src.services.report_service import get_report_service
    rids = payload.get("ids", [])
    service = get_report_service()
    count = service.delete_multi(rids)
    return {"success": True, "deleted": count}


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
