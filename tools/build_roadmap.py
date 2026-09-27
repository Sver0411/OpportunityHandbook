#!/usr/bin/env python3
"""根据 metadata 自动生成 docs/ROADMAP.md（内容路线图）。

    python3 tools/build_roadmap.py           # 重新生成
    python3 tools/build_roadmap.py --check    # 只校验是否与当前状态一致（CI 用）

路线图完全由「文件里的 status」推导，不再手工维护，避免页面已完成而清单仍写着 planned。
"""

from __future__ import annotations

import argparse
import datetime
import re
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import meta as M  # noqa: E402

OUT = ROOT / "docs" / "ROADMAP.md"
FRONT = """---
nav: false
id: docs-roadmap
title: 内容路线图
type: doc
section: index
order: 3
status: complete
summary: 由文件里的 status 自动生成的内容路线图：哪些专题与条目还没写、哪些已经完成。
last_verified: {date}
---
"""


def build() -> str:
    docs = M.load_docs(ROOT)
    errors, warnings, extra = M.validate(ROOT, docs)

    pending_docs: dict[str, list[tuple[str, str]]] = {}
    done_docs = 0
    for d in docs:
        if d.front.get("nav") is False or str(d.front.get("type") or "") in ("chapter", "intro"):
            continue
        if d.status in ("planned", "todo"):
            key = str(d.front.get("subsection") or d.front.get("section") or "未分组")
            pending_docs.setdefault(key, []).append((str(d.front.get("title") or ""), d.rel))
        elif d.status in ("complete", "partial"):
            done_docs += 1

    pending_entries: dict[str, list[tuple[str, str]]] = {}
    done_entries = 0
    for e in extra.get("entries", []):
        if e.get("kind") == "question":
            continue
        status = str(e.get("status") or "")
        if status in ("complete", "partial"):
            done_entries += 1
            continue
        sec = str(e.get("section") or "未分组")
        pending_entries.setdefault(sec, []).append((str(e.get("title") or ""), str(e.get("id") or "")))

    lines = [FRONT.format(date=datetime.date.today().isoformat()).rstrip(), "",
             "# 内容路线图", "",
             "这份清单**由每个文件 front matter / meta 块里的 `status` 自动生成**，不需要手工维护："
             "页面写完并把 `status` 改成 `complete` 之后，它会自动从下面消失。",
             "",
             "下面是尚未撰写正文的部分——它们不会出现在在线导航、搜索与筛选里，"
             "读者不会点进一个只有标题的空页面。",
             "",
             f"当前进度：**{done_docs}** 份专题文档已完成（其中部分为 `partial`），"
             f"**{done_entries}** 个条目已完成；仍有 **{sum(len(v) for v in pending_docs.values())}** 份专题文档、"
             f"**{sum(len(v) for v in pending_entries.values())}** 个条目在计划中。",
             "",
             "想认领其中一条：把对应文件里的 `status` 改成 `complete`，补上正文、`summary` 与 `last_verified`，"
             "构建会检查格式、链接与来源。路线图会在下次构建时自动更新。",
             ""]

    if pending_docs:
        lines += ["## 计划中的专题文档", ""]
        for key in sorted(pending_docs):
            lines += [f"### {key}", ""]
            for title, rel in sorted(pending_docs[key]):
                lines.append(f"- {title}（`{rel}`）")
            lines.append("")
    else:
        lines += ["## 计划中的专题文档", "", "目前没有待撰写的专题文档。", ""]

    if pending_entries:
        lines += ["## 计划中的条目", ""]
        for key in sorted(pending_entries):
            lines += [f"### {key}", ""]
            for title, eid in sorted(pending_entries[key]):
                lines.append(f"- {title}（`{eid}`）")
            lines.append("")
    else:
        lines += ["## 计划中的条目", "", "目前没有只规划未撰写的条目。", ""]

    lines += ["## 这份清单的可靠性", "",
              "它是自动生成的，因此不会出现「页面已经写完，清单还写着 planned」的偏差；"
              "如果发现不一致，说明构建没有重新运行。", "",
              "来源：仓库内文件的 `status` 字段。 （Experience-based）", ""]
    return "\n".join(lines)


def _normalize(text: str) -> str:
    """比较用：忽略 front matter 里的生成日期。"""
    return re.sub(r"^last_verified:.*$", "last_verified: <ignored>", text, flags=re.M).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只校验，不写入")
    args = ap.parse_args()
    text = build()
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.is_file() else ""
        # 只比较内容：last_verified 是生成日期，跨时区/跨天必然不同，
        # 把它纳入比较会让这个检查退化成"今天是否生成过"的日历判断。
        if _normalize(current) != _normalize(text):
            print("内容路线图与 metadata 不一致：运行 python3 tools/build_roadmap.py 重新生成")
            return 1
        print("内容路线图与 metadata 一致（忽略生成日期）")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print("已重新生成 docs/ROADMAP.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
