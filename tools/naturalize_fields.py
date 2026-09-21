#!/usr/bin/env python3
"""把旧模板字段（一句话/适合谁/能换回什么……）转换为自然文章结构。

原则：**保留全部原有内容**，只删除模板壳、按判断流程重新组织段落：

  一句话            → 文章开头段（去掉标签）
  适合谁            → ## 什么情况下值得考虑
  不太适合谁        → ## 什么情况下应该谨慎
  能换回什么        → ## 能换来什么、要付出什么
  要付出什么          （两段合一，先收益后代价）
  怎么开始          → ## 怎么开始
  常见误区          → ## 容易踩的坑
  下一步可能打开什么 → ## 接下来可以看什么
  证据与来源        → ## 来源与更新（与最后核实合并）

转换后的条目会在报告中列出，供人工复核与进一步改写。

    python3 tools/naturalize_fields.py          # 预览
    python3 tools/naturalize_fields.py --write  # 写盘
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

FIELDS = ["一句话", "适合谁", "不太适合谁", "能换回什么", "要付出什么",
          "怎么开始", "常见误区", "下一步可能打开什么", "证据与来源", "最后核实"]

SECTION_OF = {
    "适合谁": "什么情况下值得考虑",
    "不太适合谁": "什么情况下应该谨慎",
    "能换回什么": "能换来什么、要付出什么",
    "要付出什么": None,          # 并入上一节
    "怎么开始": "怎么开始",
    "常见误区": "容易踩的坑",
    "下一步可能打开什么": "接下来可以看什么",
    "证据与来源": "SOURCE",
    "最后核实": "SOURCE",
}


def split_fields(block: str):
    """把条目正文切成 [(字段名, 字段文本)]；返回 (开头正文, 字段列表)。"""
    lines = block.splitlines(keepends=True)
    intro, fields = [], []
    cur_name, cur_lines = None, []
    for ln in lines:
        m = re.match(r"^-\s*(" + "|".join(FIELDS) + r")[:：]\s*(.*)$", ln)
        if m:
            if cur_name:
                fields.append((cur_name, cur_lines))
            cur_name, cur_lines = m.group(1), [m.group(2) + "\n"] if m.group(2).strip() else []
        elif cur_name is not None:
            if ln.strip() == "" :
                cur_lines.append(ln)
            elif ln.startswith(("-", " ", "\t", "1.", "2.", "3.", "4.", "5.", "6.", "7.")):
                cur_lines.append(ln)
            else:
                fields.append((cur_name, cur_lines))
                cur_name, cur_lines = None, [ln]
        else:
            intro.append(ln)
    if cur_name:
        fields.append((cur_name, cur_lines))
    return intro, fields


def clean_field_text(lines: list[str]) -> str:
    """去掉段尾多余空行，保留内部列表结构。"""
    out = [ln.rstrip() for ln in lines]
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return "\n".join(out)


def convert(block: str) -> str | None:
    lines = block.splitlines(keepends=True)
    if not lines or not lines[0].startswith("### "):
        return None
    title_line, rest = lines[0], lines[1:]
    body = "".join(rest)
    intro, fields = split_fields(body)
    names = {n for n, _ in fields}
    if not any(n in ("一句话", "适合谁") for n in names):
        return None                      # 不是旧模板

    # 开头：去掉「一句话：」标签后的正文作为引入段
    lead = ""
    for n, ls in fields:
        if n == "一句话":
            lead = clean_field_text(ls)
            break
    out = [title_line, "\n"]
    if lead:
        out += [lead, "\n\n"]
    out += [clean_field_text(intro).strip() + "\n\n"] if clean_field_text(intro).strip() else []

    for name in ("适合谁", "不太适合谁", "能换回什么", "要付出什么",
                 "怎么开始", "常见误区", "下一步可能打开什么"):
        sec = SECTION_OF.get(name)
        if sec is None or sec == "SOURCE":
            continue
        ls = next((l for n, l in fields if n == name), None)
        if ls is None:
            continue
        out.append(f"## {sec}\n\n{clean_field_text(ls)}\n\n")

    # 来源与更新
    src = []
    for n in ("证据与来源", "最后核实"):
        ls = next((l for n2, l in fields if n2 == n), None)
        if ls:
            src.append(clean_field_text(ls))
    if src:
        out.append("## 来源与更新\n\n" + "\n\n".join(src) + "\n")

    t = "".join(out)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t + ("" if t.endswith("\n") else "\n")


def spans(lines):
    starts = [i for i, l in enumerate(lines) if l.startswith("### ")]
    out = []
    for k, s in enumerate(starts):
        e = starts[k + 1] if k + 1 < len(starts) else len(lines)
        for j in range(s + 1, e):
            if re.match(r"^## (?!来源与更新)", lines[j]):
                e = j
                break
        while e - 1 > s and not lines[e - 1].strip():
            e -= 1
        out.append((s, e))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    total = 0
    for path in sorted((ROOT / "book").glob("*.md")):
        if path.stem == "README":
            continue
        raw = path.read_text(encoding="utf-8")
        fm = re.match(r"^---\n.*?\n---\n", raw, re.S)
        head = fm.group(0) if fm else ""
        body = raw[len(head):]
        lines = body.splitlines(keepends=True)
        changed = 0
        for s, e in spans(lines):
            blk = "".join(lines[s:e])
            new = convert(blk)
            if new and new != blk:
                lines[s:e] = [new]
                changed += 1
        if changed and args.write:
            path.write_text(head + "".join(lines), encoding="utf-8")
        total += changed
        if changed:
            print(f"{path.name}: 转换 {changed} 篇")
    print(f"合计 {total} 篇" + ("（已写盘）" if args.write else "（预览，--write 生效）"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
