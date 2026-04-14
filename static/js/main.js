(function () {
  var lang = document.documentElement.lang === "ja" ? "ja" : "en";
  var base = document.documentElement.dataset.staticBase || "/static";
  var t = TRANSLATIONS[lang];

  document.title = t.pageTitle;

  document.body.insertAdjacentHTML(
    "beforeend",
    '<div class="slide_Container"></div>' +
    '<div class="slideNav_Container"></div>' +
    '<div class="content">' +
      '<div class="contentContact_Container">' +
        '<div class="contentContact">' +
          '<h3><a href="mailto:hello@03080.jp">hello@03080.jp</a></h3>' +
          '<h3><a href="tel:+817089993485">+81 70 8999 3485</a></h3>' +
        "</div>" +
      "</div>" +
      '<div class="heading_Container">' +
        '<div class="headingIcon_Container">' +
          "<picture>" +
            '<source media="(max-width: 1000px)" srcset="' + base + '/temp-h.svg" />' +
            '<source media="(min-width: 500px)" srcset="' + base + '/temp-v.svg" />' +
            '<img src="' + base + '/temp-v.svg" alt="logo" />' +
          "</picture>" +
          "<p>" + t.bio + "</p>" +
        "</div>" +
        '<div class="headingMenu_Container">' +
          '<div class="headingMenu">' +
            '<h5><a href="' + base + "/PORTFOLIO.pdf" + '">' + t.nav.works + "</a></h5>" +
            '<h5><a href="resume/">' + t.nav.resume + "</a></h5>" +
            '<h5><a href="' + t.nav.langHref + '">' + t.nav.lang + "</a></h5>" +
          "</div>" +
        "</div>" +
      "</div>" +
    "</div>"
  );
})();
