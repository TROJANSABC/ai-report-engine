"""AI 结构化报告引擎核心包。

模块划分：
- config   : 运行配置（环境变量）
- collector: 信息采集层（多源检索 + RSS + 去重排序）
- analyzer : 分析提炼层（多源融合 + 关键信息提取 + 置信度）
- generator: 生成层（标题 + 结构化内容 + 可视化建议 + 引用）
- exporter : 输出层（Markdown / HTML / PDF 导出）
- storage  : 历史报告存储（SQLite）
"""

from .config import settings
from .collector import collect, Source
from .analyzer import analyze
from .generator import generate_report, REPORT_STRUCTURES
from .exporter import to_markdown, to_html, to_pdf
from .storage import ReportStore

__all__ = [
    "settings",
    "collect",
    "Source",
    "analyze",
    "generate_report",
    "REPORT_STRUCTURES",
    "to_markdown",
    "to_html",
    "to_pdf",
    "ReportStore",
]
