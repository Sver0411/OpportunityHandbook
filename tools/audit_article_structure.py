#!/usr/bin/env python3
"""文章结构审计（report-only）：找出主线里仍然套用同一套骨架的条目。

    python3 tools/audit_article_structure.py
    python3 tools/audit_article_structure.py --json

输出：
  · 高频 H2（同一标题在多少条目里出现）
  · 连续使用 3 个以上模板式 H2 的条目
  · 同一组 H2 组合重复出现的次数

不阻塞 CI：它的作用是发现「批量模板感」，而不是禁止某个标题。
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import meta as M  # noqa: E402

# 旧字段骨架留下的典型标题（出现本身不算错，密集重复才是问题）
TEMPLATE_H2 = {
    "适合谁", "谁适合、谁不适合", "谁需要、谁不需要", "不适合谁", "哪些人适合",
    "能换回什么", "能换回什么、付出什么", "要付出什么", "收益与成本", "成本与回退",
    "怎么开始", "第一步做什么", "常见误区", "常见错误", "容易踩的坑",
    "下一步可能打开什么", "接下来可以看什么", "下一步", "它是什么",
}


def entry_h2s(seg: dict) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^## +(.+?)\s*$", "\n".join(seg["lines"]), re.M)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    docs = M.load_docs(ROOT)
    counter: collections.Counter = collections.Counter()
    combos: collections.Counter = collections.Counter()
    runs = []
    total_entries = 0
    entries_with_template = []

    for doc in docs:
        for seg in doc.segments:
            if seg["kind"] != "entry":
                continue
            meta = seg["meta"] or {}
            if str(meta.get("status")) != "complete":
                continue
            total_entries += 1
            h2s = entry_h2s(seg)
            if not h2s:
                continue
            for h in h2s:
                counter[h] += 1
            tpl = [h for h in h2s if h in TEMPLATE_H2]
            if tpl:
                entries_with_template.append({"file": doc.rel, "id": str(meta.get("id")), "title": seg["title"],
                                              "template_h2": tpl, "total_h2": len(h2s)})
            combo = " → ".join(tpl)
            if len(tpl) >= 2:
                combos[combo] += 1
            # 连续 3 个以上模板式 H2
            run = best = 0
            for h in h2s:
                run = run + 1 if h in TEMPLATE_H2 else 0
                best = max(best, run)
            if best >= 3:
                runs.append({"file": doc.rel, "id": str(meta.get("id")), "title": seg["title"], "run": best})

    top = counter.most_common(20)
    report = {
        "entries": total_entries,
        "template_h2_total": sum(len(x["template_h2"]) for x in entries_with_template),
        "entries_with_template": len(entries_with_template),
        "entries_with_run3": len(runs),
        "top_h2": top,
        "top_combos": combos.most_common(10),
        "longest_runs": sorted(runs, key=lambda x: -x["run"])[:15],
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    print(f"complete 条目：{total_entries}")
    print(f"含模板式 H2 的条目：{len(entries_with_template)}（共 {report['template_h2_total']} 个 H2）")
    print(f"连续 ≥3 个模板式 H2 的条目：{len(runs)}")
    print("\n最高频 H2：")
    for h, n in top:
        print(f"  {n:4} {h}")
    print("\n最高频模板组合：")
    for c, n in report["top_combos"][:6]:
        print(f"  {n:3} {c}")
    print("\n连续模板 H2 最长的条目：")
    for r in report["longest_runs"][:10]:
        print(f"  {r['run']} 连 {r['id']:34} 《{r['title']}》")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
