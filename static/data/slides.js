const IMAGE_INDEX = {
  "2022/WWSA": ["after_01.jpg", "after_02.jpg", "after_03.jpg", "after_04.jpg"],
  "2023/PAWD": ["PAM1.jpg", "PAM2.jpg", "PAM3.jpg"],
  "2024/001": ["preview.gif"],
  "2025/SMG": ["bathroom.jpg", "poster.jpg"],
  "2025/EER/001": [
    "preview_01.gif",
    "preview_02.gif",
    "peopleNotMet-Demachiyanagi_01.jpg",
    "peopleNotMet-Demachiyanagi_02.jpg",
    "peopleNotMet-Demachiyanagi_03.jpg",
  ],
  "2025/EER/002": [
    "preview_01.gif",
    "preview_02.gif",
    "stationMaster_01.jpg",
    "stationMaster_02.jpg",
    "stationMaster_03.jpg",
  ],
  "2026/WCC": [
    "preview_01.gif",
    "preview_02.gif",
    "driftingAway_01.jpeg",
    "driftingAway_02.jpeg",
    "driftingAway_03.jpeg",
    "driftingAway_04.jpeg",
    "driftingAway_05.jpeg",
    "driftingAway_06.jpeg",
    "driftingAway_07.jpeg",
    "driftingAway_08.jpeg",
    "driftingAway_09.jpeg",
    "driftingAway_10.jpeg",
    "driftingAway_11.jpeg",
  ],
};

const SLIDES = [
  {
    folder: "2022/WWSA",
    caption: "Warna-Warni Shah Alam, 2022",
    caption_ja: "Warna-Warni Shah Alam、2022年",
  },
  {
    folder: "2023/PAWD",
    caption: "PAM Awards 2023, 2023",
    caption_ja: "PAM Awards 2023、2023年",
  },
  {
    folder: "2024/001",
    caption: "untitled video experiment, 2024",
    caption_ja: "無題映像実験、2024年",
  },
  {
    folder: "2025/SMG",
    caption: "Mamorigami No Me, 2025",
    caption_ja: "守神の目、2025年",
  },
  {
    folder: "2025/EER/001",
    caption: "the people we have (not) met @Demachiyanagi Station, 2025",
    caption_ja: "巡り合った（ことのない）人々 @出町柳駅、2025年",
  },
  {
    folder: "2025/EER/002",
    caption: "Everyone's Stationmaster, 2025",
    caption_ja: "みんなの駅長、2025年",
  },
  {
    folder: "2026/WCC",
    caption: "Drifting Away, 2026",
    caption_ja: "離れていく、2026年",
  },
];

function getRandomImage(folder) {
  const images = IMAGE_INDEX[folder];
  const randomImage = images[Math.floor(Math.random() * images.length)];
  return `${folder}/${randomImage}`;
}

// Initialize slides with random images
const slidesWithImages = SLIDES.map((slide) => ({
  ...slide,
  image: getRandomImage(slide.folder),
}));
