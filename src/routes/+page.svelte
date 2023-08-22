<script>
    import Carousel from "./Carousel.svelte";
    import Expander from "./Expander.svelte";
    let direction1 = "left";
    let direction2 = "right";
    let images1 = [
        "test/image_01.jpg",
        "test/image_02.png",
        "test/image_03.jpg",
        "test/image_04.jpg",
        "test/image_05.png",
        "test/image_06.jpg",
        "test/image_07.jpg",
        "test/image_08.jpg",
    ];
    let images2 = [
        "test/image_09.jpg",
        "test/image_10.jpg",
        "test/image_11.jpg",
        "test/image_12.png",
        "test/image_13.png",
        "test/image_14.jpg",
        "test/image_15.jpg",
        "test/image_16.jpg",
    ];
    let time = 5;
    let pageTitle = "茉莉の山";
</script>

<div class="headerTitle">
    <h2 style="letter-spacing: 32px;">{@html pageTitle}</h2>
</div>

<div class="contentContainer">
    <div class="carouselPadding">
        <Carousel carouselAnim_Duration={time} carouselAnim_Direction={direction1} images={images1} />
    </div>
    <div class="carouselPadding">
        <Carousel carouselAnim_Duration={time} carouselAnim_Direction={direction2} images={images2} />
    </div>
    <Expander />
</div>

<style>
    .contentContainer {
        display: flex;
        flex-direction: column;
        padding: 24px 0px;
    }

    .carouselPadding {
        padding: 8px 0px;
    }
</style>
