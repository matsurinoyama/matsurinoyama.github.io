<script>
  import { onMount, afterUpdate, createEventDispatcher } from "svelte";
  const dispatch = createEventDispatcher();
  let imageContainer_Pos;
  let imageContainer_Height;
  let imageContainer_Width;
  let imageContainer_ID;
  let isExpanded = false;
  let image = {};
  export let imageSrc = "";
  export let imageSrc_Dither = "";
  export let imageAlt = "";
  export let imageUrl = "/works";

  // Get the image width based on the set height
  function getImageWidth() {
    if (imageContainer_ID) {
      const aspectRatio =
        imageContainer_ID.querySelector("img").naturalWidth /
        imageContainer_ID.querySelector("img").naturalHeight;
      const imageSrc_Height = 50;
      const imageSrc_Width = imageSrc_Height * aspectRatio;
      imageContainer_Height = imageSrc_Height;
      imageContainer_Width = imageSrc_Width;
    }
  }

  function disableScroll() {
    // Get the current scroll position
    const posY_Scroll = window.scrollY;
    // Add styles to disable scrolling
    document.body.style.overflow = "hidden";
    document.body.style.top = `-${posY_Scroll}px`;
  }

  // Expand the selected image
  function toggleExpand() {
    if (!isExpanded) {
      dispatch("pauseCarousel");
      setTimeout(() => {
        imageContainer_Pos = imageContainer_ID.getBoundingClientRect();

        image = {
          posX: `${imageContainer_Pos.x}px`,
          posY: `${imageContainer_Pos.y}px`,
        };

        isExpanded = true;
        disableScroll();
      }, 50);
      window.location.href = `${imageUrl}`;
    }
  }

  function handleKey(event) {
    if (event.key === "Enter" || event.key === " ") {
      toggleExpand();
    }
  }

  // Get the image width when first loading
  onMount(getImageWidth);
  afterUpdate(getImageWidth);
</script>

<div
  class="imageContainer"
  class:isExpanded
  style="--pos-x: {image.posX}; --pos-y: {image.posY}; --img-height: {imageContainer_Height}vh; --img-width: {imageContainer_Width}vh;"
  bind:this={imageContainer_ID}
  on:click={toggleExpand}
  on:keydown={handleKey}
  role="button"
  tabindex="0"
>
  <div class="imageContainer_Base">
    <img src={imageSrc} alt={imageAlt} />
  </div>
  <div class="imageContainer_Overlay">
    <img src={imageSrc_Dither} alt={imageAlt} />
  </div>
</div>

<style>
  .imageContainer {
    display: flex;
    position: relative;
    justify-content: center;
    align-items: center;
    filter: contrast(85%) brightness(115%) saturate(130%);
    transition: all 0.5s ease-in-out;
    cursor: pointer;
    margin-top: 16px;
    margin-left: 16px;
    border-radius: 8px;
    background-color: var(--mRED);
    width: var(--img-width);
    max-width: calc(100vw - 128px);
    height: var(--img-height);
  }

  .imageContainer img {
    transition: all 0.5s ease-in-out;
    border-radius: 8px;
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .imageContainer:hover {
    filter: contrast(100%) brightness(100%) saturate(100%);
    background-color: black;
  }

  .imageContainer_Base {
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    opacity: 1;
    mix-blend-mode: exclusion;
    transition: all 0.5s ease-in-out;
    width: 100%;
    height: 100%;
  }

  .imageContainer_Overlay {
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    opacity: 0.25;
    mix-blend-mode: screen;
    transition: all 0.75s steps(3, end);
    width: 100%;
    height: 100%;
  }

  .imageContainer_Overlay img {
    image-rendering: pixelated;
  }

  .imageContainer_Overlay:hover {
    opacity: 0;
  }

  .isExpanded {
    position: relative;
    transform: translateY(calc(var(--pos-y) * -1))
      translateX(calc(var(--pos-x) * -1));
    z-index: 100;
    cursor: progress;
    margin-bottom: 100vh;
    border-radius: 0;
    width: 100vw;
    max-width: none;
    height: 100vh;
  }

  .isExpanded img {
    z-index: 100;
    mix-blend-mode: normal;
    filter: grayscale(0%) contrast(100%) brightness(100%);
    border-radius: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
</style>
