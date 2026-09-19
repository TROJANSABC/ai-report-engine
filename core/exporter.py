"""输出层（Output）。

职责：Markdown / HTML / PDF 多格式导出。
"""
from __future__ import annotations

# 基础 CSS：用于 HTML / PDF 渲染
BASE_CSS = """
body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
       max-width: 820px; margin: 40px auto; padding: 0 20px; color: #1f2328; line-height: 1.7; }
h1 { border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; }
h2 { margin-top: 28px; color: #0f172a; }
code { background: #f3f4f6; padding: 2px 5px; border-radius: 4px; }
a { color: #0969da; }
blockquote { border-left: 4px solid #d0d7de; margin: 0; padding-left: 14px; color: #57606a; }
"""


def to_markdown(report: dict) -> str:
    """导出 Markdown 文本。"""
    return report.get("markdown", "")


def to_html(report: dict, *, full_page: bool = True) -> str:
    """Markdown -> HTML。"""
    import markdown as md

    body = md.markdown(
        report.get("markdown", ""),
        extensions=["extra", "tables", "toc", "sane_lists"],
    )
    if not full_page:
        return body
    title = report.get("title", "AI 报告")
    return (
        "<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'>"
        f"<title>{title}</title><style>{BASE_CSS}</style></head>"
        f"<body>{body}</body></html>"
    )


def to_pdf(report: dict, output_path: str) -> str:
    """HTML -> PDF（WeasyPrint）。返回写入的文件路径。"""
    from weasyprint import HTML

    html = to_html(report, full_page=True)
    HTML(string=html).write_pdf(output_path)
    return output_path


def save_all(report: dict, out_dir: str, stem: str) -> dict[str, str]:
    """一次性导出 Markdown + HTML + PDF，返回 {格式: 路径}。"""
    import os

    os.makedirs(out_dir, exist_ok=True)
    paths: dict[str, str] = {}

    md_path = os.path.join(out_dir, f"{stem}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(to_markdown(report))
    paths["md"] = md_path

    html_path = os.path.join(out_dir, f"{stem}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(to_html(report))
    paths["html"] = html_path

    try:
        paths["pdf"] = to_pdf(report, os.path.join(out_dir, f"{stem}.pdf"))
    except Exception as exc:  # PDF 依赖系统库，失败不应阻断其它格式
        paths["pdf_error"] = str(exc)

    return paths
