(function () {
  var container = document.querySelector(".slide_Container");
  var navContainer = document.querySelector(".slideNav_Container");
  if (!container || !navContainer) return;

  var slideEls = container.querySelectorAll(".slide");
  var dots = navContainer.querySelectorAll(".slideNav");
  var currentIndex = 0;

  function cdnUrl(path) {
    return "https://cdn.03080.jp/" + path;
  }

  function getRandomImage(slide) {
    var images = slide.dataset.images ? slide.dataset.images.split(",") : [];
    if (!images.length) return null;
    var folder = slide.dataset.folder;
    var file = images[Math.floor(Math.random() * images.length)];
    return cdnUrl(folder + "/" + file);
  }

  function youtubeUrl(id, duration) {
    var start = duration ? "&start=" + Math.floor(Math.random() * duration) : "";
    return (
      "https://www.youtube.com/embed/" +
      id +
      "?autoplay=1&mute=1&loop=1&playlist=" +
      id +
      start +
      "&controls=0&rel=0&iv_load_policy=3&disablekb=1&playsinline=1"
    );
  }

  var timer = null;

  function resetTimer() {
    if (timer) clearInterval(timer);
    timer = setInterval(nextSlide, 10000);
  }

  function activateSlide(index, isManual) {
    var prev = slideEls[currentIndex];
    var next = slideEls[index];

    // Kill any in-progress tweens so they don't fight the new ones
    gsap.killTweensOf(prev);
    gsap.killTweensOf(next);

    // Deactivate previous
    gsap.to(prev, { opacity: 0, duration: 0.8, ease: "power1.inOut" });
    prev.classList.remove("active");
    dots[currentIndex].classList.remove("active");

    // Clear previous YouTube iframe
    var prevIframe = prev.querySelector("iframe");
    if (prevIframe) prevIframe.src = "";

    // Refresh background image on wrap-around
    if (index === 0) {
      slideEls.forEach(function (s) {
        var img = getRandomImage(s);
        if (img) s.style.backgroundImage = "url('" + img + "')";
      });
    }

    currentIndex = index;

    // Activate next
    next.classList.add("active");
    dots[currentIndex].classList.add("active");
    gsap.fromTo(next, { opacity: 0 }, { opacity: 1, duration: 0.8, ease: "power1.inOut" });

    // Lazy-load YouTube (50% chance, matching original behavior)
    var iframe = next.querySelector("iframe");
    if (iframe && next.dataset.youtube && Math.random() < 0.5) {
      iframe.src = youtubeUrl(next.dataset.youtube, next.dataset.duration ? +next.dataset.duration : 0);
    }

    // Reset auto-advance timer so a manual click always gets the full 10s
    if (isManual) resetTimer();
  }

  function nextSlide() {
    var next = (currentIndex + 1) % slideEls.length;
    activateSlide(next, false);
  }

  // Wire up dot clicks
  dots.forEach(function (dot, i) {
    dot.addEventListener("click", function () {
      if (i !== currentIndex) activateSlide(i, true);
    });
  });

  // Set initial background image randomly for each slide
  slideEls.forEach(function (s) {
    var img = getRandomImage(s);
    if (img) s.style.backgroundImage = "url('" + img + "')";
  });

  resetTimer();
})();
