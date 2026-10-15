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
    visit(model.topics.concat(model.atlases, [model.resources]), "");
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
      // Secondary headings open the overview already present in the original
      // document. Only first-level groups receive a separate landing page.
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
      if (n.role) {
        model.topics.forEach(function (topic) {
          var refs = allOf(topic).filter(function (ref) { return ref.role === n.role; });
          if (!refs.length) return;
          var section = el("section", { class: "reader-resource-section" }, [el("h2", { text: topic.label })]);
          var list = el("ul", { class: "reader-resource-list" });
          refs.forEach(function (ref) { list.appendChild(resourceRow(ref, model.owners[ref.route])); });
          section.appendChild(list); container.appendChild(section);
        });
      } else {
        if (n.children.length) {
          if (n.intro_html) container.appendChild(el("h2", { id: "chapter-contents", text: "本章内容入口" }));
          var children = el("section", { class: "reader-task-list", "aria-label": "本组内容" });
          n.children.forEach(function (child) { children.appendChild(childLink(child)); });
          container.appendChild(children);
        }
        sections(n.refs, container, id);
      }
      if (n.intro_html) options.buildToc("");
      options.highlight(routeFor(id)); window.scrollTo(0, 0);
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
      if (owner && nodes[owner]) {
        var current = nodes[owner], currentLocation = record ? record.location : route.replace(/^#\/doc\//, "");
        var refs = current.refs.filter(function (ref) { return ref.route !== route && (ref.role !== "understand" || ref.location !== currentLocation); });
        var materials = el("section", { class: "reader-task-materials", "aria-label": "本组配套资料" });
        if (current.children.length) {
          materials.appendChild(label("继续深入"));
          current.children.forEach(function (child) { materials.appendChild(childLink(child)); });
        }
        if (refs.length) { materials.appendChild(label("本组配套资料")); sections(refs, materials, owner); }
        if (materials.children.length) article.appendChild(materials);
        var continuation = el("nav", { class: "reader-continue", "aria-label": "继续阅读" }, [
          label("继续阅读"), el("a", { href: routeFor(parents[owner] || owner), text: "← 返回「" + nodes[parents[owner] || owner].label + "」" })]);
        if (record && selected) continuation.appendChild(el("a", { class: "reader-full-chapter", href: "#/doc/" + record.location + "?from=" + owner, text: "阅读本组概览与全文 →" }));
        article.appendChild(continuation);
      }
    }
    document.body.classList.add("reader-enabled");
    return {
      handle: function (parts) { if (parts[0] === "guide") { guide(parts[1]); return true; } return false; },
      decorateArticle: decorateArticle,
      prepareSearch: function () { pageKind("search"); },
      isSingle: function () { return !!main.querySelector(".is-single-entry"); }
    };
  };
})();
