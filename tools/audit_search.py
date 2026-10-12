#!/usr/bin/env python3
"""搜索可发现性审查：用真实读者的问法跑一遍站点搜索，看能不能找到东西。

打分逻辑与 site/app.js 的 runSearch / scoreEntry 保持一致：
  同义词组内取「或」，组间取「与」；命中权重
  标题完全一致 200 / 标题前缀 120 / 标题包含 80 / summary 30 / 标签 20 / 正文 8。

    python3 tools/audit_search.py             # 跑预设问法
    python3 tools/audit_search.py --queries "保研 失败" "实习 找不到"
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent

DEFAULT_QUERIES = [
    "保研", "考研 二战", "考研还是就业", "转专业", "读博", "留学 预算",
    "实习 怎么找", "简历 没回复", "面试 紧张", "谈薪", "offer 怎么选",
    "秋招 时间", "内推", "考公", "选调", "二战", "雅思", "公派",
    "开源 贡献", "科研 入门", "导师 邮件", "论文 投稿", "竞赛", "证书",
    "副业", "转行", "跳槽", "落户", "gap year", "论文 复现",
]


def load():
    idx = json.loads((ROOT / "site" / "data" / "index.json").read_text(encoding="utf-8"))
    aliases = json.loads((ROOT / "site" / "search_aliases.json").read_text(encoding="utf-8"))
    aliases = {k: v for k, v in aliases.items() if not k.startswith("_")}
    return idx, aliases


def label_maps(idx):
    m = {}
    for facet, spec in (idx.get("facets") or {}).items():
        m[facet] = {v["key"]: v.get("label", v["key"]) for v in spec.get("values", [])}
    return m


def entry_hay(e, L):
    tags = []
    for f in ("stages", "topics", "outputs", "evidence"):
        for v in e.get(f) or []:
            tags.append(L.get(f, {}).get(v, v))
    return " ".join([e.get("title", ""), e.get("summary", ""), e.get("text", ""),
                     e.get("doc_title", ""), " ".join(tags)]).lower()


def score(e, hay, groups):
    if not groups:
        return 0
    total = 0
    title = e.get("title", "").lower()
    summary = (e.get("summary") or "").lower()
    tags = " ".join(e.get("_tags") or []).lower()
    for terms in groups:
        hit = None
        for t in terms:
            if t not in hay:
                continue
            if title == t:
                h = 200
            elif title.startswith(t):
                h = 120
            elif t in title:
                h = 80
            elif t in summary:
                h = 30
            elif t in tags:
                h = 20
            else:
                h = 8
            hit = h if hit is None else max(hit, h)
        if hit is None:
            return -1
        total += hit
    return total + (1 if e.get("last_verified") else 0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--queries", nargs="*", default=None)
    ap.add_argument("--top", type=int, default=3)
    args = ap.parse_args()

    idx, aliases = load()
    L = label_maps(idx)
    # 与 site/app.js 保持一致：搜索范围 = Book 条目 + 首页问题 + 用户侧文档
    searchable_docs = [d for d in idx.get("docs", [])
                       if d.get("kind") == "doc" and d.get("status") != "planned" and d.get("text")]
    entries = idx["entries"] + idx.get("questions", []) + searchable_docs
    for e in entries:
        e["_hay"] = entry_hay(e, L)
        tags = []
        for f in ("stages", "topics", "outputs", "evidence"):
            for v in e.get(f) or []:
                tags.append(L.get(f, {}).get(v, v))
        e["_tags"] = tags

    queries = args.queries or DEFAULT_QUERIES
    empty, weak = [], []
    for q in queries:
        tokens = [t for t in re.split(r"\s+", q.lower().strip()) if t]
        groups = []
        for t in tokens:
            terms = [t] + [s.lower() for s in aliases.get(t, []) if s.lower() != t]
            groups.append(terms)
        scored = [(score(e, e["_hay"], groups), e) for e in entries]
        scored = [(s, e) for s, e in scored if s >= 0]
        scored.sort(key=lambda x: (-x[0], x[1].get("title", "")))
        top = scored[: args.top]
        if not top:
            empty.append(q)
            print(f"✗ 「{q}」→ 无结果")
            continue
        if top[0][0] <= 30:
            weak.append((q, top))
        tops = " | ".join(f"{e.get('title','')[:18]}({s})" for s, e in top)
        print(f"{'!' if top[0][0] <= 30 else '·'} 「{q}」→ {tops}")

    print(f"\n合计 {len(queries)} 个问法：无结果 {len(empty)}，最相关结果偏弱 {len(weak)}")
    if weak:
        print("\n偏弱的问法（最高分 ≤30，说明只在摘要或正文里命中）：")
        for q, top in weak:
            print(f"  「{q}」→ " + " | ".join(f"{e.get('title','')[:24]}" for _, e in top))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
