<script>
  import { onMount } from "svelte";
  import Carousel from "../Carousel.svelte";
  let headerTitle_ID;
  let workYear_ID;
  let direction1 = "left";
  let direction2 = "right";
  let images1 = [
    {
      src: "/2020/WWSA/drawing_01.jpg",
      src_dither: "/2020/WWSA/dither.png",
      url: "/works/2021/WWSA",
    },
    {
      src: "/2021/H&R/render_01.png",
      src_dither: "/2021/H&R/dither.png",
      url: "/works/2021/H&R",
    },
    {
      src: "/test/image_03.jpg",
      src_dither: "/test/image_03d.png",
      url: "/works",
    },
    {
      src: "/test/image_04.jpg",
      src_dither: "/test/image_04d.png",
      url: "/works",
    },
    {
      src: "/test/image_05.png",
      src_dither: "/test/image_05d.png",
      url: "/works",
    },
    {
      src: "/test/image_06.jpg",
      src_dither: "/test/image_06d.png",
      url: "/works",
    },
    {
      src: "/test/image_07.jpg",
      src_dither: "/test/image_07d.png",
      url: "/works",
    },
    {
      src: "/test/image_01.jpg",
      src_dither: "/test/image_01d.png",
      url: "/works",
    },
  ];

  let images2 = [
    {
      src: "/test/image_09.jpg",
      src_dither: "/test/image_09d.png",
      url: "/works",
    },
    {
      src: "/test/image_10.jpg",
      src_dither: "/test/image_10d.png",
      url: "/works",
    },
    {
      src: "/test/image_11.jpg",
      src_dither: "/test/image_11d.png",
      url: "/works",
    },
    {
      src: "/test/image_12.png",
      src_dither: "/test/image_12d.png",
      url: "/works",
    },
    {
      src: "/test/image_13.png",
      src_dither: "/test/image_13d.png",
      url: "/works",
    },
    {
      src: "/test/image_14.jpg",
      src_dither: "/test/image_14d.png",
      url: "/works",
    },
    {
      src: "/test/image_15.jpg",
      src_dither: "/test/image_15d.png",
      url: "/works",
    },
    {
      src: "/test/image_16.jpg",
      src_dither: "/test/image_16d.png",
      url: "/works",
    },
  ];
  let time = 5;
  let pageTitle = "作品集";

  onMount(() => {
    setTimeout(() => {
      document.querySelector("header").style.opacity = "1";
      headerTitle_ID.style.opacity = "1";
      workYear_ID.style.opacity = "1";
    }, 1000); // Change the delay time as needed
  });

  // --Hide Header Title--
  function handleKey() {
    document.querySelector("header").style.opacity = "0";
    headerTitle_ID.style.opacity = "0";
    workYear_ID.style.opacity = "0";
  }
</script>

<div class="headerTitle" bind:this={headerTitle_ID}>
  <h2 style="letter-spacing: 32px;">{@html pageTitle}</h2>
</div>

<div class="contentContainer">
  <Carousel
    carouselAnim_Duration={time}
    carouselAnim_Direction={direction1}
    images={images1}
    on:removeHeader={handleKey}
  />
  <div class="yearContainer_R" bind:this={workYear_ID}>
    <h3>２０２４年度</h3>
  </div>
  <Carousel
    carouselAnim_Duration={time}
    carouselAnim_Direction={direction2}
    images={images2}
    on:removeHeader={handleKey}
  />
  <div class="yearContainer_L" bind:this={workYear_ID}>
    <h3>２０２３年度</h3>
  </div>
  <Carousel
    carouselAnim_Duration={time}
    carouselAnim_Direction={direction1}
    images={images1}
    on:removeHeader={handleKey}
  />
  <div class="yearContainer_R"><h3>２０２２年度</h3></div>
  <Carousel
    carouselAnim_Duration={time}
    carouselAnim_Direction={direction2}
    images={images2}
    on:removeHeader={handleKey}
  />
  <div class="yearContainer_L" bind:this={workYear_ID}>
    <h3>２０２１年度</h3>
  </div>
  <Carousel
    carouselAnim_Duration={time}
    carouselAnim_Direction={direction1}
    images={images1}
    on:removeHeader={handleKey}
  />
  <div class="yearContainer_R" bind:this={workYear_ID}>
    <h3>２０２０年度</h3>
  </div>
  <Carousel
    carouselAnim_Duration={time}
    carouselAnim_Direction={direction2}
    images={images2}
    on:removeHeader={handleKey}
  />
  <div class="yearContainer_L" bind:this={workYear_ID}>
    <h3>２０１９年度</h3>
  </div>
  <Carousel
    carouselAnim_Duration={time}
    carouselAnim_Direction={direction1}
    images={images1}
    on:removeHeader={handleKey}
  />
  <div class="yearContainer_R" bind:this={workYear_ID}>
    <h3>２０１８年度</h3>
  </div>
  <Carousel
    carouselAnim_Duration={time}
    carouselAnim_Direction={direction2}
    images={images2}
    on:removeHeader={handleKey}
  />
  <div class="yearContainer_L" bind:this={workYear_ID}>
    <h3>２０１７年度</h3>
  </div>
</div>

<style>
  .contentContainer {
    display: flex;
    flex-direction: column;
    padding-top: 16px;
  }

  .yearContainer_R {
    display: flex;
    flex-direction: row;
    justify-content: flex-end;
    z-index: 10;
    mix-blend-mode: exclusion;
    margin: -96px 64px 32px;
    pointer-events: none;
  }

  .yearContainer_L {
    display: flex;
    flex-direction: row;
    justify-content: flex-start;
    z-index: 10;
    mix-blend-mode: exclusion;
    margin: -96px 64px 32px;
    pointer-events: none;
  }
</style>
