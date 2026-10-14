#!/usr/bin/env python3
"""把手册导出成 PDF（命令行批量版）。

站点右上角有「导出 PDF」（浏览器打印 → 另存为 PDF）；这个工具用于**批量**导出：
用无头 Chrome 逐章调用同一个打印管线，输出一章一个 PDF。

    python3 tools/export_pdf.py --list                 # 列出可导出的章节
    python3 tools/export_pdf.py --chapter 15           # 导出第 15 章
    python3 tools/export_pdf.py --doc book/15-钱与生活基本盘/01-拿到钱的第一年
    python3 tools/export_pdf.py --all                  # 主线章 + 横切章（不含 09–13 资料层）
    python3 tools/export_pdf.py --all --out ~/Desktop/机会手册

输出目录默认 `dist/pdf/`（已在 .gitignore 中，不进仓库）。
需要本机有 Chrome / Chromium；生产环境用它导出比手工逐页打印稳得多。
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
sys.path.insert(0, str(ROOT / "tools"))

import smoke_test as S  # noqa: E402
from pdf_driver import Chrome  # noqa: E402

# 页眉页脚模板（CDP 专用）：左＝书名，中＝页码，右＝来源
HEADER = ('<div style="width:100%;font-size:8pt;color:#888;padding:0 14mm;'
          'display:flex;justify-content:space-between;">'
          '<span>机会手册 · OpportunityHandbook</span>'
          '<span class="title"></span></div>')
FOOTER = ('<div style="width:100%;font-size:8.5pt;color:#555;padding:0 14mm;'
          'display:flex;justify-content:space-between;">'
          '<span>正文 CC BY 4.0 · 站点代码 MIT</span>'
          '<span>第 <span class="pageNumber"></span> 页 / 共 <span class="totalPages"></span> 页</span>'
          '<span>sver0411.github.io/OpportunityHandbook</span></div>')

# 主线章（00–08）与横切章（14–17）默认导出；09–13 是资料层，用 --all --with-docs 才带上
MAIN_CHAPTERS = ["00", "01", "02", "03", "04", "05", "06", "07", "08", "14", "15", "16", "17"]
DOC_CHAPTERS = ["09", "10", "11", "12", "13"]


def chapter_landings(index: dict) -> dict[str, str]:
    """章号 → 该章的入口 location（用左栏里出现的第一页）。"""
    out: dict[str, str] = {}
    for d in index.get("docs", []):
        loc = d.get("location") or ""
        m = re.match(r"^book/(\d\d)-", loc)
        if not m:
            continue
        out.setdefault(m.group(1), loc)
    return out


def title_of(index: dict, location: str) -> str:
    for d in index.get("all_docs") or index.get("docs", []):
        if d.get("location") == location:
            return d.get("title") or location
    return location


def safe(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|\s]+', "-", name).strip("-")[:80]


def export(chrome: str, base: str, location: str, kind: str, out: pathlib.Path) -> tuple[bool, str]:
    url = f"{base}/index.html?export={kind}#/doc/{location}"
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [chrome, "--headless=new", "--no-sandbox", "--disable-gpu",
               f"--user-data-dir={tmp}", "--no-first-run", "--disable-extensions",
               "--no-pdf-header-footer", "--virtual-time-budget=20000",
               f"--print-to-pdf={out}", url]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if not out.exists() or out.stat().st_size < 5_000:
        return False, (r.stderr or "").strip().splitlines()[-1:] and (r.stderr or "").strip().splitlines()[-1] or "未生成 PDF"
    raw = out.read_bytes()
    if not raw.startswith(b"%PDF"):
        return False, "输出不是 PDF"
    pages = len(re.findall(rb"/Type\s*/Page[^s]", raw))
    return True, f"{out.stat().st_size/1024:.0f} KB / {pages} 页"


def render(chrome: str, base: str, location: str, kind: str, out: pathlib.Path) -> tuple[bool, str]:
    """用 CDP 打开页面 → 准备打印区 → printToPDF（带页码页脚）。"""
    driver = Chrome(chrome)
    try:
        driver.navigate(f"{base}/index.html#/doc/{location}", settle=3.0)
        info = driver.eval_js(f"window.__ohExportPdf({json.dumps(kind)}, {{ noPrint: true }})", timeout=1800)
        if not isinstance(info, dict):
            return False, "打印区未就绪（页面可能还没渲染完）"
        time.sleep(0.6)
        size, pages = driver.print_pdf(out, header=HEADER, footer=FOOTER,
                                       margin_top=0.7, margin_bottom=0.8, timeout=1800)
        return True, f"{size/1024/1024:.1f} MB / {pages} 页（{info.get('count', '?')} 个页面块）"
    except Exception as exc:                     # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"
    finally:
        driver.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="列出可导出的章节")
    ap.add_argument("--book", action="store_true", help="导出整本手册（一个 PDF，含封面与目录）")
    ap.add_argument("--all", action="store_true", help="按章导出（一章一个 PDF）")
    ap.add_argument("--with-docs", action="store_true", help="--all 时连 09–13 资料层一起导出")
    ap.add_argument("--chapter", help="只导出某一章，如 15")
    ap.add_argument("--doc", help="只导出某一页（location）")
    ap.add_argument("--kind", default="chapter", choices=["chapter", "doc"], help="单章导出范围")
    ap.add_argument("--out", help="输出文件或目录（默认 dist/pdf）")
    args = ap.parse_args()

    index = json.loads((SITE / "data" / "index.json").read_text(encoding="utf-8"))
    landings = chapter_landings(index)
    stamp = time.strftime("%Y-%m-%d")

    if args.list:
        print("可导出的章节（章号 · 入口页 · 标题）：")
        for num in sorted(landings):
            print(f"  {num}  {landings[num]}  {title_of(index, landings[num])}")
        print("\n资料层 09–13 需加 --with-docs（--all 时）")
        return 0

    chrome = S.find_chrome()
    if not chrome:
        print("未找到 Chrome / Chromium —— 导出 PDF 需要本机浏览器。")
        return 1

    if args.book:
        out = pathlib.Path(args.out).expanduser() if args.out else ROOT / "dist" / "pdf" / f"机会手册-全书-{stamp}.pdf"
        if out.is_dir():
            out = out / f"机会手册-全书-{stamp}.pdf"
        entry = landings.get("00") or next(iter(landings.values()))
        print(f"  导出整本手册（入口 {entry}）……", flush=True)
        httpd, port = S.serve(SITE)
        try:
            good, detail = render(chrome, f"http://127.0.0.1:{port}", entry, "book", out)
        finally:
            httpd.shutdown()
        print(("  ✓ " if good else "  ✗ ") + f"{out}  [{detail}]")
        return 0 if good else 1

    targets: list[tuple[str, str, str]] = []
    if args.doc:
        targets.append((safe(title_of(index, args.doc)), args.doc, "doc"))
    elif args.chapter:
        num = args.chapter.zfill(2)
        if num not in landings:
            print(f"找不到第 {num} 章的入口页；用 --list 看有哪些。")
            return 1
        targets.append((f"{num} {safe(title_of(index, landings[num]))}", landings[num], args.kind))
    elif args.all:
        nums = MAIN_CHAPTERS + (DOC_CHAPTERS if args.with_docs else [])
        for num in nums:
            if num in landings:
                targets.append((f"{num} {safe(title_of(index, landings[num]))}", landings[num], "chapter"))
    else:
        ap.print_help()
        print("\n提示：整本一个 PDF 用 --book。")
        return 2

    outdir = pathlib.Path(args.out).expanduser() if args.out else ROOT / "dist" / "pdf"
    outdir.mkdir(parents=True, exist_ok=True)
    httpd, port = S.serve(SITE)
    base = f"http://127.0.0.1:{port}"
    ok = 0
    try:
        for name, loc, kind in targets:
            dest = outdir / f"{name}.pdf"
            good, detail = render(chrome, base, loc, kind, dest)
            print(("  ✓ " if good else "  ✗ ") + f"{dest.name}  [{detail}]", flush=True)
            ok += 1 if good else 0
    finally:
        httpd.shutdown()

    print(f"\n导出完成：{ok}/{len(targets)} 个 PDF → {outdir}")
    return 0 if ok == len(targets) else 1


if __name__ == "__main__":
    raise SystemExit(main())
