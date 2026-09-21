#!/usr/bin/env python3
"""声明审计：扫描已写完条目里的高风险绝对化措辞。

只做报告，不阻塞 CI。目的不是禁用这些词，而是把「强表达」和「有没有依据」
放在一起看：有官方规则 / 研究 / 行业数据支撑的强表达可以保留；
经验性判断则不该无条件使用唯一、绝对、一定、必须、最好这类词。

用法：
    python3 tools/audit_claims.py
    python3 tools/audit_claims.py --json
    python3 tools/audit_claims.py --term 唯一 --term 必须
    python3 tools/audit_claims.py --only-risk      # 只看建议改写的那些
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import meta as M  # noqa: E402

# 高风险措辞（可在命令行覆盖）
TERMS = ["唯一", "一定", "必须", "绝对", "永远", "优先", "最好", "最有效",
         "标准只有", "大多数", "最多", "最重要", "肯定", "只要"]

# 这些证据类型支持强表达
STRONG_EVIDENCE = {"official", "research_backed", "industry_data"}
SENTENCE_SPLIT = re.compile(r"[。！？；\n]")


def sentence_of(line: str, term: str) -> str:
    parts = SENTENCE_SPLIT.split(line)
    for p in parts:
        if term in p:
            return p.strip()
    return line.strip()


def scan(root: Path, terms: list[str]) -> list[dict]:
    found: list[dict] = []
    for doc in M.load_docs(root):
        for seg in doc.segments:
            if seg["kind"] != "entry":
                continue
            meta_block = seg["meta"] or {}
            if str(meta_block.get("status") or "") != "complete":
                continue
            evidence = M._as_list(meta_block.get("evidence"))
            text = M.strip_fenced("\n".join(seg["lines"]))
            for lineno, line in enumerate(text.splitlines(), start=1):
                for term in terms:
                    if term in line:
                        found.append({
                            "file": doc.rel,
                            "entry": str(meta_block.get("id") or ""),
                            "title": seg["title"],
                            "line": lineno,
                            "term": term,
                            "sentence": sentence_of(line, term),
                            "evidence": evidence,
                            "risk": "ok" if set(evidence) & STRONG_EVIDENCE else "review",
                        })
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description="高风险绝对化措辞审计（只报告）")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--term", action="append", default=None, help="只查这些词（可重复）")
    ap.add_argument("--only-risk", action="store_true", help="只输出建议改写的命中")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    terms = args.term or TERMS
    hits = scan(Path(args.root).resolve(), terms)
    if args.only_risk:
        hits = [h for h in hits if h["risk"] == "review"]

    if args.json:
        print(json.dumps(hits, ensure_ascii=False, indent=2))
        return 0

    review = [h for h in hits if h["risk"] == "review"]
    print(f"声明审计：命中 {len(hits)} 处（其中经验性判断 {len(review)} 处建议改写）")
    by_term: dict[str, int] = {}
    for h in hits:
        by_term[h["term"]] = by_term.get(h["term"], 0) + 1
    if by_term:
        print("按词统计：" + "，".join(f"{k} {v}" for k, v in
                                  sorted(by_term.items(), key=lambda x: -x[1])))
    if review:
        print("\n需要人工判断的命中（没有官方/研究/行业数据支撑）：")
        for h in review:
            print(f"  [{h['file']}] {h['entry']} 第 {h['line']} 行 · {h['term']}")
            print(f"      {h['sentence'][:120]}")
    else:
        print("\n没有需要处理的经验性绝对化表述。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
