#!/usr/bin/env python3
"""一键构建：校验 → 生成索引 → 渲染静态页面 → 检查外链。

这是本地与 CI / Pages 共用的统一入口。

    python3 tools/build.py                     # 本地：校验 + 构建
    python3 tools/build.py --strict --report   # CI：警告也算失败，并打印统计
    python3 tools/build.py --strict --no-links # 跳过外链检查（离线环境）

--strict 的含义（与 CI 约定一致）：
  * 元数据错误、重复 id、内部链接与锚点错误、构建失败 → 失败
  * 元数据解析警告（无法识别的写法、重复键、非法列表）→ 失败
  * 外链里的永久失效（404 / 410 / 域名不存在 / URL 非法）→ 失败
  * 外链里的「暂时无法判定」（403 / 429 / 5xx / 超时）→ 只警告，不阻塞
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def run(args: list[str]) -> int:
    print("$ " + " ".join(str(a) for a in args), flush=True)
    return subprocess.call(args, cwd=str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description="构建站点与索引")
    ap.add_argument("--report", action="store_true", help="打印章节与时效统计")
    ap.add_argument("--strict", action="store_true", help="警告即失败，并严格检查外链")
    ap.add_argument("--links", action="store_true", help="即使非 strict 也检查外链")
    ap.add_argument("--no-links", action="store_true", help="跳过外链检查")
    args = ap.parse_args()

    py = sys.executable
    idx = [py, "tools/build_index.py"]
    if args.report:
        idx += ["--report", "--report-stale"]
    if args.strict:
        idx.append("--strict")

    if run(idx) != 0:
        print("内容校验未通过，构建中止。", file=sys.stderr)
        return 1
    if run([py, "tools/build_site.py"]) != 0:
        return 1

    node = shutil.which("node")
    if node:
        if run([node, "--check", "site/app.js"]) != 0:
            print("前端脚本语法检查未通过。", file=sys.stderr)
            return 1

    if not args.no_links and (args.strict or args.links):
        links = [py, "tools/check_links.py", "--jobs", "16"]
        if args.strict:
            links.append("--strict")
        if run(links) != 0:
            print("存在永久失效的外部链接。", file=sys.stderr)
            return 1

    print("构建完成。本地预览：python3 -m http.server 8000 --directory site")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
