<script>
	import { onMount } from 'svelte';
	export let data;
	let headerTitle_ID;

	onMount(() => {
        setTimeout(() => {
            document.querySelector("header").style.opacity = "1";
            headerTitle_ID.style.opacity = "1";
        }, 1000); // Change the delay time as needed
    });
</script>

<div class="headerTitle" bind:this={headerTitle_ID}>
	<h2 style="letter-spacing: 32px;">{data.work.title}</h2>
</div>
<div class="contentContainer">
	<img src="{data.work.content}" alt="image_01.jpg" />
</div>

<style>
	.contentContainer {
		position: relative;
		margin-top: -64px;
		margin-left: -64px;
		width: calc(100% + 128px);
		height: 100vh;
	}
	.contentContainer img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}
</style>
