/* 机会与成长指南 · 静态阅读页
   无框架、无后端：读取 data/index.json 与 content/**.html，hash 路由，客户端搜索与筛选。 */

(function () {
  "use strict";

  var state = {
    index: null,
    locations: [],      // 按长度倒序的 location 列表，用于最长前缀匹配
    byLocation: {},     // location -> nav item
    homeLocation: "",
    flat: [],           // 文档顺序（用于上一页/下一页）
    cache: {},
    entries: [],
    params: new URLSearchParams()
  };

  var main = document.getElementById("main");
  var navTree = document.getElementById("navTree");
  var tocEl = document.getElementById("toc");
  var input = document.getElementById("q");
  var menuBtn = document.getElementById("menuBtn");
  var searchForm = document.getElementById("searchForm");

  // ------------------------------------------------------------ 工具

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (k === "class") node.className = attrs[k];
        else if (k === "text") node.textContent = attrs[k];
        else if (k === "html") node.innerHTML = attrs[k];
        else if (k.indexOf("on") === 0) node.addEventListener(k.slice(2), attrs[k]);
        else node.setAttribute(k, attrs[k]);
      });
    }
    (children || []).forEach(function (c) { if (c) node.appendChild(c); });
    return node;
  }

  function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

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

  function entriesWithKey(params, key, value) {
    var list = (params.get(key) || "").split(",").filter(Boolean);
    var i = list.indexOf(value);
    if (i >= 0) list.splice(i, 1); else list.push(value);
    if (list.length) params.set(key, list.join(",")); else params.delete(key);
    return params;
  }

  // ------------------------------------------------------------ 数据准备

  function labelMap(facet) {
    var m = {};
    ((state.index.facets[facet] || {}).values || []).forEach(function (v) { m[v.key] = v.label; });
    return m;
  }

  function prepare() {
    var idx = state.index;
    idx.nav.forEach(function (group) {
      group.items.forEach(function (item) {
        state.byLocation[item.location] = item;
        state.flat.push(item);
      });
    });
    state.locations = Object.keys(state.byLocation).sort(function (a, b) { return b.length - a.length; });
    var home = state.flat.filter(function (i) { return i.id === "intro-start-here"; })[0];
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
  }

  // ------------------------------------------------------------ 侧栏目录

  function buildNav() {
    clear(navTree);
    state.index.nav.forEach(function (group) {
      var list = el("ul", { class: "nav-list" });
      group.items.forEach(function (item) {
        var badge = item.complete && !item.questions
          ? el("span", { class: "nav-count", text: String(item.complete) }) : null;
        var a = el("a", { href: "#/doc/" + encodeURIComponent(item.location), title: item.title || "" },
          [document.createTextNode(item.title), badge]);
        a.dataset.location = item.location;
        list.appendChild(el("li", null, [a]));
      });
      navTree.appendChild(el("div", { class: "nav-group" }, [
        el("p", { class: "nav-group-title", text: group.label }),
        list
      ]));
    });
    navTree.appendChild(el("div", { class: "nav-group" }, [
      el("p", { class: "nav-group-title", text: "其它" }),
      el("ul", { class: "nav-list" }, [
        el("li", null, [el("a", { href: "#/browse", text: "按条件筛选全部条目" })]),
        el("li", null, [el("a", { href: "#/browse?q=", text: "搜索" })])
      ])
    ]));
  }

  function markActive(location) {
    Array.prototype.forEach.call(navTree.querySelectorAll("a"), function (a) {
      var on = a.dataset.location === location;
      a.classList.toggle("active", on);
      if (on) {
        var box = document.getElementById("sidebar");
        var top = a.offsetTop;
        if (top < box.scrollTop || top > box.scrollTop + box.clientHeight - 60) {
          box.scrollTop = Math.max(0, top - 120);
        }
      }
    });
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
    markActive(location);
    document.title = (item ? item.title : "机会与成长指南") + " · 机会与成长指南";

    return fetchContent(location).then(function (html) {
      main.innerHTML = html;
      var article = main.querySelector(".doc");
      if (item && item.last_verified && item.last_verified < state.index.stale_threshold) {
        article.insertBefore(el("p", { class: "notice", text:
          "本页最后核实于 " + item.last_verified + "，已经超过 12 个月，其中的制度性信息可能需要重新核实。" }),
          article.querySelector(".doc-header").nextSibling);
      }
      if (location === state.homeLocation) insertStats(article);
      buildToc();
      buildDocNav(location);
      focusTarget(entryId);
    }).catch(function (err) {
      clear(main);
      main.appendChild(el("p", { class: "empty", text: "内容加载失败（" + err.message + "）。如果是在本地打开，请用 http 方式访问，例如：python3 -m http.server 8000 --directory site" }));
      clear(tocEl);
    });
  }

  function insertStats(article) {
    var s = state.index.stats;
    var box = el("div", { class: "stats" }, [
      el("div", { class: "stat", html: "<b>" + s.complete + "</b>已写完条目" }),
      el("div", { class: "stat", html: "<b>" + state.index.nav[0].items.length + "</b>章节与入口" }),
      el("div", { class: "stat", html: "<b>" + s.todo + "</b>规划中条目" }),
      el("div", { class: "stat", html: "<b>" + state.index.generated_at.slice(0, 10) + "</b>页面构建日期" })
    ]);
    var header = article.querySelector(".doc-header");
    header.parentNode.insertBefore(box, header.nextSibling);
  }

  function buildToc() {
    clear(tocEl);
    var heads = main.querySelectorAll(".doc h2, .entry > h3");
    if (!heads.length) return;
    var list = el("ul", { class: "toc-list" });
    Array.prototype.forEach.call(heads, function (h) {
      var id = h.id || "";
      var a = el("a", { href: "#", text: h.textContent, "data-target": id });
      a.addEventListener("click", function (ev) {
        ev.preventDefault();
        var t = id ? main.querySelector("#" + CSS.escape(id)) : null;
        if (t) { t.scrollIntoView({ block: "start", behavior: "smooth" }); }
      });
      list.appendChild(el("li", { class: h.tagName === "H3" ? "lvl-3" : "lvl-2" }, [a]));
    });
    tocEl.appendChild(el("p", { class: "toc-title", text: "本页目录" }));
    tocEl.appendChild(list);
  }

  function buildDocNav(location) {
    var i = state.flat.map(function (x) { return x.location; }).indexOf(location);
    if (i < 0) return;
    var prev = state.flat[i - 1], next = state.flat[i + 1];
    var bar = el("div", { class: "doc-nav" }, [
      prev ? el("a", { href: "#/doc/" + encodeURIComponent(prev.location), text: "← " + prev.title }) : el("span", { text: "" }),
      next ? el("a", { href: "#/doc/" + encodeURIComponent(next.location), text: next.title + " →" }) : el("span", { text: "" })
    ]);
    main.querySelector(".doc").appendChild(bar);
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
      var have = e[key] || [];
      if (key === "effort") {
        if (want.indexOf(e.effort) < 0) return false;
      } else {
        var hit = want.some(function (v) { return have.indexOf(v) >= 0; });
        if (!hit) return false;
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
    var scored = filtered.map(function (e) { return { e: e, s: scoreEntry(e, tokens) }; })
      .filter(function (x) { return x.s >= 0; });
    scored.sort(function (a, b) { return b.s - a.s || a.e.title.localeCompare(b.e.title); });
    return scored.map(function (x) { return x.e; });
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
        entriesWithKey(next, facet, v.key);
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
    var head = el("div", { class: "browse-head" }, [
      el("h1", { text: "按条件筛选" }),
      el("p", { class: "browse-count", text: "共 " + results.length + " 条已写完的条目" +
        (q ? "，匹配「" + q + "」" : "") + "。多个条件可以叠加，同一组内为“或”。" })
    ]);
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

    main.appendChild(head);
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

  function route() {
    var h = parseHash();
    var parts = h.parts;
    document.body.classList.remove("sidebar-open");
    menuBtn.setAttribute("aria-expanded", "false");

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

  function bind() {
    input.addEventListener("input", onInput);
    searchForm.addEventListener("submit", function (ev) { ev.preventDefault(); onInput(); });
    menuBtn.addEventListener("click", function () {
      var open = document.body.classList.toggle("sidebar-open");
      menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.addEventListener("click", function (ev) {
      if (!document.body.classList.contains("sidebar-open")) return;
      if (ev.target.closest(".sidebar") || ev.target.closest(".menu-btn")) return;
      document.body.classList.remove("sidebar-open");
      menuBtn.setAttribute("aria-expanded", "false");
    });
    document.addEventListener("keydown", function (ev) {
      var tag = (ev.target.tagName || "").toLowerCase();
      var typing = tag === "input" || tag === "textarea";
      if (ev.key === "/" && !typing) { ev.preventDefault(); input.focus(); input.select(); }
      if (ev.key === "Escape" && typing) {
        input.value = "";
        if (location.hash.indexOf("#/browse") === 0) { location.hash = buildHash(["browse"], new URLSearchParams()); }
        input.blur();
      }
    });
    window.addEventListener("hashchange", function () { route(); });
  }

  fetch("data/index.json")
    .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
    .then(function (data) {
      state.index = data;
      prepare();
      buildNav();
      bind();
      route();
    })
    .catch(function (err) {
      clear(main);
      main.appendChild(el("p", { class: "empty", text:
        "索引加载失败（" + err.message + "）。请先生成站点：python3 tools/build.py，然后用 http 方式访问（python3 -m http.server 8000 --directory site）。" }));
    });
})();
