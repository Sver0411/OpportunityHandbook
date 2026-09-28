#!/usr/bin/env python3
"""Knowledge Depth Audit：按知识域检查「Book / Manual / Deep Dive / Case / Playbook / Tool / Timeline」各层的覆盖。

目的不是统计字数，而是发现「哪个领域只有介绍、没有教会」。

    python3 tools/audit_knowledge_depth.py            # 打印矩阵并写 reports/knowledge-depth.md
    python3 tools/audit_knowledge_depth.py --json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import Counter

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import meta as M  # noqa: E402

# 知识域 → (topic 标签, 手册目录/文件名, 深度目录, 说明)
DOMAINS = [
    ("项目与作品", "project", "docs/manuals/项目与作品手册", ["docs/projects"]),
    ("科研", "research", "docs/manuals/科研手册", ["docs/research", "docs/research-deep"]),
    ("求职", "job", None, ["docs/job-search"]),
    ("职业发展", "job", None, ["docs/career-growth"]),
    ("升学", "study", None, ["docs/admissions"]),
    ("留学与国家", "study", "docs/manuals/语言与考试", ["docs/country-playbooks", "docs/countries"]),
    ("技能学习", "skill", "docs/manuals/技能学习手册", ["docs/learning"]),
    ("开源", "project", "docs/manuals/开源手册", ["docs/open-source"]),
    ("竞赛", "competition", "docs/manuals/竞赛手册", ["docs/competitions", "docs/competition-playbooks"]),
    ("奖学金与资助", "funding", "docs/manuals/奖学金与资助", []),
    ("创业与自由职业", "startup", "docs/manuals/创业与自由职业", ["docs/entrepreneurship"]),
    ("社群与人脉", "community", "docs/manuals/社群与行业组织", ["docs/networking"]),
    ("证书与资格", "skill", "docs/manuals/证书", ["docs/certifications"]),
    ("职业指南（岗位）", "job", None, ["docs/career-guides"]),
]

LAYER_DIRS = {
    "深度教程": ["docs/projects", "docs/research-deep", "docs/job-search", "docs/career-growth",
             "docs/admissions", "docs/learning", "docs/open-source", "docs/competition-playbooks",
             "docs/entrepreneurship", "docs/networking", "docs/certifications"],
    "完整案例": ["docs/cases"],
    "操作手册": ["docs/playbooks"],
    "工具模板": ["docs/tools"],
    "职业指南": ["docs/career-guides"],
    "国家手册": ["docs/country-playbooks"],
}


def load():
    docs = M.load_docs(ROOT)
    errs, warns, extra = M.validate(ROOT, docs)
    return docs, extra


def count_docs(docs, prefixes, status=("complete", "partial")):
    return [d for d in docs if any(d.rel.startswith(p.rstrip("/") + "/") or d.rel == p + ".md" or d.rel == p
                                  for p in prefixes) and d.status in status]


def topics_of(doc) -> set[str]:
    t = doc.front.get("topics") or ""
    if isinstance(t, (list, tuple)):
        return {str(x).strip() for x in t if str(x).strip()}
    return {x.strip().strip("'\"") for x in str(t).strip("[]").split(",") if x.strip()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    docs, extra = load()
    entries = [e for e in extra["entries"] if e.get("kind") == "entry" and e.get("status") == "complete"]

    rows = []
    for name, topic, manual, deep_dirs in DOMAINS:
        book_n = sum(1 for e in entries if topic in (e.get("topics") or []))
        manual_n = 1 if manual and any(d.rel == manual + ".md" for d in docs) else 0
        deep = count_docs(docs, deep_dirs) if deep_dirs else []
        deep_n = len([d for d in deep])
        # 案例/操作手册/工具：按 topics 匹配
        cases = [d for d in count_docs(docs, ["docs/cases"]) if topic in topics_of(d)]
        playbooks = [d for d in count_docs(docs, ["docs/playbooks"]) if topic in topics_of(d)]
        tools = [d for d in count_docs(docs, ["docs/tools"]) if topic in topics_of(d)]
        timelines = [d for d in count_docs(docs, ["docs/timelines"]) if topic in topics_of(d)]
        rows.append({
            "domain": name,
            "book": book_n,
            "manual": manual_n,
            "deep": deep_n,
            "case": len(cases),
            "playbook": len(playbooks),
            "tool": len(tools),
            "timeline": len(timelines),
            "gap": ("缺 Deep Dive" if book_n and not deep_n else
                    "缺 Case/Playbook" if deep_n and not (cases or playbooks) else ""),
        })

    # 全局层级统计
    layer_stats = {}
    for layer, dirs in LAYER_DIRS.items():
        all_docs = count_docs(docs, dirs, status=("complete", "partial", "planned"))
        done = [d for d in all_docs if d.status in ("complete", "partial")]
        layer_stats[layer] = {"total": len(all_docs), "complete": len(done),
                              "planned": len(all_docs) - len(done)}
    planned_all = [d for d in docs if d.status == "planned"]
    layer_stats["planned 待写合计"] = {"total": len(planned_all), "complete": 0, "planned": len(planned_all)}

    lines = ["# Knowledge Depth Matrix", ""]
    lines += ["| 知识域 | Book | 手册 | Deep Dive | Case | Playbook | Tool | Timeline | 缺口 |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        mark = lambda n: f"{n}" if n else "—"
        lines.append(f"| {r['domain']} | {mark(r['book'])} | {mark(r['manual'])} | {mark(r['deep'])} | "
                     f"{mark(r['case'])} | {mark(r['playbook'])} | {mark(r['tool'])} | {mark(r['timeline'])} | {r['gap'] or '—'} |")
    lines += ["", "## 层级统计", "",
              "| 层级 | 已写 | 待写 |", "| --- | --- | --- |"]
    for layer, s in layer_stats.items():
        lines.append(f"| {layer} | {s['complete']} | {s['planned']} |")
    lines += ["", "说明：Deep Dive / Case / Playbook / Tool 的「待写」由 docs/ 下的 `status: planned` 文档构成，",
              "清单同步出现在 `docs/ROADMAP.md`。Book 列为 complete 条目数（按 topics 归类）。"]

    out = ROOT / "reports" / "knowledge-depth.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps({"rows": rows, "layers": layer_stats}, ensure_ascii=False, indent=2))
    else:
        print(f"{'知识域':16} {'Book':>5} {'手册':>4} {'Deep':>5} {'Case':>5} {'Play':>5} {'Tool':>5} {'Time':>5}  缺口")
        for r in rows:
            print(f"{r['domain']:16} {r['book']:>5} {r['manual']:>4} {r['deep']:>5} {r['case']:>5} "
                  f"{r['playbook']:>5} {r['tool']:>5} {r['timeline']:>5}  {r['gap']}")
        print()
        for layer, s in layer_stats.items():
            print(f"  {layer:14} 已写 {s['complete']:>3} / 待写 {s['planned']:>3}")
        print(f"\n矩阵已写出：{out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
