<script>
  let expanded = false;

  function toggleExpand() {
    expanded = !expanded;
  }
</script>

<div class="container {expanded ? 'expanded' : ''}" on:click={toggleExpand}>
  <p>Click to expand</p>
</div>

<style>
  .container {
    transform: translateX(100px);
    width: 300px;
    height: 200px;
    background-color: lightblue;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.5s ease-in-out;
  }

  .expanded {
    position: relative;
    left: 0;
    bottom: 0;
    top: 0;
    right: 0;
    transform: translateX(0px);
    margin-left: -64px;
    width: 100vw;
    height: 100vh;
  }
</style>
