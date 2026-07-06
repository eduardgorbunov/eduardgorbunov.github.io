(function () {
  document.documentElement.classList.add("site-loaded");

  function fileName(url) {
    var name = url.pathname.split("/").pop();
    return name || "index.html";
  }

  function sameLocalPage(url) {
    return url.origin === window.location.origin && url.pathname === window.location.pathname;
  }

  function prefersReducedMotion() {
    return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function focusAnchorTarget(target) {
    if (!target.hasAttribute("tabindex")) {
      target.setAttribute("tabindex", "-1");
    }

    if (typeof target.focus !== "function") {
      return;
    }

    try {
      target.focus({ preventScroll: true });
    } catch (error) {
      target.focus();
    }
  }

  function textFromFirstMatch(container, selectors) {
    var index;
    for (index = 0; index < selectors.length; index += 1) {
      var match = container.querySelector(selectors[index]);
      if (match && match.textContent.trim()) {
        return match.textContent.trim();
      }
    }
    return "";
  }

  function setContextualActionLabels(options) {
    var cards = Array.prototype.slice.call(document.querySelectorAll(options.cardSelector));

    cards.forEach(function (card) {
      var title = textFromFirstMatch(card, options.titleSelectors);
      if (!title) {
        return;
      }

      Array.prototype.slice.call(card.querySelectorAll(options.linkSelector)).forEach(function (link) {
        var label = link.textContent.trim();
        if (!label || link.getAttribute("aria-label")) {
          return;
        }
        var ariaLabel = label + " for " + title;
        if (title === label || title.indexOf(label + " ") === 0 || title.indexOf(label + "(") === 0) {
          ariaLabel = title;
        }
        link.setAttribute("aria-label", ariaLabel);
      });
    });
  }

  function labelRepeatedActionLinks() {
    setContextualActionLabels({
      cardSelector: ".eg-activity-card",
      titleSelectors: ["h3", "h2"],
      linkSelector: ".eg-activity-actions a"
    });

    setContextualActionLabels({
      cardSelector: ".eg-publication-card",
      titleSelectors: ["h2", "h3"],
      linkSelector: ".eg-publication-actions a"
    });

    setContextualActionLabels({
      cardSelector: ".eg-news-card",
      titleSelectors: [".eg-news-title", "h2", "h3"],
      linkSelector: ".eg-news-actions-inline a, .eg-news-paper-links a"
    });

    setContextualActionLabels({
      cardSelector: ".eg-course-card",
      titleSelectors: ["h3"],
      linkSelector: ".eg-course-actions a, :scope > a"
    });

    setContextualActionLabels({
      cardSelector: ".eg-course-resource-card",
      titleSelectors: ["h3", "strong", ".eg-course-resource-body"],
      linkSelector: "a"
    });
  }

  function compactNewsArchiveAbstracts() {
    var abstracts = Array.prototype.slice.call(document.querySelectorAll(".eg-news-archive-list .eg-news-abstract"));

    abstracts.forEach(function (abstract, index) {
      var details = document.createElement("details");
      var summary = document.createElement("summary");

      details.className = "eg-news-abstract-disclosure";
      summary.textContent = "Abstract";
      summary.setAttribute("aria-label", "Toggle archived news abstract " + (index + 1));
      abstract.parentNode.insertBefore(details, abstract);
      details.appendChild(summary);
      details.appendChild(abstract);
    });
  }

  function markActiveNavigation() {
    var navAliases = {
      "amc2019.html": "teaching.html",
      "pr_th.html": "teaching.html"
    };
    var currentOriginalFile = fileName(window.location);
    var isAliasPage = Boolean(navAliases[currentOriginalFile]);
    var currentFile = navAliases[currentOriginalFile] || currentOriginalFile;
    var currentHash = window.location.hash;
    var links = Array.prototype.slice.call(document.querySelectorAll(".eg-sidebar .eg-nav-link[href]"));
    var exactHashMatches = [];
    var pageMatches = [];
    var sameFileMatches = [];
    var defaultSectionMatch = null;

    links.forEach(function (link) {
      link.classList.remove("is-active");
      link.removeAttribute("aria-current");

      var item = link.closest ? link.closest(".eg-nav-item") : null;
      if (item) {
        item.classList.remove("is-active");
      }
    });

    links.forEach(function (link) {
      var href = link.getAttribute("href");
      if (!href || href.indexOf("mailto:") === 0 || href.indexOf("http") === 0 || href.indexOf("assets/") === 0) {
        return;
      }

      var url = new URL(href, window.location.href);
      var linkFile = navAliases[fileName(url)] || fileName(url);
      var sameFile = linkFile === currentFile;

      if (!sameFile) {
        return;
      }

      sameFileMatches.push(link);

      if (currentFile === "conferences.html" && !currentHash && url.hash === "#talks") {
        defaultSectionMatch = link;
      }

      if (url.hash && url.hash === currentHash) {
        exactHashMatches.push(link);
      }

      if (!url.hash) {
        pageMatches.push(link);
      }
    });

    var bestMatch = exactHashMatches[0] || defaultSectionMatch || pageMatches[0] || sameFileMatches[0];

    if (bestMatch) {
      var currentValue = bestMatch.getAttribute("href").indexOf("#") === -1 && !isAliasPage ? "page" : "location";
      bestMatch.classList.add("is-active");
      bestMatch.setAttribute("aria-current", currentValue);

      var activeItem = bestMatch.closest ? bestMatch.closest(".eg-nav-item") : null;
      if (activeItem) {
        activeItem.classList.add("is-active");
      }
    }
  }
  labelRepeatedActionLinks();
  compactNewsArchiveAbstracts();
  markActiveNavigation();

  window.addEventListener("hashchange", markActiveNavigation);
  window.addEventListener("popstate", markActiveNavigation);

  document.addEventListener("click", function (event) {
    var link = event.target.closest ? event.target.closest("a[href]") : null;
    if (!link) {
      return;
    }

    var href = link.getAttribute("href");
    if (!href) {
      return;
    }

    var url;
    try {
      url = new URL(href, window.location.href);
    } catch (error) {
      return;
    }

    if (!url.hash || !sameLocalPage(url)) {
      return;
    }

    var target = document.getElementById(decodeURIComponent(url.hash.slice(1)));
    if (!target) {
      return;
    }

    event.preventDefault();

    if (window.history && window.history.pushState) {
      window.history.pushState(null, "", url.hash);
      markActiveNavigation();
    } else {
      window.location.hash = url.hash;
    }

    target.scrollIntoView({ behavior: prefersReducedMotion() ? "auto" : "smooth", block: "start" });
    focusAnchorTarget(target);
  });
})();
