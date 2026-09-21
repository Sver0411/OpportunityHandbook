#!/usr/bin/env python3
"""Canonical IA 一致性检查（导航与正文的 parity test）。

    python3 tools/check_ia.py            # 打印报告，有问题返回 1
    python3 tools/check_ia.py --json     # 输出机器可读结果

校验四条硬规则（CI 要求全部为 0）：

  Rule A  navigation.json 每个节点都必须有 target，且 target 指向的内容存在
  Rule B  target 必须能真实解析：entry 落在其所属文档里；doc 锚点必须真的存在
  Rule C  所有 status: complete 的公开条目，必须至少出现在 Canonical IA 一次
  Rule D  同一个条目只能有一个 canonical 挂载位置（可以交叉链接，不能重复挂载）
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import meta as M  # noqa: E402
import mdrender  # noqa: E402

NAV_PATH = ROOT / "meta" / "navigation.json"


def collect_anchors(doc: M.Doc) -> set[str]:
    """文档里所有真实的 HTML 锚点 id（## / ### 标题 + 条目 id + 文档自身 id）。"""
    ids: set[str] = set()
    for seg in doc.segments:
        if seg["kind"] == "text":
            for line in seg["lines"]:
                m = mdrender._HEADING_RE.match(line)
                if m:
                    ids.add(M.slugify(m.group(2)))
        else:
            eid = (seg.get("meta") or {}).get("id")
            if eid:
                ids.add(str(eid))
            ids.add(M.slugify(seg.get("title") or ""))
    return {i for i in ids if i}


def walk(nodes, trail=()):
    for n in nodes:
        here = trail + (n.get("title") or "",)
        yield n, here
        yield from walk(n.get("children") or [], here)


def check() -> dict:
    docs = M.load_docs(ROOT)
    errors, warnings, extra = M.validate(ROOT, docs)
    entries = extra["entries"]

    doc_by_loc = {}
    for d in docs:
        loc = d.rel[:-3] if d.rel.endswith(".md") else d.rel
        doc_by_loc[loc] = d

    entry_index = {}
    for e in entries:
        eid = str(e.get("id") or "")
        if eid:
            entry_index.setdefault(eid, e)

    nav = json.loads(NAV_PATH.read_text(encoding="utf-8"))
    items = nav.get("items") or []

    total = 0
    resolved = 0
    missing: list[str] = []          # Rule A
    broken: list[str] = []           # Rule B
    canonical_of: dict[str, list[str]] = {}   # Rule D

    for node, trail in walk(items):
        total += 1
        path = " > ".join(trail)
        target = node.get("target") or {}
        kids = node.get("children") or []

        if not target:
            # 纯分组节点：自身不需要 target，链接沿用第一个子节点
            if kids:
                resolved += 1
            else:
                missing.append(f"{path}（叶子节点没有 target）")
            continue

        if target.get("type") == "entry":
            eid = target.get("entry_id") or ""
            e = entry_index.get(eid)
            if not e:
                missing.append(f"{path} → 条目不存在：{eid}")
                continue
            if not kids:
                canonical_of.setdefault(eid, []).append(path)
            # Rule B：条目必须真的在它所属的文档里
            loc = str(e.get("location") or "")
            if loc not in doc_by_loc or eid not in collect_anchors(doc_by_loc[loc]):
                broken.append(f"{path} → 条目 {eid} 不在文档 {loc} 里")
                continue
            resolved += 1

        elif target.get("type") == "doc":
            loc = target.get("location") or ""
            d = doc_by_loc.get(loc)
            if not d:
                missing.append(f"{path} → 文档不存在：{loc}")
                continue
            anchor = (target.get("anchor") or "").strip()
            if anchor and anchor not in collect_anchors(d):
                broken.append(f"{path} → 文档 {loc} 里没有锚点 #{anchor}")
                continue
            resolved += 1
        else:
            missing.append(f"{path} → 无法识别的 target：{target}")

    # Rule C：complete 的公开条目必须至少挂载一次
    orphans: list[str] = []
    for eid, e in entry_index.items():
        if e.get("status") != "complete":
            continue
        if e.get("kind") != "entry":
            continue
        loc = str(e.get("location") or "")
        if loc.startswith("meta/"):
            continue          # meta/ 不属于 Handbook 正文
        if eid not in canonical_of:
            orphans.append(f"{eid}（{e.get('title')} · {loc}）")

    # Rule D：同一条目被挂载多次
    duplicates = {eid: paths for eid, paths in canonical_of.items() if len(paths) > 1}

    return {
        "canonical_ia_nodes": total,
        "resolved_nodes": resolved,
        "missing_nodes": len(missing),
        "broken_targets": len(broken),
        "orphan_public_entries": len(orphans),
        "duplicate_canonical_mappings": len(duplicates),
        "details": {
            "missing": missing,
            "broken": broken,
            "orphans": orphans,
            "duplicates": duplicates,
            "validate_errors": errors,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="检查 Canonical IA 与正文的一致性")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not NAV_PATH.is_file():
        print("meta/navigation.json 不存在", file=sys.stderr)
        return 1

    r = check()
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(f"Canonical IA nodes: {r['canonical_ia_nodes']}")
        print(f"Resolved nodes: {r['resolved_nodes']}")
        print(f"Missing nodes: {r['missing_nodes']}")
        print(f"Broken targets: {r['broken_targets']}")
        print(f"Orphan public entries: {r['orphan_public_entries']}")
        print(f"Duplicate canonical mappings: {r['duplicate_canonical_mappings']}")
        for key, label in (("missing", "MISSING NODE"), ("broken", "BROKEN TARGET"),
                           ("orphans", "ORPHAN ENTRY"), ("validate_errors", "VALIDATE ERROR")):
            for line in r["details"][key][:30]:
                print(f"  {label}: {line}")
        for eid, paths in list(r["details"]["duplicates"].items())[:20]:
            print(f"  DUPLICATE: {eid}")
            for p in paths:
                print(f"      - {p}")

    ok = (r["missing_nodes"] == 0 and r["broken_targets"] == 0
          and r["orphan_public_entries"] == 0 and r["duplicate_canonical_mappings"] == 0)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
