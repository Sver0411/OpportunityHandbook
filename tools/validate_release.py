#!/usr/bin/env python3
"""发布校验（Release Validation）——CI 与 Pages 必须调用同一个入口。

    python3 tools/validate_release.py            # 完整发布校验
    python3 tools/validate_release.py --quick    # 跳过浏览器冒烟

执行顺序（任一步失败即整体失败）：
  1. build.py --strict              元数据、内部链接、构建
  2. check_ia.py                    Canonical IA 一致性
  3. check_markdown_quality.py      Markdown 格式
  4. check_docs_consistency.py      规范/README 不得退回旧正文模型
  5. check_content_quality.py --hard 内容硬门（旧模板 / 缺 summary / P0 过薄）
  6. run_tests.py                   内容规则测试
  7. smoke_test.py                  浏览器冒烟（--quick 时跳过）

这样「内容不合格就不能上线」在 CI 与 Pages 两端同时成立。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PY = sys.executable

STEPS: list[tuple[str, list[str]]] = [
    ("构建与元数据校验", [PY, "tools/build.py", "--strict", "--no-links"]),
    ("Canonical IA 一致性", [PY, "tools/check_ia.py"]),
    ("Markdown 格式", [PY, "tools/check_markdown_quality.py"]),
    ("文档一致性", [PY, "tools/check_docs_consistency.py"]),
    ("内容质量硬门", [PY, "tools/check_content_quality.py", "--hard"]),
    ("内容规则测试", [PY, "tools/run_tests.py"]),
]

SMOKE = ("浏览器冒烟", [PY, "tools/smoke_test.py"])


def run(name: str, cmd: list[str]) -> bool:
    print(f"\n=== {name} ===")
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    tail = (proc.stdout or "").strip().splitlines()[-6:]
    for line in tail:
        print("   ", line)
    if proc.returncode != 0:
        err = (proc.stderr or "").strip().splitlines()[-6:]
        for line in err:
            print("   !", line)
        print(f"→ {name} 失败（exit {proc.returncode}）")
        return False
    print(f"→ {name} 通过")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="跳过浏览器冒烟（CI 常用）")
    args = ap.parse_args()

    failed: list[str] = []
    steps = list(STEPS) + ([] if args.quick else [SMOKE])
    for name, cmd in steps:
        if not run(name, cmd):
            failed.append(name)

    print("\n================ 发布校验结果 ================")
    if failed:
        print("FAIL：" + "、".join(failed))
        print("发布被阻止：修复以上问题后重跑 tools/validate_release.py")
        return 1
    print(f"PASS：{len(steps)} 项全部通过" + ("（已跳过浏览器冒烟）" if args.quick else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
