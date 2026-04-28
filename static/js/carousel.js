(function () {
  const lang = document.documentElement.lang === "ja" ? "ja" : "en";
  const container = document.querySelector(".slide_Container");
  const navContainer = document.querySelector(".slideNav_Container");
  let currentIndex = 0;

  function youtubeUrl(id, duration) {
    const startParam = duration
      ? "&start=" + Math.floor(Math.random() * duration)
      : "";
    return (
      "https://www.youtube.com/embed/" +
      id +
      "?autoplay=1&mute=1&loop=1&playlist=" +
      id +
      startParam +
      "&controls=0&rel=0&iv_load_policy=3&disablekb=1&playsinline=1"
    );
  }

  slidesWithImages.forEach(function (s) {
    const div = document.createElement("div");
    div.className = "slide";
    div.dataset.folder = s.folder;
    div.style.backgroundImage = "url(https://cdn.03080.jp/" + s.image + ")";
    const caption = lang === "ja" && s.caption_ja ? s.caption_ja : s.caption;
    div.innerHTML = '<div class="slideText"><p>' + caption + "</p></div>";

    if (s.youtube) {
      div.dataset.youtube = s.youtube;
      if (s.duration) div.dataset.duration = s.duration;
      const iframe = document.createElement("iframe");
      iframe.setAttribute("frameborder", "0");
      iframe.setAttribute("allow", "autoplay; encrypted-media");
      iframe.setAttribute("allowfullscreen", "");
      div.insertBefore(iframe, div.firstChild);
    }

    container.appendChild(div);
  });

  const slideEls = container.querySelectorAll(".slide");

  slideEls.forEach(function (_, i) {
    const dot = document.createElement("div");
    dot.className = "slideNav" + (i === 0 ? " active" : "");
    dot.addEventListener("click", function () {
      goToSlide(i);
    });
    navContainer.appendChild(dot);
  });

  const dots = navContainer.querySelectorAll(".slideNav");

  function updateSlides() {
    slideEls.forEach(function (s, i) {
      const wasActive = s.classList.contains("active");
      const isActive = i === currentIndex;
      s.classList.toggle("active", isActive);

      const iframe = s.querySelector("iframe");
      if (iframe) {
        if (isActive && !wasActive) {
          if (Math.random() < 0.5) {
            iframe.src = youtubeUrl(s.dataset.youtube, s.dataset.duration);
          }
        } else if (!isActive && wasActive) {
          iframe.src = "";
        }
      }
    });
    dots.forEach(function (d, i) {
      d.classList.toggle("active", i === currentIndex);
    });
  }

  function goToSlide(i) {
    currentIndex = i;
    updateSlides();
  }

  function nextSlide() {
    const wasLast = currentIndex === slideEls.length - 1;
    currentIndex = (currentIndex + 1) % slideEls.length;
    if (wasLast) {
      slideEls.forEach(function (slide) {
        slide.style.backgroundImage =
          "url(https://cdn.03080.jp/" +
          getRandomImage(slide.dataset.folder) +
          ")";
      });
    }
    updateSlides();
  }

  updateSlides();
  setInterval(nextSlide, 10000);
})();
