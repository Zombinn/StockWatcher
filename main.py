# -*- coding: utf-8 -*-
"""
===============================
StockWatcher - 股票智能分析系统
===============================

功能：
  - 技术分析 + LLM AI 解读
  - 大盘复盘（指数/板块/北向资金）
  - 持仓管理（组合盈亏/仓位建议）
  - 告警引擎（价格/指标触发）
  - Agent 问股（多轮对话策略分析）
  - 回测引擎（MA/MACD/RSI/布林带）
  - FastAPI 服务 + Web 仪表盘

使用方式：
    python main.py                     # 单次分析
    python main.py --market-review     # 大盘复盘
    python main.py --schedule          # 定时任务
    python main.py --serve             # API 服务
    python main.py --debug             # 调试模式
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from src.config import setup_env, get_config, reload_config

setup_env()

if os.getenv("GITHUB_ACTIONS") != "true" and os.getenv("USE_PROXY", "false").lower() == "true":
    proxy_host = os.getenv("PROXY_HOST", "127.0.0.1")
    proxy_port = os.getenv("PROXY_PORT", "10809")
    os.environ["http_proxy"] = f"http://{proxy_host}:{proxy_port}"
    os.environ["https_proxy"] = f"http://{proxy_host}:{proxy_port}"

from src.logging_config import setup_logging
from src.services.analysis_service import AnalysisService
from src.formatters import format_analysis_report, format_short_notification
from src.notification_sender.factory import send_to_all

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="StockWatcher - 股票智能分析系统")
    p.add_argument("--debug", action="store_true", help="调试模式")
    p.add_argument("--dry-run", action="store_true", help="仅获取数据不推送")
    p.add_argument("--serve", action="store_true", help="启动 API 服务")
    p.add_argument("--schedule", action="store_true", help="定时任务模式")
    p.add_argument("--market-review", action="store_true", help="大盘复盘模式")
    p.add_argument("--backtest", type=str, default="", help="回测股票代码")
    p.add_argument("--strategy", type=str, default="ma_cross", help="回测策略")
    p.add_argument("--agent", type=str, default="", help="Agent 问股代码")
    p.add_argument("--no-notify", action="store_true", help="不发送通知")
    p.add_argument("--force-run", action="store_true", help="强制运行")
    return p.parse_args()


async def run_analysis(config, dry_run: bool = False, no_notify: bool = False) -> None:
    """执行分析流程"""
    service = AnalysisService(config)
    results = await service.full_analysis()
    if not results:
        logger.warning("分析结果为空")
        return

    # AI 解读
    llm_interpretations = {}
    from src.llm.interpreter import LLMInterpreter
    interpreter = LLMInterpreter()
    if interpreter.client:
        logger.info("LLM 客户端已配置，开始 AI 解读...")
        for code, result in results.items():
            llm = await interpreter.interpret_technical(result)
            if llm:
                llm_interpretations[code] = llm

    # 生成报告
    report = format_analysis_report(results)

    if llm_interpretations:
        report += "\n## 🤖 AI 解读\n"
        for code, llm in llm_interpretations.items():
            report += f"\n### {results[code].name}({code}) AI 分析\n"
            report += f"- **结论**: {llm.summary}\n"
            report += f"- **趋势分析**: {llm.trend_analysis}\n"
            report += f"- **技术解读**: {llm.technical_insight}\n"
            report += f"- **操作建议**: {llm.operation_advice}\n"
            if llm.risk_warning:
                report += f"- ⚠️ **风险提示**: {llm.risk_warning}\n"

    # 保存报告
    report_dir = Path(config.log_dir) / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_file.write_text(report, encoding="utf-8")
    logger.info("分析报告已保存: %s", report_file)
    print("\n" + report)

    if no_notify:
        return

    from src.formatters import SIGNAL_LEGEND

    # 为每只股票获取 TimesFM 预测
    forecasts = {}
    try:
        from src.llm.timesfm_forecaster import forecast as tfm_forecast
        from src.services.stock_service import StockService
        stock_service = StockService(config)
        logger.info("开始获取 TimesFM 预测（首次将加载模型 ~880MB，需等待）...")
        for code in results:
            try:
                logger.info("TimesFM 获取 K 线: %s", code)
                klines = await stock_service.get_kline_history(code, count=60)
                if klines:
                    logger.info("TimesFM K 线获取成功: %s, %d 条", code, len(klines))
                    fc = await tfm_forecast(klines, horizon=5)
                    if fc and fc.forecast:
                        forecasts[code] = fc
                        logger.info("TimesFM 预测成功: %s → 前5天: %s", code,
                                    " ".join(f"{v:.1f}" for v in fc.forecast[:5]))
                    else:
                        logger.info("TimesFM 预测无结果: %s", code)
                else:
                    logger.info("TimesFM K 线为空: %s", code)
            except Exception as e:
                logger.warning("TimesFM 预测失败 %s: %s", code, e)
        if forecasts:
            logger.info("TimesFM 预测完成: %d 只股票", len(forecasts))
        else:
            logger.info("TimesFM 无预测结果")
    except Exception as e:
        logger.warning("TimesFM 预测模块异常: %s", e)

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
    await send_to_all("\n".join(summary_lines), title="StockWatcher 分析报告")


async def run_market_review(config) -> None:
    """执行大盘复盘"""
    from src.core.market_review import MarketReviewer
    reviewer = MarketReviewer()
    result = await reviewer.review()
    print("\n" + "=" * 60)
    print(result.market_summary)
    if result.llm_analysis:
        print("\n🤖 AI 分析:")
        for k, v in result.llm_analysis.items():
            print(f"  {k}: {v}")
    print("=" * 60)

    from src.formatters import format_analysis_report
    from src.notification_sender.factory import send_to_all
    await send_to_all(result.market_summary, title="大盘复盘")


async def run_backtest(config, code: str, strategy: str) -> None:
    """执行回测"""
    from src.core.backtest_engine import BacktestEngine
    engine = BacktestEngine()
    result = await engine.run(code, strategy)
    print("\n" + "=" * 60)
    print(f"📊 回测报告: {code}")
    print(f"策略: {strategy}")
    print(f"初始资金: {result.initial_capital:.2f}")
    print(f"最终价值: {result.final_value:.2f}")
    print(f"总收益: {result.total_return:+.2f} ({result.total_return_pct:+.2f}%)")
    print(f"最大回撤: {result.max_drawdown:.2f}%")
    print(f"交易次数: {result.total_trades}")
    print(f"胜率: {result.win_rate:.1f}%")
    print(f"夏普比率: {result.sharpe_ratio:.2f}")
    print("=" * 60)


def run_sync(config, dry_run: bool = False, no_notify: bool = False) -> None:
    """定时任务调度器的同步入口。"""
    asyncio.run(run_analysis(config, dry_run, no_notify))


def main() -> int:
    args = parse_args()
    config = get_config()
    setup_logging(log_prefix="stockwatcher", debug=args.debug, log_dir=config.log_dir)
    logging.getLogger().setLevel(logging.DEBUG if args.debug else logging.INFO)

    logger.info("=" * 50)
    logger.info("StockWatcher v2.0 启动")

    try:
        if args.serve:
            logger.info("启动 API + 定时任务模式")
            from src.scheduler import Scheduler
            if config.schedule_enabled:
                scheduler = Scheduler()
                scheduler.add_job(
                    task=lambda: run_sync(reload_config(), dry_run=args.dry_run, no_notify=args.no_notify),
                    schedule_time=config.schedule_time,
                    run_immediately=config.run_immediately,
                    name="daily_analysis",
                )
                # 调度器自带阻塞循环，放后台线程，避免挡住 API 启动
                import threading
                t = threading.Thread(target=scheduler.start, daemon=True)
                t.start()
                logger.info("定时任务已在后台启动，下次执行时间: %s，线程ID: %s", config.schedule_time, t.native_id)
            import os
            os.environ["_SW_SERVE_MODE"] = "1"
            from server import start_server
            start_server(config)
            return 0

        if args.market_review:
            logger.info("大盘复盘模式")
            asyncio.run(run_market_review(config))
            return 0

        if args.backtest:
            logger.info("回测模式: %s [%s]", args.backtest, args.strategy)
            asyncio.run(run_backtest(config, args.backtest, args.strategy))
            return 0

        if args.agent:
            logger.info("Agent 问股模式: %s", args.agent)

        if args.schedule or config.schedule_enabled:
            logger.info("定时任务模式")
            from src.scheduler import Scheduler
            scheduler = Scheduler()
            scheduler.add_job(
                task=lambda: run_sync(reload_config(), args.dry_run, args.no_notify),
                schedule_time=config.schedule_time,
                run_immediately=config.run_immediately,
                name="daily_analysis",
            )
            scheduler.start()
            return 0

        # 单次运行
        run_sync(config, args.dry_run, args.no_notify)
        logger.info("分析完成 ✓")
        return 0

    except KeyboardInterrupt:
        logger.info("用户中断")
        return 130
    except Exception as e:
        logger.exception("执行失败: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
