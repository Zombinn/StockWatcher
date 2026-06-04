"""分析服务 - 协调多只股票的分析"""
from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional

from src.config import Config
from src.data_provider.base import BaseDataProvider, canonical_stock_code
from src.data_provider.factory import get_provider_for_code
from src.services.stock_service import StockService
from src.stock_analyzer import AnalysisResult, StockAnalyzer

logger = logging.getLogger(__name__)


class AnalysisService:
    """分析服务"""

    def __init__(self, config: Optional[Config] = None):
        from src.config import get_config
        self.config = config or get_config()
        self.analyzer = StockAnalyzer()
        self.stock_service = StockService(self.config)

    async def analyze_single(self, code: str) -> Optional[AnalysisResult]:
        """分析单只股票"""
        klines = await self.stock_service.get_kline_history(code)
        if not klines:
            logger.warning("未能获取 %s 的 K 线数据", code)
            return None

        name = ""
        if klines:
            name = klines[0].code  # fallback
        info = await self.stock_service.get_stock_info(code)
        if info:
            name = info.name

        return self.analyzer.analyze(klines, name=name)

    async def analyze_batch(self, codes: List[str]) -> Dict[str, AnalysisResult]:
        """批量分析股票（并发执行）"""
        sem = asyncio.Semaphore(5)  # 限制并发数

        async def _analyze_one(code: str) -> Optional[tuple[str, AnalysisResult]]:
            async with sem:
                try:
                    result = await self.analyze_single(code)
                    if result:
                        return code, result
                except Exception as e:
                    logger.error("分析 %s 失败: %s", code, e)
                return None

        tasks = [_analyze_one(code) for code in codes]
        results_list = await asyncio.gather(*tasks)

        results = {}
        for item in results_list:
            if item:
                code, result = item
                results[code] = result

        return results

    async def full_analysis(self) -> Dict[str, AnalysisResult]:
        """完整分析所有自选股"""
        stock_list = self.config.stock_list
        if not stock_list:
            logger.warning("未配置自选股 (STOCK_LIST)")
            return {}

        logger.info("开始分析 %d 只股票", len(stock_list))
        results = await self.analyze_batch(stock_list)
        logger.info("分析完成，成功 %d 只", len(results))
        return results
