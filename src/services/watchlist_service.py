"""自选股服务 - 独立存储（data/watchlist.json），与 .env 解耦"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from src.config import get_config
from src.services.portfolio_service import _detect_market
from src.services.stock_service import StockService

logger = logging.getLogger(__name__)

WATCHLIST_FILE = "data/watchlist.json"


class WatchlistService:
    """自选股管理：增删查 + 实时行情"""

    def __init__(self):
        self.config = get_config()
        self.stock_service = StockService(self.config)
        self._codes: List[str] = self._load()

    def _load(self) -> List[str]:
        path = Path(WATCHLIST_FILE)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return list(data.get("codes", []))
            except Exception as e:
                logger.warning("加载自选股失败: %s", e)
                return []
        # 首次运行：从 .env 的 STOCK_LIST 迁移种子数据
        seed = list(self.config.stock_list)
        self._codes = seed
        self.save()
        logger.info("自选股已从 STOCK_LIST 初始化: %d 只", len(seed))
        return seed

    def save(self) -> None:
        path = Path(WATCHLIST_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"codes": self._codes, "updated_at": datetime.now().isoformat()},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_codes(self) -> List[str]:
        return list(self._codes)

    def add(self, code: str) -> bool:
        code = code.strip().upper()
        if not code or code in self._codes:
            return False
        self._codes.append(code)
        self.save()
        return True

    def remove(self, code: str) -> bool:
        code = code.strip().upper()
        if code not in self._codes:
            return False
        self._codes.remove(code)
        self.save()
        return True

    async def get_quotes(self) -> List[Dict[str, object]]:
        """获取自选股实时行情（并发）"""
        sem = asyncio.Semaphore(5)

        async def _one(code: str) -> Dict[str, object]:
            async with sem:
                price, change_pct, name = 0.0, 0.0, ""
                try:
                    quote = await self.stock_service.get_realtime_quote(code)
                    if quote:
                        price = quote.price
                        change_pct = quote.change_pct
                        name = quote.name
                    if not name:
                        info = await self.stock_service.get_stock_info(code)
                        name = info.name if info else ""
                except Exception as e:
                    logger.warning("自选股行情失败 %s: %s", code, e)
                return {
                    "code": code, "name": name or code,
                    "market": _detect_market(code),
                    "price": price, "change_pct": change_pct,
                }

        return await asyncio.gather(*[_one(c) for c in self._codes])
