<script>
  export let data;
  let headerTitle_ID;
  let pageTitle = "作品集";

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
  <p>test</p>
</div>

<style>
  .contentContainer {
    display: flex;
    flex-direction: column;
    padding: 24px 0px;
  }
</style>
