#!/usr/bin/env python3
"""给 site/index.html 里的 app.js / styles.css 引用加内容哈希版本参数。

    python3 tools/stamp_assets.py

为什么需要：GitHub Pages 对静态资源有约 10 分钟的 CDN 与浏览器缓存。改了
app.js 之后，读者可能仍拿到旧版脚本，表现为「明明改了却没生效」。用文件内容
的哈希作为查询参数后，**文件一变 URL 就变**，浏览器必须重新下载；文件没变时
URL 也不变，缓存仍然有效。

数据文件（data/index.json、search_aliases.json）不在这里处理——它们在 app.js
里用 `cache: "no-cache"` 请求，每次会带 ETag 向服务器验证，未变更时返回 304。
"""

from __future__ import annotations

import hashlib
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SITE = ROOT / "site"
ASSETS = ("styles.css", "reader.css", "reader.js", "app.js")


def content_hash(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:10]


def main() -> int:
    index = SITE / "index.html"
    if not index.exists():
        print(f"找不到 {index}")
        return 1

    html = index.read_text(encoding="utf-8")
    changed = []
    for name in ASSETS:
        asset = SITE / name
        if not asset.exists():
            continue
        h = content_hash(asset)
        # 匹配 href="styles.css" / src="app.js"，允许已带 ?v=...
        pattern = re.compile(
            r'(?P<q>["\'])' + re.escape(name) + r'(?:\?v=[0-9a-f]+)?(?P=q)'
        )
        new_html, n = pattern.subn(lambda m: f'{m.group("q")}{name}?v={h}{m.group("q")}', html)
        if n:
            html = new_html
            changed.append(f"{name}?v={h}（{n} 处）")

    index.write_text(html, encoding="utf-8")
    if changed:
        print("已写入版本参数：" + "、".join(changed))
    else:
        print("没有找到需要处理资源引用")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
