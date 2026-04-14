(function () {
  const base = document.documentElement.dataset.staticBase || "/static";
  const lang = document.documentElement.lang === "ja" ? "ja" : "en";
  const container = document.querySelector(".slide_Container");
  const navContainer = document.querySelector(".slideNav_Container");
  let currentIndex = 0;

  slidesWithImages.forEach(function (s) {
    const div = document.createElement("div");
    div.className = "slide";
    div.dataset.folder = s.folder;
    div.style.backgroundImage = "url(" + base + "/" + s.image + ")";
    const caption = (lang === "ja" && s.caption_ja) ? s.caption_ja : s.caption;
    div.innerHTML = '<div class="slideText"><p>' + caption + "</p></div>";
    container.appendChild(div);
  });

  const slideEls = container.querySelectorAll(".slide");

  slideEls.forEach(function (_, i) {
    const dot = document.createElement("div");
    dot.className = "slideNav" + (i === 0 ? " active" : "");
    dot.addEventListener("click", function () { goToSlide(i); });
    navContainer.appendChild(dot);
  });

  const dots = navContainer.querySelectorAll(".slideNav");

  function updateSlides() {
    slideEls.forEach(function (s, i) {
      s.classList.toggle("active", i === currentIndex);
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
        slide.style.backgroundImage = "url(" + base + "/" + getRandomImage(slide.dataset.folder) + ")";
      });
    }
    updateSlides();
  }

  updateSlides();
  setInterval(nextSlide, 10000);
})();
