"""Desktop browser regression checks for topic hubs and existing deep links."""
from __future__ import annotations

import html
import json
import pathlib
import re
import subprocess
import tempfile

import smoke_test as S

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

PROBE = r"""
<script>
(function () {
  var results = [], errors = [];
  window.addEventListener('error', function (event) { errors.push(event.message); });
  function ok(name, condition, detail) { results.push({name:name, pass:!!condition, detail:detail || ''}); }
  function wait(ms) { return new Promise(function (resolve) { setTimeout(resolve, ms); }); }
  async function until(test) {
    for (var i=0;i<50;i++) { if (test()) return true; await wait(100); }
    return false;
  }
  function text(selector) { var e=document.querySelector(selector); return e ? e.textContent.trim() : ''; }
  async function go(hash, heading) {
    location.hash=hash;
    await until(function () { return text('#main h1')===heading; });
  }
  async function run() {
    await until(function () { return document.querySelector('.doc'); });
    ok('原有正文首页可以打开', text('.doc-header h1')==='从这里开始');
    ok('单一重组目录，共十四个栏目', document.querySelectorAll('.nav-l1').length===14);
    ok('已移除按主题查模块', !document.querySelector('[data-nav-mode]') && !document.querySelector('.reader-topic-grid'));
    ok('首次阅读不请求全文索引', !performance.getEntriesByType('resource').some(function (r) { return r.name.indexOf('/data/index.json')>=0; }));
    ok('桌面首页无横向溢出', document.documentElement.scrollWidth<=innerWidth+1);
    await go('#/doc/book/18-内容地图','内容地图');
    ok('内容地图是独立一级章节', text('#navTree .nav-l1 > .nav-row > .nav-label')==='内容地图' && !document.querySelector('[data-nav-id="references"] a[href="#/doc/book/18-内容地图"]'));
    var mapTitles=Array.from(document.querySelectorAll('#main .doc > h2')).map(function(h){return h.textContent;});
    var navTitles=Array.from(document.querySelectorAll('.nav-l1 > .nav-row > .nav-label')).map(function(a){return a.textContent;}).slice(1);
    ok('内容地图与当前章节顺序一致', JSON.stringify(mapTitles)===JSON.stringify(navTitles));
    var mapHash=location.hash, mapHistory=history.length;
    var mapLinks=Array.from(document.querySelectorAll('#toc [data-target]'));
    mapLinks[mapLinks.length-1].click(); await wait(400);
    var right=document.querySelector('#toc a.active'), left=document.querySelector('#navTree .nav-row.active');
    ok('向后跳读时两侧目录都跟随', right && left && left.parentElement.dataset.navId==='map-section-'+right.dataset.target && right.textContent==='资料与工具');
    function inPane(pane,node) { if(!node)return false;var a=pane.getBoundingClientRect(),b=node.getBoundingClientRect();return b.top>=a.top-1 && b.bottom<=a.bottom+1; }
    ok('两侧当前项自动滚入各自可见范围', inPane(document.getElementById('toc'),right) && inPane(document.getElementById('navTree'),left));
    mapLinks[0].click(); await wait(300);
    ok('向前跳读时高亮也正确回退', text('#toc a.active')==='选择与方向' && text('#navTree .nav-row.active .nav-label')==='选择与方向');
    var middle=Array.from(document.querySelectorAll('#main .doc > h2')).find(function(h){return h.textContent==='科研与学术';});
    var readLine=document.querySelector('.topbar').getBoundingClientRect().bottom+32;
    window.scrollTo(0,window.scrollY+middle.getBoundingClientRect().top-readLine+2);
    // Virtual-time headless runs may defer the native scroll event until paint.
    window.dispatchEvent(new Event('scroll')); await wait(300);
    ok('大幅自然滚动仍能准确同步两侧', text('#toc a.active')==='科研与学术' && text('#navTree .nav-row.active .nav-label')==='科研与学术', text('#toc a.active')+' / '+text('#navTree .nav-row.active .nav-label'));
    ok('滚动联动不改地址和浏览历史', location.hash===mapHash && history.length===mapHistory);
    ok('内容地图下一篇采用新目录顺序', document.querySelector('.doc-nav [rel="next"]').getAttribute('href')==='#/guide/choices');
    await go('#/guide/library-steps','行动步骤');
    ok('行动步骤是带自然链接的完整文章', document.querySelectorAll('.reader-chapter-overview > p a').length>=15 && document.querySelectorAll('.reader-resource-list,.reader-task-list').length===0);
    ok('资料导读也有完整右侧目录', document.querySelectorAll('#toc [data-target]').length>=4);
    await go('#/guide/research','科研与学术');
    ok('一级分组有内容概览', text('#main h1')==='科研与学术');
    ok('一级概览是有独立正文的导读文章', document.querySelectorAll('.reader-chapter-overview > h2').length>=4 && Array.from(document.querySelectorAll('.reader-chapter-overview > p')).reduce(function (sum,p) { return sum+p.textContent.length; },0)>400);
    ok('概览文章保留原有正文排版和页内目录', !!document.querySelector('.reader-chapter-overview.doc .doc-header') && document.querySelectorAll('#toc [data-target]').length>=4);
    document.querySelector('#main a[href="#/guide/supervisor"]').click();
    await until(function () { return text('.doc-header h1')==='联系导师与套磁'; });
    ok('二级标题直接进入已有概览和正文', text('.doc-header h1')==='联系导师与套磁' && !document.querySelector('.reader-page-header'));
    ok('二级概览高亮所在分组而非同名叶子', document.querySelector('#navTree .nav-row.active').parentElement.dataset.navId==='supervisor');
    ok('二级没有重复概览链接', document.querySelectorAll('.nav-l2 > .nav-children > .nav-overview').length===0);
    ok('正文能汇合到模板与案例', !!document.querySelector('#main a[href*="/tools/"]') && !!document.querySelector('#main a[href*="/cases/"]'));
    document.querySelector('#navTree a[href*="research-find-supervisor"]').click();
    await until(function () { return text('.doc-header h1')==='怎么找导师'; });
    ok('具体条目使用自己的标题', text('.doc-header h1')==='怎么找导师');
    ok('只显示当前条目', Array.from(document.querySelectorAll('.entry')).filter(function (e) { return !e.hidden; }).length===1);
    // Wait for the existing sidebar expand/collapse transition to finish before
    // measuring whether reading scroll moves it.
    await wait(500);
    var sidebar=document.getElementById('navTree');
    var before=sidebar.innerHTML, top=sidebar.scrollTop, hash=location.hash, length=history.length;
    window.scrollTo(0,900); window.dispatchEvent(new Event('scroll')); await wait(200);
    ok('阅读滚动不重排或折叠目录', sidebar.innerHTML===before);
    ok('阅读滚动不移动侧栏', sidebar.scrollTop===top, top+' → '+sidebar.scrollTop);
    ok('阅读滚动不改地址和历史', location.hash===hash && history.length===length);
    ok('本页目录只指向实际可见正文', Array.from(document.querySelectorAll('#toc [data-target]')).every(function (a) { var target=document.getElementById(a.dataset.target);return target && !target.closest('[hidden]'); }));
    ok('单篇条目也能按新目录连续翻页', !!document.querySelector('.doc-nav [rel="next"]') && !!document.querySelector('.doc-nav [rel="prev"]'));
    await go('#/guide/education','升学与继续教育');
    var second=document.querySelector('[data-nav-id="graduate"]');
    var oldHash=location.hash;
    second.querySelector(':scope > .nav-row .nav-toggle').click(); await wait(100);
    ok('小箭头只展开，不跳转', location.hash===oldHash);
    second.querySelector(':scope > .nav-row .nav-label').click();
    await until(function () { return text('.doc-header h1')==='国内升学'; });
    ok('二级直接打开原有分册概览', text('.doc-header h1')==='国内升学');
    var visibleEntries=Array.from(document.querySelectorAll('.entry')).filter(function(e){return !e.hidden;});
    var later=visibleEntries[visibleEntries.length-1];
    if(later){window.scrollTo(0,window.scrollY+later.getBoundingClientRect().top-readLine+2);window.dispatchEvent(new Event('scroll'));await wait(300);}
    ok('整组正文滚动时左侧跟随当前条目', !!later && document.querySelector('#navTree .nav-row.active').parentElement.dataset.navId===later.id, (later ? later.id+' @ '+later.getBoundingClientRect().top : 'missing')+' / '+document.querySelector('#navTree .nav-row.active').parentElement.dataset.navId+' / line '+readLine);
    ok('整组正文右侧目录不随条目切换而重建', document.querySelectorAll('#toc [data-target]').length>visibleEntries.length);
    var overview=document.querySelector('[data-nav-id="education"] > .nav-children > .nav-overview a');
    ok('一级概览入口保留且有强调', overview && overview.getBoundingClientRect().height>0 && getComputedStyle(overview).fontWeight>=600);
    await go('#/guide/places','国家与地区');
    var japan=document.querySelector('#main a[href="#/guide/place-44da6bbcf2"]');
    japan.click(); await until(function () { return text('.doc-header h1')==='日本'; });
    ok('地区入口直接打开已有正文', text('.doc-header h1')==='日本');
    ok('同一地区的另一类资料可达', !!document.querySelector('#main a[href*="country-playbooks"]'));
    await go('#/guide/careers','行业与岗位');
    ok('行业与岗位分别提供入口', !!document.querySelector('#main a[href="#/guide/industries"]') && !!document.querySelector('#main a[href="#/guide/occupations"]'));
    var q=document.getElementById('q'); q.value='套磁'; q.dispatchEvent(new Event('input',{bubbles:true}));
    await until(function () { return document.querySelectorAll('.result').length>0; });
    ok('全文与同义词搜索可用', document.querySelectorAll('.result').length>0);
    location.hash='#/browse?stages=undergraduate';
    await until(function () { return text('.browse-count').indexOf('套磁')<0 && document.querySelectorAll('.result').length>0; });
    var all=document.querySelectorAll('.result').length;
    location.hash='#/browse?stages=undergraduate&effort=low';
    await until(function () { return document.querySelectorAll('.result').length<all; });
    ok('组合筛选能收窄结果', document.querySelectorAll('.result').length>0 && document.querySelectorAll('.result').length<all);
    location.hash='#/doc/book/03-升学/grad-school-worth-it';
    await until(function () { return !!document.querySelector('.is-single-entry #grad-school-worth-it'); });
    ok('已发布旧深链仍然可达', !!document.getElementById('grad-school-worth-it') && location.hash.indexOf('/book/04-')>=0);
    ok('桌面文章无横向溢出', document.documentElement.scrollWidth<=innerWidth+1);
    ok('未发生脚本异常', errors.length===0, errors.join('; '));
  }
  run().catch(function (error) { ok('浏览器流程未抛异常',false,error.message); }).finally(function () {
    var output=document.createElement('pre');output.id='reader-smoke-result';
    output.textContent='@@'+'SMOKE@@'+JSON.stringify(results)+'@@'+'END@@';document.body.appendChild(output);
  });
})();
</script>
"""


def main():
    chrome = S.find_chrome()
    if not chrome:
        print("未找到 Chrome，跳过桌面浏览器检查。")
        return 0
    source = (SITE / "index.html").read_text()
    index = json.loads((SITE / "data/index.json").read_text())
    stub = "<script>localStorage.clear();</script>"
    probe = PROBE.replace("window.__BOOK_SECTIONS__", str(len(index["nav"])))
    page = SITE / "_reader-smoke.html"
    page.write_text(source.replace("<head>", "<head>" + stub).replace("</body>", probe + "</body>"))
    server, port = S.serve(SITE)
    failures = 0
    try:
        for size in ["1440,1000", "1024,900"]:
            with tempfile.TemporaryDirectory() as profile:
                result = subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu",
                    "--disable-extensions", "--disable-background-networking", "--no-first-run",
                    "--no-default-browser-check", "--disable-smooth-scrolling", "--hide-scrollbars",
                    "--user-data-dir=" + profile, "--window-size=" + size,
                    "--virtual-time-budget=30000", "--dump-dom", f"http://127.0.0.1:{port}/{page.name}"],
                    capture_output=True, text=True, timeout=60)
            matches = re.findall(r"@@SMOKE@@(.*?)@@END@@", result.stdout, re.S)
            if not matches:
                print(size, "FAIL：浏览器未完成检查")
                failures += 1
                continue
            rows = json.loads(html.unescape(matches[-1]))
            for row in rows:
                if not row["pass"]:
                    failures += 1
                print(size, "PASS" if row["pass"] else "FAIL", row["name"], row["detail"])
    except subprocess.TimeoutExpired:
        print("桌面浏览器检查超时")
        failures += 1
    finally:
        server.shutdown()
        page.unlink(missing_ok=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
