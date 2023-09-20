<script>
    import { onMount, afterUpdate } from "svelte";
    import Carousel_Image from "./Carousel_Image.svelte";
    let carouselTrack_ID;
    let totalWidth = 0;
    let totalNum = 0;
    export let images = [""];

    // --Randomise Image Order--
    // Shuffle the array randomly
    function shuffleArray(arr) {
        for (let i = arr.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [arr[i], arr[j]] = [arr[j], arr[i]];
        }
        return arr;
    }
    // Shuffle the array on component load
    $: shuffledImages = shuffleArray(images);
    // Duplicate the shuffled array to repeat the order
    $: loopImages = [...shuffledImages, ...shuffledImages];

    // --Get Total Pixel Width of Carousel--
    let isImagesLoaded = false;
    // Total Number of Images
    totalNum = images.length * 2;

    async function getElementWidth() {
        if (carouselTrack_ID && !isImagesLoaded) {
            // Wait for the images to load
            await new Promise((resolve) => {
                const imagesToLoad = Array.from(
                    carouselTrack_ID.querySelectorAll("img")
                );
                const numImages = imagesToLoad.length;
                let imagesLoaded = 0;

                function onImageLoad() {
                    imagesLoaded++;
                    if (imagesLoaded === numImages) {
                        resolve();
                    }
                }

                imagesToLoad.forEach((img) => {
                    if (img.complete) {
                        onImageLoad();
                    } else {
                        img.addEventListener("load", onImageLoad);
                    }
                });
            });

            // Once all images have loaded, get the width of the carouselTrack
            totalWidth = carouselTrack_ID.getBoundingClientRect().width / 2;

            // Set the flag to true to prevent repeated calculations
            isImagesLoaded = true;
        }
    }
    // Get the carousel width when first loading
    onMount(getElementWidth);
    afterUpdate(getElementWidth);

    // --Carousel Animation Options--
    export let carouselAnim_Direction = "";
    export let carouselAnim_Duration = 5;
    let carouselAnim_Key1 = "";
    let carouselAnim_Key2 = "";
    // Change carousel animation direction depending on the user input
    if (
        carouselAnim_Direction === "right" ||
        carouselAnim_Direction === "Right" ||
        carouselAnim_Direction === "RIGHT"
    ) {
        carouselAnim_Key2 = "translateX(0px);";
        carouselAnim_Key1 = "translateX(calc(var(--total-width)));";
    } else {
        carouselAnim_Key1 = "translateX(0px);";
        carouselAnim_Key2 = "translateX(calc(var(--total-width)));";
    }

    // --Pause Carousel on Click--
    let isPaused = false;
    function handleKey() {
        isPaused = !isPaused;
        if (isPaused) {
            carouselTrack_ID.style.animationPlayState = "paused";
        } else {
            carouselTrack_ID.style.animationPlayState = "running";
        }
    }
</script>

<div class="carouselContainer">
    <div
        class="carouselTrack"
        bind:this={carouselTrack_ID}
        style={`--total-width: -${totalWidth}px; --total-num: ${totalNum}; --anim-time: ${carouselAnim_Duration}s; --anim-key1: ${carouselAnim_Key1}; --anim-key2: ${carouselAnim_Key2};`}
    >
        {#each loopImages as image, index}
            <Carousel_Image
                imageSrc={image}
                imageAlt={`test-${index + 1}`}
                on:pauseCarousel={handleKey}
            />
        {/each}
    </div>
</div>

<style>
    .carouselContainer {
        width: calc(100% + 128px);
        margin-left: -64px;
        position: relative;
        flex-direction: row;
        display: flex;
        overflow-x: clip;
    }

    .carouselTrack {
        display: flex;
        animation: carouselAnim calc(var(--anim-time) * var(--total-num)) linear
            infinite;
        animation-play-state: running;
    }

    @keyframes carouselAnim {
        0% {
            transform: var(--anim-key1);
        }
        100% {
            transform: var(--anim-key2);
        }
    }
</style>
