/* 机会与成长指南 · 静态阅读页
   无框架、无后端：读取 data/index.json 与 content/**.html，hash 路由，客户端搜索与筛选。

   目录是一棵「一级分组 → 二级分组 → 文档 → 条目」的树，节点可逐级展开；
   左侧目录固定在窗口最左侧，可以整体折叠（选择记在 localStorage）。 */

(function () {
  "use strict";

  var MOBILE = "(max-width: 900px)";
  var NAV_KEY = "oh.nav";
  var EXPAND_KEY = "oh.nav.expanded";

  var state = {
    index: null,
    locations: [],      // 按长度倒序的 location 列表，用于最长前缀匹配
    byLocation: {},     // location -> 目录项
    homeLocation: "",
    flat: [],           // 文档顺序（用于上一页/下一页）
    cache: {},
    entries: [],
    aliases: {},        // 搜索同义词表（search_aliases.json）
    showAdvanced: false, // 筛选页是否展开高级条件
    expanded: {},       // 展开过的节点 key
    params: new URLSearchParams()
  };

  var main = document.getElementById("main");
  var navTree = document.getElementById("navTree");
  var tocEl = document.getElementById("toc");
  var sidebar = document.getElementById("sidebar");
  var input = document.getElementById("q");
  var searchForm = document.getElementById("searchForm");
  var collapseBtn = document.getElementById("navCollapse");
  var closeBtn = document.getElementById("navClose");

  // ------------------------------------------------------------ 工具

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (k === "class") node.className = attrs[k];
        else if (k === "text") node.textContent = attrs[k];
        else if (k === "html") node.innerHTML = attrs[k];
        else if (k.indexOf("on") === 0) node.addEventListener(k.slice(2), attrs[k]);
        else if (attrs[k] !== null && attrs[k] !== undefined && attrs[k] !== "") node.setAttribute(k, attrs[k]);
      });
    }
    (children || []).forEach(function (c) { if (c) node.appendChild(c); });
    return node;
  }

  function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

  function isMobile() { return window.matchMedia(MOBILE).matches; }

  function parseHash() {
    var raw = (location.hash || "").replace(/^#/, "");
    if (!raw || raw === "/") return { parts: [], params: new URLSearchParams() };
    var qi = raw.indexOf("?");
    var path = qi >= 0 ? raw.slice(0, qi) : raw;
    var query = qi >= 0 ? raw.slice(qi + 1) : "";
    var parts = path.split("/").filter(Boolean).map(decodeURIComponent);
    return { parts: parts, params: new URLSearchParams(query) };
  }

  function buildHash(parts, params) {
    var s = "#/" + parts.map(encodeURIComponent).join("/");
    var qs = params && params.toString();
    return qs ? s + "?" + qs : s;
  }

  function toggleInList(params, key, value) {
    var list = (params.get(key) || "").split(",").filter(Boolean);
    var i = list.indexOf(value);
    if (i >= 0) list.splice(i, 1); else list.push(value);
    if (list.length) params.set(key, list.join(",")); else params.delete(key);
    return params;
  }

  function store(key, value) {
    try { if (value === null) localStorage.removeItem(key); else localStorage.setItem(key, value); } catch (e) {}
  }
  function read(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }

  // ------------------------------------------------------------ 数据准备

  function labelMap(facet) {
    var m = {};
    ((state.index.facets[facet] || {}).values || []).forEach(function (v) { m[v.key] = v.label; });
    return m;
  }

  function firstHref(node) {
    if (node.href) return node.href;
    var kids = node.children || [];
    for (var i = 0; i < kids.length; i++) {
      var h = firstHref(kids[i]);
      if (h) return h;
    }
    return "";
  }

  function prepare() {
    var idx = state.index;
    var docMeta = {};
    // all_docs 含 planned：只用于路由解析与元数据，保证旧深链不失效
    (idx.all_docs || idx.docs || []).forEach(function (d) { docMeta[d.location] = d; });

    function locOf(href) {
      var raw = String(href || "").replace(/^#\/doc\//, "");
      if (!raw) return "";
      var best = "";
      for (var i = 0; i < state.locations.length; i++) {
        var loc = state.locations[i];
        if (raw === loc || raw.indexOf(loc + "/") === 0) return loc;
      }
      return best;
    }

    // 路由表：所有文档（含 planned）都能被深链打开
    Object.keys(docMeta).forEach(function (loc) {
      var m = docMeta[loc];
      state.byLocation[loc] = {
        title: m.title, location: loc, route: m.route || ("#/doc/" + loc),
        last_verified: m.last_verified || "", status: m.status || ""
      };
    });
    state.locations = Object.keys(state.byLocation).sort(function (a, b) { return b.length - a.length; });

    // 阅读序列（上一页/下一页）：只含用户可读的文档，planned 不参与
    var seen = {};
    (function walk(nodes) {
      (nodes || []).forEach(function (n) {
        var loc = locOf(n.href);
        if (loc && !seen[loc] && state.byLocation[loc]) {
          seen[loc] = 1;
          state.flat.push(state.byLocation[loc]);
        }
        walk(n.children);
      });
    })(idx.nav);
    (idx.docs || []).forEach(function (d) {
      if (!seen[d.location] && state.byLocation[d.location]) {
        seen[d.location] = 1;
        state.flat.push(state.byLocation[d.location]);
      }
    });

    var home = state.flat.filter(function (i) { return i.location.indexOf("00-") >= 0; })[0];
    state.homeLocation = home ? home.location : (state.flat[0] || {}).location;

    var L = {
      stages: labelMap("stages"), topics: labelMap("topics"),
      outputs: labelMap("outputs"), effort: labelMap("effort"), evidence: labelMap("evidence")
    };
    state.labels = L;
    var evidenceEn = {};
    (((idx.facets || {}).evidence || {}).values || []).forEach(function (v) { evidenceEn[v.key] = v.en || ""; });
    state.entries = idx.entries.map(function (e) {
      var tags = []
        .concat(e.stages.map(function (v) { return L.stages[v] || v; }))
        .concat(e.topics.map(function (v) { return L.topics[v] || v; }))
        .concat(e.outputs.map(function (v) { return L.outputs[v] || v; }))
        .concat(e.evidence.map(function (v) { return L.evidence[v] || v; }))
        .concat(e.evidence.map(function (v) { return evidenceEn[v] || ""; }));
      var hay = [e.title, e.summary, e.text, e.doc_title, tags.join(" ")].join(" ").toLowerCase();
      return Object.assign({}, e, { _hay: hay, _title: e.title.toLowerCase(), _tags: tags });
    });

    var saved = read(EXPAND_KEY);
    if (saved) {
      try { state.expanded = JSON.parse(saved) || {}; } catch (e) { state.expanded = {}; }
    }
  }

  // ------------------------------------------------------------ 左侧目录树

  var DEPTH_CLASS = ["nav-l1", "nav-l2", "nav-l3", "nav-l4", "nav-l5"];

  function renderNode(node, depth, parentKey) {
    var key = parentKey + " / " + node.label;
    var kids = node.children || [];
    var li = el("li", { class: "nav-item " + (DEPTH_CLASS[depth] || "nav-l5") });
    li.dataset.key = key;

    var row = el("div", { class: "nav-row" });
    row.dataset.kind = node.kind || "";
    if (kids.length) {
      var btn = el("button", {
        class: "nav-toggle", type: "button",
        "aria-expanded": "false", "aria-label": "展开或收起 " + node.label
      });
      btn.addEventListener("click", function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        setOpen(li, !li.classList.contains("open"));
      });
      row.appendChild(btn);
    } else {
      row.appendChild(el("span", { class: "nav-dot" }));
    }

    var href = node.href || (node.kind === "entry" ? "" : firstHref(node));
    if (href) {
      var link = el("a", { class: "nav-label", href: href, text: node.label, title: node.label });
      if (kids.length) {
        // 分组行：点标题进入该组对应章节，同时确保展开
        link.addEventListener("click", function () { setOpen(li, true); });
      }
      row.appendChild(link);
    } else if (kids.length) {
      // 无对应章节的分组行：点标题即展开/收起（整行可点，不必瞄准小箭头）
      var groupLabel = el("span", { class: "nav-label static clickable", text: node.label, title: node.label });
      groupLabel.addEventListener("click", function () {
        setOpen(li, !li.classList.contains("open"));
      });
      row.appendChild(groupLabel);
    } else {
      row.appendChild(el("span", { class: "nav-label static", text: node.label }));
    }
    // 计数只出现在有子节点的分组行上，叶子条目不显示，避免右侧数字成排噪点
    if (node.count && kids.length) {
      row.appendChild(el("span", {
        class: "nav-count", text: String(node.count),
        title: "这一组里已写完 " + node.count + " 条"
      }));
    }
    li.appendChild(row);

    if (kids.length) {
      var ul = el("ul", { class: "nav-children" });
      kids.forEach(function (c) { ul.appendChild(renderNode(c, depth + 1, key)); });
      li.appendChild(ul);
    }
    if (state.expanded[key]) setOpen(li, true, true);
    return li;
  }

  function setOpen(li, open, silent) {
    li.classList.toggle("open", open);
    var btn = li.querySelector(":scope > .nav-row > .nav-toggle");
    if (btn) btn.setAttribute("aria-expanded", open ? "true" : "false");
    if (!silent) {
      if (open) state.expanded[li.dataset.key] = 1; else delete state.expanded[li.dataset.key];
      store(EXPAND_KEY, JSON.stringify(state.expanded));
    }
  }

  function buildNav() {
    // 首屏挂载时先关掉过渡，避免恢复上次展开状态时目录"抽"一下
    navTree.classList.add("no-anim");
    clear(navTree);
    state.index.nav.forEach(function (node) {
      var ul = el("ul", { class: "nav-group-block" });
      ul.appendChild(renderNode(node, 0, ""));
      navTree.appendChild(ul);
    });
    // 侧栏只放全书目录；「按条件筛选」入口统一由顶栏提供，避免同一界面多处重复
    requestAnimationFrame(function () {
      requestAnimationFrame(function () { navTree.classList.remove("no-anim"); });
    });
  }

  // 节点类型优先级：越精确越优先，保证同一时刻只高亮一行
  var KIND_PRIORITY = { entry: 5, doc: 4, section: 3, group: 2, subsection: 2 };

  function markActive(hash) {
    var rows = Array.prototype.slice.call(navTree.querySelectorAll(".nav-row"));
    rows.forEach(function (r) { r.classList.remove("active"); });

    function pick(want) {
      var best = null, bestScore = -1;
      rows.forEach(function (r) {
        var a = r.querySelector("a.nav-label");
        if (!a || a.getAttribute("href") !== want) return;
        var score = KIND_PRIORITY[r.dataset.kind] || 1;
        if (score > bestScore) { bestScore = score; best = r; }
      });
      return best;
    }

    function pickPrefix(want) {
      if (!want) return null;
      var best = null, bestScore = -1;
      rows.forEach(function (r) {
        var a = r.querySelector("a.nav-label");
        if (!a) return;
        var href = a.getAttribute("href") || "";
        if (href !== want && href.indexOf(want + "/") !== 0) return;
        var score = KIND_PRIORITY[r.dataset.kind] || 1;
        if (score > bestScore) { bestScore = score; best = r; }
      });
      return best;
    }

    // 章节页里 section 与它下面所有分组指向同一个 href，必须只留一行，
    // 否则一次会点亮好几行（看起来像随机变灰）
    var hit = pick(hash);
    if (!hit) {
      // 分组锚点可能指向更深的位置：先按前缀匹配（例如 #/doc/book/03-升学/本科-硕士）
      var prefix = hash.replace(/\/[^/]*$/, "");
      hit = pick(prefix);
    }
    if (!hit) {
      // 再退一步：匹配所属文档（保证章节页至少高亮它的领域）
      var raw = hash.replace(/^#\/doc\//, "");
      var parts = raw.split("/");
      for (var depth = parts.length; depth > 1 && !hit; depth--) {
        hit = pick("#/doc/" + parts.slice(0, depth - 1).join("/"));
        if (!hit) hit = pickPrefix("#/doc/" + parts.slice(0, depth - 1).join("/"));
      }
    }
    if (!hit) hit = pickPrefix(hash);
    if (!hit) return;
    hit.classList.add("active");

    var li = hit.closest(".nav-item");
    while (li) {
      setOpen(li, true);
      var up = li.parentElement ? li.parentElement.closest(".nav-item") : null;
      li = up;
    }
    var box = sidebar;
    var top = hit.getBoundingClientRect().top - box.getBoundingClientRect().top + box.scrollTop;
    if (top < box.scrollTop || top > box.scrollTop + box.clientHeight - 70) {
      box.scrollTop = Math.max(0, top - box.clientHeight / 2);
    }
  }

  // ------------------------------------------------------------ 文档视图

  function fetchContent(location) {
    if (state.cache[location]) return Promise.resolve(state.cache[location]);
    return fetch("content/" + location.split("/").map(encodeURIComponent).join("/") + ".html")
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.text();
      })
      .then(function (html) { state.cache[location] = html; return html; });
  }

  function renderDoc(location, entryId) {
    var item = state.byLocation[location];
    markActive("#/doc/" + location + (entryId ? "/" + entryId : ""));
    document.title = (item ? item.title : "机会与成长指南") + " · 机会与成长指南";

    return fetchContent(location).then(function (html) {
      main.innerHTML = html;
      var article = main.querySelector(".doc");
      var header = article.querySelector(".doc-header");
      if (item && item.last_verified && item.last_verified < state.index.stale_threshold) {
        article.insertBefore(el("p", { class: "notice", text:
          "本页最后核实于 " + item.last_verified + "，已经超过 12 个月，其中的制度性信息可能需要重新核实。" }),
          header.nextSibling);
      }
      buildToc();
      buildDocNav(location);
      focusTarget(entryId);
    }).catch(function (err) {
      clear(main);
      main.appendChild(el("p", { class: "empty", text: "内容加载失败（" + err.message + "）。如果是在本地打开，请用 http 方式访问，例如：python3 -m http.server 8000 --directory site" }));
      clear(tocEl);
    });
  }

  function buildToc() {
    clear(tocEl);
    var heads = main.querySelectorAll(".doc h2, .entry > h3");
    if (!heads.length) return;
    var list = el("ul", { class: "toc-list" });
    var links = [];
    Array.prototype.forEach.call(heads, function (h) {
      var id = h.id || "";
      // 条目标题没有自己的 id，就退到所属条目的锚点，保证点了能跳
      var target = id ? main.querySelector("#" + CSS.escape(id)) : h.closest(".entry");
      var a = el("a", { href: "#", text: h.textContent, "data-target": id });
      a.addEventListener("click", function (ev) {
        ev.preventDefault();
        (target || h).scrollIntoView({ block: "start" });
      });
      links.push({ link: a, node: target || h });
      list.appendChild(el("li", { class: h.tagName === "H3" ? "lvl-3" : "lvl-2" }, [a]));
    });
    tocEl.appendChild(el("p", { class: "toc-title", text: "本页目录" }));
    tocEl.appendChild(list);
    watchHeadings(links);
  }

  // 滚动时高亮当前小节（轻量：只比较各标题的文档位置）
  var tocObserver = null;
  function watchHeadings(links) {
    if (tocObserver) { tocObserver.disconnect(); tocObserver = null; }
    if (typeof IntersectionObserver !== "function" || !links.length) return;
    var byNode = new Map();
    links.forEach(function (x) { byNode.set(x.node, x.link); });
    tocObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var link = byNode.get(en.target);
        if (!link) return;
        if (en.isIntersecting) {
          Array.prototype.forEach.call(tocEl.querySelectorAll("a.active"), function (a) {
            a.classList.remove("active");
          });
          link.classList.add("active");
        }
      });
    }, { rootMargin: "-72px 0px -70% 0px", threshold: 0 });
    links.forEach(function (x) { tocObserver.observe(x.node); });
  }

  function buildDocNav(location) {
    var i = state.flat.map(function (x) { return x.location; }).indexOf(location);
    if (i < 0) return;
    var prev = state.flat[i - 1], next = state.flat[i + 1];
    var bar = el("div", { class: "doc-nav" }, [
      prev ? el("a", { href: "#/doc/" + encodeURIComponent(prev.location), text: "← " + prev.title }) : el("span", { text: "" }),
      next ? el("a", { href: "#/doc/" + encodeURIComponent(next.location), text: next.title + " →" }) : el("span", { text: "" })
    ]);
    var doc = main.querySelector(".doc");
    if (doc) doc.appendChild(bar);
  }

  function focusTarget(entryId) {
    if (!entryId) { window.scrollTo({ top: 0 }); return; }
    var node = main.querySelector('[id="' + entryId.replace(/"/g, '\\"') + '"]');
    if (!node) return;
    node.classList.add("highlight");
    node.scrollIntoView({ block: "start" });
  }

  // ------------------------------------------------------------ 浏览与筛选

  var FACET_ORDER = ["stages", "topics", "outputs", "effort", "evidence"];
  var FACET_LABELS_FOR_MATCH = FACET_ORDER;  // 匹配顺序与展示顺序一致

  function matchFilters(e, params) {
    for (var i = 0; i < FACET_ORDER.length; i++) {
      var key = FACET_ORDER[i];
      var raw = params.get(key);
      if (!raw) continue;
      var want = raw.split(",").filter(Boolean);
      if (!want.length) continue;
      if (key === "effort") {
        if (want.indexOf(e.effort) < 0) return false;
      } else {
        var have = e[key] || [];
        if (!want.some(function (v) { return have.indexOf(v) >= 0; })) return false;
      }
    }
    return true;
  }

  function scoreEntry(e, groups) {
    if (!groups.length) return 0;
    var score = 0;
    for (var i = 0; i < groups.length; i++) {
      var terms = groups[i];
      var hit = null;
      for (var j = 0; j < terms.length; j++) {
        var t = terms[j];
        if (e._hay.indexOf(t) < 0) continue;
        if (e._title === t) hit = Math.max(hit === null ? 0 : hit, 200);           // 标题完全一致
        else if (e._title.indexOf(t) === 0) hit = Math.max(hit === null ? 0 : hit, 120); // 标题前缀
        else if (e._title.indexOf(t) >= 0) hit = Math.max(hit === null ? 0 : hit, 80);   // 标题包含
        else if ((e.summary || "").toLowerCase().indexOf(t) >= 0) hit = Math.max(hit === null ? 0 : hit, 30);
        else if (e._tags.join(" ").toLowerCase().indexOf(t) >= 0) hit = Math.max(hit === null ? 0 : hit, 20);
        else hit = Math.max(hit === null ? 0 : hit, 8);                            // 正文命中
      }
      if (hit === null) return -1;   // 同一词（含同义词组）一个都没命中
      score += hit;
    }
    if (e.last_verified) score += 1;
    return score;
  }

  // 查询词 → 同义词组：组内取「或」，组间取「与」
  // 例：「日本 套磁」→ 日本 AND (套磁 OR 联系导师 OR 联系教授)
  function queryGroups(q) {
    var tokens = String(q || "").toLowerCase().split(/\s+/).filter(Boolean);
    return tokens.map(function (t) {
      var syn = (state.aliases && state.aliases[t]) || [];
      var terms = [t];
      syn.forEach(function (s) {
        var v = String(s).toLowerCase();
        if (terms.indexOf(v) < 0) terms.push(v);
      });
      return terms;
    });
  }

  function runSearch(params) {
    var q = (params.get("q") || "").trim().toLowerCase();
    var groups = queryGroups(q);
    var filtered = state.entries.filter(function (e) { return matchFilters(e, params); });
    if (!groups.length) {
      return filtered.slice().sort(function (a, b) {
        return (a.order - b.order) || a.doc.localeCompare(b.doc) || a.title.localeCompare(b.title);
      });
    }
    return filtered.map(function (e) { return { e: e, s: scoreEntry(e, groups) }; })
      .filter(function (x) { return x.s >= 0; })
      .sort(function (a, b) { return b.s - a.s || a.e.title.localeCompare(b.e.title); })
      .map(function (x) { return x.e; });
  }

  // 默认只展开最常用的两维；其余收进「更多筛选」，但已选条件始终在顶部可见
  var PRIMARY_FACETS = ["stages", "topics"];
  var ADVANCED_FACETS = ["outputs", "effort", "evidence"];

  function chipRow(facet) {
    var spec = state.index.facets[facet];
    var params = state.params;
    var row = el("div", { class: "facet" }, [el("div", { class: "facet-label", text: spec.label })]);
    var vals = el("div", { class: "facet-values" });
    var selected = (params.get(facet) || "").split(",").filter(Boolean);
    spec.values.forEach(function (v) {
      var on = selected.indexOf(v.key) >= 0;
      var attrs = {
        class: "facet-chip", type: "button", text: v.label,
        "aria-pressed": on ? "true" : "false"
      };
      if (v.en) attrs.title = v.en;          // 证据类型：中文为主，英文标识放 tooltip
      var b = el("button", attrs);
      b.addEventListener("click", function () {
        var next = new URLSearchParams(state.params.toString());
        toggleInList(next, facet, v.key);
        location.hash = buildHash(["browse"], next);
      });
      vals.appendChild(b);
    });
    row.appendChild(vals);
    return row;
  }

  // 已选中的高级条件：折叠状态下也要看得见，并且能逐个去掉
  function activeAdvancedRow(params) {
    var chips = [];
    ADVANCED_FACETS.forEach(function (facet) {
      var spec = state.index.facets[facet];
      var selected = (params.get(facet) || "").split(",").filter(Boolean);
      selected.forEach(function (key) {
        var label = key;
        spec.values.forEach(function (v) { if (v.key === key) label = v.label; });
        var b = el("button", {
          class: "facet-chip facet-chip-active", type: "button",
          text: spec.label + "：" + label, title: "点击去掉这个条件"
        });
        b.addEventListener("click", function () {
          var next = new URLSearchParams(state.params.toString());
          toggleInList(next, facet, key);
          location.hash = buildHash(["browse"], next);
        });
        chips.push(b);
      });
    });
    if (!chips.length) return null;
    var row = el("div", { class: "facet facet-active" }, [
      el("div", { class: "facet-label", text: "已选高级条件" }),
      el("div", { class: "facet-values" }, chips)
    ]);
    return row;
  }

  function facetsPanel(params) {
    var panel = el("div", { class: "facets" });
    var summary = activeAdvancedRow(params);
    if (summary) panel.appendChild(summary);
    PRIMARY_FACETS.forEach(function (f) { panel.appendChild(chipRow(f)); });

    var advancedBox = el("div", { class: "facets-advanced" });
    var toggle = el("button", {
      class: "facet-more", type: "button",
      "aria-expanded": state.showAdvanced ? "true" : "false",
      text: state.showAdvanced ? "收起高级筛选" : "更多筛选：能换回什么 / 投入 / 证据类型"
    });
    toggle.addEventListener("click", function () {
      state.showAdvanced = !state.showAdvanced;
      var next = new URLSearchParams(state.params.toString());
      location.hash = buildHash(["browse"], next);   // 重绘（状态保留在内存里）
    });
    panel.appendChild(el("div", { class: "facet-actions facet-more-row" }, [toggle]));
    if (state.showAdvanced) {
      ADVANCED_FACETS.forEach(function (f) { advancedBox.appendChild(chipRow(f)); });
      panel.appendChild(advancedBox);
    }
    panel.appendChild(el("div", { class: "facet-actions" }, [
      el("button", { type: "button", text: "清除全部筛选", onclick: function () {
        var next = new URLSearchParams();
        var q = params.get("q");
        if (q) next.set("q", q);
        location.hash = buildHash(["browse"], next);
      } }),
      el("span", { text: "证据类型中「官方规则」表示有政府、院校或机构的官方文件依据（内部标识 Official）" })
    ]));
    return panel;
  }

  function renderBrowse(params) {
    state.params = params;
    var q = params.get("q");
    if (q === null) {
      q = input.value.trim();
      if (q) { params.set("q", q); history.replaceState(null, "", buildHash(["browse"], params)); state.params = params; }
    } else {
      input.value = q;
    }
    markActive("");
    document.title = "按条件筛选 · 机会与成长指南";

    var results = runSearch(params);
    clear(main);
    main.appendChild(el("div", { class: "browse-head" }, [
      el("h1", { text: "按条件筛选" }),
      el("p", { class: "browse-count", text: "共 " + results.length + " 条可读条目" +
        (q ? "，匹配「" + q + "」" : "") + "。多个条件可以叠加，同一组内为“或”。" })
    ]));
    main.appendChild(facetsPanel(params));

    if (!results.length) {
      main.appendChild(el("p", { class: "empty", text: "没有符合条件的条目。可以去掉一两个条件，或换一个关键词试试。" }));
    } else {
      var list = el("ul", { class: "results" });
      results.forEach(function (e) { list.appendChild(resultItem(e)); });
      main.appendChild(list);
    }
    clear(tocEl);
  }

  function resultItem(e) {
    var meta = el("p", { class: "result-meta" });
    meta.appendChild(el("span", { text: e.doc_title }));
    (e.topics || []).forEach(function (t) { meta.appendChild(el("span", { class: "chip chip-topics", text: state.labels.topics[t] || t })); });
    (e.stages || []).forEach(function (t) { meta.appendChild(el("span", { class: "chip chip-stages", text: state.labels.stages[t] || t })); });
    if (e.effort) meta.appendChild(el("span", { class: "chip chip-effort", text: "投入 " + (state.labels.effort[e.effort] || e.effort) }));
    (e.evidence || []).forEach(function (t) { meta.appendChild(el("span", { class: "chip chip-evidence", text: state.labels.evidence[t] || t })); });
    if (e.last_verified) {
      var stale = e.last_verified < state.index.stale_threshold;
      meta.appendChild(el("span", {
        class: "chip " + (stale ? "chip-stale" : "chip-verified"),
        text: (stale ? "可能需要重新核实：" : "最后核实：") + e.last_verified
      }));
    }
    return el("li", { class: "result" }, [
      el("a", { class: "result-title", href: e.route, text: e.title }),
      el("p", { class: "result-summary", text: e.summary || "" }),
      meta
    ]);
  }

  // ------------------------------------------------------------ 路由

  function closeDrawer() {
    document.body.classList.remove("sidebar-open");
    if (collapseBtn) collapseBtn.setAttribute("aria-expanded", "false");
  }

  function route() {
    var h = parseHash();
    var parts = h.parts;
    if (isMobile()) closeDrawer();

    if (parts.length && parts[0] === "browse") { renderBrowse(h.params); return; }

    if (parts.length && parts[0] === "doc") {
      var rest = parts.slice(1).join("/");
      for (var i = 0; i < state.locations.length; i++) {
        var loc = state.locations[i];
        if (rest === loc) { renderDoc(loc, ""); return; }
        if (rest.indexOf(loc + "/") === 0) { renderDoc(loc, decodeURIComponent(rest.slice(loc.length + 1))); return; }
      }
    }
    renderDoc(state.homeLocation, "");
  }

  // ------------------------------------------------------------ 交互绑定

  var debounce = null;
  function onInput() {
    if (debounce) clearTimeout(debounce);
    debounce = setTimeout(function () {
      var next = new URLSearchParams(state.params.toString());
      var v = input.value.trim();
      if (v) next.set("q", v); else next.delete("q");
      var hash = buildHash(["browse"], next);
      if (location.hash === hash) { renderBrowse(next); } else { location.hash = hash; }
    }, 220);
  }

  function applyCollapsed(collapsed) {
    document.body.classList.toggle("nav-collapsed", collapsed);
    document.documentElement.classList.remove("pre-collapsed");
    if (collapseBtn) collapseBtn.setAttribute("aria-expanded", collapsed ? "false" : "true");
    store(NAV_KEY, collapsed ? "collapsed" : "expanded");
  }

  function bind() {
    input.addEventListener("input", onInput);
    searchForm.addEventListener("submit", function (ev) { ev.preventDefault(); onInput(); });

    if (collapseBtn) {
      collapseBtn.addEventListener("click", function () {
        if (isMobile()) {
          var open = document.body.classList.toggle("sidebar-open");
          collapseBtn.setAttribute("aria-expanded", open ? "true" : "false");
        } else {
          applyCollapsed(!document.body.classList.contains("nav-collapsed"));
        }
      });
    }
    if (closeBtn) closeBtn.addEventListener("click", closeDrawer);

    document.addEventListener("click", function (ev) {
      if (!document.body.classList.contains("sidebar-open")) return;
      if (ev.target.closest(".sidebar") || ev.target.closest(".nav-collapse")) return;
      closeDrawer();
    });
    // 点击目录里的链接后自动收起抽屉
    navTree.addEventListener("click", function (ev) {
      if (ev.target.closest("a") && isMobile()) closeDrawer();
    });
    // 已经在当前页时点同一个链接，hashchange 不触发，手动重定位
    navTree.addEventListener("click", function (ev) {
      var a = ev.target.closest("a");
      if (!a) return;
      var href = a.getAttribute("href") || "";
      if (href && location.hash === href) { ev.preventDefault(); route(); }
    });

    document.addEventListener("keydown", function (ev) {
      var tag = (ev.target.tagName || "").toLowerCase();
      var typing = tag === "input" || tag === "textarea";
      if (ev.key === "/" && !typing) { ev.preventDefault(); input.focus(); input.select(); }
      if (ev.key === "Escape") {
        if (document.body.classList.contains("sidebar-open")) { closeDrawer(); return; }
        if (typing) {
          input.value = "";
          if (location.hash.indexOf("#/browse") === 0) { location.hash = buildHash(["browse"], new URLSearchParams()); }
          input.blur();
        }
      }
    });

    window.addEventListener("hashchange", function () { route(); });
    window.addEventListener("resize", function () {
      if (!isMobile()) closeDrawer();
    });
  }

  // 同义词表：缺失也不影响搜索（只是没有别名扩展）
  function loadAliases() {
    return fetch("search_aliases.json")
      .then(function (r) { return r.ok ? r.json() : {}; })
      .then(function (data) {
        var out = {};
        Object.keys(data || {}).forEach(function (k) {
          if (k.charAt(0) === "_") return;            // 跳过注释字段
          var v = data[k];
          if (Object.prototype.toString.call(v) === "[object Array]") out[k.toLowerCase()] = v;
        });
        state.aliases = out;
      })
      .catch(function () { state.aliases = {}; });
  }

  loadAliases().then(function () {
    return fetch("data/index.json")
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (data) {
        state.index = data;
        prepare();
        buildNav();
        bind();
        if (read(NAV_KEY) === "collapsed" && !isMobile()) applyCollapsed(true);
        route();
      });
  })
    .catch(function (err) {
      clear(main);
      main.appendChild(el("p", { class: "empty", text:
        "索引加载失败（" + err.message + "）。请先生成站点：python3 tools/build.py，然后用 http 方式访问（python3 -m http.server 8000 --directory site）。" }));
    });
})();
