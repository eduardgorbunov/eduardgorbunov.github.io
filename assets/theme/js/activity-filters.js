(function () {
  var cards = Array.prototype.slice.call(document.querySelectorAll(".eg-activity-card"));
  var yearFilter = document.getElementById("activity-year-filter");
  var searchFilter = document.getElementById("activity-search-filter");
  var clearButton = document.querySelector(".eg-activity-clear");
  var status = document.getElementById("activity-filter-status");
  var archives = Array.prototype.slice.call(document.querySelectorAll(".eg-activity-archive"));

  if (!cards.length || !yearFilter || !searchFilter) {
    return;
  }

  function normalize(value) {
    return (value || "").toLowerCase().replace(/\s+/g, " ").trim();
  }

  function cardYear(card) {
    var meta = card.querySelector(".eg-activity-meta");
    var match = meta ? meta.textContent.match(/\b(20\d{2})\b/g) : null;
    return match ? match[match.length - 1] : "";
  }

  cards.map(cardYear).filter(Boolean).filter(function (year, index, values) {
    return values.indexOf(year) === index;
  }).sort(function (left, right) {
    return Number(right) - Number(left);
  }).forEach(function (year) {
    var option = document.createElement("option");
    option.value = year;
    option.textContent = year;
    yearFilter.appendChild(option);
  });

  function updateArchives(active) {
    archives.forEach(function (archive) {
      var visible = Array.prototype.some.call(archive.querySelectorAll(".eg-activity-card"), function (card) {
        return !card.hidden;
      });
      archive.hidden = active && !visible;
      if (active && visible) {
        archive.open = true;
        archive.setAttribute("data-filter-opened", "true");
      } else if (!active && archive.getAttribute("data-filter-opened") === "true") {
        archive.open = false;
        archive.removeAttribute("data-filter-opened");
      }
    });
  }

  function applyFilters() {
    var selectedYear = yearFilter.value;
    var query = normalize(searchFilter.value);
    var active = selectedYear !== "all" || Boolean(query);
    var visible = 0;

    cards.forEach(function (card) {
      var yearMatches = selectedYear === "all" || cardYear(card) === selectedYear;
      var searchMatches = !query || normalize(card.textContent).indexOf(query) !== -1;
      card.hidden = !(yearMatches && searchMatches);
      if (!card.hidden) {
        visible += 1;
      }
    });

    updateArchives(active);
    clearButton.hidden = !active;
    clearButton.disabled = !active;
    status.textContent = visible + (visible === 1 ? " presentation shown" : " presentations shown");
  }

  yearFilter.addEventListener("change", applyFilters);
  searchFilter.addEventListener("input", applyFilters);
  clearButton.addEventListener("click", function () {
    yearFilter.value = "all";
    searchFilter.value = "";
    applyFilters();
    searchFilter.focus();
  });

  [yearFilter, searchFilter].forEach(function (control) {
    control.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        yearFilter.value = "all";
        searchFilter.value = "";
        applyFilters();
      }
    });
  });

  applyFilters();
}());
