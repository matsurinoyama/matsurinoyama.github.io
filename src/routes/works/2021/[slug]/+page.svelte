<script>
  import { IconArrowDownLeft } from "@tabler/icons-svelte";
  import { onMount } from "svelte";
  export let data;
  let headerWork_ID;
  let contentContainer_mainTitle_ID;

  onMount(() => {
    setTimeout(() => {
      document.querySelector("header").style.opacity = "1";
      headerWork_ID.style.opacity = "1";
      contentContainer_mainTitle_ID.style.opacity = "1";
    }, 1000); // Change the delay time as needed
  });
</script>

<div class="headerTitle" bind:this={headerWork_ID}>
  <a href="../2021"
    ><IconArrowDownLeft size={32} stroke={1.5} />
    <h5>2021年度作品集に戻る</h5></a
  >
</div>

<div class="contentContainer_Main">
  <img src={data.work.content} alt="image_01.jpg" />
  <div
    class="contentContainer_mainOverlay"
    bind:this={contentContainer_mainTitle_ID}
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

<style>
  .contentContainer_Main {
    position: relative;
    width: 100%;
  }

  .contentContainer_Main img {
    width: 100%;
    height: 100vh;
    object-fit: cover;
  }

  .gradientSmall {
    position: absolute;
    top: calc(100% - 64px);
    left: 0;
    background: url(/gradient_128.svg) repeat-x;
    width: 100vw;
    height: 64px;
  }

  .contentContainer_mainOverlay {
    display: flex;
    position: absolute;
    top: 0;
    left: 0;
    align-items: flex-end;
    opacity: 0;
    transition: opacity 1s ease-out;
    background: bottom url(/gradient_256.svg) repeat-x;
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

  .headerTitle a {
    display: flex;
    flex-direction: row;
    color: white;
  }

  .headerTitle a:hover,
  .headerTitle h5:hover {
    color: var(--mYELLOW);
  }
</style>
