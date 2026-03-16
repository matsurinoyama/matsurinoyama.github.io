(function () {
  var overlay = document.getElementById("page-transition");
  if (!overlay) return;

  // Fade page in
  requestAnimationFrame(function () {
    requestAnimationFrame(function () {
      overlay.classList.remove("active");
    });
  });

  // Fade to red before navigating internal links
  document.addEventListener("click", function (e) {
    var link = e.target.closest("a[href]");
    if (!link) return;

    var href = link.getAttribute("href");
    if (
      !href ||
      href.startsWith("http") ||
      href.startsWith("//") ||
      href.startsWith("mailto:") ||
      href.startsWith("tel:") ||
      href.startsWith("#") ||
      link.target === "_blank"
    )
      return;

    e.preventDefault();
    overlay.classList.add("active");

    overlay.addEventListener(
      "transitionend",
      function () {
        window.location.href = link.href;
      },
      { once: true }
    );
  });
})();
