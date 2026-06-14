(function () {
  var isResume = !!document.querySelector(".resume-wrap");

  if (isResume) {
    // Resume: ScrollTrigger reveals for each entry
    if (typeof ScrollTrigger !== "undefined") {
      gsap.registerPlugin(ScrollTrigger);
      gsap.utils.toArray(".entry, .section-title, .subsection-label").forEach(function (el) {
        gsap.from(el, {
          y: 24,
          opacity: 0,
          duration: 0.5,
          ease: "power2.out",
          scrollTrigger: {
            trigger: el,
            start: "top 92%",
            toggleActions: "play none none none",
          },
        });
      });

      // Hero entrance — same delayedCall pattern so opacity:0 isn't set before overlay fades
      gsap.delayedCall(0.4, function () {
        gsap.from(".resume-name", { y: 16, opacity: 0, duration: 0.6, ease: "power2.out" });
        gsap.from(".resume-overview", { y: 16, opacity: 0, duration: 0.6, ease: "power2.out", delay: 0.1 });
      });
    }
  } else {
    // Hide elements now, while the red overlay still covers them — no visible blink.
    // gsap.from() sets opacity:0 the moment it's called regardless of delay, so we
    // use gsap.set() here + gsap.to() inside the page-in-complete handler instead.
    gsap.set(".contentContact h3", { opacity: 0, y: 20 });
    gsap.set(".headingMenu h5", { opacity: 0, y: 12 });
    gsap.set(".headingIcon_Container p", { opacity: 0, y: 10 });

    // transitions.js dispatches this event after the overlay fully fades out.
    document.addEventListener("page-in-complete", function () {
      gsap.to(".contentContact h3", {
        opacity: 1, y: 0, duration: 0.6, ease: "power2.out", stagger: 0.1,
      });
      gsap.to(".headingMenu h5", {
        opacity: 1, y: 0, duration: 0.5, ease: "power2.out", stagger: 0.08, delay: 0.15,
      });
      gsap.to(".headingIcon_Container p", {
        opacity: 1, y: 0, duration: 0.5, ease: "power2.out", delay: 0.25,
      });
    }, { once: true });
  }
})();
