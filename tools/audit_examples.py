#!/usr/bin/env python3
"""审查「例子密度」：找出只讲道理、没有实例的文章。

判据（启发式，只报告不修改）：
  · 例子标记：例如 / 例： / 示例 / 举例 / 比如 / 例如说 / 走一遍 / 下面是一个
  · 代码块与代码片段
  · 表格
  · 带单位的数字（秒/分钟/小时/天/周/月/年/次/条/人/元/ms/%/KB/MB/GB/个/种）
  · 可执行结构：编号步骤、检查清单、命令块

输出：按缺例子程度排序的工作清单，用于安排增写顺序。

    python3 tools/audit_examples.py                 # 打印清单
    python3 tools/audit_examples.py --json
    python3 tools/audit_examples.py --dir docs/projects
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

EX_MARK = re.compile(r"(例如|例：|示例|举例|比如|例如说|走一遍|下面是一个|以你为例|举个例子|具体的人|具体场景|一个真实|完整示例|填入示例|示例：)")
EX_HEAD = re.compile(r"^#{2,3} .*(例|场景|案例|走一遍|具体的人|示例|实操|一天)", re.M)
NUM_UNIT = re.compile(r"\d+(\.\d+)?\s*(%|ms|毫秒|秒|分钟|小时|天|周|个月|月|年|次|条|人|元|万|KB|MB|GB|个|种|分|小时|周|刀)")
CODE_FENCE = re.compile(r"^```", re.M)
CMD_HINT = re.compile(r"(python3?|npm|git|curl|export|\$ |命令行|运行命令)")


def analyse(path: pathlib.Path) -> dict:
    text = path.read_text(encoding="utf-8")
    body = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)
    return {
        "rel": str(path.relative_to(ROOT)),
        "chars": len(re.sub(r"\s", "", body)),
        "examples": len(EX_MARK.findall(body)) + len(EX_HEAD.findall(body)),
        "fences": len(CODE_FENCE.findall(body)) // 2,
        "tables": len(re.findall(r"^\|\s*---", body, re.M)),
        "numbers": len(NUM_UNIT.findall(body)),
        "steps": len(re.findall(r"^\d+\.\s", body, re.M)),
        "checklists": len(re.findall(r"^- \[ \]", body, re.M)),
        "commands": len(CMD_HINT.findall(body)),
        "status": (re.search(r"^status:\s*(\w+)", text, re.M) or [None, "?"])[1],
    }


def score(r: dict) -> int:
    """缺例子程度的粗评分：越高越需要补例子。"""
    s = 0
    if r["examples"] == 0:
        s += 3
    elif r["examples"] == 1:
        s += 2
    if r["fences"] == 0 and r["commands"] == 0:
        s += 2
    if r["tables"] == 0:
        s += 1
    if r["numbers"] < 8:
        s += 2
    elif r["numbers"] < 20:
        s += 1
    if r["steps"] + r["checklists"] == 0:
        s += 1
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--dir", default=None, help="只审查某个目录，如 docs/projects")
    ap.add_argument("--top", type=int, default=200)
    args = ap.parse_args()

    root = ROOT / args.dir if args.dir else None
    files = sorted((root or ROOT / "docs").rglob("*.md")) if root else \
        sorted((ROOT / "docs").rglob("*.md")) + sorted((ROOT / "book").glob("*.md"))
    files = [p for p in files if p.name not in ("README.md", "ROADMAP.md")]

    rows = [analyse(p) for p in files]
    rows = [r for r in rows if r["status"] in ("complete", "partial", "?")]
    for r in rows:
        r["need"] = score(r)
    rows.sort(key=lambda r: (-r["need"], r["rel"]))

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0

    buckets = {}
    for r in rows:
        d = r["rel"].split("/")[1] if r["rel"].startswith("docs/") else "book"
        b = buckets.setdefault(d, {"n": 0, "need": 0, "no_ex": 0})
        b["n"] += 1
        b["need"] += r["need"]
        if r["examples"] == 0:
            b["no_ex"] += 1

    print(f"{'目录':24} {'篇数':>4} {'缺例总分':>8} {'零例子':>6}")
    for d, b in sorted(buckets.items(), key=lambda x: -x[1]["need"]):
        print(f"{d:24} {b['n']:>4} {b['need']:>8} {b['no_ex']:>6}")

    print(f"\n最需要补例子的 {min(args.top, len(rows))} 篇：")
    for r in rows[: args.top]:
        print(f"  [{r['need']}] {r['rel']:52} 例子{r['examples']:>2} 表{r['tables']:>2} "
              f"数字{r['numbers']:>3} 步骤{r['steps']:>2} 代码块{r['fences']:>2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
