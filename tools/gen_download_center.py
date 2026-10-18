#!/usr/bin/env python3
"""从 downloads/manifest.json 生成「模板与下载中心」静态页。

输出 site/downloads/index.html：服务端渲染全部卡片（无 JS 也能看），
再叠一层纯 JS 的筛选（场景、格式、关键词），不引入任何依赖。
"""

from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SCENE_ORDER = ["新生入学", "奖助学金", "学习与科研", "毕业论文与毕业设计",
               "实习与求职", "毕业离校", "学籍与申诉", "防骗与权益保障"]


def human(n: int) -> str:
    if n >= 1024 * 1024:
        return f"{n / 1024 / 1024:.1f} MB"
    return f"{max(1, round(n / 1024))} KB"


def route_for(rel: str) -> str:
    return "../#/doc/" + rel[:-3] if rel.endswith(".md") else "../#/doc/" + rel


def build() -> tuple[int, str]:
    manifest = json.loads((ROOT / "downloads" / "manifest.json").read_text(encoding="utf-8"))
    items = manifest["items"]
    scenes = [s for s in SCENE_ORDER if any(i["scene"] == s for i in items)]
    scenes += sorted({i["scene"] for i in items} - set(scenes))
    formats = sorted({i["format"] for i in items})

    def card(it: dict) -> str:
        path = ROOT / it["path"]
        size = human(path.stat().st_size) if path.exists() else ""
        fmt = it["format"].upper()
        return f"""
      <li class="res-row" data-scene="{html.escape(it['scene'])}" data-format="{html.escape(it['format'])}"
          data-text="{html.escape((it['title'] + ' ' + it['desc'] + ' ' + it['scene'] + ' ' + it['audience']).lower())}">
        <a class="res-main" href="../{html.escape(it['path'])}" download>
          <span class="res-fmt">{fmt}</span>
          <span class="res-body">
            <span class="res-name">{html.escape(it['title'])}</span>
            <span class="res-desc">{html.escape(it['desc'])}</span>
            <span class="res-meta">{html.escape(it['scene'])} ｜ {html.escape(it['audience'])} ｜ {size} ｜ 更新 {html.escape(it['updated'])}</span>
          </span>
        </a>
        <a class="res-art" href="{html.escape(route_for(it['article']))}">对应文章 →</a>
      </li>"""

    grouped = []
    for scene in scenes:
        rows = "".join(card(i) for i in items if i["scene"] == scene)
        grouped.append(f"""
    <section class="res-group" data-group="{html.escape(scene)}">
      <h2>{html.escape(scene)} <span class="res-count">{sum(1 for i in items if i['scene'] == scene)}</span></h2>
      <ul class="res-list">{rows}</ul>
    </section>""")

    chips = "".join(
        f'<button class="chip-btn" type="button" data-filter="scene" data-value="{html.escape(s)}">{html.escape(s)}</button>'
        for s in scenes)
    fmt_chips = "".join(
        f'<button class="chip-btn" type="button" data-filter="format" data-value="{html.escape(f)}">{f.upper()}</button>'
        for f in formats)

    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>模板与下载中心｜机会手册</title>
<meta name="description" content="新生入学、奖助学金、毕业论文、实习求职、毕业离校、学籍申诉的清单与模板，可直接下载 PDF、DOCX、XLSX。">
<link rel="stylesheet" href="../styles.css">
<style>
.dl-head {{ max-width: 1080px; margin: 0 auto; padding: 40px 20px 8px; }}
.dl-head h1 {{ font-size: 26px; margin: 0 0 10px; }}
.dl-head p {{ color: var(--muted); font-size: 14px; line-height: 1.75; margin: 0 0 6px; max-width: 46em; }}
.dl-tools {{ max-width: 1080px; margin: 18px auto 6px; padding: 0 20px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
.dl-search {{ flex: 1 1 240px; min-width: 200px; font: inherit; font-size: 14px; padding: 8px 12px;
  border: 1px solid var(--line); border-radius: 8px; background: #fff; }}
.chip-btn {{ font: inherit; font-size: 12.5px; padding: 4px 11px; border-radius: 999px;
  border: 1px solid var(--line); background: #fff; color: var(--ink-2); cursor: pointer; }}
.chip-btn[aria-pressed="true"] {{ background: var(--surface-2); border-color: transparent; color: var(--ink); }}
.dl-body {{ max-width: 1080px; margin: 0 auto; padding: 8px 20px 64px; }}
.res-group h2 {{ font-size: 16px; margin: 28px 0 10px; display: flex; align-items: baseline; gap: 8px; }}
.res-count {{ font-size: 12px; color: var(--muted); font-weight: 400; }}
.res-list {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }}
.res-row {{ display: flex; align-items: stretch; gap: 8px; border: 1px solid var(--line);
  border-radius: 10px; background: #fff; }}
.res-row[hidden] {{ display: none; }}
.res-main {{ flex: 1 1 auto; display: flex; gap: 12px; padding: 12px 14px; text-decoration: none; min-width: 0; }}
.res-main:hover {{ background: var(--surface-2); }}
.res-fmt {{ flex: 0 0 auto; align-self: flex-start; min-width: 46px; text-align: center;
  font-size: 11px; color: var(--muted); border: 1px solid var(--line); border-radius: 5px; padding: 3px 0; }}
.res-body {{ display: flex; flex-direction: column; gap: 3px; min-width: 0; }}
.res-name {{ font-size: 14.5px; color: var(--ink); }}
.res-desc {{ font-size: 13px; color: var(--ink-2); line-height: 1.6; }}
.res-meta {{ font-size: 11.5px; color: var(--muted); }}
.res-art {{ flex: 0 0 auto; align-self: center; padding: 0 14px; font-size: 12.5px;
  color: var(--ink-2); text-decoration: none; white-space: nowrap; }}
.res-art:hover {{ color: var(--ink); text-decoration: underline; }}
.dl-empty {{ display: none; padding: 40px 0; color: var(--muted); font-size: 14px; }}
.dl-note {{ font-size: 12.5px; color: var(--muted); line-height: 1.7; margin-top: 28px;
  border-top: 1px solid var(--line); padding-top: 14px; }}
@media (max-width: 640px) {{
  .res-row {{ flex-direction: column; }}
  .res-art {{ align-self: flex-start; padding: 0 14px 12px; }}
}}
</style>
</head>
<body>
<header class="dl-head">
  <p><a href="../">← 回到《机会手册》</a></p>
  <h1>模板与下载中心</h1>
  <p>这里放的是能直接用的东西：打印出来逐项勾的清单、可以自己填的记录表、会自动算数的进度表。</p>
  <p>共 {len(items)} 个文件，全部来自正文里已有的条目；具体金额、日期与政策以学校或官方当年通知为准。</p>
</header>

<div class="dl-tools">
  <input class="dl-search" id="dlSearch" type="search" placeholder="搜索：新生、毕设、实习、申诉……" aria-label="搜索资源">
  <button class="chip-btn" type="button" data-filter="reset">全部</button>
  {chips}
  {fmt_chips}
</div>

<main class="dl-body">
  <p class="dl-empty" id="dlEmpty">没有匹配的资源，换个关键词试试。</p>
  {"".join(grouped)}
  <p class="dl-note">文件由 <code>tools/gen_downloads.py</code> 从结构化内容生成，清单见
  <code>downloads/manifest.json</code>。发现内容与正文不一致，请在 GitHub 提 issue。</p>
</main>

<script>
(function () {{
  var search = document.getElementById("dlSearch");
  var empty = document.getElementById("dlEmpty");
  var rows = Array.prototype.slice.call(document.querySelectorAll(".res-row"));
  var groups = Array.prototype.slice.call(document.querySelectorAll(".res-group"));
  var chips = Array.prototype.slice.call(document.querySelectorAll(".chip-btn"));
  var state = {{ scene: "", format: "", q: "" }};

  function apply() {{
    var shown = 0;
    rows.forEach(function (row) {{
      var okScene = !state.scene || row.dataset.scene === state.scene;
      var okFormat = !state.format || row.dataset.format === state.format;
      var okText = !state.q || row.dataset.text.indexOf(state.q) !== -1;
      var show = okScene && okFormat && okText;
      row.hidden = !show;
      if (show) shown++;
    }});
    groups.forEach(function (g) {{
      g.hidden = !g.querySelector(".res-row:not([hidden])");
    }});
    empty.style.display = shown ? "none" : "block";
  }}

  chips.forEach(function (btn) {{
    btn.addEventListener("click", function () {{
      var f = btn.dataset.filter;
      if (f === "reset") {{ state.scene = ""; state.format = ""; }}
      else if (f === "scene") {{ state.scene = state.scene === btn.dataset.value ? "" : btn.dataset.value; }}
      else {{ state.format = state.format === btn.dataset.value ? "" : btn.dataset.value; }}
      chips.forEach(function (b) {{
        var on = (b.dataset.filter === "scene" && b.dataset.value === state.scene) ||
                 (b.dataset.filter === "format" && b.dataset.value === state.format) ||
                 (b.dataset.filter === "reset" && !state.scene && !state.format);
        b.setAttribute("aria-pressed", on ? "true" : "false");
      }});
      apply();
    }});
  }});

  search.addEventListener("input", function () {{
    state.q = search.value.trim().toLowerCase();
    apply();
  }});
}})();
</script>
</body>
</html>
"""
    out = ROOT / "site" / "downloads" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")

    # 自检：页面在 /downloads/ 下，相对链接必须能落到真实文件上。
    # 这里按「输出文件所在目录」解析每个 href/src，缺文件直接报错，
    # 避免再出现 /downloads/downloads/... 这种 404。
    import re
    bad = []
    for attr in re.findall(r'(?:href|src)="([^"#?]+)"', doc):
        if attr.startswith(("http://", "https://", "//", "mailto:")):
            continue
        target = (out.parent / attr).resolve()
        if not target.exists():
            bad.append(attr)
    if bad:
        raise ValueError("下载中心存在无法解析的链接：" + ", ".join(sorted(set(bad))[:5]))
    return len(items), str(out.relative_to(ROOT))


if __name__ == "__main__":
    n, path = build()
    print(f"下载中心：{n} 个资源 → {path}")
