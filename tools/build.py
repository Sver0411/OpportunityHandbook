#!/usr/bin/env python3
"""一键构建：校验 → 生成索引 → 渲染静态页面。

    python3 tools/build.py            # 完整构建
    python3 tools/build.py --report   # 附带章节与时效报告
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def run(args: list[str]) -> int:
    print("$ " + " ".join(str(a) for a in args))
    return subprocess.call(args, cwd=str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description="构建站点与索引")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--strict", action="store_true")
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
    print("构建完成。本地预览：python3 -m http.server 8000 --directory site")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
