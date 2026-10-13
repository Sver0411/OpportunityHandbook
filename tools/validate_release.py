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
  6b. check_html_ids.py             HTML id 唯一性与条目前缀
  6c. build_roadmap.py --check      路线图是否与 metadata 一致
  7. check_links.py --strict        外部链接（仅永久失效 404/410 阻塞）
  8. smoke_test.py                  浏览器冒烟（--quick 时跳过）
  9. check_chapter_size.py          正文文件长度（防止长回大章节）

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
    ("HTML id 唯一性", [PY, "tools/check_html_ids.py"]),
    ("内容路线图与 metadata 一致", [PY, "tools/build_roadmap.py", "--check"]),
    # 外链可达性：只有真正的永久失效（HTTP 404/410）才失败；
    # SSL / 超时 / 代理出口问题一律记为「无法判定」
    ("外部链接可达性", [PY, "tools/check_links.py", "--strict"]),
    # 读者视角的三项审查：动线（断头路/下一步/回程）、搜索可发现性、来源可核对性。
    # 它们都是启发式检查，但已把历史问题清空——留在门禁里防止回退。
    ("读者动线检查", [PY, "tools/audit_reading_path.py"]),
    ("搜索可发现性", [PY, "tools/audit_search.py"]),
    ("来源一致性", [PY, "tools/audit_sources.py"]),
    # 排版实测：用无头 Chrome 量各级标题的计算字号，防止标题层级倒挂或小于正文
    # （没有 Chrome 时该脚本自行跳过并返回 0）
    ("标题层级实测", [PY, "tools/probe_typography.py"]),
    # 正文文件不能重新长回几千行的大章节（拆分成小分册是维护成本的前提）
    ("正文文件长度", [PY, "tools/check_chapter_size.py"]),
]

SMOKE = ("浏览器冒烟", [PY, "tools/smoke_test.py"])


# 依赖无头 Chrome 的两步（排版实测、浏览器冒烟）在机器负载高时会偶发失败
# （首屏还没渲染完、定时器被拖住）。它们各允许重试一次：真有问题时两次都会失败，
# 因此不会掩盖回归，但能避免把「这一次没跑起来」当成内容问题。
FLAKY = {"标题层级实测", "浏览器冒烟"}


def run(name: str, cmd: list[str]) -> bool:
    attempts = 2 if name in FLAKY else 1
    for attempt in range(1, attempts + 1):
        print(f"\n=== {name} ==={'' if attempt == 1 else '（重试）'}")
        proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
        tail = (proc.stdout or "").strip().splitlines()[-6:]
        for line in tail:
            print("   ", line)
        if proc.returncode == 0:
            print(f"→ {name} 通过")
            return True
        err = (proc.stderr or "").strip().splitlines()[-6:]
        for line in err:
            print("   !", line)
        if attempt == attempts:
            print(f"→ {name} 失败（exit {proc.returncode}）")
            return False
        print(f"   （首次失败，重试一次；此类检查依赖无头 Chrome，偶发失败不代表回归）")
    return False


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
