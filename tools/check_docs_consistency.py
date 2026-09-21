#!/usr/bin/env python3
"""文档一致性检查：防止公开规范/README 退回旧正文模型。

    python3 tools/check_docs_consistency.py

检查对象（公开维护规范与入口文档）：
  README.md、CONTRIBUTING.md、book/README.md、docs/README.md、meta/*.md

已知废弃短语一旦出现即 FAIL：
  - 每个条目都是同一套字段 / 同一套字段
  - 十个固定字段 / 十个字段 / 固定字段的正文
  - 「一句话 · 适合谁」式的固定字段串
  - 旧章节引用（第 02 章 / 第 11 章 等被重构掉的编号说法）
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

TARGETS = ["README.md", "CONTRIBUTING.md", "book/README.md", "docs/README.md"]
TARGETS += sorted(str(p.relative_to(ROOT)) for p in (ROOT / "meta").glob("*.md"))
TARGETS += sorted(str(p.relative_to(ROOT)) for p in (ROOT / "docs").rglob("*.md"))

FORBIDDEN = [
    ("同一套字段", "旧正文模型：已改为按问题自然组织"),
    ("十个固定字段", "旧正文模型：字段制已废弃"),
    ("十个字段", "旧正文模型：字段制已废弃"),
    ("固定字段的正文", "旧正文模型：正文不要求固定栏目"),
    ("一句话 · 适合谁", "旧正文模型：固定字段串"),
    ("一句话：", "旧正文模型：字段标签"),
    ("- 适合谁：", "旧正文模型：字段标签"),
    ("- 能换回什么：", "旧正文模型：字段标签"),
    ("第 02 章", "旧章节编号：已改为当前 Canonical IA 位置"),
    ("第 11 章", "旧章节编号：已改为当前 Canonical IA 位置"),
    ("第二章", "旧章节编号：已改为具体条目链接"),
    ("第三章", "旧章节编号：已改为具体条目链接"),
    ("第四章", "旧章节编号：已改为具体条目链接"),
    ("第五章", "旧章节编号：已改为具体条目链接"),
    ("第六章", "旧章节编号：已改为具体条目链接"),
    ("第七章", "旧章节编号：已改为具体条目链接"),
    ("第八章", "旧章节编号：已改为具体条目链接"),
    ("第十一章", "旧章节编号：已改为具体条目链接"),
]

# 「不太适合谁」类表述允许出现在正文里，但规范文档中不得作为固定栏目要求
SOFT = [
    ("必须写清“不太适合谁”", "不再要求固定栏目名"),
]


def main() -> int:
    problems: list[str] = []
    for rel in TARGETS:
        p = ROOT / rel
        if not p.exists():
            problems.append(f"缺少文件：{rel}")
            continue
        text = p.read_text(encoding="utf-8")
        for phrase, why in FORBIDDEN:
            if phrase in text:
                line = text[: text.find(phrase)].count("\n") + 1
                problems.append(f"{rel}:{line} 出现废弃表述「{phrase}」（{why}）")
        for phrase, why in SOFT:
            if phrase in text:
                line = text[: text.find(phrase)].count("\n") + 1
                problems.append(f"{rel}:{line} 仍把「{phrase}」当作必填要求（{why}）")

    if problems:
        for x in problems:
            print("  x", x)
        print(f"文档一致性问题：{len(problems)}")
        return 1
    print(f"文档一致性：PASS（检查 {len(TARGETS)} 个文件）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
