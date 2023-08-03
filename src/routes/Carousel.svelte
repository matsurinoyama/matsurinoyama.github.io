<script>
    import { onMount, afterUpdate } from "svelte";
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

    // --Total Number & Width of Images--
    let totalNum = images.length * 2;
    let totalWidth = 0;
    let carouselTrack_ID;
    // Calculate the total width of all images
    function calc_totalWidth() {
        if (carouselTrack_ID) {
            const loadedImages = carouselTrack_ID.querySelectorAll("img");

            totalWidth = Array.from(loadedImages).reduce(
                (acc, img) => acc + img.width,
                0
            );
        }
    }
    // Calculate initial total width on component load
    onMount(() => {
        calc_totalWidth();
    });
    // Recalculate total width after loading all elements
    afterUpdate(() => {
        calc_totalWidth();
    });

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
        carouselAnim_Key2 = "translateX(-8px);";
        carouselAnim_Key1 =
            "translateX(calc(var(--total-width) / 2 * -1 - 64px - calc(8px * var(--total-num) - 16px)));";
    } else {
        carouselAnim_Key1 = "translateX(-8px);";
        carouselAnim_Key2 =
            "translateX(calc(var(--total-width) / 2 * -1 - 64px - calc(8px * var(--total-num) - 16px)));";
    }
</script>

<div class="carouselContainer">
    <div
        class="carouselTrack"
        bind:this={carouselTrack_ID}
        style={`--total-width: ${totalWidth}px; --total-num: ${totalNum}; --anim-time: ${carouselAnim_Duration}s; --anim-key1: ${carouselAnim_Key1}; --anim-key2: ${carouselAnim_Key2};`}
    >
        {#each loopImages as image, index}
            <div class="imageContainer">
                <img src={image} alt={`test-${index + 1}`} />
            </div>
        {/each}
    </div>
</div>

<style>
    .carouselContainer {
        width: 100vw;
        transform: translateX(-64px);

        overflow: hidden;
        position: relative;
    }

    .carouselTrack {
        display: flex;
        animation: carouselAnim calc(var(--anim-time) * var(--total-num)) linear
            infinite;
    }

    .imageContainer {
        background-color: var(--mRED);
        border-radius: 32px;
        margin: 0px 8px;
        border: 1px solid white;
        height: calc(50vh + 2px);
    }

    .imageContainer img {
        mix-blend-mode: exclusion;
        filter: grayscale(15%) contrast(130%);
        width: auto;
        height: 50vh;
        border-radius: 32px;
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
