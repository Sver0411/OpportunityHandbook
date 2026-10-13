#!/usr/bin/env python3
"""实测站点排版：用无头 Chrome 量出各级标题与正文的计算字号，检查层级是否成立。

要求（读者能一眼看出层级）：
    正文 < 条目内 ### ≤ 条目内 ## < 条目标题 < 章节分组标题 < 文档标题
且任何标题不得小于正文字号。

    python3 tools/probe_typography.py
"""

from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
sys.path.insert(0, str(ROOT / "tools"))

import smoke_test as S  # noqa: E402

# 覆盖两种页面：书章条目页（有分组标题 + 条目标题 + 条目内小节）与文档页（深度教程）
ROUTES = [
    ("书章条目页", "#/doc/book/02-%E5%9C%A8%E5%AD%A6%E6%A0%A1%E9%87%8C%E5%85%88%E6%8A%8A%E5%9F%BA%E7%A1%80%E6%89%93%E5%A5%BD/gpa-matters"),
    ("文档页（深度教程）", "#/doc/docs/projects/%E6%B5%8B%E8%AF%95%E4%B8%8E%E6%8C%87%E6%A0%87%E4%BD%93%E7%B3%BB"),
]

PROBE = """
<script>
(function () {
  function px(el) { return el ? parseFloat(getComputedStyle(el).fontSize) : null; }
  function wt(el) { return el ? getComputedStyle(el).fontWeight : null; }
  function pick(sel) { return document.querySelector(sel); }
  function measure() {
    var doc = pick(".doc");
    var probe = [
      ["文档标题 h1", pick(".doc-header h1")],
      ["章节分组 h2", doc ? doc.querySelector(":scope > h2") : null],
      ["条目标题 h3", doc ? doc.querySelector(".entry > h3") : null],
      ["条目内 ## (h2)", doc ? doc.querySelector(".entry h2") : null],
      ["### 小节", doc ? (doc.querySelector(".entry h2") ? doc.querySelector(".doc h4") : doc.querySelector(".doc h3")) : null],
      ["正文 p", document.querySelector(".doc p:not(.doc-summary):not(.doc-meta):not(.entry-badges)")]
    ].map(function (pair) {
      return { name: pair[0], size: px(pair[1]), weight: wt(pair[1]) };
    });
    var el = document.createElement("div");
    el.id = "typo-probe";
    el.textContent = "@@" + "SMOKE@@" + JSON.stringify(probe) + "@@" + "END@@";
    document.body.appendChild(el);
  }
  setTimeout(measure, 1200);
})();
</script>
"""

CASES = [("桌面 1280×900", "1280,900"), ("移动 390×844", "390,844")]


def run(chrome: str, base: str, size: str, route: str) -> list[dict]:
    url = f"{base}?mode=typography&{route}"
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [
            chrome, "--headless=new", "--no-sandbox", "--disable-gpu",
            f"--user-data-dir={tmp}", "--no-first-run", "--disable-smooth-scrolling",
            "--disable-extensions", "--disable-background-networking",
            "--disable-default-apps", "--no-default-browser-check", "--mute-audio",
            "--virtual-time-budget=6000", f"--window-size={size}", "--dump-dom", url,
        ]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            out = r.stdout
        except subprocess.TimeoutExpired as e:
            out = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
    hits = re.findall(r"@@SMOKE@@(.*?)@@END@@", out, re.S)
    if not hits:
        return []
    import html as _html
    return json.loads(_html.unescape(hits[-1]))


def check(rows: list[dict]) -> list[str]:
    bad = []
    by = {r["name"]: r["size"] for r in rows}
    body = by.get("正文 p")
    order = [n for n in ["正文 p", "### 小节", "条目内 ## (h2)", "条目标题 h3", "章节分组 h2", "文档标题 h1"]
             if by.get(n) is not None]
    if body is None:
        return ["没有量到正文字号"]
    for name, size in by.items():
        if size is not None and name != "正文 p" and size < body:
            bad.append(f"{name}（{size}px）小于正文（{body}px）")
    seq = [by.get(n) for n in order]
    for i in range(1, len(seq)):
        if seq[i] is not None and seq[i - 1] is not None and seq[i] < seq[i - 1]:
            bad.append(f"{order[i]}（{seq[i]}px）小于 {order[i-1]}（{seq[i-1]}px），层级倒挂")
    return bad


def main() -> int:
    chrome = S.find_chrome()
    if not chrome:
        print("未找到 Chrome / Chromium，跳过排版探针。")
        return 0

    probe_path = SITE / "_typography.html"
    src = (SITE / "index.html").read_text(encoding="utf-8")
    src = src.replace("<script src=\"app.js\"></script>", PROBE + "\n<script src=\"app.js\"></script>")
    probe_path.write_text(src, encoding="utf-8")

    failures = 0
    try:
        httpd, port = S.serve(SITE)
        base = f"http://127.0.0.1:{port}/_typography.html"
        try:
            for page_label, route in ROUTES:
                for label, size in CASES:
                    rows = run(chrome, base, size, route)
                    # 机器负载高时首屏可能还没渲染完（无头 Chrome 偶发），重试两次再判定，
                    # 避免把「这次没测到」当成排版问题
                    for _ in range(2):
                        if rows:
                            break
                        rows = run(chrome, base, size, route)
                    print(f"\n== {page_label} · {label} ==")
                    if not rows:
                        print("  未取到测量结果"); failures += 1; continue
                    for r in rows:
                        print(f"  {r['name']:18} {str(r['size']):>6}px  字重 {r['weight']}")
                    bad = check(rows)
                    if bad:
                        failures += 1
                        for b in bad:
                            print(f"  ✗ {b}")
                    else:
                        asc = sorted([r for r in rows if r["size"] is not None],
                                 key=lambda r: r["size"])
                    seq_txt = " < ".join(f"{r['name']}({r['size']}px)" for r in asc)
                    print(f"  ✓ 层级正确：{seq_txt}")
        finally:
            httpd.shutdown()
    finally:
        probe_path.unlink(missing_ok=True)
    print(f"\n排版检查：{'全部通过' if not failures else f'{failures} 个尺寸下存在问题'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
