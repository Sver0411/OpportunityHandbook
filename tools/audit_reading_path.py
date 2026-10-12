#!/usr/bin/env python3
"""读者动线审查：从「第一眼看到什么 → 能不能找到 → 读完有没有下一步」检查。

检查项：
  1. 断头路页面：没有任何出链（读完就卡住）
  2. 缺少「下一步」：既没有「相关」小节，也没有指向上下层的链接
  3. 重复标题：不同页面用相同标题，读者在搜索里分不清
  4. 首页问题是否都能落地（锚点存在、目标页面存在）
  5. 过长页面缺少小节结构（>6000 字但 H2 少于 5 个）
  6. 深层页面是否有回程链接（回到所属章节/手册）

    python3 tools/audit_reading_path.py
    python3 tools/audit_reading_path.py --json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from collections import defaultdict

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import meta as M  # noqa: E402


def analyse(path: pathlib.Path) -> dict:
    text = path.read_text(encoding="utf-8")
    body = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)
    links = re.findall(r"\]\(([^)]+)\)", body)
    internal = [l for l in links if not l.startswith(("http", "mailto"))]
    title = (re.search(r"^title:\s*(.+?)\s*$", text, re.M) or [None, path.stem])[1]
    m = re.search(r"^summary:\s*(.+?)\s*$", text, re.M)
    return {
        "rel": str(path.relative_to(ROOT)),
        "title": title.strip(),
        "status": (re.search(r"^status:\s*(\w+)", text, re.M) or [None, "?"])[1],
        "section": (re.search(r"^section:\s*(.+?)\s*$", text, re.M) or [None, "?"])[1],
        "chars": len(re.sub(r"\s", "", body)),
        "h2": len(re.findall(r"^## ", body, re.M)),
        "internal": len(internal),
        "has_related": bool(re.search(r"^## (相关|下一步|继续|可以继续看)", body, re.M)),
        "up_link": any(l.startswith("../") or l.startswith("../../book") for l in internal),
        "summary": (m.group(1).strip() if m else ""),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    files = [p for p in list((ROOT / "docs").rglob("*.md")) + list((ROOT / "book").glob("*.md"))
             if p.name not in ("README.md", "ROADMAP.md")]
    rows = [r for r in (analyse(p) for p in files) if r["status"] in ("complete", "partial", "?")]

    dead_end = [r for r in rows if r["internal"] == 0]
    no_next = [r for r in rows if not r["has_related"]]
    no_up = [r for r in rows if not r["up_link"] and r["rel"].startswith("docs/")]
    thin_structure = [r for r in rows if r["chars"] > 6000 and r["h2"] < 5]
    missing_summary = [r for r in rows if not r["summary"] or len(r["summary"]) < 12]

    # 远距离指代：「前者/后者」的先行词在 120 字以前（读者需要回找）
    distant_ref = []
    for p in files:
        body = re.sub(r"^---\n.*?\n---\n", "", p.read_text(encoding="utf-8"), flags=re.S)
        for m in re.finditer(r"前者|后者", body):
            pre = body[max(0, m.start() - 120):m.start()]
            if not re.search(r"(区分|还是|与|和|、)", pre):
                distant_ref.append((str(p.relative_to(ROOT)), re.sub(r"\s+", " ", body[max(0, m.start() - 40):m.end() + 30])))

    titles = defaultdict(list)
    for r in rows:
        titles[r["title"]].append(r["rel"])
    dup_titles = {t: v for t, v in titles.items() if len(v) > 1}

    # 首页问题能否落地
    hq = ROOT / "meta" / "home-questions.md"
    broken_q = []
    if hq.is_file():
        text = hq.read_text(encoding="utf-8")
        entry_titles = {}
        for p in list((ROOT / "book").glob("*.md")) + list((ROOT / "docs").rglob("*.md")):
            t = p.read_text(encoding="utf-8")
            for m in re.finditer(r"^#{2,3} (.+?)\s*$", t, re.M):
                entry_titles.setdefault(m.group(1).strip(), str(p.relative_to(ROOT)))
        for m in re.finditer(r"](\.\./[^)]+)\)", text):
            target = m.group(1)
            path_part, _, anchor = target.partition("#")
            p = (hq.parent / path_part).resolve()
            if not p.is_file():
                broken_q.append(target)
                continue
            if anchor:
                body = p.read_text(encoding="utf-8")
                slugs = set()
                for h in re.findall(r"^#{2,4} (.+?)\s*$", body, re.M):
                    slugs.add(re.sub(r"[^\w\u4e00-\u9fa5]+", "-", h).strip("-"))
                if anchor not in slugs:
                    broken_q.append(target)

    report = {
        "total": len(rows),
        "dead_end": dead_end,
        "no_next": no_next,
        "no_up": no_up,
        "thin_structure": thin_structure,
        "missing_summary": missing_summary,
        "dup_titles": dup_titles,
        "broken_questions": broken_q,
        "distant_ref": distant_ref,
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    print(f"审查页面：{report['total']}")
    print(f"\n① 断头路（无任何出链）：{len(dead_end)}")
    for r in dead_end[:10]:
        print(f"   {r['rel']}")
    print(f"\n② 没有「相关/下一步」小节：{len(no_next)}")
    for r in no_next[:15]:
        print(f"   {r['rel']}  ({r['section']})")
    print(f"\n③ 深层页面没有回程链接：{len(no_up)}")
    for r in no_up[:10]:
        print(f"   {r['rel']}")
    print(f"\n④ 长文缺少小节结构（>6000 字且 H2<5）：{len(thin_structure)}")
    for r in thin_structure[:8]:
        print(f"   {r['rel']}  {r['chars']}字 / {r['h2']} 个 H2")
    print(f"\n⑤ summary 缺失或过短：{len(missing_summary)}")
    for r in missing_summary[:8]:
        print(f"   {r['rel']}")
    print(f"\n⑥ 重复标题：{len(dup_titles)} 组")
    for t, v in list(dup_titles.items())[:12]:
        print(f"   《{t}》 → {v}")
    print(f"\n⑦ 首页问题无法落地：{len(broken_q)}")
    print(f"\n⑧ 远距离指代（前者/后者，需要回找）：{len(distant_ref)}")
    for rel, frag in distant_ref[:8]:
        print(f"   {rel}: …{frag}…")
    for b in broken_q[:10]:
        print(f"   {b}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
