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
  <a href="../2021"
    ><IconArrowDownLeft size={32} stroke={1.5} />
    <h5>2021年度作品集に戻る</h5></a
  >
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
    margin-top: -64px;
    margin-left: -64px;
    width: 100vw;
    height: 100vh;
  }

  .contentContainer img {
    width: 100vw;
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

  .contentContainer_Title {
    display: flex;
    position: absolute;
    top: 0;
    left: 0;
    justify-content: space-between;
    align-items: flex-end;
    background: bottom url(/gradient_256.svg) repeat-x;
    background-size: auto 128px;
    padding: 64px;
    width: 100%;
    height: 100%;
    pointer-events: none;
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
    top: 64px;
    opacity: 0;
    z-index: 50;
    transition: opacity 1s ease-out;
    padding-top: 32px;
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
