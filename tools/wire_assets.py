#!/usr/bin/env python3
"""把图解与下载卡片接进正文（幂等：重复执行不会重复插入）。

规则：
- 图解插在指定标题之前，正文里保留完整步骤文字，图只是补充；
- 下载卡片插在 `## 相关` 之前，符合本项目「相关 → 来源与更新 收尾」的约定；
- 章内条目（book/*.md）的图插在 meta 块之后，资源放在该条目末尾。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FIGS = {
    "new-student-timeline": ("assets/diagrams/new-student-timeline.svg",
                             "新生报到时间线：报到前 2 周、报到当天、第一周、第一个月各自要做的事"),
    "funding-types": ("assets/diagrams/funding-types.svg",
                      "五类资助的区别：要不要还、谁评定、在哪办"),
    "funding-lookup": ("assets/diagrams/funding-lookup.svg",
                       "怎么从学校官网找到学生资助管理部门与正式通知"),
    "thesis-flow": ("assets/diagrams/thesis-flow.svg",
                    "毕业论文流程：选题、开题、中期、初稿、查重、送审、答辩、归档"),
    "internship-flow": ("assets/diagrams/internship-flow.svg",
                        "第一次找实习的流程，中间有一道岗位核验"),
    "internship-phases": ("assets/diagrams/internship-phases.svg",
                          "实习前、实习中、实习结束后各自要留下什么"),
    "graduation-paths": ("assets/diagrams/graduation-paths.svg",
                         "五种毕业去向对应的档案与户口走法"),
    "graduation-timeline": ("assets/diagrams/graduation-timeline.svg",
                            "毕业前 6 个月到离校后 1 个月的五个节点"),
    "status-appeal": ("assets/diagrams/status-appeal.svg",
                      "学籍异常的处理流程：发现、查规定、收证据、书面申请、复核"),
    "part-time-risk": ("assets/diagrams/part-time-risk.svg",
                       "五种兼职风险类型、识别信号与立刻要做的事"),
    "scam-response": ("assets/diagrams/scam-response.svg",
                      "遭遇诈骗后的六步处置顺序"),
    "four-year-plan": ("assets/diagrams/four-year-plan.svg",
                       "大一到大四的四条线：课程、科研竞赛、实习实践、升学就业"),
    "opportunity-relations": ("assets/diagrams/opportunity-relations.svg",
                              "科研、竞赛、实习与升学就业之间怎么互相供料"),
}

DOCS: list[dict] = [
    {"file": "docs/playbooks/大学新生入学与第一个月.md",
     "figs": [("## Step 2 · 到校第一周：六件事", "new-student-timeline")],
     "res": ["new-student-checklist", "enrollment-record", "freshman-budget"]},
    {"file": "docs/playbooks/本科毕业论文与毕业设计.md",
     "figs": [("## 三、做不出来怎么办：七种故障的处理顺序", "thesis-flow")],
     "res": ["thesis-final-checklist", "thesis-schedule", "weekly-research-log", "defense-outline"]},
    {"file": "docs/playbooks/毕业去向与离校手续总清单.md",
     "figs": [("## 四、按去向：五条分支", "graduation-paths"),
              ("## 六、必须向学校/单位确认的问题", "graduation-timeline")],
     "res": ["graduation-clearance-checklist", "graduation-archive-list", "graduation-progress"]},
    {"file": "docs/playbooks/兼职与校园诈骗风险.md",
     "figs": [("## 三、转账前的四步核验", "part-time-risk"),
              ("## 五、证据留存清单", "scam-response")],
     "res": ["parttime-risk-checklist", "incident-timeline-log"]},
    {"file": "docs/playbooks/学籍异常与学校事务申诉.md",
     "figs": [("## 三、五类情况怎么做", "status-appeal")],
     "res": ["campus-issue-evidence", "written-request-template", "appeal-submit-checklist"]},
    {"file": "docs/playbooks/第一次找实习.md",
     "figs": [("## 用求职漏斗判断该改哪里", "internship-flow")],
     "res": ["internship-vet-checklist", "application-tracker", "jd-analysis-example"]},
    {"file": "docs/tools/实习协议核对表.md",
     "figs": [("## 三、出问题时的顺序", "internship-phases")],
     "res": ["internship-agreement-checklist", "internship-issue-log", "internship-weekly-report"]},
    {"file": "docs/timelines/本科四年.md",
     "figs": [("## 每学年的核心任务与判断信号", "four-year-plan"),
              ("## 硬截止与软节奏", "opportunity-relations")],
     "res": ["opportunity-tracker", "semester-review"]},
]

BOOK: list[dict] = [
    {"file": "book/01-先决定下一步往哪里走.md", "entry": "### 奖助学金",
     "figs": ["funding-types", "funding-lookup"],
     "res": ["funding-materials-checklist", "funding-policy-tracker"]},
    {"file": "book/06-从学校走向第一份工作.md", "entry": "### Offer 怎么比较",
     "figs": [], "res": ["offer-comparison"]},
]


def fig_block(name: str, prefix: str) -> str:
    src, alt = FIGS[name]
    return f"![{alt}]({prefix}{src})"


def rel_prefix(path: Path) -> str:
    """从 Markdown 文件所在目录回到仓库根：book/x.md → ../，docs/a/x.md → ../../"""
    return "../" * len(path.relative_to(ROOT).parent.parts)


def res_block(ids: list[str]) -> str:
    return ":::resources " + ", ".join(ids) + "\n:::"


def insert_before(lines: list[str], heading: str, block: list[str], path: Path) -> bool:
    idx = [i for i, l in enumerate(lines) if l.strip() == heading.strip()]
    if len(idx) != 1:
        raise SystemExit(f"{path}: 找不到唯一标题 {heading!r}（命中 {len(idx)} 次）")
    i = idx[0]
    lines[i:i] = block + [""]
    return True


def process_doc(spec: dict) -> str:
    path = ROOT / spec["file"]
    lines = path.read_text(encoding="utf-8").split("\n")
    orig = "\n".join(lines)
    changed = []
    for heading, name in spec.get("figs", []):
        if FIGS[name][0].split("/")[-1] in orig:
            continue
        insert_before(lines, heading, [fig_block(name, rel_prefix(path))], path)
        changed.append(name)
    if spec.get("res") and ":::resources " + spec["res"][0] not in "\n".join(lines):
        insert_before(lines, "## 相关", [res_block(spec["res"])], path)
        changed.append("resources")
    if changed:
        path.write_text("\n".join(lines), encoding="utf-8")
    return ", ".join(changed) or "已是最新"


def process_book(spec: dict) -> str:
    path = ROOT / spec["file"]
    lines = path.read_text(encoding="utf-8").split("\n")
    hits = [i for i, l in enumerate(lines) if l.strip() == spec["entry"]]
    if len(hits) != 1:
        raise SystemExit(f"{path}: 找不到唯一条目 {spec['entry']!r}")
    start = hits[0]
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("### ")),
               len(lines))
    changed = []
    for name in spec.get("figs", []):
        if FIGS[name][0].split("/")[-1] in "\n".join(lines[start:end]):
            continue
        fence = next(i for i in range(start, end) if lines[i].strip() == "```")
        lines[fence + 1:fence + 1] = ["", fig_block(name, rel_prefix(path))]
        end += 2
        changed.append(name)
    if spec.get("res"):
        block = res_block(spec["res"])
        if block not in "\n".join(lines[start:end]):
            rel = next((i for i in range(start, end) if lines[i].strip() == "## 相关"), None)
            pos = rel if rel is not None else end
            lines[pos:pos] = [block, ""]
            changed.append("resources")
    if changed:
        path.write_text("\n".join(lines), encoding="utf-8")
    return ", ".join(changed) or "已是最新"


def main() -> int:
    for spec in DOCS:
        print(f"{spec['file']:48s} {process_doc(spec)}")
    for spec in BOOK:
        print(f"{spec['file']:48s} {process_book(spec)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
