# -*- coding: utf-8 -*-
"""HTML 唯一 id 与导航锚点检查（对构建产物 site/content/*.html）。"""
import collections
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/mac/WorkBuddy/OpportunityHandbook")
SITE = ROOT / "site" / "content"


def check_duplicate_ids() -> list[str]:
    problems = []
    for p in sorted(SITE.rglob("*.html")):
        html = p.read_text(encoding="utf-8")
        ids = re.findall(r'\bid="([^"]+)"', html)
        dup = [k for k, v in collections.Counter(ids).items() if v > 1]
        if dup:
            problems.append(f"{p.relative_to(SITE)}: 重复 id {dup[:5]}（共 {len(dup)} 个）")
    return problems


def check_entry_heading_prefix() -> list[str]:
    """条目内的 heading id 必须带 `{entry_id}--` 前缀，避免跨条目污染。"""
    problems = []
    for p in sorted(SITE.rglob("*.html")):
        html = p.read_text(encoding="utf-8")
        for m in re.finditer(r'<section class="entry" id="([^"]+)">(.*?)</section>', html, re.S):
            eid, block = m.group(1), m.group(2)
            for hid in re.findall(r'<h2 id="([^"]+)"', block):
                if not hid.startswith(eid + "--"):
                    problems.append(f"{p.relative_to(SITE)}: #{eid} 的 H2 id 「{hid}」缺少条目前缀")
                    break
    return problems


def main() -> int:
    problems = check_duplicate_ids() + check_entry_heading_prefix()
    if problems:
        for x in problems[:20]:
            print("  x", x)
        print(f"HTML id 问题：{len(problems)}")
        return 1
    pages = len(list(SITE.rglob("*.html")))
    print(f"HTML id 检查：PASS（{pages} 个页面，重复 id = 0，条目 H2 前缀齐全）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
