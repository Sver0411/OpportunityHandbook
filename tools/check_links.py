#!/usr/bin/env python3
"""检查正文里的外部链接是否可达，并区分「永久失效」与「暂时无法判定」。

分类规则（与 CI 约定一致）：

  PASS   2xx / 跟随重定向后 2xx
  WARN   403 / 429 / 5xx / 超时 / TLS 握手失败 / 反爬拦截
         —— 对方限制自动访问，不代表链接失效，不阻塞合并
  FAIL   404 / 410 / 451 / 域名不存在 / URL 格式明显非法
         —— 真正失效的来源，CI 必须失败

用法：
    python3 tools/check_links.py
    python3 tools/check_links.py --strict --timeout 20 --jobs 16
    python3 tools/check_links.py --json
    python3 tools/check_links.py --only book/ docs/countries/
"""

from __future__ import annotations

import argparse
import concurrent.futures as futures
import json
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import meta as M  # noqa: E402

LINK_RE = re.compile(r"\[[^\]]*\]\((https?://[^)\s]+?)\)")
UA = "Mozilla/5.0 (compatible; OpportunityHandbook link checker; +https://github.com/Sver0411/OpportunityHandbook)"

# 永久失效：这些状态直接判定链接坏了
PERMANENT_CODES = (404, 410, 451)
# 暂时无法判定：对方限制自动访问或临时故障
TRANSIENT_CODES = (401, 403, 405, 406, 407, 409, 418, 429,
                   500, 502, 503, 504, 520, 521, 522, 523, 524)
TRANSIENT_REASONS = (
    "timeout", "timed out", "ssl", "tls", "certificate", "connection reset",
    "connection refused", "remote end closed", "temporarily unavailable",
    "name or service not known", "nodename nor servname",
)


def collect(root: Path, only: list[str]) -> dict[str, list[str]]:
    """返回 {url: [出现位置, ...]}"""
    found: dict[str, list[str]] = {}
    for doc in M.load_docs(root):
        if only and not any(doc.rel.startswith(p) for p in only):
            continue
        for url in LINK_RE.findall(doc.raw):
            url = url.rstrip(".,;)")
            found.setdefault(url, []).append(doc.rel)
    return found


def classify(url: str, timeout: float) -> tuple[str, str]:
    """返回 (分类, 说明)：pass / warn / fail"""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return ("fail", "URL 格式非法")

    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.status
            if code < 400:
                return ("pass", str(code))
            if code in PERMANENT_CODES:
                return ("fail", f"HTTP {code}")
            return ("warn", f"HTTP {code}")
    except urllib.error.HTTPError as e:
        if e.code in PERMANENT_CODES:
            return ("fail", f"HTTP {e.code}")
        if e.code in TRANSIENT_CODES:
            return ("warn", f"HTTP {e.code}（对方限制自动访问或临时故障）")
        return ("warn", f"HTTP {e.code}")
    except urllib.error.URLError as e:
        reason = str(getattr(e, "reason", e)).lower()
        if any(r in reason for r in TRANSIENT_REASONS):
            return ("warn", f"无法建立连接：{getattr(e, 'reason', e)}")
        return ("fail", f"域名或网络不可达：{getattr(e, 'reason', e)}")
    except socket.timeout:
        return ("warn", "请求超时")
    except Exception as e:  # pragma: no cover
        return ("warn", type(e).__name__)


def main() -> int:
    ap = argparse.ArgumentParser(description="外链可达性检查（区分永久失效与暂时无法判定）")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--jobs", type=int, default=12)
    ap.add_argument("--strict", action="store_true", help="存在永久失效时返回非零（CI 用）")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--only", nargs="*", default=[], help="只检查这些前缀下的文件")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    urls = collect(root, args.only)
    if not args.json:
        print(f"收集到 {len(urls)} 个外部链接，开始检查（并发 {args.jobs}，超时 {args.timeout}s）")

    results: dict[str, tuple[str, str]] = {}
    with futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        jobs = {pool.submit(classify, u, args.timeout): u for u in urls}
        for job in futures.as_completed(jobs):
            url = jobs[job]
            try:
                results[url] = job.result()
            except Exception as e:  # pragma: no cover
                results[url] = ("warn", type(e).__name__)

    passed = [u for u, (s, _) in results.items() if s == "pass"]
    warned = {u: d for u, (s, d) in results.items() if s == "warn"}
    failed = {u: d for u, (s, d) in results.items() if s == "fail"}

    if args.json:
        print(json.dumps({"pass": len(passed), "warn": warned, "fail": failed},
                         ensure_ascii=False, indent=2))
    else:
        if warned:
            print(f"\n无法判定（{len(warned)}）——对方限制自动访问或临时故障，不算失效：")
            for u, d in sorted(warned.items()):
                print(f"  ? {u}  [{d}]")
        if failed:
            print(f"\n永久失效（{len(failed)}）——需要替换或删除：")
            for u, d in sorted(failed.items()):
                print(f"  x {u}  [{d}]")
                for loc in urls[u][:3]:
                    print(f"      出现在 {loc}")
        print(f"\nExternal links: PASS {len(passed)} · WARN {len(warned)} · FAIL {len(failed)}")

    return 1 if (args.strict and failed) else 0


if __name__ == "__main__":
    raise SystemExit(main())
