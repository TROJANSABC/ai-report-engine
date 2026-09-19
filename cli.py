"""命令行入口：无需前端即可生成报告。

用法：
    python cli.py "生成式AI 行业" --type weekly --out ./output
"""
from __future__ import annotations

import argparse
from datetime import date

from core import ReportStore, analyze, collect, generate_report, save_all
from core.exporter import save_all  # noqa: F401  (显式导出)
from core.config import settings


def main() -> None:
    parser = argparse.ArgumentParser(description="AI 结构化报告引擎 CLI")
    parser.add_argument("topic", help="话题 / 关键词，多个用空格分隔")
    parser.add_argument(
        "--type",
        default="weekly",
        choices=["weekly", "daily", "trend"],
        help="报告类型：weekly / daily / trend",
    )
    parser.add_argument("--out", default="output", help="导出目录")
    parser.add_argument("--no-save", action="store_true", help="不写入历史库")
    args = parser.parse_args()

    keywords = [t for t in args.topic.split() if t]
    print(f"[1/4] 采集多源信息：{args.topic}")
    sources = collect(keywords, settings)
    print(f"      采集到 {len(sources)} 条来源")

    print("[2/4] 分析提炼 + 交叉验证")
    analysis = analyze(args.topic, sources, args.type, settings)

    print("[3/4] 结构化生成")
    report = generate_report(args.topic, sources, analysis, args.type, settings)

    stem = f"{args.type}_{date.today().isoformat()}"
    print(f"[4/4] 导出到 {args.out}/")
    paths = save_all(report, args.out, stem)
    for fmt, p in paths.items():
        print(f"      {fmt}: {p}")

    if not args.no_save:
        store = ReportStore(settings.db_path)
        rid = store.save(
            topic=args.topic,
            report_type=args.type,
            title=report["title"],
            markdown=report["markdown"],
            meta={"visual_tips": report["visual_tips"]},
        )
        print(f"      已存为历史报告 #{rid}")


if __name__ == "__main__":
    main()
