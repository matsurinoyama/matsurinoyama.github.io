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
  const iconSrc = [
    "/icon_10-white.png",
    "/icon_15-white.png",
    "/icon_20-white.png",
    "/icon_25-white.png",
    "/icon_30-white.png",
  ];
  // Icons on hover
  const iconAlt = [
    "/icon_10-yellow.png",
    "/icon_15-yellow.png",
    "/icon_20-yellow.png",
    "/icon_25-yellow.png",
    "/icon_30-yellow.png",
  ];
  // Set a default image to avoid undefined source before the first mount
  let randSpeed_iconSrc = iconSrc[1];
  let randSpeed_iconAlt = iconAlt[1];
  // Function to select a random image
  function selectRand_iconSpeed() {
    const randIndex = Math.floor(Math.random() * iconSrc.length);
    randSpeed_iconSrc = iconSrc[randIndex];
    randSpeed_iconAlt = iconAlt[randIndex];
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
  <a href="/" target="_self">
    <div class="headerIcon">
      <div class="headerIcon_Alt">
        <img src={randSpeed_iconAlt} alt="Home" />
      </div>
      <div class="headerIcon_Src">
        <img src={randSpeed_iconSrc} alt="Home" />
      </div>
    </div>
  </a>
</header>

<slot />

<footer>
  <div class="footerNotice">
    <img src="/icon_1-yellow.png" alt="Icon" height="32px" />
    <div class="footerNotice_Text">
      <h6>
        Copyright (c) 2023 - {currentYear} Muhammad Azhan Bin Fadzlan Rizan (AKA:
        Azhan Rizan, Reiji Rizan, matsurinoyama). All code written for this website
        is licensed under the EUPL. Read the
        <a
          href="https://raw.githubusercontent.com/matsurinoyama/matsurinoyama.github.io/master/LICENSE.md"
          >license</a
        > for more details.
      </h6>
    </div>
  </div>
  <div class="footerLinks">
    <a href="https://twitter.com/matsurinoyama"
      ><IconBrandTwitter size={18} stroke={1.5} /></a
    >
    <a href="https://instagram.com/matsurinoyama"
      ><IconBrandInstagram size={18} stroke={1.5} /></a
    >
    <a href="https://linkedin.com/in/matsurinoyama"
      ><IconBrandLinkedin size={18} stroke={1.5} /></a
    >
    <a href="mailto:matsurinoyama@proton.me"><p>matsurinoyama@proton.me</p></a>
  </div>
</footer>
