"""分析提炼层（Analyzer）。

职责：
- 多源信息融合（交叉验证 + 置信度标注）
- 关键信息提取（事件、数据、观点、趋势）
- 结构化框架映射（根据报告类型选择模板）

关键设计：对关键数据点做多源一致性检查，输出
"该数据在 N 个来源中一致" 或 "来源A显示X，来源B显示Y"，
并在 UI 上以置信度标签呈现，同时降低模型幻觉风险。
"""
from __future__ import annotations

import json

from .collector import Source
from .config import Settings

ANALYST_SYSTEM = (
    "你是一名资深信息分析师。你的任务是从多个来源中提炼结构化信息，"
    "而不是复述或改写原文。请严格输出 JSON，不要输出多余解释。"
)

_ANALYSIS_SCHEMA = {
    "summary": "一句话概括整体情况",
    "events": [{"title": "事件", "detail": "说明", "sources": ["url1", "url2"]}],
    "data_points": [
        {
            "metric": "指标名",
            "value": "数值",
            "confidence": "high|medium|low",
            "agreement": "多源一致性说明，如：3 个来源一致 / 来源A=1，来源B=2",
            "sources": ["url1", "url2"],
        }
    ],
    "opinions": [{"viewpoint": "观点", "sources": ["url1"]}],
    "trends": [{"trend": "趋势判断", "evidence": "依据"}],
    "keywords": ["关键词"],
}


def build_analysis_prompt(topic: str, sources: list[Source], report_type: str) -> str:
    blocks = []
    for i, s in enumerate(sources, 1):
        blocks.append(
            f"[来源{i}] {s.title}\nURL: {s.url}\n发布时间: {s.published or '未知'}\n摘要: {s.snippet}"
        )
    corpus = "\n\n".join(blocks) if blocks else "（无可用来源，请基于常识谨慎分析并说明信息不足）"
    schema = json.dumps(_ANALYSIS_SCHEMA, ensure_ascii=False, indent=2)
    return (
        f"报告类型：{report_type}\n主题：{topic}\n\n"
        f"以下是采集到的来源材料：\n\n{corpus}\n\n"
        "请完成：\n"
        "1) 交叉验证：对关键数据点，比对多个来源是否一致，给出置信度（high/medium/low）与一致性说明；\n"
        "2) 关键信息提取：事件、数据、观点、趋势；\n"
        "3) 用中文输出，严格符合以下 JSON schema（所有字段均需存在）：\n\n"
        f"{schema}"
    )


def _call_llm(prompt: str, settings: Settings, system: str = ANALYST_SYSTEM) -> str:
    """统一 LLM 调用入口，支持 OpenAI / Anthropic。"""
    if settings.openai_api_key:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        resp = client.chat.completions.create(
            model=settings.model or "gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        return resp.choices[0].message.content or ""

    if settings.anthropic_api_key:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        msg = client.messages.create(
            model=settings.model or "claude-3-5-sonnet-latest",
            max_tokens=2000,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")

    raise RuntimeError("未配置 LLM API Key（OPENAI_API_KEY / ANTHROPIC_API_KEY）")


def _extract_json(text: str) -> dict:
    """从模型输出中稳健地取出 JSON。"""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    return json.loads(text)


def _mock_analysis(topic: str, sources: list[Source]) -> dict:
    """无 LLM 时的降级结果：用启发式规则产出结构化骨架。"""
    data_points = [
        {
            "metric": "来源数量",
            "value": str(len(sources)),
            "confidence": "high",
            "agreement": f"{len(sources)} 个来源被采集并纳入分析",
            "sources": [s.url for s in sources],
        }
    ]
    events = [
        {"title": s.title, "detail": s.snippet, "sources": [s.url]} for s in sources
    ]
    return {
        "summary": f"围绕「{topic}」共采集 {len(sources)} 条来源，以下为结构化提炼（启发式模式）。",
        "events": events,
        "data_points": data_points,
        "opinions": [],
        "trends": [],
        "keywords": [topic],
    }


def analyze(
    topic: str,
    sources: list[Source],
    report_type: str,
    settings: Settings,
) -> dict:
    """分析主入口：返回结构化分析结果 dict。"""
    if not settings.has_llm:
        return _mock_analysis(topic, sources)

    prompt = build_analysis_prompt(topic, sources, report_type)
    raw = _call_llm(prompt, settings)
    try:
        data = _extract_json(raw)
    except Exception:
        # 解析失败时保留可追溯信息，不静默丢弃
        data = _mock_analysis(topic, sources)
        data["summary"] = raw[:500]
        data["_parse_error"] = True
    # 补齐缺省字段
    for k in ("summary", "events", "data_points", "opinions", "trends", "keywords"):
        data.setdefault(k, [] if k != "summary" else "")
    return data
