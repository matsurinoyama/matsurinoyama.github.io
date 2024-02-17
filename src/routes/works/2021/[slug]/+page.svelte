<script>
  import { IconArrowDownLeft, IconQuestionMark } from "@tabler/icons-svelte";
  import { onMount } from "svelte";
  import Slideshow from "../../../Slideshow.svelte";
  export let data;
  let headerTitle_ID;
  let contentContainer_headerOverlay_ID;

  function disableScroll() {
    // Get the current scroll position
    const posY_Scroll = window.scrollY;
    // Add styles to disable scrolling
    document.body.style.overflow = "hidden";
    document.body.style.top = `-${posY_Scroll}px`;
  }

  function enableScroll() {
    // Add styles to enable scrolling
    document.body.style.overflow = "";
    document.body.style.top = "";
  }

  onMount(() => {
    disableScroll();
    setTimeout(() => {
      document.querySelector("header").style.opacity = "1";
      headerTitle_ID.style.opacity = "1";
      contentContainer_headerOverlay_ID.style.opacity = "1";
      setTimeout(() => {
        enableScroll();
      }, 1000);
    }, 1000); // Change the delay time as needed
  });
</script>

<div class="headerTitle" bind:this={headerTitle_ID}>
  <a href="./">
    <IconArrowDownLeft size={32} stroke={1.5} />
    <h5>{data.work.collection}</h5>
  </a>
</div>

<div class="contentContainer_Header">
  <img src={data.work.thumbnail} alt={data.work.thumbnail_alt} />
  <div
    class="contentContainer_headerOverlay"
    bind:this={contentContainer_headerOverlay_ID}
  >
    <div class="overlayText">
      <h3>{data.work.title}</h3>
      <div class="overlayText_Subtitle">
        <h5>{data.work.production}</h5>
        <p>{@html data.work.scope}</p>
      </div>
    </div>
  </div>
</div>

{#each data.work.content as content, index}
  {#if index === 0}
    <!-- Render the first content without the surrounding div -->
    <div class="contentContainer_Body" id="wSeparator">
      {@html content.html}
    </div>
  {/if}

  {#if index > 0 && index < data.work.content.length - 1}
    <!-- Render the middle content with the surrounding div -->
    <div class="contentContainer_Body">
      {@html content.html}
    </div>
  {/if}

  {#if index === data.work.content.length - 1}
    <!-- Render the last content without the surrounding div -->
    <div class="contentContainer_Body">
      {@html content.html}
      <div class="contentContainer_Footer">
        <div class="mediaContainer_Bottom">
          <h6>{@html data.work.finalimg_sub}</h6>
          <img src={data.work.finalimg} alt={data.work.finalimg_alt} />
        </div>
        <p>{data.work.finaltxt}</p>
        <div class="linkContainer">
          <a href="./">
            <IconArrowDownLeft size={32} stroke={1.5} />
            <h5>{data.work.collection}</h5>
          </a>
          <a href="./">
            <IconQuestionMark size={32} stroke={1.5} />
            <h5>ランダムに作品を見る</h5>
          </a>
        </div>
      </div>
    </div>
  {/if}
{/each}

<style>
  .headerTitle a,
  .linkContainer a {
    display: flex;
    flex-direction: row;
    align-items: center;
    padding-bottom: 8px;
    color: white;
  }

  .headerTitle a:hover,
  .headerTitle h5:hover,
  .linkContainer a:hover,
  .linkContainer h5:hover {
    color: var(--mYELLOW);
  }
  .contentContainer_Header {
    display: flex;
    position: relative;
    width: 100%;
  }

  .contentContainer_Header img {
    width: 100%;
    height: 100vh;
    object-fit: cover;
  }

  .contentContainer_headerOverlay {
    display: flex;
    position: absolute;
    top: 0;
    left: 0;
    align-items: flex-end;
    opacity: 0;
    transition: opacity 1s ease-out;
    background: bottom url(/gradient_256-B.svg) repeat-x;
    background-size: auto 128px;
    padding: 64px;
    width: 100%;
    height: 100vh;
  }

  .overlayText {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    width: 100%;
  }
  .overlayText_Subtitle {
    display: flex;
    flex-direction: column;
  }

  .overlayText_Subtitle p {
    margin-top: 16px;
  }
</style>
