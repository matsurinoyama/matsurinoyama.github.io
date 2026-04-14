(function () {
  var lang = document.documentElement.lang === "ja" ? "ja" : "en";
  var base = document.documentElement.dataset.staticBase || "/static";
  var t = TRANSLATIONS[lang].resume;
  var s = t.sections;

  document.title = t.pageTitle;

  // Build full resume structure
  var wrap = document.querySelector(".resume-wrap");
  wrap.innerHTML =
    '<a class="back-nav" href="' + t.backHref + '">' + t.backNav + "</a>" +
    '<div class="resume-hero">' +
      '<div class="resume-picture-wrap">' +
        '<img src="' + base + '/profile.jpg" alt="' + t.profileAlt + '" class="resume-picture" />' +
        '<div class="resume-picture-gradient" aria-hidden="true"></div>' +
      "</div>" +
      '<div class="resume-hero-content">' +
        '<div class="resume-header">' +
          "<div>" +
            '<div class="resume-name">' + t.name + "</div>" +
          "</div>" +
          '<div class="resume-contact">' +
            '<img src="' + base + '/temp-h.svg" alt="logo" class="resume-logo" />' +
          "</div>" +
        "</div>" +
      "</div>" +
    "</div>" +
    '<div class="resume-overview">' +
      t.overview.map(function (p) { return "<div>" + p + "</div>"; }).join("") +
    "</div>" +
    '<hr class="divider" />' +
    '<div class="section-title">' + s.exhibitions + "</div>" +
    '<div class="subsection-label">' + s.group + "</div>" +
    '<div id="entries-group"></div>' +
    '<div class="subsection-label">' + s.awards + "</div>" +
    '<div id="entries-awards"></div>' +
    '<div class="subsection-label">' + s.scholarships + "</div>" +
    '<div id="entries-scholarships"></div>' +
    '<div class="subsection-label">' + s.installations + "</div>" +
    '<div id="entries-installations"></div>' +
    '<hr class="divider" />' +
    '<div class="section-title">' + s.work + "</div>" +
    '<div id="entries-work"></div>' +
    '<hr class="divider" />' +
    '<div class="section-title">' + s.education + "</div>" +
    '<div class="subsection-label">' + s.diplomas + "</div>" +
    '<div id="entries-diplomas"></div>' +
    '<div class="subsection-label">' + s.qualifications + "</div>" +
    '<div id="entries-qualifications"></div>';

  // Entry rendering
  function pick(entry, field) {
    return (lang === "ja" && entry[field + "_ja"]) || entry[field] || "";
  }

  function renderEntry(entry) {
    var titleText = pick(entry, "title");
    var titleHtml = entry.url
      ? '<a href="' + entry.url + '">' + titleText + "</a>"
      : titleText;

    var html =
      '<div class="entry"><div class="entry-row">' +
      '<span class="entry-title">' + titleHtml + "</span>" +
      '<span class="entry-date">' + pick(entry, "date") + "</span>" +
      "</div>";

    var subtitle = pick(entry, "subtitle");
    if (subtitle) html += '<div class="entry-subtitle">' + subtitle + "</div>";

    var location = pick(entry, "location");
    if (location) html += '<div class="entry-location">' + location + "</div>";

    var role = pick(entry, "role");
    if (role) html += '<div class="entry-role">' + role + "</div>";

    var detail = pick(entry, "detail");
    if (detail) html += '<div class="entry-detail">' + detail + "</div>";

    var bullets = (lang === "ja" && entry.bullets_ja) || entry.bullets;
    if (bullets && bullets.length) {
      html += "<ul>" + bullets.map(function (b) { return "<li>" + b + "</li>"; }).join("") + "</ul>";
    }

    html += "</div>";
    return html;
  }

  function fill(id, entries) {
    var el = document.getElementById(id);
    if (el && entries) el.innerHTML = entries.map(renderEntry).join("");
  }

  fill("entries-group",         RESUME.exhibitions && RESUME.exhibitions.group);
  fill("entries-awards",        RESUME.exhibitions && RESUME.exhibitions.awards);
  fill("entries-scholarships",  RESUME.exhibitions && RESUME.exhibitions.scholarships);
  fill("entries-installations", RESUME.exhibitions && RESUME.exhibitions.installations);
  fill("entries-work",          RESUME.work);
  fill("entries-diplomas",      RESUME.education && RESUME.education.diplomas);
  fill("entries-qualifications",RESUME.education && RESUME.education.qualifications);
})();
