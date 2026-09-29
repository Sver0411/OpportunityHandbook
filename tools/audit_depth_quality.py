#!/usr/bin/env python3
"""Depth Quality Audit：审查深度层内容本身，而不只是检查有没有文件。

输出：
- 正文长度、H2 数、表格、内部链接等结构信号
- 动作、案例/对照、失败/边界、证据/来源等内容信号
- 值得人工复核的文档
- 同目录下高度重复的 H2 骨架

运行：
    python3 tools/audit_depth_quality.py
"""

from __future__ import annotations

import collections
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPORT = ROOT / "reports" / "depth-quality.md"

LAYER_DIRS = {
    "Deep Dive": [
        "docs/projects", "docs/research-deep", "docs/job-search", "docs/career-growth",
        "docs/admissions", "docs/learning", "docs/open-source", "docs/competition-playbooks",
        "docs/entrepreneurship", "docs/networking", "docs/certifications", "docs/funding",
    ],
    "Case": ["docs/cases"],
    "Playbook": ["docs/playbooks"],
    "Career Guide": ["docs/career-guides"],
    "Country Playbook": ["docs/country-playbooks"],
}

ACTION = re.compile(r"怎么|如何|步骤|流程|检查|验证|先.{0,8}再|记录|比较|拆|问|准备|执行|复盘")
EXAMPLE = re.compile(r"例如|比如|案例|示例|正例|反例|假设|完整链路|Before|After|Case")
FAILURE = re.compile(r"失败|边界|限制|不适用|风险|误区|异常|退路|回退|失败分支|Stop")
EVIDENCE = re.compile(r"来源与更新|Official|Research-backed|Industry-data|Experience-based|证据|数据|指标")
VOLATILE_NUM = re.compile(r"\b\d+(?:\.\d+)?\s*(?:–|-|到|~)\s*\d+(?:\.\d+)?\s*(?:天|周|个月|年|小时|分钟|%|％)")

def strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[end + 5:]
    return text

def compact_chars(text: str) -> int:
    return len(re.sub(r"\s+", "", text))

def h2s(text: str) -> list[str]:
    return re.findall(r"^##\s+(.+?)\s*$", text, re.M)

def status(text: str) -> str:
    m = re.search(r"^status:\s*(\S+)", text, re.M)
    return m.group(1) if m else ""

def collect() -> list[dict]:
    rows = []
    for layer, dirs in LAYER_DIRS.items():
        for d in dirs:
            base = ROOT / d
            if not base.exists():
                continue
            for p in sorted(base.glob("*.md")):
                raw = p.read_text(encoding="utf-8")
                if status(raw) not in {"complete", "partial"}:
                    continue
                body = strip_frontmatter(raw)
                heads = h2s(body)
                rows.append({
                    "layer": layer,
                    "path": p.relative_to(ROOT).as_posix(),
                    "chars": compact_chars(body),
                    "h2": len(heads),
                    "tables": body.count("| ---"),
                    "links": len(re.findall(r"\[[^\]]+\]\([^\)]+\)", body)),
                    "action": bool(ACTION.search(body)),
                    "example": bool(EXAMPLE.search(body)),
                    "failure": bool(FAILURE.search(body)),
                    "evidence": bool(EVIDENCE.search(body)),
                    "ranges": len(VOLATILE_NUM.findall(body)),
                    "signature": tuple(h for h in heads if h not in {"相关", "来源与更新"}),
                })
    return rows

def review_reason(r: dict) -> list[str]:
    reasons = []
    # 阈值只用于找值得读的页面，不是合格线。
    if r["chars"] < 1400:
        reasons.append("正文较短")
    if r["h2"] < 3:
        reasons.append("展开层次较少")
    if not r["action"]:
        reasons.append("动作/判断信号弱")
    if r["layer"] in {"Deep Dive", "Case", "Playbook", "Career Guide"} and not r["example"]:
        reasons.append("缺案例/对照信号")
    if r["layer"] in {"Deep Dive", "Case", "Playbook"} and not r["failure"]:
        reasons.append("缺失败/边界信号")
    if not r["evidence"]:
        reasons.append("来源/证据信号弱")
    return reasons

def main() -> int:
    rows = collect()
    by_layer = collections.Counter(r["layer"] for r in rows)
    review = [(r, review_reason(r)) for r in rows]
    review = [(r, why) for r, why in review if len(why) >= 2]

    sig_groups = collections.defaultdict(list)
    for r in rows:
        parent = str(pathlib.PurePosixPath(r["path"]).parent)
        if r["signature"]:
            sig_groups[(parent, r["signature"])].append(r["path"])
    repeated = [(k, v) for k, v in sig_groups.items() if len(v) >= 4]

    lines = [
        "# Depth Quality Audit",
        "",
        "本报告检查的是已有深度文档是否值得人工再读，不用字数自动宣布合格。",
        "长度、标题数、关键词都只是检索信号；最终判断必须读正文。",
        "",
        "## 层级规模",
        "",
        "| 层级 | 文档数 |",
        "| --- | ---: |",
    ]
    for layer in LAYER_DIRS:
        lines.append(f"| {layer} | {by_layer[layer]} |")

    lines += [
        "",
        "## 建议人工复核",
        "",
        "只有同时命中至少两个风险信号才进入这里，避免把短而完整的文章机械判差。",
        "",
        "| 文档 | 层级 | 有效字符 | H2 | 原因 |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    if review:
        for r, why in sorted(review, key=lambda x: (x[0]["chars"], x[0]["path"])):
            lines.append(f"| {r['path']} | {r['layer']} | {r['chars']} | {r['h2']} | {'；'.join(why)} |")
    else:
        lines.append("| — | — | — | — | 当前没有同时命中两个风险信号的文档 |")

    lines += [
        "",
        "## 重复结构信号",
        "",
        "同一目录中 4 篇以上文档拥有完全相同的非通用 H2 序列时列出。它不一定是错误，但值得人工确认是否批量模板化。",
        "",
    ]
    if repeated:
        for (parent, sig), paths in repeated:
            lines.append(f"### {parent}（{len(paths)} 篇）")
            lines.append("")
            lines.append("H2：" + " → ".join(sig))
            lines.append("")
            for p in paths:
                lines.append(f"- {p}")
            lines.append("")
    else:
        lines.append("没有发现 4 篇以上完全相同的非通用 H2 骨架。")
        lines.append("")

    lines += [
        "## 数字区间提示",
        "",
        "这里只提醒人工判断：数字究竟是制度事实、案例数据，还是被误写成通用规则的经验阈值。",
        "",
        "| 文档 | 时间/比例区间命中数 |",
        "| --- | ---: |",
    ]
    ranged = [r for r in rows if r["ranges"]]
    if ranged:
        for r in sorted(ranged, key=lambda x: (-x["ranges"], x["path"])):
            lines.append(f"| {r['path']} | {r['ranges']} |")
    else:
        lines.append("| — | 0 |")

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"扫描 {len(rows)} 篇深度层文档；建议人工复核 {len(review)} 篇；重复结构组 {len(repeated)}。")
    print(f"报告：{REPORT.relative_to(ROOT)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
