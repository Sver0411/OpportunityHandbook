#!/usr/bin/env python3
"""编辑审校辅助：定位条目内部的重复内容（启发式，只报告不修改）。\n\n注意：只比对段落，不比对列表项与表格——并列条目的句式相似是正常的，\n真正要抓的是「同一段意思出现两次」。

检查三类信号：
  1. 近似重复段落/句子（同一段意思出现两次）
  2. 重复小节标题（H2 语义相同，如「低质量赛事的识别」与「识别低质量比赛」）
  3. 重复表格（同一张表出现两次）

用法：
    python3 tools/report_duplication.py                 # 全库
    python3 tools/report_duplication.py --id <entry_id> # 单条目
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import meta as M  # noqa: E402


def sentences(text: str) -> list[str]:
    """取出可比对的段落句子：跳过列表项、表格与标题（并列条目句式相似是正常的）。"""
    out: list[str] = []
    for block in re.split(r"\n\s*\n", text):
        block = block.strip()
        if not block or block.startswith(("-", "|", "#", ">", "```")):
            continue
        for p in re.split(r"[。；]+", block):
            p = p.strip()
            if len(p) >= 12:
                out.append(p)
    return out


def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def check_entry(eid: str, text: str) -> list[str]:
    issues: list[str] = []
    body = text.split("## 来源与更新")[0]

    # 1) 近似重复句
    sents = sentences(body)
    flagged = set()
    for i, a in enumerate(sents):
        for j in range(i + 1, len(sents)):
            b = sents[j]
            if abs(len(a) - len(b)) > max(len(a), len(b)) * 0.6:
                continue
            if similarity(a, b) >= 0.75:
                key = (a[:20], b[:20])
                if key in flagged:
                    continue
                flagged.add(key)
                issues.append(f"近似重复句：\n      A: {a[:70]}\n      B: {b[:70]}")

    # 2) 重复/近义小节标题
    heads = re.findall(r"^## (.+?)[ \t]*$", body, re.M)
    for i, h in enumerate(heads):
        for j in range(i + 1, len(heads)):
            if similarity(h, heads[j]) >= 0.5:
                issues.append(f"近义小节标题：《{h}》 / 《{heads[j]}》")

    # 3) 重复表格（同一表头出现两次）
    tables = re.findall(r"^\|(.+?)\|[ \t]*\n\|[\s\-|:]+\|[ \t]*$", body, re.M)
    seen = {}
    for t in tables:
        key = t.strip()
        if key in seen:
            issues.append(f"重复表格：表头「{key[:40]}」出现两次")
        seen[key] = True
    return issues


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", dest="only", help="只检查某个 entry id")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    docs = M.load_docs(ROOT)
    errors, warnings, extra = M.validate(ROOT, docs)

    report = {}
    for e in extra["entries"]:
        if e.get("kind") != "entry":
            continue
        eid = e.get("id")
        if args.only and eid != args.only:
            continue
        issues = check_entry(eid, e.get("text") or "")
        if issues:
            report[eid] = issues

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        total = sum(len(v) for v in report.values())
        if args.only:
            for i in report.get(args.only, []):
                print("  -", i)
            if args.only not in report:
                print("  未发现重复信号")
            return 0
        print(f"含重复信号的条目：{len(report)}，信号条数：{total}")
        for eid, issues in report.items():
            print(f"\n## {eid}")
            for i in issues:
                print("  -", i)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
