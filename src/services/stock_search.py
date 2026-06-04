"""股票搜索 — 代码/名称/拼音模糊匹配（A 股全量 + 港美股精选）"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# 港美股精选（akshare 不便全量拉取，维护常用标的）
_HK_US: List[Dict[str, str]] = [
    {"code": "0700.HK", "name": "腾讯控股", "market": "hk"},
    {"code": "9988.HK", "name": "阿里巴巴", "market": "hk"},
    {"code": "0999.HK", "name": "网易", "market": "hk"},
    {"code": "9618.HK", "name": "京东集团", "market": "hk"},
    {"code": "03690.HK", "name": "美团", "market": "hk"},
    {"code": "1810.HK", "name": "小米集团", "market": "hk"},
    {"code": "AAPL", "name": "Apple", "market": "us"},
    {"code": "TSLA", "name": "Tesla", "market": "us"},
    {"code": "MSFT", "name": "Microsoft", "market": "us"},
    {"code": "AMZN", "name": "Amazon", "market": "us"},
    {"code": "GOOGL", "name": "Alphabet", "market": "us"},
    {"code": "NVDA", "name": "NVIDIA", "market": "us"},
    {"code": "META", "name": "Meta", "market": "us"},
    {"code": "AMD", "name": "AMD", "market": "us"},
]


def _pinyin_keys(name: str) -> tuple[str, str]:
    """返回 (全拼, 首字母)，pypinyin 不可用时返回空串"""
    try:
        from pypinyin import Style, lazy_pinyin

        full = "".join(lazy_pinyin(name)).upper()
        initials = "".join(lazy_pinyin(name, style=Style.FIRST_LETTER)).upper()
        return full, initials
    except Exception:
        return "", ""


@lru_cache(maxsize=1)
def _a_share_index() -> List[Dict[str, str]]:
    """A 股全量索引（code/name/拼音），失败返回空列表"""
    try:
        import akshare as ak

        df = ak.stock_info_a_code_name()
        index: List[Dict[str, str]] = []
        for _, r in df.iterrows():
            name = str(r["name"])
            full, initials = _pinyin_keys(name)
            index.append({
                "code": str(r["code"]), "name": name, "market": "cn",
                "py": full, "py0": initials,
            })
        logger.info("A 股搜索索引已构建: %d 只", len(index))
        return index
    except Exception as e:
        logger.warning("A 股索引构建失败: %s", e)
        return []


def search_stocks(query: str, market: str = "cn", limit: int = 8) -> List[Dict[str, str]]:
    """模糊搜索股票。支持代码、名称、拼音全拼、拼音首字母。"""
    q = query.strip().upper()
    if not q:
        return []

    pool: List[Dict[str, str]] = []
    if market in ("cn", "all"):
        pool.extend(_a_share_index())
    if market in ("hk", "us", "all"):
        pool.extend(_HK_US)
    elif market == "cn":
        pass  # 仅 A 股

    results: List[Dict[str, str]] = []
    for item in pool:
        if (q in item["code"].upper()
                or q in item["name"].upper()
                or (item.get("py") and q in item["py"])
                or (item.get("py0") and item["py0"].startswith(q))):
            results.append({"code": item["code"], "name": item["name"], "market": item["market"]})
            if len(results) >= limit:
                break
    return results
