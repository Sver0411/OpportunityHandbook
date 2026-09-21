#!/usr/bin/env python3
"""检查正文里的外部链接是否可达。

默认只报告，不改变退出码；加 --strict 时，任何「不可达」都视为失败（CI 用）。
403/405/429 这类「对方不欢迎自动访问」的响应单独归类为 unknown，不算失败。

    python3 tools/check_links.py
    python3 tools/check_links.py --strict --timeout 20 --jobs 16
    python3 tools/check_links.py --only book/ docs/countries/
"""

from __future__ import annotations

import argparse
import concurrent.futures as futures
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import meta as M  # noqa: E402

LINK_RE = re.compile(r"\[[^\]]*\]\((https?://[^)\s]+?)\)")
UA = "Mozilla/5.0 (compatible; OpportunityHandbook link checker; +https://github.com/Sver0411/OpportunityHandbook)"


def collect(root: Path, only: list[str]) -> dict[str, list[str]]:
    """返回 {url: [出现位置, ...]}"""
    found: dict[str, list[str]] = {}
    docs = M.load_docs(root)
    for doc in docs:
        if only and not any(doc.rel.startswith(p) for p in only):
            continue
        for url in LINK_RE.findall(doc.raw):
            url = url.rstrip(".,;)")
            found.setdefault(url, []).append(doc.rel)
    return found


def check(url: str, timeout: float) -> tuple[str, str]:
    """返回 (状态, 说明)：ok / unknown / fail"""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return ("ok", str(resp.status)) if resp.status < 400 else ("fail", str(resp.status))
    except urllib.error.HTTPError as e:
        if e.code in (401, 403, 405, 406, 429):
            return ("unknown", f"HTTP {e.code}（对方限制自动访问）")
        return ("fail", f"HTTP {e.code}")
    except Exception as e:  # 超时、DNS、证书等
        return ("fail", type(e).__name__)


def main() -> int:
    ap = argparse.ArgumentParser(description="外链可达性检查")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--jobs", type=int, default=12)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--only", nargs="*", default=[], help="只检查这些前缀下的文件")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    urls = collect(root, args.only)
    print(f"收集到 {len(urls)} 个外部链接，开始检查（并发 {args.jobs}，超时 {args.timeout}s）")

    results: dict[str, tuple[str, str]] = {}
    with futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        jobs = {pool.submit(check, u, args.timeout): u for u in urls}
        for job in futures.as_completed(jobs):
            url = jobs[job]
            try:
                results[url] = job.result()
            except Exception as e:  # pragma: no cover
                results[url] = ("fail", type(e).__name__)

    ok = [u for u, (s, _) in results.items() if s == "ok"]
    unknown = {u: d for u, (s, d) in results.items() if s == "unknown"}
    failed = {u: d for u, (s, d) in results.items() if s == "fail"}

    if unknown:
        print(f"\n无法判定（{len(unknown)}）——多为对方限制自动访问，需要人工打开确认：")
        for u, d in sorted(unknown.items()):
            print(f"  ? {u}  [{d}]")
    if failed:
        print(f"\n不可达（{len(failed)}）：")
        for u, d in sorted(failed.items()):
            print(f"  x {u}  [{d}]")
            for loc in urls[u][:3]:
                print(f"      出现在 {loc}")
    print(f"\n汇总：可达 {len(ok)} · 无法判定 {len(unknown)} · 不可达 {len(failed)}")
    return 1 if (args.strict and failed) else 0


if __name__ == "__main__":
    raise SystemExit(main())
