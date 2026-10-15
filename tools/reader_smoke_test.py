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
  var results=[], errors=[];
  window.addEventListener('error',function(e){errors.push(e.message);});
  function ok(name,value,detail){results.push({name:name,pass:!!value,detail:detail||''});}
  function wait(ms){return new Promise(function(resolve){setTimeout(resolve,ms);});}
  async function until(test){for(var i=0;i<80;i++){if(test())return true;await wait(100);}return false;}
  function text(s){var e=document.querySelector(s);return e?e.textContent.trim():'';}
  function active(){var r=document.querySelector('#navTree .nav-row.active');return r?r.parentElement.dataset.navId:'';}
  function sections(){return Array.from(document.querySelectorAll('.reader-chapter-section'));}
  function inPane(pane,node){if(!node)return false;var a=pane.getBoundingClientRect(),b=node.getBoundingClientRect();return b.top>=a.top-1&&b.bottom<=a.bottom+1;}
  function scrollToNode(node){var line=document.querySelector('.topbar').getBoundingClientRect().bottom+32;window.scrollTo(0,scrollY+node.getBoundingClientRect().top-line+3);window.dispatchEvent(new Event('scroll'));}
  async function go(hash,heading){location.hash=hash;await until(function(){return text('#main h1')===heading;});await wait(180);}
  async function run(){
    await until(function(){return document.querySelector('.doc');});
    ok('原有首页保留',text('#main h1')==='从这里开始');
    ok('一级目录保持十四个栏目',document.querySelectorAll('.nav-l1').length===14);
    var navIds=Array.from(document.querySelectorAll('.nav-item')).map(function(n){return n.dataset.navId;});
    ok('正文与资料库的导航标识不再互相冲突',navIds.length===new Set(navIds).size);
    ok('初次阅读不加载全文搜索索引',!performance.getEntriesByType('resource').some(function(r){return r.name.indexOf('/data/index.json')>=0;}));
    await go('#/doc/book/18-内容地图','内容地图');
    var mapLinks=Array.from(document.querySelectorAll('#toc a'));
    mapLinks[mapLinks.length-1].click();await wait(220);
    ok('内容地图两侧仍然同步',text('#toc a.active')==='资料与工具'&&active()==='map-section-'+document.querySelector('#toc a.active').dataset.target);
    await go('#/chapter/academic','学业与学习安排');
    ok('二级章节先显示现有概览',!!document.querySelector('.reader-chapter-intro p')&&text('.reader-chapter-intro').indexOf('课要学到什么程度')>=0);
    var academic=sections(),article=document.querySelector('.reader-assembled-chapter');
    ok('打开二级标题会展开全部三级目录',document.querySelector('[data-nav-id="academic"]').classList.contains('open')&&getComputedStyle(document.querySelector('[data-nav-id="academic"] .nav-children .nav-label')).visibility==='visible');
    var menu=Array.from(document.querySelectorAll('[data-nav-id="academic"] .nav-item')).filter(function(n){return !n.querySelector(':scope > .nav-children');}).map(function(n){return n.dataset.navId;});
    ok('整章包含二级下全部三级正文且顺序相同',academic.length===menu.length&&JSON.stringify(academic.map(function(n){return n.dataset.navId;}))===JSON.stringify(menu));
    ok('合并只包含本组正文',!!document.getElementById('gpa-matters')&&!document.getElementById('digital-online-identity'));
    var last=academic[academic.length-1],rightTree=document.querySelector('#toc .toc-list');
    var hash=location.hash,historyLength=history.length;
    scrollToNode(last);await wait(250);
    ok('下滚时左侧高亮当前三级条目',active()===last.dataset.navId,active());
    ok('右侧跟随且将当前小节滚入可见范围',inPane(document.getElementById('toc'),document.querySelector('#toc a.active')));
    scrollToNode(academic[0]);await wait(250);
    ok('向前回滚时高亮也正确回退',active()===academic[0].dataset.navId);
    ok('自然滚动不重建目录或增加历史',rightTree===document.querySelector('#toc .toc-list')&&location.hash===hash&&history.length===historyLength);
    document.querySelector('[data-nav-id="academic"] [data-nav-id="'+last.dataset.navId+'"] > .nav-row > .nav-label').click();await wait(250);
    ok('点击三级标题在同一整章定位',document.querySelector('.reader-assembled-chapter')===article&&sections().length===academic.length&&active()===last.dataset.navId);
    await go('#/guide/supervisor','导师与实验室');
    ok('跨文件的二级内容确实合并而非只打开第一篇',sections().length===8&&!!document.getElementById('research-find-supervisor')&&!!document.getElementById('tool-contacting-supervisor-email')&&!!document.getElementById('depth-case-联系导师'));
    ok('模板与案例显示的是完整正文',document.getElementById('tool-contacting-supervisor-email').querySelectorAll('p,li,pre').length>3&&document.getElementById('depth-case-联系导师').querySelectorAll('p,li').length>3);
    ok('整章翻页不再逐个重复打开三级单篇',document.querySelector('.doc-nav [rel="next"]').getAttribute('href')==='#/chapter/literature');
    await go('#/guide/reference-library','资料与工具');
    await go('#/guide/library-tool','工具与模板');
    document.querySelector('[data-nav-id="library-tool--tool-contacting-supervisor-email"] > .nav-row > .nav-label').click();
    await until(function(){return text('#main h1')==='联系导师邮件模板';});await wait(200);
    ok('资料与工具中同一模板仍单独打开',!document.querySelector('.reader-assembled-chapter')&&text('#main h1')==='联系导师邮件模板'&&!document.getElementById('research-find-supervisor'));
    ok('资料库高亮留在资料库而不跳到正文',active()==='library-tool--tool-contacting-supervisor-email',active());
    await go('#/doc/docs/tools/联系导师邮件模板','导师与实验室');
    ok('正文中的同一篇链接进入完整二级章节',sections().length===8&&active()==='tool-contacting-supervisor-email');
    await go('#/guide/library-risk','风险与核实');
    var risk=document.querySelector('[data-nav-id="library-risk"] > .nav-children > .nav-item > .nav-row > .nav-label');
    risk.click();await until(function(){return document.querySelector('.is-single-entry');});await wait(200);
    ok('资料库中的风险条目也保持独立单篇',!!document.querySelector('.is-single-entry')&&Array.from(document.querySelectorAll('.entry')).filter(function(e){return !e.hidden;}).length===1);
    ok('独立条目滚动不会串到正文高亮',active().indexOf('library-risk--')===0);
    await go('#/chapter/graduate','国内读研');
    ok('存在下一级分组时全部正文也在当前章',sections().length===24&&!!document.getElementById('chapter-kaoyan'));
    var graduate=document.querySelector('.reader-assembled-chapter');
    document.querySelector('[data-nav-id="kaoyan"] > .nav-row > .nav-label').click();await wait(250);
    ok('嵌套分组在整章内定位',document.querySelector('.reader-assembled-chapter')===graduate&&active()==='kaoyan');
    await go('#/guide/place-44da6bbcf2','日本');
    ok('同一地区两份现有正文连续阅读',sections().length===2&&sections()[0].querySelectorAll('p,li').length>3&&sections()[1].querySelectorAll('p,li').length>3);
    await go('#/doc/book/03-升学/grad-school-worth-it','国内读研');
    ok('旧深链仍然定位到整章中的原条目',!!document.getElementById('grad-school-worth-it')&&location.hash.indexOf('/chapter/graduate')>=0&&sections().length===24);
    var ids=Array.from(document.querySelectorAll('#main [id]')).map(function(n){return n.id;});
    ok('整章合并后的锚点没有重复',ids.length===new Set(ids).size);
    var q=document.getElementById('q');q.value='套磁';q.dispatchEvent(new Event('input',{bubbles:true}));
    await until(function(){return document.querySelectorAll('.result').length>0;});
    ok('全文搜索仍可用',document.querySelectorAll('.result').length>0);
    ok('桌面无横向溢出',document.documentElement.scrollWidth<=innerWidth+1);
    ok('浏览器未出现脚本错误',errors.length===0,errors.join('; '));
  }
  run().catch(function(e){ok('浏览器流程完成',false,e.message);}).finally(function(){var p=document.createElement('pre');p.id='reader-smoke-result';p.textContent='@@'+'SMOKE@@'+JSON.stringify(results)+'@@'+'END@@';document.body.appendChild(p);});
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
