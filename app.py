"""AI 结构化报告引擎 · Streamlit 前端（MVP）。

运行：
    streamlit run app.py

流程：输入话题 -> 采集 -> 分析提炼 -> 结构化生成 -> 预览 / 导出 / 存历史。
"""
from __future__ import annotations

import os

import streamlit as st

from core import (
    REPORT_STRUCTURES,
    ReportStore,
    analyze,
    collect,
    generate_report,
    to_html,
    to_pdf,
)
from core.config import settings

st.set_page_config(page_title="AI 结构化报告引擎", page_icon="📊", layout="wide")

store = ReportStore(settings.db_path)

# --------------------------------------------------------------------------- #
# 侧边栏：配置状态 + 历史报告
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("⚙️ 运行状态")
    st.write(f"搜索 API：{'✅ 已配置' if settings.has_search else '⚠️ 未配置（走空采集）'}")
    st.write(f"LLM：{'✅ 已配置' if settings.has_llm else '⚠️ 未配置（启发式模式）'}")
    if not settings.has_search or not settings.has_llm:
        st.info("在 .env 中配置 TAVILY_API_KEY / OPENAI_API_KEY 以启用完整能力。")

    st.divider()
    st.header("🕘 历史报告")
    for row in store.list(limit=20):
        label = f"#{row['id']} · {row['title'] or row['topic']}"
        if st.button(label, key=f"hist_{row['id']}"):
            st.session_state["loaded"] = store.get(row["id"])

st.title("📊 AI 结构化报告引擎")
st.caption("从噪音中提炼结构：输入话题 → 多源采集 → 交叉验证 → 结构化报告")

# --------------------------------------------------------------------------- #
# 主输入区
# --------------------------------------------------------------------------- #
col1, col2 = st.columns([3, 1])
with col1:
    topic = st.text_input("话题 / 关键词（多个用空格分隔）", placeholder="例：生成式 AI 行业")
with col2:
    report_type = st.selectbox(
        "报告模板",
        options=list(REPORT_STRUCTURES.keys()),
        format_func=lambda k: REPORT_STRUCTURES[k]["name"],
    )

if st.button("🚀 生成报告", type="primary", disabled=not topic.strip()):
    keywords = [t for t in topic.split() if t]
    with st.status("正在生成…", expanded=True) as status:
        st.write("① 采集多源信息…")
        sources = collect(keywords, settings)
        st.write(f"   采集到 {len(sources)} 条来源")

        st.write("② 分析提炼 + 交叉验证…")
        analysis = analyze(topic, sources, report_type, settings)

        st.write("③ 结构化生成…")
        report = generate_report(topic, sources, analysis, report_type, settings)
        st.session_state["report"] = report
        st.session_state["analysis"] = analysis

        rid = store.save(
            topic=topic,
            report_type=report_type,
            title=report["title"],
            markdown=report["markdown"],
            meta={"visual_tips": report["visual_tips"], "sources": [s.url for s in sources]},
        )
        status.update(label=f"✅ 生成完成（已存为历史 #{rid}）", state="complete")

# --------------------------------------------------------------------------- #
# 结果展示
# --------------------------------------------------------------------------- #
report = st.session_state.get("report") or (
    st.session_state.get("loaded") and _loaded_to_report(st.session_state["loaded"])
)
