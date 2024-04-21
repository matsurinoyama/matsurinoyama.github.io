<script>
  import { onMount } from "svelte";
  import { fade } from "svelte/transition";

  let images = [
    { src: "/2020/WWSA/before_01.jpg", sub: "Before" },
    { src: "/2020/WWSA/after_01.jpg", sub: "After" },
    { src: "/2020/WWSA/before_02.jpg", sub: "Before" },
    { src: "/2020/WWSA/after_02.jpg", sub: "After" },
    // Add more image paths as needed
  ];

  let currentIndex = 0;

  onMount(() => {
    // Start the slideshow when the component mounts
    startSlideshow();
  });

  const startSlideshow = () => {
    setInterval(() => {
      // Increment the currentIndex and loop back to the first image if needed
      currentIndex = (currentIndex + 1) % images.length;
    }, 5000); // Change the duration as needed
  };
</script>

<div class="slideshowContainer">
  {#each images as image, index}
    <img
      src={image.src}
      alt={`Image ${index + 1}`}
      style="opacity: {index === currentIndex ? 1 : 0}"
      in:fade
      out:fade
    />
    <h5 style="opacity: {index === currentIndex ? 1 : 0}" in:fade out:fade>
      {image.sub}
    </h5>
  {/each}
</div>

<style>
  .slideshowContainer {
    display: flex;
    position: relative;
    width: 100%;
    height: calc(100vh - 64px);
  }

  .slideshowContainer h5 {
    position: absolute;
    bottom: 0;
    left: 0;
    margin-top: 0%;
    padding: 16px;
    width: 100%;
    font-weight: 400;
    text-align: left;
  }

  .slideshowContainer img {
    position: absolute;
    transition: all 0.75s ease-in-out;
    width: 100%;
    max-width: none;
    height: 100%;
    max-height: none;
  }
</style>
