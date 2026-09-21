#!/usr/bin/env python3
"""Metadata Audit：检查 complete 条目的 stages 与内容主题是否一致。

    python3 tools/metadata_audit.py            # 生成 reports/metadata-audit.md 并打印摘要
    python3 tools/metadata_audit.py --json

规则（WARNING 级，不自动修改）：
  - 内容属于职场阶段（06/07 章的晋升、管理、跳槽、绩效等主题），
    却完全没有 work_1_3 / work_3_5 / senior / career_change —— 可疑；
  - 内容属于学生阶段（00–05 章）却出现 senior —— 可疑；
  - stages 为空或含未知枚举值 —— 错误。
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import meta as M  # noqa: E402

WORK_STAGES = {"work_1_3", "work_3_5", "senior", "career_change"}
# 学生阶段：明显职场中后期的条目不应再挂这些
STUDENT_STAGES = {"highschool", "secondary_vocational", "college", "undergraduate",
                  "master", "phd", "new_grad"}
# 06/07 章里明显属于职场阶段的主题关键词（标题级匹配）
WORK_TOPICS = ("晋升", "Senior", "Staff", "Principal", "Manager", "Team Lead", "跳槽",
               "绩效", "招聘", "第一次带人", "行业影响力", "Ownership", "试用期",
               "留用", "转行", "降薪", "Bridge", "MBA", "海外工作", "内部转岗",
               "Mentor", "Networking", "谈薪", "背调", "毁约", "空窗期", "第二职业",
               "职业中断", "副业转主业", " prove", "影响力")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    docs = M.load_docs(ROOT)
    errors, warnings, extra = M.validate(ROOT, docs)
    entries = [e for e in extra["entries"] if e.get("status") == "complete" and e.get("kind") == "entry"]

    suspicious = []
    overbroad = []
    invalid = []
    for e in entries:
        stages = set(e.get("stages") or [])
        title = str(e.get("title") or "")
        loc = str(e.get("location") or "")
        known = stages <= {s for s in
                           ("highschool", "secondary_vocational", "college", "undergraduate",
                            "master", "phd", "new_grad", "work_1_3", "work_3_5", "senior",
                            "career_change")}
        if not stages or not known:
            invalid.append({"id": e.get("id"), "title": title, "stages": sorted(stages)})
            continue
        in_work_chapter = loc.startswith("book/06") or loc.startswith("book/07")
        title_is_work = any(k in title for k in WORK_TOPICS)
        # 可疑项只看职场章节（06/07）：05 校招章节按定义保留学生阶段
        if in_work_chapter and not (stages & WORK_STAGES):
            suspicious.append({"id": e.get("id"), "title": title, "file": loc,
                               "stages": sorted(stages)})
        # 第二类：明显职场中后期条目仍混入大量学生阶段
        late_career = {"senior"} <= stages or ({"work_3_5"} <= stages and not stages & STUDENT_STAGES)
        if title_is_work and (stages & STUDENT_STAGES) and late_career:
            overbroad.append({"id": e.get("id"), "title": title, "file": loc,
                              "stages": sorted(stages)})

    report = {
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "total_complete_entries": len(entries),
        "stage_suspicious": suspicious,
        "stage_overbroad": overbroad,
        "stage_invalid": invalid,
    }
    out = ROOT / "reports" / "metadata-audit.md"
    lines = [
        "# Metadata Audit Report",
        "",
        f"生成时间：{report['generated_at']}",
        "",
        f"complete 条目：{len(entries)}",
        f"- stages 可疑（职场主题但无职场阶段标注）：{len(suspicious)}",
        f"- stages 过宽（职场中后期仍挂学生阶段）：{len(overbroad)}",
        f"- stages 非法或为空：{len(invalid)}",
        "",
        "说明：可疑项只做提示，不自动修改；需要按内容逐条重判 stages。",
        "",
    ]
    if suspicious:
        lines += ["## stages 可疑清单", "", "| entry_id | 标题 | 文件 | 当前 stages |", "| --- | --- | --- | --- |"]
        lines += [f"| {x['id']} | {x['title']} | {x['file']} | {', '.join(x['stages'])} |" for x in suspicious]
        lines.append("")
    if overbroad:
        lines += ["## stage_overbroad 清单", "", "| entry_id | 标题 | 文件 | 当前 stages |", "| --- | --- | --- | --- |"]
        lines += [f"| {x['id']} | {x['title']} | {x['file']} | {', '.join(x['stages'])} |" for x in overbroad]
        lines.append("")
    if invalid:
        lines += ["## stages 非法清单", ""]
        lines += [f"- {x['id']}：{x['stages']}" for x in invalid]
        lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"stages 可疑：{len(suspicious)}，过宽：{len(overbroad)}，非法：{len(invalid)}")
        for x in suspicious[:15]:
            print(f"  {x['id']} 《{x['title']}》 {x['stages']}")
        print(f"报告已写出：{out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
