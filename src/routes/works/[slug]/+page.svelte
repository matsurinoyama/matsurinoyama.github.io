<script>
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
  <h3 style="letter-spacing: 32px;">{data.work.title}</h3>
  <h5>{data.work.description}</h5>
</div>

<div class="contentContainer">
  <img src={data.work.content} alt="image_01.jpg" />
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

  .headerWork {
    position: absolute;
    z-index: 50;
    top: 64px;
    opacity: 0;
    padding-top: 32px;
    transition: opacity 1s ease-out;
  }
</style>
