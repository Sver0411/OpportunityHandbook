#!/usr/bin/env python3
"""运行内容与工程规则测试。

    python3 tools/run_tests.py            # 全部测试
    python3 tools/run_tests.py -v         # 详细输出
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def main() -> int:
    cmd = [sys.executable, "-m", "unittest", "discover",
           "-s", str(HERE / "tests"), "-t", str(ROOT), "-p", "test_*.py"]
    if "-v" in sys.argv[1:]:
        cmd.append("-v")
    print("$ " + " ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=str(ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
