<script>
    import Carousel from './Carousel.svelte';
    let pageTitle = '茉莉の山'
</script>

<div class="headerTitle">
    <h2 style="letter-spacing: 32px;">{@html pageTitle}</h2>
</div>

<Carousel />