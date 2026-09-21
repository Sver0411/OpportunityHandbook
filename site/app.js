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
    (idx.docs || []).forEach(function (d) { docMeta[d.location] = d; });

    // 按目录顺序（深度优先）登记文档级节点，用于路由与上一页/下一页
    (function collect(nodes) {
      (nodes || []).forEach(function (n) {
        var h = n.href || "";
        if (n.kind !== "entry" && h.indexOf("#/doc/") === 0) {
          var loc = h.replace(/^#\/doc\//, "");
          if (!state.byLocation[loc] && loc.split("/").length >= 2) {
            var m = docMeta[loc] || {};
            state.byLocation[loc] = {
              title: n.label, location: loc, route: h,
              last_verified: m.last_verified || "", status: m.status || ""
            };
            state.flat.push(state.byLocation[loc]);
          }
        }
        collect(n.children);
      });
    })(idx.nav);

    // 有些章节（单文档分组）在目录里没有独立节点，补登记，保证路由与翻页完整
    (idx.docs || []).forEach(function (d) {
      if (!state.byLocation[d.location]) {
        state.byLocation[d.location] = {
          title: d.title, location: d.location, route: d.route,
          last_verified: d.last_verified || "", status: d.status || ""
        };
        state.flat.push(state.byLocation[d.location]);
      }
    });

    state.locations = Object.keys(state.byLocation).sort(function (a, b) { return b.length - a.length; });

    var home = state.flat.filter(function (i) { return i.location.indexOf("00-") >= 0; })[0];
    state.homeLocation = home ? home.location : (state.flat[0] || {}).location;

    var L = {
      stages: labelMap("stages"), topics: labelMap("topics"),
      outputs: labelMap("outputs"), effort: labelMap("effort"), evidence: labelMap("evidence")
    };
    state.labels = L;
    state.entries = idx.entries.map(function (e) {
      var tags = []
        .concat(e.stages.map(function (v) { return L.stages[v] || v; }))
        .concat(e.topics.map(function (v) { return L.topics[v] || v; }))
        .concat(e.outputs.map(function (v) { return L.outputs[v] || v; }))
        .concat(e.evidence.map(function (v) { return L.evidence[v] || v; }));
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
    clear(navTree);
    var lastSection = null;
    state.index.nav.forEach(function (node) {
      var ul = el("ul", { class: "nav-group-block" });
      ul.appendChild(renderNode(node, 0, ""));
      navTree.appendChild(ul);
      lastSection = node;
    });
    navTree.appendChild(el("div", { class: "nav-group-block" }, [
      el("ul", null, [
        el("li", { class: "nav-item nav-l1" }, [
          el("div", { class: "nav-row" }, [
            el("span", { class: "nav-dot" }),
            el("a", { class: "nav-label", href: "#/browse", text: "按条件筛选全部条目" })
          ])
        ])
      ])
    ]));
    void lastSection;
  }

  function markActive(hash) {
    var links = navTree.querySelectorAll("a.nav-label");
    var hit = null;
    Array.prototype.forEach.call(links, function (a) {
      var on = a.getAttribute("href") === hash;
      var row = a.closest(".nav-row");
      if (row) row.classList.toggle("active", on);
      if (on) hit = a;
    });
    if (!hit) {
      // 条目深链：退一步高亮它所属的文档
      var loc = hash.replace(/^#\/doc\//, "").split("/")[0];
      Array.prototype.forEach.call(links, function (a) {
        if (a.getAttribute("href") === "#/doc/" + loc) {
          var row = a.closest(".nav-row");
          if (row) row.classList.add("active");
          hit = a;
        }
      });
    }
    if (!hit) return;
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
      if (location === state.homeLocation) insertStats(article, header);
      buildToc();
      buildDocNav(location);
      focusTarget(entryId);
    }).catch(function (err) {
      clear(main);
      main.appendChild(el("p", { class: "empty", text: "内容加载失败（" + err.message + "）。如果是在本地打开，请用 http 方式访问，例如：python3 -m http.server 8000 --directory site" }));
      clear(tocEl);
    });
  }

  function insertStats(article, header) {
    var s = state.index.stats;
    var box = el("div", { class: "stats" }, [
      el("div", { class: "stat", html: "<b>" + s.complete + "</b>已写完条目" }),
      el("div", { class: "stat", html: "<b>" + state.index.nav.length + "</b>主题分组" }),
      el("div", { class: "stat", html: "<b>" + s.todo + "</b>规划中条目" }),
      el("div", { class: "stat", html: "<b>" + state.index.generated_at.slice(0, 10) + "</b>页面构建日期" })
    ]);
    header.parentNode.insertBefore(box, header.nextSibling);
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
    if (!("IntersectionObserver" in window) || !links.length) return;
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

  function scoreEntry(e, tokens) {
    if (!tokens.length) return 0;
    var score = 0;
    for (var i = 0; i < tokens.length; i++) {
      var t = tokens[i];
      if (e._hay.indexOf(t) < 0) return -1;
      if (e._title.indexOf(t) >= 0) score += 60;
      if ((e.summary || "").toLowerCase().indexOf(t) >= 0) score += 20;
      if (e._tags.join(" ").toLowerCase().indexOf(t) >= 0) score += 12;
      score += 2;
    }
    if (e.last_verified) score += 1;
    return score;
  }

  function runSearch(params) {
    var q = (params.get("q") || "").trim().toLowerCase();
    var tokens = q.split(/\s+/).filter(Boolean);
    var filtered = state.entries.filter(function (e) { return matchFilters(e, params); });
    if (!tokens.length) {
      return filtered.slice().sort(function (a, b) {
        return (a.order - b.order) || a.doc.localeCompare(b.doc) || a.title.localeCompare(b.title);
      });
    }
    return filtered.map(function (e) { return { e: e, s: scoreEntry(e, tokens) }; })
      .filter(function (x) { return x.s >= 0; })
      .sort(function (a, b) { return b.s - a.s || a.e.title.localeCompare(b.e.title); })
      .map(function (x) { return x.e; });
  }

  function chipRow(facet) {
    var spec = state.index.facets[facet];
    var params = state.params;
    var row = el("div", { class: "facet" }, [el("div", { class: "facet-label", text: spec.label })]);
    var vals = el("div", { class: "facet-values" });
    var selected = (params.get(facet) || "").split(",").filter(Boolean);
    spec.values.forEach(function (v) {
      var on = selected.indexOf(v.key) >= 0;
      var b = el("button", {
        class: "facet-chip", type: "button", text: v.label, "aria-pressed": on ? "true" : "false"
      });
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
      el("p", { class: "browse-count", text: "共 " + results.length + " 条已写完的条目" +
        (q ? "，匹配「" + q + "」" : "") + "。多个条件可以叠加，同一组内为“或”。" })
    ]));
    var facets = el("div", { class: "facets" });
    FACET_ORDER.forEach(function (f) { facets.appendChild(chipRow(f)); });
    facets.appendChild(el("div", { class: "facet-actions" }, [
      el("button", { type: "button", text: "清除全部筛选", onclick: function () {
        var next = new URLSearchParams();
        if (q) next.set("q", q);
        location.hash = buildHash(["browse"], next);
      } }),
      el("span", { text: "证据类型中 Official 表示有官方文件依据" })
    ]));
    main.appendChild(facets);

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

  fetch("data/index.json")
    .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
    .then(function (data) {
      state.index = data;
      prepare();
      buildNav();
      bind();
      if (read(NAV_KEY) === "collapsed" && !isMobile()) applyCollapsed(true);
      route();
    })
    .catch(function (err) {
      clear(main);
      main.appendChild(el("p", { class: "empty", text:
        "索引加载失败（" + err.message + "）。请先生成站点：python3 tools/build.py，然后用 http 方式访问（python3 -m http.server 8000 --directory site）。" }));
    });
})();
