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
            "translateX(calc(var(--total-width) / 2  * -1 - calc(9px * var(--total-num))));";
    } else {
        carouselAnim_Key1 = "translateX(-8px);";
        carouselAnim_Key2 =
            "translateX(calc(var(--total-width) / 2  * -1 - calc(9px * var(--total-num))));";
    }

    // --Expand Image on Click--
    let imageContainer_ID;
    let isPaused = false;
    let expandedIndex = null; // Track the index of the expanded image
    let expandedTop = 0; // Track the top position of the expanded image

    // Pauses carousel animation and toggles the expanded state
    function toggleImageExpansion(index) {
        isPaused = !isPaused;
        if (isPaused) {
            carouselTrack_ID.style.animationPlayState = "paused";
        } else {
            carouselTrack_ID.style.animationPlayState = "running";
        }

        // Toggle the expanded state for the clicked image
        if (expandedIndex === index) {
            expandedIndex = null;
        } else {
            expandedIndex = index;
        }
    }

    function handleKey(event, index) {
        if (event.key === "Enter" || event.key === " ") {
            toggleImageExpansion(index);
        }
    }

    // Calculate the top position for the expanded image
    $: {
        if (expandedIndex !== null) {
            const clickedImage = imageContainer_ID.getBoundingClientRect();
            expandedTop = window.scrollY + clickedImage.top;
        }
    }
</script>

<div class="carouselContainer">
    <div
        class="carouselTrack"
        bind:this={carouselTrack_ID}
        style={`--total-width: ${totalWidth}px; --total-num: ${totalNum}; --anim-time: ${carouselAnim_Duration}s; --anim-key1: ${carouselAnim_Key1}; --anim-key2: ${carouselAnim_Key2};`}
    >
        {#each loopImages as image, index}
            <div
                class="imageContainer {expandedIndex === index ? 'expanded' : ''}"
                bind:this={imageContainer_ID}
                on:click={() => toggleImageExpansion(index)}
                on:keydown={(event) => handleKey(event, index)}
                style={`--top-position: ${expandedTop}px;`}
                role="button" tabindex="0">
                <img src={image} alt={`test-${index + 1}`} />
            </div>
        {/each}
    </div>
</div>

<style>
    .imageContainer.expanded, .imageContainer.expanded img {
        width: 100vw;
        height: 100vh;
        position: fixed;
        top: var(--top-position);
        left: 0;
        margin: 0;
        z-index: 777;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .imageContainer.expanded::before, .imageContainer.expanded::after {
        position: fixed;
        top: var(--top-position);
        left: 0;
        margin: 0;
        z-index: 777;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    .carouselContainer {
        width: calc(100% + 128px);
        margin-left: -64px;
        overflow: hidden;
        position: relative;
    }

    .carouselTrack {
        display: flex;
        animation: carouselAnim calc(var(--anim-time) * var(--total-num)) linear
            infinite;
        animation-play-state: running;
    }

    .imageContainer::before {
        content: "";
        background: url("noise.png");
        height: 100%;
        border-radius: 8px;
        position: absolute;
        left: 0;
        bottom: 0;
        top: 0;
        right: 0;
        opacity: 1;
        transition: border-radius 0.5s ease-out, opacity 0.7s ease-out;
    }

    .imageContainer:hover::before {
        border-radius: 0px;
        opacity: 0;
    }

    .imageContainer {
        background-color: none;
        margin: 0px 8px;
        height: 50vh;
        max-width: calc(100vw - 128px);
        position: relative;
    }

    .imageContainer img {
        mix-blend-mode: exclusion;
        filter: grayscale(30%) contrast(130%) brightness(115%);
        object-fit: cover;
        max-width: calc(100vw - 128px);
        height: 50vh;
        border-radius: 8px;
        transition: 0.5s ease-out;
    }

    .imageContainer:hover img {
        filter: grayscale(0%) contrast(100%) brightness(100%);
        border-radius: 0px;
    }

    .imageContainer::after {
        content: "";
        border: 1px solid white;
        border-radius: 8px;
        height: calc(50vh - 2px);
        position: absolute;
        left: 0;
        bottom: 0;
        top: 0;
        right: 0;
        transition: 0.5s ease-out;
    }

    .imageContainer:hover::after {
        border: 1px solid rgba(255, 255, 255, 0);
        border-radius: 0px;
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
