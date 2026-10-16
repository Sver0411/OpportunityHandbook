# -*- coding: utf-8 -*-
"""构建产物锚点可达性检查。

背景：正文里用 `[文字](#锚点)` 形式的站内跳转，构建后原样写进 href。
前端（site/app.js）只在同页存在该 id 时才接管点击；找不到时浏览器改写 hash，
触发路由兜底分支，读者被带到「找不到这个入口」页。所以这类链接必须在**同一页**
存在目标 id，或者是前端认识的路由 / 节点 id，否则就是死链。

判定为「可达」的三种情况：
  1. 同页存在 `id="锚点"`；
  2. 锚点是前端阅读模型里的节点 id（site/data/reader.json → reader.map/topics/
     atlases/resources 的 id）。此时路由兜底分支会调用 guide(id)，按其归属打开
     概览页或对应分组，而不是错误页；
  3. 以 `/` 开头 —— `#/doc/...`、`#/chapter/...` 等路由链接，由前端解析。

用法：
    python3 tools/check_anchors.py            # 打印报告；有死链则退出码 1
    python3 tools/check_anchors.py --stats    # 只打印一行统计
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
READER_JSON = SITE / "data" / "reader.json"

HREF_RE = re.compile(r'href="#([^"]+)"')
ID_RE = re.compile(r'\bid="([^"]+)"')


def reader_node_ids(path: pathlib.Path = READER_JSON) -> set[str]:
    """前端阅读模型里可被 guide(id) 解析的节点 id。"""
    if not path.is_file():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    reader = data.get("reader") or {}
    found: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            nid = node.get("id")
            if isinstance(nid, str) and nid:
                found.add(nid)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for key in ("map", "topics", "atlases", "resources"):
        walk(reader.get(key))
    return found


def check(site: pathlib.Path = SITE):
    node_ids = reader_node_ids(site / "data" / "reader.json")
    dead = collections.Counter()
    where = collections.defaultdict(set)
    total = 0

    for page in sorted(site.rglob("*.html")):
        text = page.read_text(encoding="utf-8", errors="ignore")
        page_ids = set(ID_RE.findall(text))
        for target in HREF_RE.findall(text):
            if target.startswith("/"):
                continue                      # 路由链接
            total += 1
            if target in page_ids or target in node_ids:
                continue
            dead[target] += 1
            where[target].add(page)

    return dead, total, where, node_ids


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true", help="只打印一行统计")
    args = ap.parse_args()

    if not SITE.is_dir():
        print("未找到 site/，请先运行 python3 tools/build.py", file=sys.stderr)
        return 2

    dead, total, where, node_ids = check()
    pages_hit = len(set().union(*where.values())) if where else 0

    if args.stats or not dead:
        print(f"页内锚点 {total} 条 · 已知节点 id {len(node_ids)} 个 · 死链 {sum(dead.values())} 条")
        if not dead:
            print("PASS：所有页内锚点都能在同页或前端路由里解析。")
        return 1 if dead else 0

    print(f"页内锚点 {total} 条 · 已知节点 id {len(node_ids)} 个 · 死链 {sum(dead.values())} 条，"
          f"分布在 {pages_hit} 个页面\n")
    for target, count in dead.most_common():
        files = sorted(p.relative_to(ROOT) for p in where[target])
        print(f"  {count:4d}  #{target}")
        print(f"        例：{files[0]}（共 {len(files)} 个页面）")
    print(f"\nFAIL：{sum(dead.values())} 条页内锚点无法解析，会跳到「找不到这个入口」。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
