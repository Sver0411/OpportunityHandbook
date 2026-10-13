#!/usr/bin/env python3
"""把分册文件里的一个 `## 分组` 拆成独立分册，恢复「一个分组 = 一个文件 = 一个导航分组」。

    python3 tools/split_inner_group.py "book/07-晋升、跳槽还是转行/05-转行.md" "职业中段与年龄"

背景：章节按分组拆分后，约定是每个 `## 分组` 对应一个分册文件。后来往分册里直接
追加新的 `## 分组` 会破坏这条对应关系——导航里的分组名与它指向的页面标题不一致，
同一个页面还会被两个分组指向。这个工具把这种内部小组提成独立分册。

做三件事：
  1. 把该分组（标题 + 其下条目）整体搬到一个新文件 `NN-<组名>.md`；
  2. 原文件里删掉这一段，其余内容保持不变；
  3. 全库重写指向被搬走条目的链接（按条目 id 定位新位置、重算相对路径）。

只搬条目，不改正文内容。
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from meta import slugify  # noqa: E402

FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")


def fm_get(fm: str, key: str) -> str:
    m = re.search(rf"^{key}:\s*(.*)$", fm, re.M)
    return m.group(1).strip() if m else ""


def next_index(directory: Path) -> int:
    used = []
    for p in directory.glob("*.md"):
        m = re.match(r"^(\d\d)-", p.name)
        if m:
            used.append(int(m.group(1)))
    return (max(used) + 1) if used else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("parent", help="分册文件（仓库相对路径）")
    ap.add_argument("group", help="要拆出的二级分组标题")
    args = ap.parse_args()

    parent = (ROOT / args.parent).resolve()
    text = parent.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        raise SystemExit("父文件没有 front matter")
    fm, body = m.group(0), text[m.end():]
    lines = body.split("\n")

    # 找目标分组：## 标题，且下一个非空行是 ### 或 ##
    start = None
    for i, l in enumerate(lines):
        if l.strip() == f"## {args.group}":
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and (lines[j].startswith("### ") or lines[j].startswith("## ")):
                start = i
                break
    if start is None:
        raise SystemExit(f"在 {args.parent} 里找不到分组「{args.group}」")

    end = len(lines)
    for k in range(start + 1, len(lines)):
        if lines[k].startswith("## "):
            j = k + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and (lines[j].startswith("### ") or lines[j].startswith("## ")):
                end = k
                break

    group_lines = lines[start + 1 : end]
    moved_ids = re.findall(r"^id:\s*(\S+)\s*$", "\n".join(group_lines), re.M)
    if not moved_ids:
        raise SystemExit("该分组下没有条目（找不到 ```meta 里的 id）")

    parent_lines = lines[:start] + lines[end:]
    parent.write_text(fm + "\n".join(parent_lines).rstrip("\n") + "\n", encoding="utf-8")

    directory = parent.parent
    idx = next_index(directory)
    target = directory / f"{idx:02d}-{args.group}.md"
    head = [
        "---",
        f"id: {fm_get(fm, 'id')}-{idx:02d}",
        f"title: {args.group}",
        "type: chapter",
        f"section: {fm_get(fm, 'section')}",
        f"section_order: {fm_get(fm, 'section_order')}",
        "status: complete",
    ]
    for key in ("topics", "stages"):
        if fm_get(fm, key):
            head.append(f"{key}: {fm_get(fm, key)}")
    head.append(f"summary: {fm_get(fm, 'title')} · {args.group}。")
    head.append(f"last_verified: {fm_get(fm, 'last_verified')}")
    head += ["---", f"# {args.group}", ""]
    target.write_text("\n".join(head) + "\n" + "\n".join(group_lines).strip("\n") + "\n", encoding="utf-8")

    # 全库重写链接：父文件 + 所有 book/docs/meta + 根 README
    files: list[Path] = []
    for d in ("book", "docs", "meta"):
        files.extend(sorted((ROOT / d).rglob("*.md")))
    files += [ROOT / f for f in ("README.md", "README.en.md", "CONTRIBUTING.md") if (ROOT / f).exists()]

    entry_map = {eid: target for eid in moved_ids}
    changed = 0
    for f in files:
        txt = f.read_text(encoding="utf-8")
        hits = 0

        def repl(mm: re.Match) -> str:
            nonlocal hits
            href = mm.group(1)
            if href.startswith(("http://", "https://", "mailto:", "#")):
                return mm.group(0)
            tgt, _sep, anchor = href.partition("#")
            if not tgt or not anchor or anchor not in entry_map:
                return mm.group(0)
            abs_tgt = (f.parent / tgt)
            try:
                abs_tgt = abs_tgt.resolve()
            except OSError:
                return mm.group(0)
            if abs_tgt != parent:
                return mm.group(0)
            new_rel = Path(os.path.relpath(entry_map[anchor], f.parent)).as_posix()
            hits += 1
            return f"]({new_rel}#{anchor})"

        new_txt = LINK_RE.sub(repl, txt)
        if new_txt != txt:
            f.write_text(new_txt, encoding="utf-8")
        if hits:
            changed += 1

    print(f"拆出 {target.relative_to(ROOT)}（{len(moved_ids)} 条：{', '.join(moved_ids)}）")
    print(f"  重写 {changed} 个文件的链接")
    print(f"  导航节点请补：  {args.group} @d:{target.relative_to(ROOT).as_posix()[:-3]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
