#!/usr/bin/env python3
"""声明审计：把高风险措辞按类型分级，并标出「经验性判断里的统计式断言」。

只做报告，不阻塞 CI。目的不是禁用这些词，而是把「强表达」和「有没有依据」
放在一起看：有官方规则 / 研究 / 行业数据支撑的强表达可以保留；
经验性判断（evidence: experience_based）则不该出现统计式表述。

用法：
    python3 tools/audit_claims.py
    python3 tools/audit_claims.py --only-risk      # 只看建议改写的命中
    python3 tools/audit_claims.py --only-expensive # 只看「经验性 + 统计式」这类最该改的
    python3 tools/audit_claims.py --term 唯一 --term 必须
    python3 tools/audit_claims.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import meta as M  # noqa: E402

# 按类型分组的词表
CLAIM_TYPES: dict[str, list[str]] = {
    # 绝对化断言：只有官方规则或明确事实支撑才应保留
    "absolute": [
        "唯一", "一定", "必须", "绝对", "永远", "肯定", "只要", "标准只有",
        "最重要", "不会", "一定会", "基本上", "几乎",
    ],
    # 统计式断言：没有可靠数据就不该写
    "statistical": [
        "大多数", "多数人", "多数行业", "多数岗位", "多数项目", "多数企业",
        "通常", "普遍", "往往", "显著", "大幅", "成功率", "更容易", "更可能",
        "一般都会", "基本都是", "比例", "概率", "平均",
    ],
    # 建议型措辞：可以用于官方硬规则，经验性内容需要给出条件
    "recommendation": [
        "最好", "优先", "更重要", "应该", "建议", "最有效", "更划算", "首选",
    ],
}

ALL_TERMS = [t for terms in CLAIM_TYPES.values() for t in terms]
TERM_TYPE = {t: k for k, terms in CLAIM_TYPES.items() for t in terms}

STRONG_EVIDENCE = {"official", "research_backed", "industry_data"}
SENTENCE_SPLIT = re.compile(r"[。！？；\n]")


def sentence_of(line: str, term: str) -> str:
    for p in SENTENCE_SPLIT.split(line):
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
                    if term not in line:
                        continue
                    kind = TERM_TYPE.get(term, "recommendation")
                    strong = bool(set(evidence) & STRONG_EVIDENCE)
                    if strong:
                        risk = "ok"
                    elif kind == "statistical":
                        # 经验性条目里的统计式断言：最该改的一类
                        risk = "experience-statistical"
                    else:
                        risk = "review"
                    found.append({
                        "file": doc.rel,
                        "entry": str(meta_block.get("id") or ""),
                        "title": seg["title"],
                        "line": lineno,
                        "term": term,
                        "type": kind,
                        "sentence": sentence_of(line, term),
                        "evidence": evidence,
                        "risk": risk,
                    })
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description="高风险措辞审计（只报告）")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--term", action="append", default=None, help="只查这些词（可重复）")
    ap.add_argument("--only-risk", action="store_true", help="只输出建议改写的命中")
    ap.add_argument("--only-expensive", action="store_true",
                    help="只输出「经验性判断 + 统计式断言」")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    terms = args.term or ALL_TERMS
    hits = scan(Path(args.root).resolve(), terms)
    if args.only_expensive:
        hits = [h for h in hits if h["risk"] == "experience-statistical"]
    elif args.only_risk:
        hits = [h for h in hits if h["risk"] != "ok"]

    if args.json:
        print(json.dumps(hits, ensure_ascii=False, indent=2))
        return 0

    by_type: dict[str, int] = {}
    for h in hits:
        by_type[h["type"]] = by_type.get(h["type"], 0) + 1
    exp_stat = [h for h in hits if h["risk"] == "experience-statistical"]
    review = [h for h in hits if h["risk"] == "review"]

    print(f"声明审计：命中 {len(hits)} 处")
    print("按类型：" + "，".join(f"{k} {v}" for k, v in sorted(by_type.items(), key=lambda x: -x[1])))
    print(f"经验性判断里的统计式断言（建议优先改写）：{len(exp_stat)} 处")
    print(f"其余建议人工判断（absolute / recommendation 无强证据）：{len(review)} 处")

    if exp_stat:
        print("\n=== 经验性 + 统计式（最该改） ===")
        for h in exp_stat[:40]:
            print(f"  [{h['file']}] {h['entry']} 第 {h['line']} 行 · {h['term']}")
            print(f"      {h['sentence'][:130]}")
        if len(exp_stat) > 40:
            print(f"  … 还有 {len(exp_stat) - 40} 处")
    if review:
        print("\n=== 其他建议人工判断 ===")
        for h in review[:25]:
            print(f"  [{h['file']}] {h['entry']} 第 {h['line']} 行 · {h['term']}（{h['type']}）")
        if len(review) > 25:
            print(f"  … 还有 {len(review) - 25} 处")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
