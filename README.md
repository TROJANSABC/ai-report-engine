# AI 结构化报告引擎 (ai-report-engine)

> 从噪音中提炼结构 —— 输入话题，多源采集 → 交叉验证 → 结构化周报/日报/趋势简报，支持 Markdown / HTML / PDF 导出与历史管理。

这不是一个"自动写文章"的工具，而是一个 **AI 信息提炼与结构化引擎**。核心价值在于：面对碎片、噪声、互相矛盾的多源信息，自动抽取事件 / 数据 / 观点 / 趋势，并映射到可复用的报告结构里。

---

## ✨ 核心特性

| 能力 | 说明 |
| --- | --- |
| 🔍 信息采集（Collector） | 关键词输入 · Tavily / SerpAPI 搜索 · RSS 热点聚合 · 去重与相关性排序 |
| 🧠 分析提炼（Analyzer） | 多源信息融合 · 交叉验证与置信度标注 · 关键信息提取（事件/数据/观点/趋势） |
| 📝 结构化生成（Generator） | 标题生成 · 按模板填充章节 · 数据可视化建议 · 引用来源自动标注 |
| 📤 多格式输出（Output） | Markdown / HTML / PDF 导出 · 可定制模板 · 历史报告管理 |

### 关键设计决策

1. **模板系统是核心差距**：不做"一段描述生成一篇文章"，而是预置周报 / 日报 / 竞品分析 / 趋势简报等结构，用户选定模板后由 AI 按章节填充。
2. **多源交叉验证**：对关键数据点自动比对 2-3 个来源，输出一致性说明与置信度（`high / medium / low`），例如 *"该数据在 3 个来源中一致"* vs *"来源 A 显示 X，来源 B 显示 Y"*。
3. **引用溯源**：每条信息附原文链接，用户可点击验证，既提升可信度，也缓解大模型的幻觉（hallucination）问题。

---

## 🏗️ 架构

```
AI 结构化报告引擎
├── 信息采集层（Collector）   core/collector.py
│   ├── 关键词/话题输入
│   ├── 搜索引擎 API 集成（Tavily / SerpAPI）
│   ├── RSS / 热点源聚合（可选扩展）
│   └── 去重与相关性排序
├── 分析提炼层（Analyzer）    core/analyzer.py
│   ├── 多源信息融合（交叉验证 + 置信度标注）
│   ├── 关键信息提取（事件、数据、观点、趋势）
│   └── 结构化框架映射（按报告类型选模板）
├── 生成层（Generator）       core/generator.py  +  templates/
│   ├── 标题生成（主标题 + 摘要副标题）
│   ├── 结构化内容生成（按模板填充各章节）
│   ├── 数据可视化建议（识别可图表化数据点）
│   └── 引用来源标注（自动附原文链接）
└── 输出层（Output）          core/exporter.py  +  core/storage.py
    ├── Markdown / HTML / PDF 多格式导出
    ├── 可定制报告模板
    └── 历史报告管理（SQLite）
```

---

## 🧰 技术栈

| 层级 | 选型 | 说明 |
| --- | --- | --- |
| 前端 | Streamlit | 快速原型 |
| 搜索 | Tavily API / SerpAPI | 面向 AI 应用、结构化输出更好 |
| LLM | OpenAI GPT-4 系列 / Anthropic Claude | 按成本选择 |
| 模板引擎 | Jinja2 | 灵活的报告模板系统 |
| 导出 | WeasyPrint (PDF) + Markdown | 多格式支持 |
| 存储 | SQLite | 保存历史报告与模板配置 |

---

## 🚀 快速开始

```bash
# 1. 克隆
git clone https://github.com/TROJANSABC/ai-report-engine.git
cd ai-report-engine

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 TAVILY_API_KEY / OPENAI_API_KEY 等（可留空，自动降级）

# 4. 启动
streamlit run app.py
```

> 💡 **无 Key 也能跑**：未配置搜索 / LLM API 时，引擎自动降级为「空采集 + 启发式分析 + 骨架生成」，保证全流程可运行、可演示。

### 命令行调用（可选）

```bash
python cli.py "生成式AI 行业" --type weekly --out ./output
```

---

## 📁 项目结构

```
ai-report-engine/
├── app.py                 # Streamlit 前端
├── cli.py                 # 命令行入口
├── core/
│   ├── config.py          # 运行配置（环境变量）
│   ├── collector.py       # 信息采集层
│   ├── analyzer.py        # 分析提炼层（含交叉验证）
│   ├── generator.py       # 生成层
│   ├── exporter.py        # 输出层（MD/HTML/PDF）
│   └── storage.py         # SQLite 历史存储
├── templates/             # Jinja2 报告模板
│   ├── weekly.md.j2       # 周报
│   ├── daily.md.j2        # 日报
│   └── trend.md.j2        # 趋势简报
├── requirements.txt
└── .env.example
```

---

## 🗺️ 路线图（MVP → V2）

**MVP（3 个功能，2 周内）**
- [x] 输入话题关键词 → AI 搜索并生成结构化周报
- [x] 3 个预置模板（周报 / 日报 / 趋势简报）
- [x] 导出为 Markdown / PDF

**V2 规划**
- [ ] 竞品分析模板 + 自定义模板编辑器
- [ ] 数据可视化建议落地为内嵌图表
- [ ] RSS 定时任务 + 邮件推送
- [ ] 多语言输出

---

## ⚠️ 免责声明

本工具产出的报告内容由大模型基于检索到的公开信息自动生成，可能存在误差或过时信息。所有关键数据请以来源链接中的原文为准，本工具不构成任何投资、法律或商业决策建议。

## 📄 License

MIT
