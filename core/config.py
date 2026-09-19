"""全局配置：从环境变量加载运行参数。

所有外部依赖（搜索 API、LLM）都是可选的，缺失时会自动降级为
本地启发式 / mock 模式，方便在没有任何 API Key 的情况下跑通全流程。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env_list(name: str) -> list[str]:
    raw = os.getenv(name, "")
    return [x.strip() for x in raw.split(",") if x.strip()]


@dataclass
class Settings:
    # ---- 搜索层 ----
    search_provider: str = "tavily"          # tavily | serpapi | none
    tavily_api_key: str = ""
    serpapi_api_key: str = ""

    # ---- LLM 层 ----
    llm_provider: str = "openai"             # openai | anthropic | none
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    model: str = "gpt-4o-mini"

    # ---- 采集参数 ----
    max_sources: int = 8
    rss_feeds: list[str] = field(default_factory=list)

    # ---- 存储 ----
    db_path: str = "reports.db"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            search_provider=os.getenv("SEARCH_PROVIDER", "tavily"),
            tavily_api_key=os.getenv("TAVILY_API_KEY", ""),
            serpapi_api_key=os.getenv("SERPAPI_API_KEY", ""),
            llm_provider=os.getenv("LLM_PROVIDER", "openai"),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            max_sources=int(os.getenv("MAX_SOURCES", "8")),
            rss_feeds=_env_list("RSS_FEEDS"),
            db_path=os.getenv("DB_PATH", "reports.db"),
        )

    # ---- 能力探测 ----
    @property
    def has_search(self) -> bool:
        return bool(self.tavily_api_key or self.serpapi_api_key)

    @property
    def has_llm(self) -> bool:
        return bool(self.openai_api_key or self.anthropic_api_key)


settings = Settings.from_env()
