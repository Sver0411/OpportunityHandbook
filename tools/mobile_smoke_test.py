"""Mobile reading, responsive layout and modal navigation regression checks."""
from __future__ import annotations

import html
import json
import re
import subprocess
import tempfile

import smoke_test as S

PROBE = r"""<script>
(async function () {
  var rows = [], errors = [];
  window.addEventListener('error', function (e) { errors.push(e.message); });
  function ok(name, pass, detail) { rows.push({name:name, pass:!!pass, detail:detail || ''}); }
  function wait(ms) { return new Promise(function (resolve) { setTimeout(resolve, ms || 100); }); }
  async function until(test) { for (var i=0;i<100;i++) { if(test()) return; await wait(); } throw Error('页面未就绪'); }
  function widthOK() { return document.documentElement.scrollWidth <= innerWidth + 1; }
  async function go(hash, heading) {
    location.hash=hash;
    await until(function(){ return document.querySelector('#main h1') && document.querySelector('#main h1').textContent===heading; });
    await wait(180);
  }
  try {
    await until(function(){return document.querySelector('.doc');});
    ok('浏览器使用目标屏宽',innerWidth===__EXPECTED_WIDTH__,String(innerWidth));
    var sidebar=document.getElementById('sidebar'), shell=document.getElementById('shell');
    var button=document.getElementById('navCollapse'), backdrop=document.getElementById('navBackdrop');
    ok('手机搜索框可输入且避免自动放大',getComputedStyle(document.getElementById('q')).fontSize==='16px' && document.getElementById('q').clientWidth>=innerWidth-100);
    ok('顶栏入口不换行且不互相遮挡',Array.from(document.querySelectorAll('.topnav a')).every(function(a){return a.getBoundingClientRect().height<=40 && a.getBoundingClientRect().right<=innerWidth;}));
    ok('关闭的目录不可被键盘访问',sidebar.inert && sidebar.getAttribute('aria-hidden')==='true' && button.getAttribute('aria-expanded')==='false');
    await go('#/chapter/academic','学业与学习安排');
    window.scrollTo(0,600); await wait(150);
    var position=scrollY;
    button.click(); await wait(350);
    // Virtual time does not reliably advance compositor transitions in Chrome.
    sidebar.getAnimations().forEach(function(animation){animation.finish();});
    ok('目录打开后锁定背景并保留阅读位置',getComputedStyle(document.documentElement).overflow==='hidden' && shell.inert && Math.abs(scrollY-position)<2,position+' → '+scrollY);
    ok('抽屉是模态且焦点进入关闭按钮',sidebar.getAttribute('aria-modal')==='true' && document.activeElement.id==='navClose' && !backdrop.hidden);
    ok('抽屉在手机可视范围内',sidebar.getBoundingClientRect().left>=-1 && sidebar.getBoundingClientRect().right<=innerWidth && sidebar.getBoundingClientRect().height<=innerHeight+1,JSON.stringify(sidebar.getBoundingClientRect().toJSON()));
    var controls=Array.from(sidebar.querySelectorAll('a[href],button')).filter(function(n){return n.getClientRects().length && getComputedStyle(n).visibility==='visible';});
    controls[controls.length-1].focus();document.dispatchEvent(new KeyboardEvent('keydown',{key:'Tab',bubbles:true,cancelable:true}));
    ok('键盘焦点留在抽屉内',document.activeElement===controls[0]);
    backdrop.click();await wait(350);
    ok('遮罩可关闭并恢复焦点与阅读位置',sidebar.inert && !shell.inert && backdrop.hidden && document.activeElement===button && Math.abs(scrollY-position)<2);
    button.click();await wait(350);
    document.querySelector('[data-nav-id="academic"] .nav-item .nav-label').click();await wait(350);
    ok('点击三级目录保留整章并自动关闭',!document.body.classList.contains('sidebar-open') && document.querySelectorAll('.reader-chapter-section').length>1 && !shell.inert);
    button.click();await wait(350);document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));
    ok('Escape 能关闭目录',!document.body.classList.contains('sidebar-open'));
    ok('连续正文无横向溢出',widthOK());
    await go('#/doc/book/18-内容地图','内容地图');
    var table=document.querySelector('.table-wrap');
    ok('宽表格可在容器内横向滚动',table.scrollWidth>table.clientWidth || innerWidth>=600);
    if(table.scrollWidth>table.clientWidth) { table.scrollLeft=100; ok('表格可实际滑动',table.scrollLeft>0); }
    ok('内容地图不撑宽页面',widthOK());
    await go('#/guide/choices','选择与方向');ok('一级概览不溢出',widthOK());
    await go('#/guide/reference-library','资料与工具');ok('资料库概览不溢出',widthOK());
    await go('#/browse?q=套磁','按条件筛选');await until(function(){return document.querySelector('.result');});
    ok('手机搜索与筛选可用且不溢出',widthOK() && document.querySelectorAll('.result').length>0);
    ok('手机页面无脚本错误',errors.length===0,errors.join('; '));
  } catch(e) { ok('移动阅读流程完成',false,e.message); }
  var result=document.createElement('pre');result.textContent='@@'+'MOBILE@@'+JSON.stringify(rows)+'@@'+'END@@';document.body.appendChild(result);
  parent.postMessage({source:'mobile-smoke',rows:rows},location.origin);
})();</script>"""


def main() -> int:
    chrome = S.find_chrome()
    if not chrome:
        print("未找到 Chrome，跳过移动端浏览器检查。")
        return 0
    page = S.SITE / "_mobile-smoke.html"
    frame = S.SITE / "_mobile-smoke-frame.html"
    source = (S.SITE / "index.html").read_text()
    server, port = S.serve(S.SITE)
    failures = 0
    try:
        for size in ("320,740", "390,844", "768,1024"):
            probe = PROBE.replace("__EXPECTED_WIDTH__", size.split(",")[0])
            page.write_text(source.replace("<head>", "<head><script>localStorage.clear();</script>").replace("</body>", probe + "</body>"))
            width, height = size.split(",")
            # Chrome's macOS window has a 500px minimum. A real child viewport
            # tests the requested CSS/media width without scaling or spoofing it.
            frame.write_text(f'''<!doctype html><html><body style="margin:0">
<iframe src="{page.name}" width="{width}" height="{height}" style="border:0"></iframe>
<script>addEventListener('message',function(e){{
if(e.origin===location.origin && e.data.source==='mobile-smoke'){{
var p=document.createElement('pre');p.textContent='@@'+'MOBILE@@'+JSON.stringify(e.data.rows)+'@@'+'END@@';document.body.appendChild(p);
}}}});</script></body></html>''')
            with tempfile.TemporaryDirectory() as profile:
                result = subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu",
                    "--disable-extensions", "--disable-background-networking", "--no-first-run",
                    "--no-default-browser-check", "--disable-smooth-scrolling", "--hide-scrollbars",
                    "--user-data-dir=" + profile, "--window-size=" + size,
                    "--virtual-time-budget=30000", "--dump-dom", f"http://127.0.0.1:{port}/{frame.name}"],
                    capture_output=True, text=True, timeout=60)
            matches = re.findall(r"@@MOBILE@@(.*?)@@END@@", result.stdout, re.S)
            if not matches:
                print(size, "FAIL 浏览器未完成移动端检查")
                failures += 1
                continue
            for row in json.loads(html.unescape(matches[-1])):
                failures += not row["pass"]
                print(size, "PASS" if row["pass"] else "FAIL", row["name"], row["detail"])
    except subprocess.TimeoutExpired:
        print("移动端浏览器检查超时")
        failures += 1
    finally:
        server.shutdown()
        page.unlink(missing_ok=True)
        frame.unlink(missing_ok=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
