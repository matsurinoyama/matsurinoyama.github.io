<script>
  import { onMount } from "svelte";
  // --Tabler Icons--
  import { IconBrandTwitter } from "@tabler/icons-svelte";
  import { IconBrandInstagram } from "@tabler/icons-svelte";
  import { IconBrandLinkedin } from "@tabler/icons-svelte";

  // --Loading Animation--
  import Loader from "./Loader.svelte";
  let isLoading = true;
  // Simulate a loading delay using a setTimeout
  onMount(() => {
    setTimeout(() => {
      isLoading = false;
    }, 1000); // Change the delay time as needed
  });

  // --Random Icon on Reload--
  // Icon speed variations
  const icon = [
    "/icon_10-white.png",
    "/icon_15-white.png",
    "/icon_20-white.png",
    "/icon_25-white.png",
    "/icon_30-white.png",
  ];
  // Set a default image to avoid undefined source before the first mount
  let rand_iconSpeed = icon[3];
  // Function to select a random image
  function selectRand_iconSpeed() {
    const randIndex = Math.floor(Math.random() * icon.length);
    rand_iconSpeed = icon[randIndex];
  }
  // Call the function on component mount to set the initial image
  onMount(selectRand_iconSpeed);

  // --Get Current Year--
  let currentYear = new Date().getFullYear();
</script>

{#if isLoading}
  <Loader />
{/if}

<header>
  <div class="headerLinks">
    <a href="/about" target="_self"><h5>自己紹介</h5></a>
    <a href="/resume" target="_self"><h5>履歴書</h5></a>
  </div>
  <div class="headerLinks">
    <a href="/works" target="_self"><h5>作品集</h5></a>
    <a href="/contact" target="_self"><h5>お問い合わせ</h5></a>
  </div>
  <a href="/" target="_self"
    ><img src={rand_iconSpeed} alt="Home" height="64px" /></a
  >
</header>

<slot />

<footer>
  <div class="footerNotice">
    <img src="/icon_1-yellow.png" alt="Icon" height="32px" />
    <div class="footerNotice_Text">
      <h6>
        Copyright (c) {currentYear} Azhan Rizan / 莉山礼司. All code written for
        this website are licensed under the MIT License. Read the
        <a
          href="https://github.com/matsurinoyama/matsurinoyama.github.io/blob/master/LICENSE.md"
          >license</a
        > for more details.
      </h6>
    </div>
  </div>
  <div class="footerLinks">
    <a href="https://twitter.com/matsurinoyama"
      ><IconBrandTwitter size={16} stroke={1.5} color={"#ffffff"} /></a
    >
    <a href="https://instagram.com/matsurinoyama"
      ><IconBrandInstagram size={16} stroke={1.5} color={"#ffffff"} /></a
    >
    <a href="https://linkedin.com/in/matsurinoyama"
      ><IconBrandLinkedin size={16} stroke={1.5} color={"#ffffff"} /></a
    >
    <a href="mailto:matsurinoyama@proton.me"><p>matsurinoyama@proton.me</p></a>
  </div>
</footer>
