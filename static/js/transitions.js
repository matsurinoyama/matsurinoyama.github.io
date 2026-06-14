(function () {
  var overlay = document.getElementById("page-transition");
  if (!overlay) return;

  // Fade page in, then signal animations.js to start entrance animations
  gsap.to(overlay, { opacity: 0, duration: 0.35, ease: "power2.out", onComplete: function () {
    overlay.style.pointerEvents = "none";
    document.dispatchEvent(new Event("page-in-complete"));
  }});

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
    overlay.style.pointerEvents = "all";
    gsap.to(overlay, {
      opacity: 1,
      duration: 0.35,
      ease: "power2.in",
      onComplete: function () {
        window.location.href = link.href;
      },
    });
  });
})();
