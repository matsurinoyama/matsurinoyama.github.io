module.exports = function (eleventyConfig) {
  eleventyConfig.addPassthroughCopy("static");
  eleventyConfig.addPassthroughCopy("CNAME");
  eleventyConfig.addPassthroughCopy("works");
  eleventyConfig.addPassthroughCopy("seika");
  eleventyConfig.addPassthroughCopy("tma1");
  eleventyConfig.addPassthroughCopy("tma2");
  eleventyConfig.addPassthroughCopy({
    "node_modules/gsap/dist/gsap.min.js": "static/gsap/gsap.min.js",
    "node_modules/gsap/dist/ScrollTrigger.min.js": "static/gsap/ScrollTrigger.min.js",
    "node_modules/gsap/dist/ScrambleTextPlugin.min.js":
      "static/gsap/ScrambleTextPlugin.min.js",
  });

  return {
    dir: {
      input: ".",
      output: "_site",
      data: "static/data",
      includes: "_includes",
    },
  };
};
