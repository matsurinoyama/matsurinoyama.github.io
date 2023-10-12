<script>
  import { IconArrowDownLeft } from "@tabler/icons-svelte";
  import { onMount } from "svelte";
  export let data;
  let headerWork_ID;

  onMount(() => {
    setTimeout(() => {
      document.querySelector("header").style.opacity = "1";
      headerWork_ID.style.opacity = "1";
    }, 1000); // Change the delay time as needed
  });
</script>

<div class="headerWork" bind:this={headerWork_ID}>
  <a href="../2021"><IconArrowDownLeft size={32} stroke={1.5} /><h5>2021年度作品集に戻る</h5></a>
</div>

<div class="contentContainer">
  <img src={data.work.content} alt="image_01.jpg" />
  <div class="contentContainer_Title">
      <h3>{data.work.title}</h3>
      <div class="contentContainer_Subtitle">
        <h5>{data.work.production}</h5>
        <p>{@html data.work.scope}</p>
      </div>
  </div>
</div>

<style>
  .contentContainer {
    position: relative;
    width: 100vw;
    height: 100vh;
    margin-top: -64px;
    margin-left: -64px;
  }

  .contentContainer img {
    object-fit: cover;
    width: 100vw;
    height: 100vh;
  }

  .gradientSmall {
    position: absolute;
    top: calc(100% - 64px);
    left: 0;
    height: 64px;
    width: 100vw;
    background: url(/gradient_128.svg) repeat-x;
  }

  .contentContainer_Title {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: 100%;
    background: bottom url(/gradient_256.svg) repeat-x;
    background-size: auto 128px;
    pointer-events: none;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    padding: 64px;
  }

  .contentContainer_Subtitle {
    display: flex;
    flex-direction: column;
  }

  .contentContainer_Subtitle p {
    margin-top: 16px;
  }

  .headerWork {
    position: absolute;
    z-index: 50;
    top: 64px;
    opacity: 0;
    padding-top: 32px;
    transition: opacity 1s ease-out;
  }

  .headerWork a {
    display: flex;
    flex-direction: row;
    color: white;
  }

  .headerWork a:hover,
  .headerWork h5:hover {
    color: var(--mYELLOW);
  }
</style>
