/* One reading catalogue: first-level guides, existing bodies and task resources. */
(function () {
  "use strict";
  window.HandbookReader = function (options) {
    var index = options.index, model = index.reader, main = options.main, toc = options.toc, el = options.el;
    var nodes = {}, parents = {};
    var roleOrder = ["understand", "guide", "steps", "timeline", "tool", "case", "risk"];
    function visit(items, parent) {
      items.forEach(function (n) {
        nodes[n.id] = n;
        if (parent) parents[n.id] = parent;
        visit(n.children || [], n.id);
      });
    }
    visit([model.map].concat(model.topics, model.atlases, [model.resources]), "");
    var standalone = new Set();
    (function collect(n) { standalone.add(n.id); n.children.forEach(collect); })(model.resources);
    var chapterCache = {};
    function path(id) {
      var out = [];
      while (id && nodes[id]) { out.unshift(nodes[id]); id = parents[id]; }
      return out;
    }
    function routeFor(id) { return "#/guide/" + encodeURIComponent(id); }
    function allOf(n) { return (n.refs || []).concat.apply(n.refs || [], (n.children || []).map(allOf)); }
    function pageKind(kind) {
      document.body.classList.toggle("reader-overview", kind !== "article");
      main.dataset.view = kind;
      toc.replaceChildren();
    }
    function label(text) { return el("p", { class: "reader-section-label", text: text }); }
    function breadcrumb(items) {
      var b = el("nav", { class: "reader-breadcrumb", "aria-label": "当前位置" });
      b.appendChild(el("a", { href: "#/", text: "机会手册" }));
      items.forEach(function (item) {
        b.appendChild(el("span", { class: "crumb-divider", "aria-hidden": "true", text: "/" }));
        b.appendChild(el("a", { href: routeFor(item.id), text: item.label }));
      });
      return b;
    }
    function header(kicker, title, summary) {
      return el("header", { class: "reader-page-header" }, [label(kicker), el("h1", { text: title }),
        summary ? el("p", { class: "reader-intro", text: summary }) : null]);
    }
    function childLink(n) {
      return el("a", { href: routeFor(n.id), class: "reader-task-row" }, [
        el("span", { class: "reader-link-main" }, [el("span", { class: "reader-link-title", text: n.label }),
          n.summary ? el("span", { class: "reader-link-summary", text: n.summary }) : null]),
        el("span", { class: "reader-link-arrow", "aria-hidden": "true", text: "→" })]);
    }
    function resourceRow(ref, from) {
      return el("li", { class: "reader-resource" }, [
        el("a", { href: ref.route + (from ? "?from=" + encodeURIComponent(from) : ""), text: ref.title }),
        ref.summary ? el("p", { text: ref.summary }) : null]);
    }
    function sections(refs, container, owner) {
      roleOrder.forEach(function (role) {
        var selected = refs.filter(function (ref) { return ref.role === role; });
        if (!selected.length) return;
        var section = el("section", { class: "reader-resource-section" }, [el("h2", { text: model.roles[role] })]);
        var list = el("ul", { class: "reader-resource-list" });
        selected.forEach(function (ref) { list.appendChild(resourceRow(ref, owner || model.owners[ref.route])); });
        section.appendChild(list); container.appendChild(section);
      });
    }
    function guide(id) {
      var n = nodes[id];
      if (!n) {
        pageKind("missing");
        main.replaceChildren(header("找不到这个入口", "从目录继续查找", "这个分组可能已经调整。"), el("a", { href: "#/", text: "返回首页 →" }));
        return;
      }
      if (n.document) {
        // 带上 from：文档可能是几个入口共用的（例如 00 章分给多个分组），
        // 没有它前端就只能按文档前缀猜归属，高亮会落到别的组上。
        var sep = n.document.indexOf("?") < 0 ? "?from=" : "&from=";
        options.openOverview(n.document + sep + encodeURIComponent(id));
        return;
      }
      if (n.chapter_root) {
        options.openOverview("#/chapter/" + n.chapter_root + (n.chapter_anchor ? "?section=" + encodeURIComponent(n.chapter_anchor) : ""));
        return;
      }
      // Task headings keep their existing overview and body. Resource guides
      // use authored prose, just like the first-level chapter introductions.
      if (parents[id] && n.refs.length && !n.role) {
        options.openOverview(n.overview + "?from=" + encodeURIComponent(id));
        return;
      }
      pageKind("guide"); main.replaceChildren(); document.title = n.label + " · 机会手册";
      var container = main;
      if (n.intro_html) {
        pageKind("article");
        container = el("article", { class: "doc reader-chapter-overview" });
        main.appendChild(container);
      }
      container.appendChild(breadcrumb(path(id).slice(0, -1)));
      var pageHeader = header(parents[id] ? "资料目录" : "本组概览", n.label, n.summary);
      if (n.intro_html) pageHeader.className = "doc-header";
      container.appendChild(pageHeader);
      if (n.intro_html) container.insertAdjacentHTML("beforeend", n.intro_html);
      appendPager(container, routeFor(id));
      options.highlight(routeFor(id), { nodeId: id }); window.scrollTo(0, 0);
      options.mountReading({ route: routeFor(id), nodeId: id });
    }
    function routeKey(route) {
      try { return decodeURI(route); } catch (_) { return route; }
    }
    function appendPager(container, route) {
      var sequence = model.reading_order, key = routeKey(route);
      var i = sequence.findIndex(function (item) { return routeKey(item.route) === key; });
      if (i < 0) i = sequence.findIndex(function (item) { return routeKey(item.route).split("?")[0] === key.split("?")[0]; });
      if (i < 0) return;
      var prev = sequence[i - 1], next = sequence[i + 1];
      container.appendChild(el("nav", { class: "doc-nav", "aria-label": "按目录顺序阅读" }, [
        prev ? el("a", { href: prev.route, rel: "prev", text: "← " + prev.title }) : el("span"),
        next ? el("a", { href: next.route, rel: "next", text: next.title + " →" }) : el("span") ]));
    }
    function resolveDocument(route, params) {
      var from = params && params.get("from"), n = from && nodes[from];
      if (standalone.has(from)) return "";
      if (model.chapter_aliases[route]) return model.chapter_aliases[route];
      if (n && n.chapter_root && (n.overview === route || n.document === route)) return "#/chapter/" + n.chapter_root;
      var target = model.chapter_for[route];
      return target ? "#/chapter/" + target.chapter + "?section=" + encodeURIComponent(target.section) : "";
    }
    function chapter(id, params) {
      var n = nodes[id];
      if (n && n.chapter_root && n.chapter_root !== id) {
        options.openOverview("#/chapter/" + n.chapter_root + "?section=" + encodeURIComponent(n.chapter_anchor)); return;
      }
      if (!model.chapters[id]) { guide("missing"); return; }
      var expected = location.hash, route = "#/chapter/" + id;
      function show(html) {
        if (location.hash !== expected) return;
        pageKind("article");
        var article = main.querySelector('.reader-assembled-chapter[data-chapter="' + CSS.escape(id) + '"]');
        if (!article) {
          main.innerHTML = html;
          article = main.querySelector(".doc");
          article.insertBefore(breadcrumb(path(id)), article.firstChild);
          appendPager(article, route);
        }
        document.title = n.label + " · 机会手册";
        var section = params.get("section"), target = section && document.getElementById(section);
        if (!target || !article.contains(target)) window.scrollTo(0, 0);
        options.highlight(route, { nodeId: id });
        options.mountReading({ route: route, nodeId: id, chapter: true });
        if (target && article.contains(target)) {
          options.jumpToHeading(target);
          if (target.dataset.navId) options.highlight(route + "?section=" + encodeURIComponent(section), { nodeId: target.dataset.navId });
        }
        else { window.scrollTo(0, 0); options.highlight(route, { nodeId: id, follow: true }); }
      }
      if (main.querySelector('.reader-assembled-chapter[data-chapter="' + CSS.escape(id) + '"]')) { show(""); return; }
      if (!chapterCache[id]) chapterCache[id] = fetch("chapters/" + encodeURIComponent(id) + ".html?v=" + encodeURIComponent(index.generated_at), { cache: "no-cache" })
        .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.text(); })
        .catch(function (error) { delete chapterCache[id]; throw error; });
      chapterCache[id].then(show).catch(function () {
        if (location.hash !== expected) return;
        main.replaceChildren(el("p", { role: "alert", text: "章节暂时无法加载，请重试。" }));
      });
    }
    function decorateArticle(article, entryId, route, params) {
      pageKind("article");
      var requested = params && params.get("from"), owner = model.owners[route];
      if (requested && nodes[requested] && (nodes[requested].overview === route || allOf(nodes[requested]).some(function (ref) { return ref.route === route; }))) owner = requested;
      if (!owner) {
        var match = Object.keys(model.owners).find(function (key) { return key.indexOf(route + "/") === 0; });
        owner = match ? model.owners[match] : "";
      }
      var record = index.entries.find(function (entry) { return entry.id === entryId; });
      var selected = entryId && Array.from(article.querySelectorAll("section.entry")).find(function (section) { return section.id === entryId; });
      if (!entryId && requested && nodes[owner]) {
        var allowed = new Set(allOf(nodes[owner]).map(function (ref) { return ref.id; }));
        article.querySelectorAll("section.entry").forEach(function (entry) { if (!allowed.has(entry.id)) entry.hidden = true; });
      }
      if (selected && record) {
        article.classList.add("is-single-entry");
        Array.from(article.children).forEach(function (child) { if (child !== selected && !child.classList.contains("doc-header")) child.hidden = true; });
        article.querySelector(".doc-header h1").textContent = record.title;
        var summary = article.querySelector(".doc-summary");
        if (summary) summary.textContent = record.summary;
        var verified = article.querySelector(".doc-meta .chip-verified");
        if (verified) verified.textContent = "最后核实：" + record.last_verified;
        var badges = selected.querySelector(".entry-badges");
        if (badges) {
          var metadata = el("details", { class: "reader-article-meta" }, [el("summary", { text: "适用范围与依据" })]);
          badges.replaceWith(metadata); metadata.appendChild(badges);
        }
        document.title = record.title + " · 机会手册";
        window.scrollTo(0, 0);
      }
      article.insertBefore(breadcrumb(path(owner)), article.firstChild);
      if (owner && nodes[owner] && owner !== "content-map") {
        var current = nodes[owner];
        // 这里只保留「继续深入」（子栏目入口）。原先这里还会把本组的其他条目
        // 按角色列成「本组配套资料」，但左栏已经列了同一批，重复且很长；
        // 需要哪篇资料时，从左栏或文章自身的「相关」里进更直接。
        var materials = el("section", { class: "reader-task-materials", "aria-label": "继续深入" });
        if (current.children.length) {
          materials.appendChild(label("继续深入"));
          current.children.forEach(function (child) { materials.appendChild(childLink(child)); });
        }
        if (materials.children.length) article.appendChild(materials);
      }
      var ownerNode = nodes[owner];
      var overview = requested && ownerNode && ownerNode.overview === route;
      appendPager(article, route + (overview && !entryId ? "?from=" + owner : ""));
      var ref = ownerNode && allOf(ownerNode).find(function (item) { return item.route === route; });
      var independent = standalone.has(requested);
      if (independent) {
        article.querySelectorAll('a[href^="#/doc/"]').forEach(function (a) {
          var destination = routeKey(a.getAttribute("href")).split("?")[0];
          var library = model.libraries.find(function (item) { return item.refs.some(function (r) { return r.route === destination; }); });
          if (library) a.href = destination + "?from=" + library.id;
        });
      }
      return { route: route, nodeId: independent && ref ? requested + "--" + ref.id : (owner === "content-map" ? owner : (overview ? owner : (ref ? ref.id : owner))),
        entryId: entryId, fixedNode: independent, isMap: owner === "content-map" };
    }
    document.body.classList.add("reader-enabled");
    return {
      handle: function (parts, params) {
        if (parts[0] === "guide") { guide(parts[1]); return true; }
        if (parts[0] === "chapter") { chapter(parts[1], params || new URLSearchParams()); return true; }
        return false;
      },
      resolveDocument: resolveDocument,
      decorateArticle: decorateArticle,
      appendPager: appendPager,
      prepareSearch: function () { pageKind("search"); },
      isSingle: function () { return !!main.querySelector(".is-single-entry"); }
    };
  };
})();
