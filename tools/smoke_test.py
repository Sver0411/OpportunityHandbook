#!/usr/bin/env python3
"""前端冒烟测试：用无头 Chrome 真跑一遍关键交互。

不引入 Playwright：起一个本地 http.server，把 probe 脚本注入到站点首页的副本里，
用 Chrome 的 headless + virtual-time 执行一串断言，读回 JSON 结果。

覆盖（本轮收敛目标）：
  桌面：首页能打开 / 目录有内容 / 文档能加载 / 深链能定位 / 搜索有结果 /
        筛选能改变结果 / planned 文档不在目录里
  移动：菜单能打开 / 能关闭 / 点击文章后抽屉自动关闭

没有 Chrome 时跳过（退出码 0），便于在没有浏览器的 CI 里跑。

    python3 tools/smoke_test.py
"""

from __future__ import annotations

import functools
import http.server
import json
import pathlib
import re
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]

# 套在 <head> 里的桩：无头 Chrome 的虚拟时间会被 IntersectionObserver 与平滑滚动拖住，
# 冒烟测试不需要它们，先关掉，测试完再恢复（只影响这份临时副本）
STUBS = """
<script>
try { delete window.IntersectionObserver; } catch (e) {}
</script>
"""

HASHES = {"home": "/", "deep": "/", "browse": "/browse?q=%E4%BF%9D%E7%A0%94",
          "mobile": "/", "legacy": "/doc/book/03-%E5%8D%87%E5%AD%A6/grad-school-worth-it"}

PROBE = r"""
<pre id="smoke" style="position:fixed;left:0;bottom:0;z-index:9999;background:#fff;color:#000;font:11px monospace;padding:6px;max-width:100%;white-space:pre-wrap"></pre>
<script>
(function () {
  var results = [];
  function wait(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  function ok(name, cond, detail) { results.push({ name: name, pass: !!cond, detail: detail || "" }); }
  function text(sel) { var n = document.querySelector(sel); return n ? n.textContent.trim() : ""; }
  function count(sel) { return document.querySelectorAll(sel).length; }

  async function run() {
    var mode = (location.search.match(/mode=(\w+)/) || [])[1] || "home";
    document.documentElement.style.scrollBehavior = "auto";
    await wait(1500);

    if (mode === "home") {
      ok("首页能打开", !!document.querySelector(".doc .doc-header h1"), text(".doc-header h1"));
      ok("目录有内容", count(".nav-tree .nav-row") > 10, count(".nav-tree .nav-row") + " 行");
      ok("首页不再有项目 Dashboard", count(".stats") === 0);
      var navText = (document.getElementById("navTree") || {}).textContent || "";
      ok("planned 文档不在目录", navText.indexOf("日本") < 0 && navText.indexOf("制造业") < 0);
      location.hash = "#/doc/book/03-升学";
      await wait(900);
      ok("文档能加载", count(".doc .entry") > 0, count(".doc .entry") + " 个条目");
      ok("页内目录有内容", count(".toc-list li") > 0);
    }

    if (mode === "deep") {
      location.hash = "#/doc/book/03-升学/grad-school-worth-it";
      await wait(1200);
      var deep = document.querySelector("#grad-school-worth-it");
      ok("深链能定位", !!deep && deep.classList.contains("highlight"));
      ok("深链页面有正文", count("#grad-school-worth-it h2") > 0 ||
         count("#grad-school-worth-it ul.fields") > 0);   // 文章格式与旧格式都算
    }

    if (mode === "legacy") {
      // IA 重构前的旧地址：应当自动跳转到新地址并渲染出同一篇文章
      await wait(1500);
      var legacy = document.querySelector("#grad-school-worth-it");
      ok("旧深链能打开", !!legacy);
      ok("旧深链被改写成新地址", location.hash.indexOf("#/doc/book/04-") === 0, location.hash);
      ok("旧深链页面有正文", count("#grad-school-worth-it h2") > 0 ||
         count("#grad-school-worth-it ul.fields") > 0);
    }

    if (mode === "browse") {
      var n1 = count(".result");
      ok("搜索能返回结果", n1 > 0, n1 + " 条（保研）");
      location.hash = "#/browse?stages=undergraduate";
      await wait(1000);
      var n2 = count(".result");
      ok("筛选能返回结果", n2 > 0, n2 + " 条（本科）");
      location.hash = "#/browse?stages=undergraduate&effort=low";
      await wait(1000);
      var n3 = count(".result");
      ok("叠加条件会收窄结果", n3 > 0 && n3 < n2, n3 + " 条（本科 + 低投入）");
      location.hash = "#/browse?evidence=official";
      await wait(1000);
      ok("证据筛选可用", count(".result") > 0, count(".result") + " 条（官方规则）");
      location.hash = "#/browse?q=%E5%A5%97%E7%A3%81";
      await wait(1000);
      ok("同义词搜索可用（套磁）", count(".result") > 0, count(".result") + " 条");
    }

    if (mode === "mobile") {
      var btn = document.getElementById("navCollapse");
      btn.click();
      await wait(500);
      ok("菜单能打开", document.body.classList.contains("sidebar-open"));
      document.getElementById("navClose").click();
      await wait(500);
      ok("菜单能关闭", !document.body.classList.contains("sidebar-open"));
      btn.click();
      await wait(500);
      var link = document.querySelector("#navTree a.nav-label");
      if (link) {
        link.click();
        await wait(1400);
        ok("点击文章后抽屉自动关闭", !document.body.classList.contains("sidebar-open"));
        ok("移动端能加载文档", count(".doc .entry") > 0);
      } else {
        ok("点击文章后抽屉自动关闭", false, "目录里没有链接");
      }
      ok("移动端无横向溢出",
         document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1,
         document.documentElement.scrollWidth + " vs " + document.documentElement.clientWidth);
    }

    document.getElementById("smoke").textContent = "@@SMOKE@@" + JSON.stringify(results) + "@@END@@";
  }

  run();
})();
</script>
"""


def find_chrome() -> str | None:
    for c in CHROME_CANDIDATES:
        if pathlib.Path(c).is_file():
            return c
    return shutil.which("google-chrome") or shutil.which("chromium")


def serve(directory: pathlib.Path):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def run_case(chrome: str, base: str, size: str, mode: str, budget: int = 8000) -> list[dict]:
    url = f"{base}?mode={mode}#" + HASHES[mode]
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [
            chrome, "--headless=new", "--no-sandbox", "--disable-gpu",
            f"--user-data-dir={tmp}", "--no-first-run", "--disable-smooth-scrolling",
            "--disable-extensions", "--disable-background-networking",
            "--disable-default-apps", "--no-default-browser-check", "--mute-audio",
            f"--virtual-time-budget={budget}", f"--window-size={size}",
            "--dump-dom", url,
        ]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            out = r.stdout
        except subprocess.TimeoutExpired as e:
            out = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
            if "@@SMOKE@@" not in out:
                return [{"name": f"{mode} 用例超时", "pass": False, "detail": "Chrome 未在 90s 内返回"}]
    m = re.search(r"@@SMOKE@@(.*?)@@END@@", out, re.S)
    if not m:
        return [{"name": f"{mode} 用例未返回结果", "pass": False, "detail": out[-200:]}]
    import html as _html
    return json.loads(_html.unescape(m.group(1)))


def main() -> int:
    chrome = find_chrome()
    if not chrome:
        print("未找到 Chrome / Chromium，跳过前端冒烟测试。")
        return 0

    probe_path = SITE / "_smoke.html"
    src = (SITE / "index.html").read_text(encoding="utf-8")
    src = src.replace("<script src=\"app.js\"></script>", STUBS + "<script src=\"app.js\"></script>")
    probe_path.write_text(src.replace("</body>", PROBE + "</body>"), encoding="utf-8")

    httpd, port = serve(SITE)
    base = f"http://127.0.0.1:{port}/_smoke.html"
    failures = 0
    try:
        for label, size, mode in (("桌面 · 首页与文档", "1440,1400", "home"),
                                  ("桌面 · 深链", "1440,1400", "deep"),
                                  ("桌面 · 搜索与筛选", "1440,1400", "browse"),
                                  ("旧深链重定向", "1440,1400", "legacy"),
                                  ("移动端", "500,1000", "mobile")):
            results = run_case(chrome, base, size, mode)
            if results and all("超时" in r["name"] for r in results):
                print(f"  （{label}：首次超时，重试一次）", flush=True)
                results = run_case(chrome, base, size, mode)
            print(f"\n== 前端冒烟（{label}）==")
            for r in results:
                mark = "PASS" if r["pass"] else "FAIL"
                if not r["pass"]:
                    failures += 1
                extra = f"  [{r['detail']}]" if r.get("detail") else ""
                print(f"  [{mark}] {r['name']}{extra}", flush=True)
    finally:
        httpd.shutdown()
        try:
            probe_path.unlink(missing_ok=True)
        except OSError as e:
            # 某些环境会拦截删除（批量删除保护等），不影响测试结论
            print(f"（临时页未能删除：{e.__class__.__name__}，可手动清理 site/_smoke.html）")

    print(f"\n冒烟测试：{'全部通过' if not failures else str(failures) + ' 项失败'}", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
