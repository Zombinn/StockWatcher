"""新闻 / 公告资讯获取（基于 AkShare 东方财富个股新闻）"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    """资讯条目"""
    title: str
    content: str = ""
    source: str = ""
    url: str = ""
    publish_time: str = ""


def _clean_code(code: str) -> str:
    code = code.strip().upper()
    for prefix in ("SH", "SZ", "BJ", ".HK", ".US"):
        code = code.replace(prefix, "")
    return code


async def get_stock_news(code: str, limit: int = 10) -> List[NewsItem]:
    """获取个股相关新闻（A 股）。失败返回空列表，调用方需容错。"""
    try:
        import akshare as ak

        df = ak.stock_news_em(symbol=_clean_code(code))
        if df is None or df.empty:
            return []
        items: List[NewsItem] = []
        for _, r in df.head(limit).iterrows():
            items.append(NewsItem(
                title=str(r.get("新闻标题", "")),
                content=str(r.get("新闻内容", "")),
                source=str(r.get("文章来源", "")),
                url=str(r.get("新闻链接", "")),
                publish_time=str(r.get("发布时间", "")),
            ))
        return items
    except Exception as e:
        logger.warning("个股新闻获取失败 %s: %s", code, e)
        return []
