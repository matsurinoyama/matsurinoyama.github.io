<script>
    import { onMount, afterUpdate } from "svelte";

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

    // Function to shuffle the array randomly
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

    let totalNum = images.length * 2;
    let totalWidth = 0;

    onMount(() => {
        calc_totalWidth();
    });

    afterUpdate(() => {
        calc_totalWidth();
    });

    function calc_totalWidth() {
        const carouselTrack = document.querySelector(".carouselTrack");
        const loadedImages = carouselTrack.querySelectorAll("img");

        totalWidth = Array.from(loadedImages).reduce(
            (acc, img) => acc + img.width,
            0
        );
    }
</script>

<div class="carouselContainer">
    <div
        class="carouselTrack"
        style={`--total-width: ${totalWidth}px; --total-num: ${totalNum};`}
    >
        {#each loopImages as image, index}
            <img src={image} alt={`test-${index + 1}`} />
        {/each}
    </div>
</div>

<style>
    .carouselContainer {
        width: 100vw;
        transform: translateX(-64px);
        mix-blend-mode: exclusion;
        filter: grayscale(15%) contrast(130%);
        overflow: hidden;
        position: relative;
    }

    .carouselTrack {
        display: flex;
        animation: carouselAnim calc(5s * var(--total-num)) linear infinite;
    }

    .carouselTrack img {
        margin: 32px 8px;
        width: auto;
        height: 512px;
        border-radius: 32px;
        border: white 1px;
        border-style: solid;
    }

    @keyframes carouselAnim {
        0% {
            transform: translateX(-8px);
        }
        100% {
            transform: translateX(
                calc(
                    var(--total-width) / 2 * -1 - 64px -
                        calc(8px * var(--total-num) - 16px)
                )
            );
        }
    }
</style>
