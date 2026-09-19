"""信息采集层（Collector）。

职责：
- 关键词/话题输入
- 搜索引擎 API 集成（Tavily / SerpAPI）
- RSS / 热点源聚合（可选扩展）
- 去重与相关性排序

设计为「无 Key 可降级」：没有任何搜索 API Key 时，返回空列表，
由上层给出提示，而不会直接崩溃。
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from .config import Settings


@dataclass
class Source:
    """一条原始信息源。"""

    title: str
    url: str
    snippet: str = ""
    source: str = ""
    published: str = ""
    score: float = 0.0

    def key(self) -> str:
        base = (self.url or self.title).strip().lower()
        return hashlib.md5(base.encode("utf-8")).hexdigest()


_TOKEN_RE = re.compile(r"[a-zA-Z0-9\u4e00-\u9fff]+")


def _tokenize(text: str) -> set[str]:
    return set(_TOKEN_RE.findall((text or "").lower()))


# --------------------------------------------------------------------------- #
# 搜索后端
# --------------------------------------------------------------------------- #
def search_tavily(query: str, max_results: int, api_key: str) -> list[Source]:
    """Tavily：面向 AI 应用的搜索 API，返回结果自带相关性分数。"""
    from tavily import TavilyClient  # 延迟导入，避免无依赖时报错

    client = TavilyClient(api_key=api_key)
    resp = client.search(query=query, max_results=max_results, search_depth="advanced")
    out: list[Source] = []
    for r in resp.get("results", []):
        out.append(
            Source(
                title=r.get("title", ""),
                url=r.get("url", ""),
                snippet=r.get("content", ""),
                source="tavily",
                published=r.get("published_date", "") or "",
                score=float(r.get("score") or 0.0),
            )
        )
    return out


def search_serpapi(query: str, max_results: int, api_key: str) -> list[Source]:
    """SerpAPI：Google 结果的托管接口。"""
    import requests

    params = {
        "q": query,
        "api_key": api_key,
        "engine": "google",
        "num": max_results,
    }
    data = requests.get("https://serpapi.com/search", params=params, timeout=30).json()
    out: list[Source] = []
    for r in data.get("organic_results", []):
        out.append(
            Source(
                title=r.get("title", ""),
                url=r.get("link", ""),
                snippet=r.get("snippet", ""),
                source="serpapi",
                published=r.get("date", "") or "",
            )
        )
    return out


def collect_rss(feeds: list[str], limit_per_feed: int = 5) -> list[Source]:
    """RSS / Atom 聚合（可选扩展点）。"""
    import feedparser

    out: list[Source] = []
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:limit_per_feed]:
                summary = re.sub(r"<[^>]+>", "", entry.get("summary", ""))[:300]
                out.append(
                    Source(
                        title=entry.get("title", ""),
                        url=entry.get("link", ""),
                        snippet=summary,
                        source=url,
                        published=entry.get("published", "") or "",
                    )
                )
        except Exception:  # 单个源失败不应影响整体
            continue
    return out


# --------------------------------------------------------------------------- #
# 去重与排序
# --------------------------------------------------------------------------- #
def deduplicate(items: list[Source]) -> list[Source]:
    seen: set[str] = set()
    out: list[Source] = []
    for it in items:
        k = it.key()
        if k in seen:
            continue
        seen.add(k)
        out.append(it)
    return out


def rank_relevance(items: list[Source], keywords: list[str] | str, top_k: int) -> list[Source]:
    """关键词重叠度 + 原始相关性分数的轻量打分排序。"""
    kw = _tokenize(" ".join(keywords) if isinstance(keywords, (list, tuple)) else keywords)
    for it in items:
        text = _tokenize(f"{it.title} {it.snippet}")
        overlap = len(kw & text)
        it.score = overlap + it.score * 0.1
    items = sorted(items, key=lambda x: x.score, reverse=True)
    return items[:top_k]


# --------------------------------------------------------------------------- #
# 主入口
# --------------------------------------------------------------------------- #
def collect(
    keywords: list[str] | str,
    settings: Settings,
    *,
    extra_rss: list[str] | None = None,
) -> list[Source]:
    """采集主入口：检索 -> 合并 RSS -> 去重 -> 相关性排序。"""
    query = " ".join(keywords) if isinstance(keywords, (list, tuple)) else keywords
    items: list[Source] = []

    if settings.tavily_api_key:
        items += search_tavily(query, settings.max_sources, settings.tavily_api_key)
    elif settings.serpapi_api_key:
        items += search_serpapi(query, settings.max_sources, settings.serpapi_api_key)

    feeds = list(settings.rss_feeds) + list(extra_rss or [])
    if feeds:
        items += collect_rss(feeds)

    items = deduplicate(items)
    items = rank_relevance(items, keywords, settings.max_sources)
    return items
