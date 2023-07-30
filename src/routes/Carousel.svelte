<div class="carousel-container">
    <div class="carousel-track">
      <img src="test/image_01.jpg" alt="test1">
      <img src="test/image_02.png" alt="test2">
      <img src="test/image_03.jpg" alt="test3">
      <img src="test/image_04.jpg" alt="test4">
      <img src="test/image_05.png" alt="test5">
      <img src="test/image_06.jpg" alt="test6">
      <img src="test/image_07.jpg" alt="test7">
      <img src="test/image_08.jpg" alt="test8">
      <img src="test/image_09.jpg" alt="test9">
      <img src="test/image_10.jpg" alt="test10">
      <img src="test/image_11.jpg" alt="test11">
      <img src="test/image_12.png" alt="test12">
      <img src="test/image_13.png" alt="test13">
      <img src="test/image_14.jpg" alt="test14">
      <img src="test/image_15.jpg" alt="test15">
      <img src="test/image_16.jpg" alt="test16">
      <img src="test/image_01.jpg" alt="test1">
      <img src="test/image_02.png" alt="test2">
      <img src="test/image_03.jpg" alt="test3">
      <!-- Add more images here -->
    </div>
</div>

<style>

    .carousel-container {
        width: 100vw;
        transform: translateX(-64px);
        mix-blend-mode: exclusion;
        overflow: hidden;
        position: relative;
    }

    .carousel-track {
        display: flex;
        animation: carouselSlide 180s linear infinite;
    }

    .carousel-track img {
        margin: 32px 8px;
        width: auto;
        height: 512px;
        border-radius: 32px;
        border: white 1px;
        border-style: solid;
    }

    @keyframes carouselSlide {
    0% {
        transform: translateX(0);
    }
    100% {
        transform: translateX(-740%);
    }
    }

</style>