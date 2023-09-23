<script>
  import { onMount } from "svelte";
  import Carousel from "./Carousel.svelte";
  let headerTitle_ID;
  let direction1 = "left";
  let direction2 = "right";
  let images1 = [
    { src: "/test/image_01.jpg", url: "/works/one" },
    { src: "/test/image_02.png", url: "/works/two" },
    { src: "/test/image_03.jpg", url: "/works" },
    { src: "/test/image_04.jpg", url: "/works" },
    { src: "/test/image_05.png", url: "/works" },
    { src: "/test/image_06.jpg", url: "/works" },
    { src: "/test/image_07.jpg", url: "/works" },
    { src: "/test/image_08.jpg", url: "/works" },
  ];

  let images2 = [
    { src: "/test/image_09.jpg", url: "/works" },
    { src: "/test/image_10.jpg", url: "/works" },
    { src: "/test/image_11.jpg", url: "/works" },
    { src: "/test/image_12.png", url: "/works" },
    { src: "/test/image_13.png", url: "/works" },
    { src: "/test/image_14.jpg", url: "/works" },
    { src: "/test/image_15.jpg", url: "/works" },
    { src: "/test/image_16.jpg", url: "/works" },
  ];
  let time = 5;
  let pageTitle = "茉莉の山";

  onMount(() => {
    setTimeout(() => {
      document.querySelector("header").style.opacity = "1";
      headerTitle_ID.style.opacity = "1";
    }, 1000); // Change the delay time as needed
  });

  // --Hide Header Title--
  function handleKey() {
    document.querySelector("header").style.opacity = "0";
    headerTitle_ID.style.opacity = "0";
  }
</script>

<div class="headerTitle" bind:this={headerTitle_ID}>
  <h2 style="letter-spacing: 32px;">{@html pageTitle}</h2>
</div>

<div class="contentContainer">
  <div class="carouselPadding">
    <Carousel
      carouselAnim_Duration={time}
      carouselAnim_Direction={direction1}
      images={images1}
      on:removeHeader={handleKey}
    />
  </div>
  <div class="carouselPadding">
    <Carousel
      carouselAnim_Duration={time}
      carouselAnim_Direction={direction2}
      images={images2}
      on:removeHeader={handleKey}
    />
  </div>
</div>

<style>
  .contentContainer {
    display: flex;
    flex-direction: column;
    padding: 24px 0px;
  }

  .carouselPadding {
    padding: 8px 0px;
  }
</style>
