(function () {
  var cards = Array.prototype.slice.call(document.querySelectorAll(".eg-publication-list .eg-publication-card"));
  var labelledCards = Array.prototype.slice.call(document.querySelectorAll(".eg-publication-list .eg-publication-card, .eg-book-card"));
  var typeFilter = document.querySelector(".eg-publication-type-filter");
  var markerFilter = document.querySelector(".eg-publication-marker-filter");
  var tagFilter = document.querySelector(".eg-publication-tag-filter");
  var searchFilter = document.querySelector(".eg-publication-search-filter");
  var filterForm = document.querySelector(".eg-publication-controls");
  var activeTagList = document.querySelector(".eg-active-tag-list");
  var clearButton = document.querySelector(".eg-clear-filters");
  var count = document.getElementById("publication-count");
  var countLabel = document.getElementById("publication-count-label");
  var filterSummary = document.getElementById("publication-filter-summary");
  var empty = document.querySelector(".eg-publication-empty");
  var overviewStats = Array.prototype.slice.call(document.querySelectorAll(".eg-publication-stat"));
  var venueStats = Array.prototype.slice.call(document.querySelectorAll(".eg-conference-summary [data-venue]"));
  var abstractToggle = document.querySelector(".eg-abstract-toggle");
  var selectedTags = [];
  var authorMarkerClasses = {
    "team": "eg-author-relation-team",
    "visitor": "eg-author-relation-visitor",
    "external-bsc": "eg-author-relation-external-bsc",
    "external-msc": "eg-author-relation-external-msc",
    "external-phd": "eg-author-relation-external-phd",
    "external-researcher": "eg-author-relation-external-researcher"
  };

  if (!cards.length || !typeFilter) {
    return;
  }

  function uniqueValues(values) {
    return values.filter(function (value, index, array) {
      return value && array.indexOf(value) === index;
    });
  }

  function labelForTag(tag) {
    if (!tagFilter) {
      return tag;
    }

    var option = Array.prototype.filter.call(tagFilter.options, function (candidate) {
      return candidate.value === tag;
    })[0];

    return option ? option.textContent.trim() : tag;
  }

  function labelForMarker(marker) {
    return labelForSelectValue(markerFilter, marker);
  }

  function labelForSelectValue(select, value) {
    if (!select) {
      return value;
    }

    var option = Array.prototype.filter.call(select.options, function (candidate) {
      return candidate.value === value;
    })[0];

    return option ? option.textContent.trim() : value;
  }

  function hasOption(select, value) {
    return Array.prototype.some.call(select.options, function (option) {
      return option.value === value;
    });
  }

  function escapeRegExp(value) {
    return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function venuePattern(venue) {
    return new RegExp("\\b" + escapeRegExp(venue) + "\\b");
  }

  function normalizeSearch(value) {
    return (value || "").toLowerCase().replace(/\s+/g, " ").trim();
  }

  function normalizeMarkerValue(value) {
    var normalized = normalizeSearch(value).replace(/\s+/g, "-");
    var aliases = {
      "t": "team",
      "team-member": "team",
      "team-student": "team",
      "current-team-student": "team",
      "v": "visitor",
      "visiting-student": "visitor",
      "eb": "external-bsc",
      "externally-mentored-bsc-student": "external-bsc",
      "em": "external-msc",
      "externally-mentored-msc-student": "external-msc",
      "ep": "external-phd",
      "externally-mentored-phd-student": "external-phd",
      "er": "external-researcher",
      "externally-mentored-postdoc-or-research-assistant": "external-researcher"
    };

    return aliases[normalized] || normalized;
  }

  function searchTextForCard(card) {
    var tagLabels = (card.getAttribute("data-tags") || "")
      .split(/\s+/)
      .filter(Boolean)
      .map(labelForTag)
      .join(" ");
    var authorMarkerLabels = cardAuthorMarkers(card).map(labelForMarker).join(" ");
    var fields = [
      card.querySelector("h2") ? card.querySelector("h2").textContent : "",
      card.querySelector(".eg-publication-authors") ? card.querySelector(".eg-publication-authors").textContent : "",
      card.querySelector(".eg-publication-venue") ? card.querySelector(".eg-publication-venue").textContent : "",
      card.querySelector(".eg-publication-meta") ? card.querySelector(".eg-publication-meta").textContent : "",
      tagLabels,
      authorMarkerLabels
    ];

    return normalizeSearch(fields.join(" "));
  }

  function cardAuthorMarkers(card) {
    return Object.keys(authorMarkerClasses).filter(function (marker) {
      return Boolean(card.querySelector("." + authorMarkerClasses[marker]));
    });
  }

  function searchMatches(card, query) {
    return !query || searchTextForCard(card).indexOf(query) !== -1;
  }

  function isMainConferenceVenue(card, venueText) {
    var isConferencePaper = card.getAttribute("data-type") === "conference paper";
    var normalizedVenue = venueText.toLowerCase();
    return isConferencePaper && normalizedVenue.indexOf("workshop") === -1 && normalizedVenue.indexOf("short version") === -1;
  }

  function updatePublicationSummaries() {
    var typeCounts = {};
    var venueCounts = {};

    cards.forEach(function (card) {
      var cardType = card.getAttribute("data-type");
      if (cardType) {
        typeCounts[cardType] = (typeCounts[cardType] || 0) + 1;
      }

      var venueText = "";
      var venue = card.querySelector(".eg-publication-venue");
      if (venue) {
        venueText = venue.textContent;
      }

      venueStats.forEach(function (item) {
        var venueName = item.getAttribute("data-venue");
        if (venueName && isMainConferenceVenue(card, venueText) && venuePattern(venueName).test(venueText)) {
          venueCounts[venueName] = (venueCounts[venueName] || 0) + 1;
        }
      });
    });

    overviewStats.forEach(function (stat) {
      var target = stat.querySelector("strong");
      var type = stat.getAttribute("data-count-type");
      var value = stat.getAttribute("data-count-all") === "true" ? cards.length : (typeCounts[type] || 0);
      if (target) {
        target.textContent = String(value);
      }
    });

    venueStats.forEach(function (item) {
      var target = item.querySelector("strong");
      var venueName = item.getAttribute("data-venue");
      if (target && venueName) {
        target.textContent = String(venueCounts[venueName] || 0);
      }
    });
  }

  function readFilterParams() {
    return new URLSearchParams(window.location.search);
  }

  function tagsFromParams(params) {
    var values = params.getAll("tag");
    var grouped = params.get("tags");
    if (grouped) {
      values = values.concat(grouped.split(","));
    }
    return uniqueValues(values
      .map(function (value) { return value.trim(); })
      .filter(Boolean));
  }

  function validTagsFromParams(params) {
    if (!tagFilter) {
      return [];
    }

    return tagsFromParams(params).filter(function (tag) {
      return hasOption(tagFilter, tag);
    });
  }

  function activeTags() {
    return uniqueValues(selectedTags);
  }

  function addTag(tag) {
    if (!tag || tag === "all" || selectedTags.indexOf(tag) !== -1) {
      return;
    }
    selectedTags.push(tag);
  }

  function removeTag(tag) {
    selectedTags = selectedTags.filter(function (value) { return value !== tag; });
  }

  function renderActiveTags() {
    if (!activeTagList) {
      return;
    }

    activeTagList.innerHTML = "";
    var tags = activeTags();
    activeTagList.classList.toggle("is-empty", !tags.length);
    activeTagList.setAttribute("aria-label", tags.length ? "Selected topic tags" : "No topic tags selected");
    if (!tags.length) {
      var emptyState = document.createElement("span");
      emptyState.className = "eg-visually-hidden";
      emptyState.textContent = "No topic tags selected";
      activeTagList.appendChild(emptyState);
      return;
    }

    tags.forEach(function (tag) {
      var chip = document.createElement("button");
      chip.type = "button";
      chip.className = "eg-active-tag-chip";
      chip.setAttribute("data-tag", tag);
      chip.setAttribute("aria-label", "Remove topic tag " + labelForTag(tag));
      chip.setAttribute("aria-controls", "publication-list publication-count-status publication-filter-summary");
      chip.textContent = labelForTag(tag);
      chip.addEventListener("click", function () {
        removeTag(tag);
        applyFilters("push");
      });
      activeTagList.appendChild(chip);
    });
  }

  function enhanceActionLabels() {
    labelledCards.forEach(function (card) {
      var heading = card.querySelector("h2");
      var title = heading ? heading.textContent.trim() : "";
      if (!title) {
        return;
      }

      Array.prototype.slice.call(card.querySelectorAll(".eg-publication-actions a, .eg-book-actions a"))
        .forEach(function (link) {
          var label = link.textContent.trim();
          if (label && !link.getAttribute("aria-label")) {
            link.setAttribute("aria-label", label + " for " + title);
          }
        });
    });
  }

  function enhanceAbstractLabels() {
    cards.forEach(function (card) {
      var heading = card.querySelector("h2");
      var summary = card.querySelector(".eg-publication-abstract summary");
      var title = heading ? heading.textContent.trim() : "";
      if (!summary || !title || summary.getAttribute("aria-label")) {
        return;
      }
      summary.setAttribute("aria-label", "Toggle abstract for " + title);
    });
  }

  function updateAbstractDisclosureState(details) {
    var summary = details.querySelector("summary");
    if (!summary) {
      return;
    }

    summary.setAttribute("aria-expanded", details.open ? "true" : "false");
  }

  function abstractDetails(visibleOnly) {
    var details = Array.prototype.slice.call(document.querySelectorAll(".eg-publication-list .eg-publication-abstract"));
    if (!visibleOnly) {
      return details;
    }

    return details.filter(function (item) {
      var card = item.closest ? item.closest(".eg-publication-card") : null;
      return card && !card.hidden;
    });
  }

  function updateAbstractToggleState() {
    if (!abstractToggle) {
      return;
    }

    var details = abstractDetails(true);
    var allOpen = details.length > 0 && details.every(function (item) {
      return item.open;
    });

    abstractToggle.disabled = !details.length;
    abstractToggle.setAttribute("aria-pressed", allOpen ? "true" : "false");
    abstractToggle.textContent = allOpen ? "Collapse abstracts" : "Expand abstracts";
  }

  function setAllAbstracts(open) {
    var details = abstractDetails(true);
    details.forEach(function (item) {
      item.open = open;
      updateAbstractDisclosureState(item);
    });
    updateAbstractToggleState();

    if (open && window.MathJax && window.MathJax.typesetPromise) {
      window.MathJax.typesetPromise(details);
    }
  }

  function enhanceAbstractStates() {
    cards.forEach(function (card) {
      var details = card.querySelector(".eg-publication-abstract");
      if (!details) {
        return;
      }

      updateAbstractDisclosureState(details);
      details.addEventListener("toggle", function () {
        updateAbstractDisclosureState(details);
        updateAbstractToggleState();
      });
    });
    updateAbstractToggleState();
  }

  function updateClearState() {
    if (!clearButton) {
      return;
    }

    var hasActiveSearch = searchFilter && normalizeSearch(searchFilter.value);
    var hasActiveMarker = markerFilter && markerFilter.value !== "all";
    var hasActiveFilter = typeFilter.value !== "all" || hasActiveMarker || activeTags().length > 0 || Boolean(hasActiveSearch);
    clearButton.disabled = !hasActiveFilter;
    clearButton.hidden = !hasActiveFilter;
    clearButton.classList.toggle("is-available", hasActiveFilter);
  }

  function updateFilterSummary(selectedType, selectedMarker, selectedActiveTags, searchQuery) {
    if (!filterSummary) {
      return;
    }

    var parts = [];
    if (selectedType !== "all") {
      parts.push("type: " + labelForSelectValue(typeFilter, selectedType));
    }
    if (selectedMarker !== "all") {
      parts.push("author marker: " + labelForMarker(selectedMarker));
    }
    if (selectedActiveTags.length) {
      parts.push("tags: " + selectedActiveTags.map(labelForTag).join(", "));
    }
    if (searchQuery) {
      parts.push("search: \"" + searchQuery + "\"");
    }

    filterSummary.textContent = parts.length ? "Active filters: " + parts.join("; ") + "." : "No filters applied.";
  }

  function updateVenueButtonState(selectedType, searchQuery) {
    venueStats.forEach(function (button) {
      var venueName = button.getAttribute("data-venue") || "";
      var active = selectedType === "conference paper" && normalizeSearch(venueName) === searchQuery;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", active ? "true" : "false");
    });
  }

  function applyVenueFilter(venueName) {
    if (!venueName || !searchFilter) {
      return;
    }

    typeFilter.value = "conference paper";
    if (markerFilter) {
      markerFilter.value = "all";
    }
    selectedTags = [];
    if (tagFilter) {
      tagFilter.value = "all";
    }
    searchFilter.value = venueName;
    applyFilters("push");
  }

  function resetFilters(syncMode) {
    typeFilter.value = "all";
    if (markerFilter) {
      markerFilter.value = "all";
    }
    selectedTags = [];
    if (searchFilter) {
      searchFilter.value = "";
    }
    if (tagFilter) {
      tagFilter.value = "all";
    }
    applyFilters(syncMode);
  }

  function syncUrl(mode) {
    if (!window.history || !window.history.replaceState) {
      return;
    }

    var params = new URLSearchParams(window.location.search);
    params.delete("tag");
    params.delete("tags");
    params.delete("type");
    params.delete("marker");
    params.delete("q");

    if (typeFilter.value !== "all") {
      params.set("type", typeFilter.value);
    }
    if (markerFilter && markerFilter.value !== "all") {
      params.set("marker", markerFilter.value);
    }
    if (searchFilter && normalizeSearch(searchFilter.value)) {
      params.set("q", normalizeSearch(searchFilter.value));
    }
    activeTags().forEach(function (tag) {
      params.append("tag", tag);
    });

    var query = params.toString();
    var nextUrl = window.location.pathname + (query ? "?" + query : "") + window.location.hash;
    var currentUrl = window.location.pathname + window.location.search + window.location.hash;
    var shouldPush = mode === "push" && window.history.pushState && nextUrl !== currentUrl;
    window.history[shouldPush ? "pushState" : "replaceState"](null, "", nextUrl);
  }

  function applyFilters(syncMode) {
    var selectedType = typeFilter.value;
    var selectedMarker = markerFilter ? markerFilter.value : "all";
    var selectedActiveTags = activeTags();
    var searchQuery = searchFilter ? normalizeSearch(searchFilter.value) : "";
    var visible = 0;

    cards.forEach(function (card) {
      var cardType = card.getAttribute("data-type");
      var cardTags = (card.getAttribute("data-tags") || "").split(/\s+/);
      var cardMarkers = cardAuthorMarkers(card);
      var typeMatches = selectedType === "all" || cardType === selectedType;
      var markerMatches = selectedMarker === "all" || cardMarkers.indexOf(selectedMarker) !== -1;
      var tagsMatch = selectedActiveTags.every(function (tag) {
        return cardTags.indexOf(tag) !== -1;
      });
      var show = typeMatches && markerMatches && tagsMatch && searchMatches(card, searchQuery);

      card.hidden = !show;
      if (show) {
        visible += 1;
      }
    });

    if (tagFilter) {
      tagFilter.value = "all";
    }
    renderActiveTags();

    if (count) {
      count.textContent = String(visible);
    }
    if (countLabel) {
      countLabel.textContent = visible === 1 ? "publication shown" : "publications shown";
    }
    updateFilterSummary(selectedType, selectedMarker, selectedActiveTags, searchQuery);
    updateVenueButtonState(selectedType, searchQuery);
    if (empty) {
      empty.hidden = visible !== 0;
    }

    updateClearState();
    updateAbstractToggleState();
    if (syncMode) {
      syncUrl(syncMode);
    }
  }

  function applyUrlState(syncMode) {
    var params = readFilterParams();
    var selectedInitialType = params.get("type");
    var selectedInitialMarker = normalizeMarkerValue(params.get("marker"));
    var selectedInitialSearch = params.get("q");

    typeFilter.value = selectedInitialType && hasOption(typeFilter, selectedInitialType) ? selectedInitialType : "all";
    if (markerFilter) {
      markerFilter.value = selectedInitialMarker && hasOption(markerFilter, selectedInitialMarker) ? selectedInitialMarker : "all";
    }
    if (searchFilter) {
      searchFilter.value = normalizeSearch(selectedInitialSearch);
    }
    selectedTags = validTagsFromParams(params);
    if (tagFilter) {
      tagFilter.value = "all";
    }
    applyFilters(syncMode);
  }

  venueStats.forEach(function (button) {
    button.setAttribute("aria-pressed", "false");
    button.addEventListener("click", function () {
      applyVenueFilter(button.getAttribute("data-venue"));
    });
  });

  if (abstractToggle) {
    abstractToggle.addEventListener("click", function () {
      setAllAbstracts(abstractToggle.getAttribute("aria-pressed") !== "true");
    });
  }

  typeFilter.addEventListener("change", function () {
    applyFilters("push");
  });

  if (markerFilter) {
    markerFilter.addEventListener("change", function () {
      applyFilters("push");
    });

    markerFilter.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        event.preventDefault();
        resetFilters("push");
      }
    });
  }

  if (searchFilter) {
    searchFilter.addEventListener("input", function () {
      applyFilters("replace");
    });

    searchFilter.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        event.preventDefault();
        resetFilters("push");
      }
    });
  }

  if (tagFilter) {
    tagFilter.addEventListener("change", function () {
      addTag(tagFilter.value);
      applyFilters("push");
    });

    tagFilter.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        event.preventDefault();
        resetFilters("push");
      }
    });
  }

  typeFilter.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      event.preventDefault();
      resetFilters("push");
    }
  });

  if (clearButton) {
    clearButton.addEventListener("click", function () {
      resetFilters("push");
    });
  }

  if (filterForm) {
    filterForm.addEventListener("submit", function (event) {
      event.preventDefault();
      applyFilters("push");
    });
  }

  window.addEventListener("popstate", function () {
    applyUrlState(false);
  });

  updatePublicationSummaries();
  enhanceActionLabels();
  enhanceAbstractLabels();
  enhanceAbstractStates();
  applyUrlState("replace");
}());
