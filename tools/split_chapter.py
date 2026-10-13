#!/usr/bin/env python3
"""把一个过长的章节 md 按「## 分组」拆成多个分册文件，内容一条不删。

    python3 tools/split_chapter.py book/04-升学、就业还是出国.md --dry-run
    python3 tools/split_chapter.py book/04-升学、就业还是出国.md

做什么：
  1. 解析章节 front matter 与正文；
  2. 以「下一个非空行是 ### 或 ##」判定真正的分组标题（与写作规范一致），
     把每个分组写成 book/<章节名>/NN-<分组名>.md（分组标题升级为该文件的 H1）；
  3. 原文件保留为「章节导读页」：front matter + 原有开篇 + 一张分册目录表；
  4. 全仓库重写指向被搬运条目的链接（按条目 id 找到它现在所在的分册）。

设计约束：
  - 条目 id 不变 → 左栏导航、站内锚点、搜索都按 id 走，自动跟随；
  - 原路径仍然存在（导读页）→ 指向章节本身的链接与旧 hash 深链不失效；
  - 幂等：已拆过的章节再跑一次会拒绝执行（目录已存在）。
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

SCAN_ROOTS = ["book", "docs", "meta"]
SCAN_FILES = ["README.md", "README.en.md", "CONTRIBUTING.md"]

LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
META_BLOCK_RE = re.compile(r"```meta\n(.*?)\n```", re.S)


def read_fm(text: str) -> tuple[str, str]:
    """返回 (front matter 原文含 ---, 正文)。"""
    m = FM_RE.match(text)
    if not m:
        raise SystemExit("文件没有 front matter")
    return m.group(0), text[m.end():]


def fm_get(fm_text: str, key: str) -> str:
    m = re.search(rf"^{key}:\s*(.*)$", fm_text, re.M)
    return m.group(1).strip() if m else ""


def safe_component(name: str) -> str:
    bad = '\\/:*?"<>|'
    out = "".join("" if c in bad else c for c in name).strip()
    return out.replace(" ", "")


def split_segments(body_lines: list[str]) -> tuple[list[str], list[tuple[str, list[str]]]]:
    """按分组标题切分：返回 (开篇行, [(分组名, 行列表)])。"""
    marks: list[tuple[int, str]] = []
    for i, line in enumerate(body_lines):
        if line.startswith("## "):
            j = i + 1
            while j < len(body_lines) and not body_lines[j].strip():
                j += 1
            nxt = body_lines[j] if j < len(body_lines) else ""
            if nxt.startswith("### ") or nxt.startswith("## "):
                marks.append((i, line[3:].strip()))
    if not marks:
        raise SystemExit("没有找到任何分组标题，无法拆分")
    intro = body_lines[: marks[0][0]]
    groups: list[tuple[str, list[str]]] = []
    for k, (start, name) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else len(body_lines)
        groups.append((name, body_lines[start + 1 : end]))
    return intro, groups


def entry_ids(lines: list[str]) -> list[tuple[str, str]]:
    """返回该段里的 (entry_id, 条目标题)。meta 块紧跟 ### 标题，因此按标题归属即可。"""
    out: list[tuple[str, str]] = []
    cur_title = ""
    for line in lines:
        if line.startswith("### "):
            cur_title = line[4:].strip()
        m = re.match(r"id:\s*(\S+)\s*$", line)
        if m and cur_title:
            out.append((m.group(1), cur_title))
            cur_title = ""
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("chapter", help="要拆分的章节 md（仓库相对路径）")
    ap.add_argument("--dry-run", action="store_true", help="只打印计划，不写文件")
    args = ap.parse_args()

    src = (ROOT / args.chapter).resolve()
    if not src.exists():
        raise SystemExit(f"找不到 {args.chapter}")
    rel = src.relative_to(ROOT).as_posix()
    fm_text, body = read_fm(src.read_text(encoding="utf-8"))
    body_lines = body.split("\n")
    # 去掉开篇里已有的 H1（它会成为分册之外的东西，保留在导读页）
    intro, groups = split_segments(body_lines)

    dir_name = safe_component(src.stem)
    out_dir = src.parent / dir_name
    if out_dir.exists():
        raise SystemExit(f"{out_dir.relative_to(ROOT)} 已存在，章节可能已拆分过")

    chapter_id = fm_get(fm_text, "id")
    section = fm_get(fm_text, "section")
    section_order = fm_get(fm_text, "section_order")
    chapter_title = fm_get(fm_text, "title")
    last_verified = fm_get(fm_text, "last_verified")
    topics = fm_get(fm_text, "topics")
    stages = fm_get(fm_text, "stages")

    entry_map: dict[str, Path] = {}
    plan: list[tuple[str, Path, list[str], list[tuple[str, str]]]] = []
    for idx, (name, lines) in enumerate(groups, 1):
        fname = f"{idx:02d}-{safe_component(name)}.md"
        target = out_dir / fname
        ids = entry_ids(lines)
        for eid, _t in ids:
            entry_map[eid] = target
        plan.append((name, target, lines, ids))

    print(f"章节：{rel}")
    print(f"分册目录：{out_dir.relative_to(ROOT)}/")
    for name, target, lines, ids in plan:
        print(f"  {target.name:28s} {len(lines):5d} 行  {len(ids):2d} 条  {name}")
    print(f"共 {len(entry_map)} 个条目将移动位置")

    unassigned = [ln for ln in intro if ln.startswith("### ")]
    if unassigned:
        print(f"注意：开篇里有 {len(unassigned)} 个顶层条目标题（不会被搬走）")

    if args.dry_run:
        return 0

    out_dir.mkdir(parents=True)
    for idx, (name, target, lines, ids) in enumerate(plan, 1):
        head = [
            "---",
            f"id: {chapter_id}-{idx:02d}",
            f"title: {name}",
            "type: chapter",
            f"section: {section}",
            f"section_order: {section_order}",
            "status: complete",
        ]
        if topics:
            head.append(f"topics: {topics}")
        if stages:
            head.append(f"stages: {stages}")
        head.append(f"summary: {chapter_title} · {name}。")
        head.append(f"last_verified: {last_verified}")
        head += ["---", f"# {name}", ""]
        body_text = "\n".join(lines).strip("\n")
        target.write_text("\n".join(head) + "\n" + body_text + "\n", encoding="utf-8")

    # 导读页：front matter + 开篇 + 分册目录表
    rows = ["| 分册 | 这一组回答什么 |", "| --- | --- |"]
    for idx, (name, target, lines, ids) in enumerate(plan, 1):
        sub_rel = target.relative_to(src.parent).as_posix()
        preview = "、".join(t for _i, t in ids[:3])
        if len(ids) > 3:
            preview += " 等"
        rows.append(f"| [{name}]({sub_rel}) | {len(ids)} 条：{preview} |")
    landing_intro = "\n".join(intro).rstrip("\n")
    landing = (
        fm_text
        + landing_intro
        + "\n\n## 本部分册\n\n"
        + "章节太长，按内容分成下面几册，条目编号与搜索不受影响。\n\n"
        + "\n".join(rows)
        + "\n"
    )
    src.write_text(landing, encoding="utf-8")

    # ---- 全库重写链接 ----
    files: list[Path] = []
    for d in SCAN_ROOTS:
        base = ROOT / d
        if base.is_dir():
            files.extend(sorted(base.rglob("*.md")))
    files.extend(ROOT / f for f in SCAN_FILES if (ROOT / f).exists())

    # 分组标题的锚点（站点按 slugify(分组名) 生成）→ 现在住在哪个分册
    group_slug_map: dict[str, Path] = {}
    for name, target, _lines, _ids in plan:
        group_slug_map[slugify(name)] = target

    def rebase(f: Path, text: str, old_base: Path) -> tuple[str, int, list[str]]:
        """把以 old_base 为基准写的相对链接，改写成以 f.parent 为基准。

        同时把指向被搬运条目的链接改到它现在所在的分册。
        """
        hits = 0
        missed: list[str] = []

        def repl(m: re.Match) -> str:
            nonlocal hits
            href = m.group(1)
            if href.startswith(("http://", "https://", "mailto:", "#")):
                return m.group(0)
            target, _sep, anchor = href.partition("#")
            if not target:
                return m.group(0)
            abs_target = (old_base / target)
            try:
                abs_target = abs_target.resolve()
            except OSError:
                return m.group(0)

            dest: Path | None = None
            if abs_target == src:
                if anchor and anchor in entry_map:
                    dest = entry_map[anchor]
                elif anchor and anchor in group_slug_map:
                    dest = group_slug_map[anchor]
                elif not anchor:
                    dest = src  # 指向章节本身 → 导读页
                else:
                    missed.append(f"{f.relative_to(ROOT)}: {href}")
                    return m.group(0)
            elif abs_target.exists():
                dest = abs_target
            else:
                missed.append(f"{f.relative_to(ROOT)}: {href}")
                return m.group(0)

            new_rel = Path(os.path.relpath(dest, f.parent)).as_posix()
            new_href = new_rel + (("#" + anchor) if anchor else "")
            if new_href != href:
                hits += 1
            return "](%s)" % new_href

        return LINK_RE.sub(repl, text), hits, missed

    changed = 0
    all_missed: list[str] = []
    for f in files:
        # 新建的分册：原有链接是以原章节所在目录为基准写的，需要整体重新定位
        old_base = src.parent if out_dir in f.parents else f.parent
        if f == src and old_base == f.parent:
            # 导读页自己也可能链接到被搬走的条目，同样需要改；基准还是它自己所在目录
            pass
        text = f.read_text(encoding="utf-8")
        new_text, hits, missed = rebase(f, text, old_base)
        all_missed.extend(missed)
        if new_text != text:
            f.write_text(new_text, encoding="utf-8")
        if hits:
            changed += 1
            print(f"  重写 {f.relative_to(ROOT)}：{hits} 处")

    print(f"共重写 {changed} 个文件")
    if all_missed:
        print("以下链接未处理，需要人工确认：")
        for u in sorted(set(all_missed)):
            print("   ?", u)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
