<script>
    import Carousel from "./Carousel.svelte";
    let carouselAnim_Direction = "left";
    let images = [
        "test/image_01.jpg",
        "test/image_02.png",
        "test/image_03.jpg",
        "test/image_04.jpg",
        "test/image_05.png",
        "test/image_06.jpg",
        "test/image_07.jpg",
        "test/image_08.jpg",
        "test/image_09.jpg",
        "test/image_10.jpg",
        "test/image_11.jpg",
        "test/image_12.png",
        "test/image_13.png",
        "test/image_14.jpg",
        "test/image_15.jpg",
        "test/image_16.jpg",
    ];
    let pageTitle = "茉莉の山";
</script>

<div class="headerTitle">
    <h2 style="letter-spacing: 32px;">{@html pageTitle}</h2>
</div>

<Carousel {carouselAnim_Direction} {images} />
