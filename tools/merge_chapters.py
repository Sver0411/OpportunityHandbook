#!/usr/bin/env python3
"""把已拆分的章节合回一个大文件：二级纵览 + 各分组连续可读。

    python3 tools/merge_chapters.py --dry-run
    python3 tools/merge_chapters.py --only 09
    python3 tools/merge_chapters.py

为什么按「IA 分组顺序」而不是文件名编号合并：
  文件名里的 NN 只是拆分时的序号，与左栏顺序无关（01 章是 01/05/02/03/06/
  04/07/08/09/15）。按文件名拼会得到「上一页下一页左右横跳」的乱序，这正是
  读者反馈「滑动顺序是乱的、左栏一会上一会下」的根因。这里一律按
  tools/ia_canonical.py 的分组顺序落盘。

分组与分册的对应关系用**条目 id**判定，不用名字：改名、改标题都不会错配。

做什么：
  1. 章文件保留 front matter、`# 章名`、`> 导读`；
  2. 原「## 本部分册」表改成「## 本章分组」锚点表；
  3. 每个分册去掉 front matter，`# 分组名` 降为 `## 分组名`，正文原样追加；
  4. 条目 id 不变（左栏、搜索、旧深链按 id 走，自动跟随）；
  5. 删除分册目录与分册文件，全库重写链接，旧路径写进重定向表。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import ia_canonical  # noqa: E402
from meta import slugify  # noqa: E402

FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
ENTRY_RE = re.compile(r"(?m)^### [^\n]+\n\n```meta\n(.*?)\n```", re.S)
META_ID_RE = re.compile(r"(?m)^id:\s*(\S+)\s*$")
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
SCAN_ROOTS = ["book", "docs", "meta", "reader"]
SCAN_FILES = ["README.md", "README.en.md", "CONTRIBUTING.md"]


def rebase_links(text: str, sub_dir: Path, chapter_file: Path, sub_names: set[str]) -> str:
    """分册比章文件深一层，合并后所有相对链接都要重新算一遍。

    同章分册之间原来写的是 `02-国内升学.md#xxx` 或 `../04-x/02-国内升学.md`
    —— 合并后它们就在同一个文件里，直接变成 `#xxx`。
    """
    chapter_dir = chapter_file.parent

    def fix(m: re.Match) -> str:
        target = m.group(1)
        if "://" in target or target.startswith("#"):
            return m.group(0)
        path, sep, anchor = target.partition("#")
        if not path:
            return m.group(0)
        resolved = (sub_dir / path).resolve()
        if resolved == chapter_file.resolve() or any(
                resolved == (sub_dir / name).resolve() for name in sub_names):
            return "](" + ("#" + anchor if anchor else chapter_file.name) + ")"
        return "](" + os.path.relpath(resolved, chapter_dir) + sep + anchor + ")"

    return LINK_RE.sub(fix, text)


def read_fm(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        raise SystemExit(f"{path} 没有 front matter")
    return m.group(0), text[m.end():]


def fm_get(fm: str, key: str) -> str:
    m = re.search(rf"^{key}:\s*(.*)$", fm, re.M)
    return m.group(1).strip() if m else ""


def entry_ids(text: str) -> list[str]:
    """条目 id：`### 标题` 后面紧跟的 meta 块里的 id。"""
    out = []
    for block in ENTRY_RE.findall(text):
        m = META_ID_RE.search(block)
        if m:
            out.append(m.group(1))
    return out


def ia_plan(chapter_title: str) -> list[tuple[str, list[str]]]:
    """从 Canonical IA 取 [(分组名, 该组条目 id)]，顺序即左栏顺序。"""
    out: list[tuple[str, list[str]]] = []
    cur: list[str] | None = None
    in_chapter = False
    for line in ia_canonical.TREE.splitlines():
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        raw = line.strip()
        name, _, target = raw.partition(" @")
        eid = target.split(":", 1)[-1] if ":" in target else ""
        if indent == 0:
            in_chapter = (name.split(" ", 1)[-1] == chapter_title)
            cur = None
        elif indent == 2 and in_chapter:
            cur = []
            out.append((name, cur))
        elif indent >= 4 and cur is not None and eid:
            cur.append(eid)
    return out


def split_head(body: str) -> tuple[str, list[tuple[str, str]]]:
    blocks = re.split(r"(?m)^(## .+)$", body)
    head = blocks[0].rstrip("\n")
    rest: list[tuple[str, str]] = []
    for i in range(1, len(blocks), 2):
        rest.append((blocks[i][3:].strip(), blocks[i + 1].strip("\n")))
    return head, rest


def table_rows(section: str) -> list[list[str]]:
    rows = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|") or set(line) <= set("| -"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 2:
            rows.append(cells)
    return rows


def discover(only: str) -> list[Path]:
    out = []
    for path in sorted((ROOT / "book").glob("[0-9][0-9]-*.md")):
        if not (ROOT / "book" / path.stem).is_dir():
            continue
        if only and not path.name.startswith(only):
            continue
        out.append(path)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="只处理指定章号，例如 09")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    chapters = discover(args.only)
    if not chapters:
        raise SystemExit("没有找到需要合并的章节（可能已经合并过了）")

    plans = []
    for chapter in chapters:
        fm, body = read_fm(chapter)
        title = fm_get(fm, "title")
        head, rest = split_head(body)

        sub_dir = ROOT / "book" / chapter.stem
        subs = {}
        for sub in sorted(sub_dir.glob("*.md")):
            sfm, sbody = read_fm(sub)
            subs[sub] = (fm_get(sfm, "title"), sbody)

        owner = {}
        for sub, (_t, sbody) in subs.items():
            for eid in entry_ids(sbody):
                owner[eid] = sub

        order = []
        for group, ids in ia_plan(title):
            hits = [owner[i] for i in ids if i in owner]
            if not hits:
                raise SystemExit(f"{chapter.name}: 分组「{group}」找不到对应分册")
            sub = Counter(hits).most_common(1)[0][0]
            order.append((group, sub))
        used = [s for _g, s in order]
        if len(set(used)) != len(used):
            raise SystemExit(f"{chapter.name}: 同一个分册被分给多个分组")
        if set(used) != set(subs):
            raise SystemExit(f"{chapter.name}: 有分册没被 IA 覆盖："
                             f"{sorted(p.name for p in set(subs) - set(used))}")

        desc = {}
        for name, section in rest:
            if name == "本部分册":
                for cells in table_rows(section):
                    label = re.sub(r"^\[(.+)\]\(.+\)$", r"\1", cells[0])
                    desc[label] = cells[1] if len(cells) > 1 else ""

        keep_tail = [s for n, s in rest if n in ("相关", "来源与更新")]
        keep_mid = [s for n, s in rest if n not in ("本部分册", "相关", "来源与更新")]

        parts = [head, ""]
        rows = ["## 本章分组", "", "| 分组 | 这一组回答什么 |", "| --- | --- |"]
        for group, sub in order:
            n = len(entry_ids(subs[sub][1]))
            rows.append(f"| [{group}](#{slugify(group)}) | {desc.get(group) or f'{n} 条'} |")
        parts.append("\n".join(rows))
        parts.extend(keep_mid)

        moved: list[tuple[str, str]] = []
        sub_names = {p.name for p in subs}
        for group, sub in order:
            sbody = rebase_links(subs[sub][1], sub_dir, chapter, sub_names)
            moved.extend((sub.stem, eid) for eid in entry_ids(sbody))
            lines = sbody.strip("\n").split("\n")
            if not lines[0].startswith("# "):
                raise SystemExit(f"{sub.name}: 分册正文不是以 H1 开头")
            lines[0] = "## " + lines[0][2:].strip()
            parts.append("\n".join(lines))
        parts.extend(keep_tail)

        new_body = "\n\n".join(p.strip("\n") for p in parts) + "\n"
        plans.append({"chapter": chapter, "fm": fm, "body": new_body,
                      "subs": list(subs), "dir": sub_dir, "moved": moved})
        print(f"{chapter.name}: {len(order)} 组 · {len(new_body.splitlines())} 行 · "
              f"{len(moved)} 条 · {'／'.join(g for g, _ in order[:3])}…")

    if args.dry_run:
        print("\n（dry-run，未写盘）")
        return 0

    # ---- 写章文件、删分册目录 ----
    for plan in plans:
        assert plan["dir"] != plan["chapter"], "目录与章文件同名，拒绝删除"
        plan["chapter"].write_text(plan["fm"] + plan["body"], encoding="utf-8")
        shutil.rmtree(plan["dir"])

    # ---- 全库md 链接重写 ----
    files: list[Path] = []
    for d in SCAN_ROOTS:
        base = ROOT / d
        if base.is_dir():
            files.extend(sorted(base.rglob("*.md")))
    files.extend(ROOT / f for f in SCAN_FILES if (ROOT / f).exists())

    changed = 0
    for f in files:
        text = original = f.read_text(encoding="utf-8")
        for plan in plans:
            stem = plan["chapter"].stem
            for sub in plan["subs"]:
                text = text.replace(f"{stem}/{sub.name}", f"{stem}.md")
                text = text.replace(f"#/doc/book/{stem}/{sub.stem}", f"#/doc/book/{stem}")
        if text != original:
            f.write_text(text, encoding="utf-8")
            changed += 1
    print(f"链接重写：{changed} 个文件")

    # ---- Canonical IA 的 @d: 目标 ----
    ia_path = ROOT / "tools" / "ia_canonical.py"
    text = ia_path.read_text(encoding="utf-8")
    for plan in plans:
        stem = plan["chapter"].stem
        for sub in plan["subs"]:
            text = text.replace(f"@d:book/{stem}/{sub.stem}", f"@d:book/{stem}")
    ia_path.write_text(text, encoding="utf-8")

    # ---- 重定向表：旧分册路径 -> 章文件（location 级 + 条目级） ----
    red_path = ROOT / "meta" / "ia-redirects.json"
    red = json.loads(red_path.read_text(encoding="utf-8"))
    added = 0
    for plan in plans:
        stem = plan["chapter"].stem
        for sub in plan["subs"]:
            key = f"book/{stem}/{sub.stem}"
            if red["docs"].get(key) != f"book/{stem}":
                red["docs"][key] = f"book/{stem}"
                added += 1
        for sub_stem, eid in plan["moved"]:
            old = f"#/doc/book/{stem}/{sub_stem}/{eid}"
            new = f"#/doc/book/{stem}/{eid}"
            if red["entries"].get(old) != new:
                red["entries"][old] = new
                added += 1
    red_path.write_text(json.dumps(red, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"重定向表：新增/更新 {added} 条（docs {len(red['docs'])} · entries {len(red['entries'])}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
