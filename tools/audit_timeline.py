#!/usr/bin/env python3
"""时间线专项审计（report-only）：找出把「经验节奏」写成「统一规则」的表述。

    python3 tools/audit_timeline.py            # 打印报告并写出 reports/timeline-review.md
    python3 tools/audit_timeline.py --json

对 docs/timelines/* 逐条扫描高风险措辞，人工判断属于哪一类：
  · 官方固定日程（可以保留强表达）
  · 经验性范围（应写明是常见范围）
  · 错误泛化（不能写成全国统一规则）
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

# 高风险措辞：固定月份/小时、伪统一、承诺式
PATTERNS = [
    (r"\d+\s*小时", "把时间点写成固定小时"),
    (r"\d+\s*[–\-—~]\s*\d+\s*月", "把批次写成固定月份区间"),
    (r"主战场", "军事化强表达"),
    (r"名额明显少", "统计式断言"),
    (r"确保", "承诺式表达"),
    (r"都会", "全称断言"),
    (r"通常两年|通常三|通常四|都能", "统计式断言"),
    (r"一定", "绝对化"),
    (r"必须", "需区分官方硬规则与经验建议"),
    (r"多数(人|项目|学校|公司)", "统计式断言"),
    (r"最(早|晚)", "绝对化"),
]

BOUNDARY_HINTS = ("以官方", "以当年", "以目标", "为准", "常见范围", "示意节奏", "不是统一")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = []
    for p in sorted((ROOT / "docs" / "timelines").glob("*.md")):
        text = p.read_text(encoding="utf-8")
        body = text.split("---", 2)[2] if text.startswith("---") else text
        hits = []
        for pat, why in PATTERNS:
            for m in re.finditer(pat, body):
                line = body[: m.start()].count("\n") + 1
                snippet = body.splitlines()[line - 1].strip()[:80]
                hits.append({"line": line, "pattern": m.group(0), "why": why, "text": snippet})
        has_boundary = any(h in body for h in BOUNDARY_HINTS)
        rows.append({"file": p.name, "hits": hits, "has_boundary_note": has_boundary})

    total = sum(len(r["hits"]) for r in rows)
    no_boundary = [r["file"] for r in rows if not r["has_boundary_note"]]

    if args.json:
        print(json.dumps({"total_hits": total, "files": rows, "no_boundary_note": no_boundary},
                         ensure_ascii=False, indent=2))
        return 0

    lines = [
        "# Timeline Review Report",
        "",
        f"生成时间：{datetime.datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        f"命中高风险措辞：{total} 处",
        f"缺少「以官方为准 / 常见范围」边界说明的文件：{len(no_boundary)}",
        "",
        "人工判断口径：官方固定日程可保留强表达；经验性范围必须写明是常见范围；"
        "把各国、各校、各公司差异写成统一规则的属于错误泛化，需要改写。",
        "",
    ]
    for r in rows:
        lines.append(f"## {r['file']}（命中 {len(r['hits'])}）")
        lines.append("")
        lines.append(f"- 边界说明：{'有' if r['has_boundary_note'] else '**缺**'}")
        for h in r["hits"][:12]:
            lines.append(f"- 第 {h['line']} 行 · `{h['pattern']}`（{h['why']}）：{h['text']}")
        lines.append("")
    out = ROOT / "reports" / "timeline-review.md"
    out.write_text("\n".join(lines), encoding="utf-8")

    print(f"时间线审计：命中 {total} 处；缺边界说明 {len(no_boundary)} 个文件")
    for r in rows:
        if r["hits"]:
            print(f"  {r['file']}: {len(r['hits'])} 处")
    print(f"报告已写出：reports/timeline-review.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
