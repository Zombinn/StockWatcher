"""报告持久化服务 — 将分析报告保存为 JSON 文件，支持分页/删除"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional

from src.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class ReportRecord:
    id: str
    title: str
    created_at: str
    summary: str = ""
    stock_count: int = 0
    details: dict = field(default_factory=dict)


class ReportService:
    """报告持久化服务"""

    def __init__(self):
        self.config = get_config()
        self._dir = os.path.join(self.config.log_dir, "..", "data", "reports")
        os.makedirs(self._dir, exist_ok=True)

    def _path(self, rid: str) -> str:
        return os.path.join(self._dir, f"{rid}.json")

    def _index_path(self) -> str:
        return os.path.join(self._dir, "_index.json")

    def _load_index(self) -> List[dict]:
        try:
            with open(self._index_path()) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_index(self, items: List[dict]):
        with open(self._index_path(), "w") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

    def save(self, title: str, summary: str, stock_count: int, details: dict) -> str:
        """保存一条报告"""
        rid = datetime.now().strftime("%Y%m%d_%H%M%S")
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = {
            "id": rid,
            "title": title,
            "created_at": created_at,
            "summary": summary,
            "stock_count": stock_count,
            "details": details,
        }
        with open(self._path(rid), "w") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        index = self._load_index()
        index.insert(0, {"id": rid, "title": title, "created_at": created_at,
                         "summary": summary, "stock_count": stock_count})
        self._save_index(index)
        return rid

    def list(self, page: int = 1, page_size: int = 10) -> tuple[List[dict], int]:
        """分页返回报告列表 (items, total)"""
        index = self._load_index()
        total = len(index)
        start = (page - 1) * page_size
        items = index[start: start + page_size]
        return items, total

    def get(self, rid: str) -> Optional[dict]:
        """获取报告详情"""
        try:
            with open(self._path(rid)) as f:
                return json.load(f)
        except FileNotFoundError:
            return None

    def delete(self, rid: str) -> bool:
        """删除单条报告"""
        path = self._path(rid)
        if not os.path.isfile(path):
            return False
        os.remove(path)
        index = [i for i in self._load_index() if i["id"] != rid]
        self._save_index(index)
        return True

    def delete_multi(self, rids: List[str]) -> int:
        """批量删除，返回删除数量"""
        count = 0
        for rid in rids:
            if self.delete(rid):
                count += 1
        return count

    def save_current_analysis(self, results: Dict, report_text: str):
        """自动保存前台触发的分析结果为报告"""
        stocks = results.get("stocks", [])
        if not stocks:
            return
        title = f"分析报告 {datetime.now().strftime('%m-%d %H:%M')}"
        summary = report_text[:200] if report_text else f"共 {len(stocks)} 只股票"
        self.save(title=title, summary=summary, stock_count=len(stocks), details=results)


_report_service: Optional[ReportService] = None


def get_report_service() -> ReportService:
    global _report_service
    if _report_service is None:
        _report_service = ReportService()
    return _report_service
