/* 机会与成长指南 · 静态阅读页
   无框架、无后端：读取 data/index.json 与 content/**.html，hash 路由，客户端搜索与筛选。

   目录是一棵「一级分组 → 二级分组 → 文档 → 条目」的树，节点可逐级展开；
   左侧目录固定在窗口最左侧，可以整体折叠（选择记在 localStorage）。 */

(function () {
  "use strict";

  var MOBILE = "(max-width: 900px)";
  var NAV_KEY = "oh.nav";
  // 用户「手动」展开的分组（点击小箭头）。语义上与系统为 active 路径临时展开
  // 的状态严格分开：后者不持久化，只体现在 DOM 的 open class 上。
  // 旧 key oh.nav.expanded 曾混入大量系统自动展开数据，不再读取，见下方一次性清理。
  var MANUAL_KEY = "oh.nav.manual-expanded.v2";
  var LEGACY_EXPAND_KEY = "oh.nav.expanded";
  var legacyKeyCleaned = false;

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
    manualExpanded: {}, // 用户点击小箭头手动展开的节点 key（持久化）
    autoOpen: {},       // 系统为 active 路径临时展开的节点 key（不持久化）
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
  var readerUI = null;
  var searchPromise = null;
  var searchReady = false;

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

    prepareSearch(idx);

    var saved = read(MANUAL_KEY);
    if (saved) {
      try { state.manualExpanded = JSON.parse(saved) || {}; } catch (e) { state.manualExpanded = {}; }
    }
    // 旧 key 里混有系统自动展开的历史数据：只清理一次，之后不再读取
    if (!legacyKeyCleaned && read(LEGACY_EXPAND_KEY)) {
      try { localStorage.removeItem(LEGACY_EXPAND_KEY); } catch (e) {}
      legacyKeyCleaned = true;
    }
  }

  function prepareSearch(idx) {
    var L = {
      stages: labelMap("stages"), topics: labelMap("topics"),
      outputs: labelMap("outputs"), effort: labelMap("effort"), evidence: labelMap("evidence")
    };
    state.labels = L;
    var evidenceEn = {};
    (((idx.facets || {}).evidence || {}).values || []).forEach(function (v) { evidenceEn[v.key] = v.en || ""; });
    // 搜索范围 = Book 条目 + 首页问题 + 用户侧文档（深度教程/职业指南/国家手册/案例/操作手册/工具）
    // 文档此前不在搜索范围内，读者搜不到这些页面——这里把它们并入同一套字段。
    var searchableDocs = (idx.docs || []).filter(function (d) {
      return d.kind === "doc" && d.status !== "planned" && d.text;
    });
    state.entries = idx.entries.concat(searchableDocs).map(function (e) {
      var tags = []
        .concat(e.stages.map(function (v) { return L.stages[v] || v; }))
        .concat(e.topics.map(function (v) { return L.topics[v] || v; }))
        .concat(e.outputs.map(function (v) { return L.outputs[v] || v; }))
        .concat(e.evidence.map(function (v) { return L.evidence[v] || v; }))
        .concat(e.evidence.map(function (v) { return evidenceEn[v] || ""; }));
      var hay = [e.title, e.summary, e.text, e.doc_title, tags.join(" ")].join(" ").toLowerCase();
      return Object.assign({}, e, { _hay: hay, _title: e.title.toLowerCase(), _tags: tags });
    });

  }

  // ------------------------------------------------------------ 左侧目录树

  var DEPTH_CLASS = ["nav-l1", "nav-l2", "nav-l3", "nav-l4", "nav-l5"];

  function renderNode(node, depth, parentKey) {
    var key = parentKey + " / " + node.label;
    var kids = node.children || [];
    var li = el("li", { class: "nav-item " + (DEPTH_CLASS[depth] || "nav-l5") });
    li.dataset.key = key;
    li.dataset.navId = node.nav_id || "";

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
        toggleManual(li);
      });
      row.appendChild(btn);
    } else {
      row.appendChild(el("span", { class: "nav-dot" }));
    }

    var href = node.href || (node.kind === "entry" ? "" : firstHref(node));
    if (kids.length && !href) {
      row.appendChild(el("button", { type: "button", class: "nav-label nav-group-label", text: node.label,
        onclick: function () { toggleManual(li); } }));
    } else if (href) {
      var link = el("a", { class: "nav-label", href: href, text: node.label, title: node.label });
      if (kids.length) {
        // 分组行：点标题表示「我要去这个内容」，展开动作交给 markActive 的
        // accordion（focus path）；这里不再直接持久化任何展开状态。
      }
      row.appendChild(link);
    } else if (kids.length) {
      // 无对应章节的分组行：点标题即展开/收起（整行可点，不必瞄准小箭头）
      var groupLabel = el("span", { class: "nav-label static clickable", text: node.label, title: node.label });
      groupLabel.addEventListener("click", function () {
        toggleManual(li);
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
      if (href && depth === 0) ul.appendChild(el("li", { class: "nav-overview" }, [el("a", { href: href, text: "本组概览 →" })]));
      kids.forEach(function (c) { ul.appendChild(renderNode(c, depth + 1, key)); });
      li.appendChild(ul);
    }
    if (state.manualExpanded[key]) setOpen(li, true, { persist: false });
    return li;
  }

  // 只改视觉状态；persist=true 时才写入「用户手动展开」偏好
  function setOpen(li, open, opts) {
    opts = opts || {};
    li.classList.toggle("open", open);
    var btn = li.querySelector(":scope > .nav-row > .nav-toggle");
    if (btn) btn.setAttribute("aria-expanded", open ? "true" : "false");
    var key = li.dataset.key;
    if (opts.persist) {
      if (open) state.manualExpanded[key] = 1; else delete state.manualExpanded[key];
      store(MANUAL_KEY, JSON.stringify(state.manualExpanded));
    }
    if (!open) delete state.autoOpen[key];
    else if (opts.auto) state.autoOpen[key] = 1;
  }

  // 小箭头点击：用户「只想展开看看」——允许多个分组同时手动展开
  function toggleManual(li) {
    setOpen(li, !li.classList.contains("open"), { persist: true });
  }

  function itemKey(li) { return li ? li.dataset.key : ""; }

  function getAncestorPath(li) {
    var path = [];
    var up = li.parentElement ? li.parentElement.closest(".nav-item") : null;
    while (up) { path.push(up); up = up.parentElement ? up.parentElement.closest(".nav-item") : null; }
    return path;
  }

  // 把 active 节点与其祖先展开（不持久化），并收起同一父下
  // 「非手动、也不在 active 路径上」的 auto 展开 —— 即 accordion 效果。
  // manualExpanded 的节点永远不会被收起。
  function syncNavOpenState(hit) {
    var activeKeys = {};
    if (hit) {
      if (hit.querySelector(":scope > .nav-row > .nav-toggle")) activeKeys[itemKey(hit)] = 1;
      getAncestorPath(hit).forEach(function (a) { activeKeys[itemKey(a)] = 1; });
    }
    Array.prototype.forEach.call(navTree.querySelectorAll(".nav-item"), function (item) {
      var key = itemKey(item);
      var hasKids = !!item.querySelector(":scope > .nav-row > .nav-toggle");
      var isManual = !!state.manualExpanded[key];
      var isOnPath = !!activeKeys[key];
      var isOpen = item.classList.contains("open");
      if (hasKids && isOnPath && !isOpen) {
        setOpen(item, true, { persist: false, auto: true });
      } else if (hasKids && isOpen && !isManual && !isOnPath) {
        setOpen(item, false, { persist: false });
      }
    });
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

  function routeKey(hash) {
    try { return decodeURI((hash || "").split("?")[0]); } catch (_) { return (hash || "").split("?")[0]; }
  }

  function keepVisible(pane, node) {
    if (!pane || !node || pane.clientHeight < 1 || !node.getClientRects().length) return;
    var box = pane.getBoundingClientRect(), rect = node.getBoundingClientRect(), pad = 12;
    if (rect.top < box.top + pad) pane.scrollTop += rect.top - box.top - pad;
    else if (rect.bottom > box.bottom - pad) pane.scrollTop += rect.bottom - box.bottom + pad;
  }

  function markActive(hash, opts) {
    opts = opts || {};
    var rows = Array.prototype.slice.call(navTree.querySelectorAll(".nav-row"));
    var hit = opts.nodeId && rows.find(function (r) { return r.parentElement.dataset.navId === opts.nodeId; });
    function href(r) { var a = r.querySelector("a.nav-label"); return a ? a.getAttribute("href") : ""; }
    if (!hit) hit = rows.find(function (r) { return href(r) === hash; });
    if (!hit) {
      var key = routeKey(hash), best = -1;
      rows.forEach(function (r) {
        if (routeKey(href(r)) !== key) return;
        var score = KIND_PRIORITY[r.dataset.kind] || 1;
        if (score > best) { hit = r; best = score; }
      });
    }
    if (!hit) {
      var target = routeKey(hash), length = 0;
      rows.forEach(function (r) {
        var key = routeKey(href(r));
        if (key && target.indexOf(key + "/") === 0 && key.length > length) { hit = r; length = key.length; }
      });
    }
    rows.forEach(function (r) {
      r.classList.toggle("active", r === hit);
      var a = r.querySelector("a.nav-label");
      if (a) { if (r === hit) a.setAttribute("aria-current", r.dataset.kind === "anchor" ? "location" : "page"); else a.removeAttribute("aria-current"); }
    });
    if (!hit || opts.scroll === false) return;
    var item = hit.closest(".nav-item");
    if (opts.follow) {
      // Reading reveals only the active ancestry. It never folds other branches
      // or overwrites the reader's manual expand/collapse preferences.
      navTree.classList.add("no-anim");
      getAncestorPath(item).forEach(function (ancestor) {
        if (!ancestor.classList.contains("open")) setOpen(ancestor, true, { persist: false, auto: true });
      });
      keepVisible(navTree, hit);
      requestAnimationFrame(function () { navTree.classList.remove("no-anim"); });
    } else {
      syncNavOpenState(item);
      keepVisible(navTree, hit);
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
    var requestedHash = window.location.hash;
    var params = parseHash().params;
    markActive("#/doc/" + location + (entryId ? "/" + entryId : ""));
    document.title = (item ? item.title + " · " : "") + "机会手册";

    return fetchContent(location).then(function (html) {
      if (window.location.hash !== requestedHash) return;
      main.innerHTML = html;
      var article = main.querySelector(".doc");
      var context = readerUI ? readerUI.decorateArticle(article, entryId, "#/doc/" + location + (entryId ? "/" + entryId : ""), params) : {};
      var header = article.querySelector(".doc-header");
      if (item && item.last_verified && item.last_verified < state.index.stale_threshold) {
        article.insertBefore(el("p", { class: "notice", text:
          "本页最后核实于 " + item.last_verified + "，已经超过 12 个月，其中的制度性信息可能需要重新核实。" }),
          header.nextSibling);
      }
      if (!readerUI) buildDocNav(location);
      focusTarget(readerUI && readerUI.isSingle() ? "" : entryId);
      context.location = location;
      context.entryId = entryId;
      mountReading(context);
      var section = params.get("section"), sectionNode = section && document.getElementById(section);
      if (sectionNode && main.contains(sectionNode)) jumpToHeading(sectionNode);
    }).catch(function (err) {
      if (window.location.hash !== requestedHash) return;
      clear(main);
      main.appendChild(el("p", { class: "empty", text: "内容暂时加载失败，请重试，或返回首页继续查找。" }));
      main.appendChild(el("a", { href: "#/", text: "返回首页 →" }));
      clear(tocEl);
    });
  }

  // Both sidebars observe the headings and entries actually rendered on this
  // page. One geometry-based watcher also handles large jumps and reverse scroll.
  var readingWatch = { links: [], context: {}, handler: null, frame: 0, timer: 0,
    observer: null, activeHeading: null, activeLeft: "" };

  function stopReading() {
    if (readingWatch.handler) {
      window.removeEventListener("scroll", readingWatch.handler);
      window.removeEventListener("resize", readingWatch.handler);
    }
    if (readingWatch.frame) cancelAnimationFrame(readingWatch.frame);
    if (readingWatch.timer) clearTimeout(readingWatch.timer);
    if (readingWatch.observer) readingWatch.observer.disconnect();
    readingWatch.handler = null; readingWatch.frame = 0; readingWatch.timer = 0; readingWatch.observer = null;
    readingWatch.links = []; readingWatch.activeHeading = null; readingWatch.activeLeft = "";
  }

  function readingLine() {
    var bar = document.querySelector(".topbar");
    return (bar ? Math.max(0, bar.getBoundingClientRect().bottom) : 64) + 32;
  }

  function jumpToHeading(node) {
    var top = window.scrollY + node.getBoundingClientRect().top - readingLine() + 1;
    window.scrollTo({ top: Math.max(0, top), behavior: "instant" });
    updateReading();
  }

  function buildToc(entryId) {
    clear(tocEl);
    var article = main.querySelector(".doc");
    if (!article) return [];
    var heads = Array.from(article.querySelectorAll("h2, h3")).filter(function (h) {
      return !h.closest("[hidden], .sources-details") && h.getClientRects().length > 0;
    });
    var links = [], list = el("ul", { class: "toc-list" });
    heads.forEach(function (h, i) {
      var entryTitle = h.tagName === "H3" && h.parentElement.classList.contains("entry");
      var target = entryTitle ? h.parentElement : h;
      if (!target.id) {
        var id = "reader-heading-" + i;
        while (document.getElementById(id)) id += "-section";
        target.id = id;
      }
      var a = el("a", { href: "#", text: h.textContent, "data-target": target.id });
      a.addEventListener("click", function (event) { event.preventDefault(); jumpToHeading(target); });
      var nested = !entryTitle && (h.tagName === "H3" || (!entryId && h.closest(".entry")));
      list.appendChild(el("li", { class: nested ? "lvl-3" : "lvl-2" }, [a]));
      links.push({ node: target, link: a });
    });
    if (links.length) {
      tocEl.appendChild(el("p", { class: "toc-title", text: "本页目录" }));
      tocEl.appendChild(list);
    }
    return links;
  }

  function updateReading() {
    var links = readingWatch.links, line = readingLine(), current = null;
    links.forEach(function (item) { if (item.node.getBoundingClientRect().top <= line + 1) current = item; });
    var bottom = document.documentElement.scrollHeight - innerHeight;
    if (bottom > 0 && window.scrollY >= bottom - 2 && links.length) current = links[links.length - 1];
    if (current !== readingWatch.activeHeading) {
      links.forEach(function (item) {
        item.link.classList.toggle("active", item === current);
        if (item === current) item.link.setAttribute("aria-current", "location"); else item.link.removeAttribute("aria-current");
      });
      readingWatch.activeHeading = current;
      if (current) keepVisible(tocEl, current.link);
    }
    var context = readingWatch.context, entryId = context.entryId || "";
    if (!entryId && !context.fixedNode && !context.chapter) {
      Array.from(main.querySelectorAll(".entry")).forEach(function (entry) {
        if (entry.hidden) return;
        var rect = entry.getBoundingClientRect();
        if (rect.top <= line) entryId = entry.id;
      });
      var materials = main.querySelector(".reader-task-materials");
      if (materials && materials.getBoundingClientRect().top <= line) entryId = "";
    }
    var nodeId = context.nodeId || "", href = context.route || "";
    if (context.chapter) {
      Array.from(main.querySelectorAll(".reader-chapter-group, .reader-chapter-section")).forEach(function (section) {
        if (section.getBoundingClientRect().top <= line) { nodeId = section.dataset.navId; href = context.route + "?section=" + encodeURIComponent(section.id); }
      });
    } else if (context.isMap && current) nodeId = "map-section-" + current.node.id;
    else if (entryId && context.location && !context.fixedNode) { nodeId = entryId; href = "#/doc/" + context.location + "/" + entryId; }
    var left = nodeId || href;
    if (left && left !== readingWatch.activeLeft) {
      readingWatch.activeLeft = left;
      markActive(href, { nodeId: nodeId, follow: true });
    }
  }

  function mountReading(context) {
    stopReading();
    readingWatch.context = context || {};
    readingWatch.links = buildToc(context.entryId || "");
    readingWatch.handler = function () {
      if (readingWatch.frame) return;
      function flush() {
        if (readingWatch.frame) cancelAnimationFrame(readingWatch.frame);
        if (readingWatch.timer) clearTimeout(readingWatch.timer);
        readingWatch.frame = 0; readingWatch.timer = 0;
        updateReading();
      }
      readingWatch.frame = requestAnimationFrame(flush);
      // Keep the last position accurate when a background tab delays painting.
      readingWatch.timer = setTimeout(flush, 100);
    };
    window.addEventListener("scroll", readingWatch.handler, { passive: true });
    window.addEventListener("resize", readingWatch.handler, { passive: true });
    if (typeof ResizeObserver === "function") {
      readingWatch.observer = new ResizeObserver(readingWatch.handler);
      readingWatch.observer.observe(main);
    }
    updateReading();
  }

  function buildDocNav(location) {
    var i = state.flat.map(function (x) { return x.location; }).indexOf(location);
    if (i < 0) return;
    var prev = state.flat[i - 1], next = state.flat[i + 1];
    var bar = el("div", { class: "doc-nav" }, [
      prev ? el("a", { href: "#/doc/" + encodeURIComponent(prev.location), text: "← " + prev.title }) : el("span"),
      next ? el("a", { href: "#/doc/" + encodeURIComponent(next.location), text: next.title + " →" }) : el("span") ]);
    var doc = main.querySelector(".doc");
    if (doc) doc.appendChild(bar);
  }

  function focusTarget(entryId) {
    if (!entryId) { window.scrollTo({ top: 0, behavior: "instant" }); return; }
    var node = document.getElementById(entryId);
    if (node && main.contains(node)) { node.classList.add("highlight"); jumpToHeading(node); }
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
        return ((a.order || 0) - (b.order || 0)) || String(a.doc || a.doc_title || a.location || "").localeCompare(String(b.doc || b.doc_title || b.location || "")) || a.title.localeCompare(b.title);
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
    if (readerUI) readerUI.prepareSearch();
    state.params = params;
    var q = params.get("q");
    if (q === null) {
      q = input.value.trim();
      if (q) { params.set("q", q); history.replaceState(null, "", buildHash(["browse"], params)); state.params = params; }
    } else {
      input.value = q;
    }
    markActive("");
    document.title = "按条件筛选 · 机会手册";

    var results = runSearch(params);
    clear(main);
    main.appendChild(el("div", { class: "browse-head" }, [
      el("h1", { text: "按条件筛选" }),
      el("p", { class: "browse-count", text: "共 " + results.length + " 条可读条目" +
        (q ? "，匹配「" + q + "」" : "") + "。多个条件可以叠加，同一组内为“或”。" })
    ]));
    main.appendChild(facetsPanel(params));

    if (!results.length) {
      main.appendChild(emptyState(q, params));
    } else {
      var list = el("ul", { class: "results" });
      results.forEach(function (e) { list.appendChild(resultItem(e)); });
      main.appendChild(list);
    }
    clear(tocEl);
  }

  // 无结果时不要只说「没找到」：给出可点的常见词与两个兜底入口，
  // 读者至少还有路可走（搜不到是检索体验里最伤的一步）
  var EMPTY_TIPS = ["保研", "实习", "科研", "转行", "留学", "考公", "简历", "中职", "40 岁"];

  function emptyState(q, params) {
    var box = el("div", { class: "empty-block" });
    box.appendChild(el("p", { class: "empty-title", text: "没有匹配的条目" }));
    box.appendChild(el("p", {
      class: "empty-desc",
      text: q ? "搜索按字面与同义词匹配，不认近义改写。换一个说法、去掉一个条件，或从下面进入。"
              : "当前条件下没有内容。去掉一两个条件试试。"
    }));
    var tips = el("ul", { class: "empty-tips" });
    EMPTY_TIPS.forEach(function (t) {
      tips.appendChild(el("li", {}, [el("a", { href: "#/browse?q=" + encodeURIComponent(t), text: t })]));
    });
    box.appendChild(el("p", { class: "empty-hint", text: "常见入口：" }));
    box.appendChild(tips);
    var links = el("p", { class: "empty-links" });
    links.appendChild(el("span", { text: "也可以直接进 " }));
    links.appendChild(el("a", { href: "#/doc/book/17-内容地图", text: "内容地图" }));
    links.appendChild(el("span", { text: "（按阶段与方向索引全书）或 " }));
    links.appendChild(el("a", { href: "#/doc/book/00-从这里开始", text: "从这里开始" }));
    links.appendChild(el("span", { text: "。" }));
    box.appendChild(links);
    if (params && params.toString()) {
      box.appendChild(el("p", { class: "empty-clear" }, [
        el("a", { href: "#/browse", text: "清除全部条件" })
      ]));
    }
    return box;
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
    stopReading();
    if (isMobile()) closeDrawer();

    if (readerUI && readerUI.handle(parts, h.params)) { input.value = ""; state.params = new URLSearchParams(); return; }
    if (parts.length && parts[0] === "browse") {
      if (searchReady) { renderBrowse(h.params); return; }
      var requestedHash = location.hash;
      clear(main); clear(tocEl);
      main.appendChild(el("p", { role: "status", text: "正在准备全文搜索……" }));
      if (!searchPromise) searchPromise = Promise.all([
        fetch("data/index.json", { cache: "no-cache" }).then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); }),
        loadAliases()
      ]).then(function (values) { prepareSearch(values[0]); searchReady = true; });
      searchPromise.then(function () { if (location.hash === requestedHash) renderBrowse(h.params); })
        .catch(function () {
          searchPromise = null;
          if (location.hash !== requestedHash) return;
          main.replaceChildren(el("p", { role: "alert", text: "搜索暂时不可用，请重试，或从主题目录继续查找。" }),
            el("button", { type: "button", class: "reader-retry", text: "重试搜索", onclick: route }));
        });
      return;
    }

    if (parts.length && parts[0] === "doc") {
      var rest = parts.slice(1).join("/");

      // IA 重构前的旧地址：先查重定向，再按新地址渲染（顺带把地址栏换成规范地址）
      var redirects = state.index.redirects || { docs: {}, entries: {} };
      var oldRoute = "#/doc/" + rest;
      var target = (redirects.entries || {})[oldRoute];
      if (target) {
        history.replaceState(null, "", target);
        var tparts = target.replace(/^#\//, "").split("/");
        rest = tparts.slice(1).join("/");
      }
      var chapterRoute = readerUI && readerUI.resolveDocument("#/doc/" + rest, h.params);
      if (chapterRoute) { history.replaceState(null, "", chapterRoute); route(); return; }

      for (var i = 0; i < state.locations.length; i++) {
        var loc = state.locations[i];
        if (rest === loc) { renderDoc(loc, ""); return; }
        if (rest.indexOf(loc + "/") === 0) { renderDoc(loc, decodeURIComponent(rest.slice(loc.length + 1))); return; }
      }

      // 整份文档被搬走：把旧 location 映射到新 location
      var slash = rest.indexOf("/");
      var oldLoc = slash < 0 ? rest : rest.slice(0, slash);
      var entryId = slash < 0 ? "" : decodeURIComponent(rest.slice(slash + 1));
      var newLoc = (redirects.docs || {})[oldLoc];
      if (newLoc && state.byLocation[newLoc]) {
        history.replaceState(null, "", "#/doc/" + newLoc + (entryId ? "/" + entryId : ""));
        route();
        return;
      }
    }
    if (!parts.length) { renderDoc(state.homeLocation, ""); return; }
    if (readerUI) readerUI.handle(["guide", "missing"]); else renderDoc(state.homeLocation, "");
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
      if (location.hash === hash) { route(); } else { location.hash = hash; }
    }, 220);
  }

  function applyCollapsed(collapsed) {
    document.body.classList.toggle("nav-collapsed", collapsed);
    document.documentElement.classList.remove("pre-collapsed");
    if (collapseBtn) collapseBtn.setAttribute("aria-expanded", collapsed ? "false" : "true");
    store(NAV_KEY, collapsed ? "collapsed" : "expanded");
  }

  function bind() {
    main.addEventListener("click", function (event) {
      var a = event.target.closest('a[href^="#"]');
      if (!a) return;
      var href = a.getAttribute("href");
      if (href.indexOf("#/") === 0 || href === "#") return;
      var name = href.slice(1);
      try { name = decodeURIComponent(name); } catch (_) {}
      var target = document.getElementById(name);
      if (target && main.contains(target)) { event.preventDefault(); jumpToHeading(target); }
    });
    document.querySelector(".skip-link").addEventListener("click", function (event) {
      event.preventDefault(); main.focus();
    });
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
      var same = location.hash === href;
      try { same = same || decodeURI(location.hash) === decodeURI(href); } catch (_) {}
      if (href && same) { ev.preventDefault(); route(); }
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
    return fetch("search_aliases.json", { cache: "no-cache" })
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

  fetch("data/reader.json", { cache: "no-cache" })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (data) {
        state.index = data;
        prepare();
        if (data.reader && window.HandbookReader) {
          state.index.nav = data.reader.navigation;
          buildNav();
          readerUI = window.HandbookReader({ index: data, main: main, nav: navTree, toc: tocEl,
            el: el, read: read, store: store, bookNav: buildNav, mountReading: mountReading, jumpToHeading: jumpToHeading,
            openOverview: function (destination) { history.replaceState(null, "", destination); route(); },
            highlight: function (href, options) { markActive(href, options); } });
        } else buildNav();
        bind();
        if (read(NAV_KEY) === "collapsed" && !isMobile()) applyCollapsed(true);
        route();
      })
    .catch(function (err) {
      clear(main);
      main.appendChild(el("p", { class: "empty", text:
        "内容暂时无法加载，请刷新页面重试。" }));
    });
})();
