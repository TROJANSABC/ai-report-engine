"""生成层（Generator）。

职责：
- 标题生成（主标题 + 摘要副标题）
- 结构化内容生成（按模板填充各章节）
- 数据可视化建议（自动识别可图表化的数据点）
- 引用来源标注（自动附原文链接）

模板系统是核心差异点：不是"一段描述生成一篇文章"，
而是先选定报告结构，再由 LLM 按章节填充。
"""
from __future__ import annotations

import os
from datetime import date

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .analyzer import _call_llm
from .collector import Source
from .config import Settings

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

# 预置报告结构（MVP：周报 / 日报 / 趋势简报）
REPORT_STRUCTURES: dict[str, dict] = {
    "weekly": {
        "name": "周报",
        "sections": ["本周概览", "重点事件", "关键数据", "观点与讨论", "趋势判断", "下周关注"],
    },
    "daily": {
        "name": "日报",
        "sections": ["今日摘要", "重要动态", "数据速览", "值得关注"],
    },
    "trend": {
        "name": "趋势简报",
        "sections": ["趋势定义", "支撑证据", "驱动因素", "潜在影响", "风险与不确定性"],
    },
}


def get_structure(report_type: str) -> dict:
    return REPORT_STRUCTURES.get(report_type, REPORT_STRUCTURES["weekly"])


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(enabled_extensions=("html",)),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_skeleton(report_type: str, context: dict) -> str:
    """渲染 Jinja2 骨架模板。"""
    tpl_name = f"{report_type}.md.j2"
    if not os.path.exists(os.path.join(TEMPLATE_DIR, tpl_name)):
        tpl_name = "weekly.md.j2"
    return _env().get_template(tpl_name).render(**context)


def build_generation_prompt(
    topic: str, analysis: dict, report_type: str, skeleton: str, sources: list[Source]
) -> str:
    struct = get_structure(report_type)
    return (
        f"请根据以下结构化分析结果，撰写一份中文【{struct['name']}】。\n"
        f"主题：{topic}\n\n"
        "要求：\n"
        f"1) 严格按章节填充：{ '、'.join(struct['sections']) }；\n"
        "2) 每个关键数据点后标注置信度与来源序号（如 [1][2]）；\n"
        "3) 不要编造材料中没有的信息，信息不足时明确写"材料未覆盖"；\n"
        "4) 在末尾保留「参考来源」列表占位（由程序自动补齐链接）；\n"
        "5) 只输出 Markdown 正文。\n\n"
        f"【结构化分析 JSON】\n{analysis}\n\n"
        f"【报告骨架（可调整标题层级）】\n{skeleton}"
    )


def suggest_visualizations(analysis: dict) -> list[str]:
    """自动识别可图表化的数据点，给出可视化建议。"""
    tips: list[str] = []
    dps = analysis.get("data_points", []) or []
    numeric = [d for d in dps if any(ch.isdigit() for ch in str(d.get("value", "")))]
    if len(numeric) >= 2:
        tips.append("检测到多个数值型数据点，建议用「柱状图」对比指标大小。")
    if analysis.get("trends"):
        tips.append("存在趋势判断，建议用「折线图」展示时间维度变化。")
    if analysis.get("events"):
        tips.append("事件较多，建议用「时间轴」梳理事件脉络。")
    return tips


def _citations(sources: list[Source]) -> str:
    lines = ["", "---", "", "## 参考来源"]
    for i, s in enumerate(sources, 1):
        date_txt = f"（{s.published}）" if s.published else ""
        title = s.title or s.url or "未命名来源"
        lines.append(f"{i}. [{title}]({s.url}){date_txt}")
    return "\n".join(lines)


def generate_report(
    topic: str,
    sources: list[Source],
    analysis: dict,
    report_type: str,
    settings: Settings,
) -> dict:
    """生成主入口：返回 {markdown, visual_tips, sources}。"""
    struct = get_structure(report_type)
    context = {
        "topic": topic,
        "date": date.today().isoformat(),
        "report_name": struct["name"],
        "sections": struct["sections"],
        "analysis": analysis,
    }
    skeleton = render_skeleton(report_type, context)

    if settings.has_llm:
        prompt = build_generation_prompt(topic, analysis, report_type, skeleton, sources)
        body = _call_llm(
            prompt,
            settings,
            system="你是专业的报告撰稿人，擅长把碎片信息写成结构清晰、可追溯的报告。",
        )
    else:
        body = skeleton.replace("{{", "").replace("}}", "")  # 降级：直接给出骨架

    markdown = body.rstrip() + "\n" + _citations(sources)
    return {
        "markdown": markdown,
        "visual_tips": suggest_visualizations(analysis),
        "sources": sources,
        "report_type": report_type,
        "title": f"{topic} · {struct['name']}",
    }
