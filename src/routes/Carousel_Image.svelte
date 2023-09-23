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
  <img src={imageSrc} alt={imageAlt} />
</div>

<style>
  .imageContainer {
    outline: 1px solid white;
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative;
    width: var(--img-width);
    max-width: calc(100vw - 128px);
    height: var(--img-height);
    margin: 0px calc(8px + 1px);
    transition: all 0.5s ease-in-out;
    background-color: var(--mRED);
    cursor: pointer;
    border-radius: 8px;
  }

  .imageContainer:hover {
    outline: 0px solid rgba(255, 255, 255, 0);
    background-color: black;
    border-radius: 0px;
  }

  .imageContainer img {
    object-fit: cover;
    mix-blend-mode: exclusion;
    filter: grayscale(30%) contrast(130%) brightness(115%);
    width: 100%;
    height: 100%;
    transition: all 0.5s ease-in-out;
    border-radius: 8px;
  }

  .imageContainer img:hover {
    filter: grayscale(0%) contrast(100%) brightness(100%);
    border-radius: 0px;
  }

  .isExpanded {
    outline: 0px solid rgba(255, 255, 255, 0);
    position: relative;
    z-index: 100;
    transform: translateY(calc(var(--pos-y) * -1))
      translateX(calc(var(--pos-x) * -1));
    width: 100vw;
    max-width: none;
    height: 100vh;
    margin-bottom: 100vh;
    cursor: progress;
    border-radius: 0px;
  }

  .isExpanded img {
    mix-blend-mode: normal;
    filter: grayscale(0%) contrast(100%) brightness(100%);
    z-index: 100;
    width: 100%;
    height: 100%;
    border-radius: 0;
  }
</style>
