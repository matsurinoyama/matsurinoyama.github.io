// Drifting Away — Control Panel logic
// Adds mic reset buttons for both players

document.addEventListener("DOMContentLoaded", () => {
  const btnResetMic1 = document.getElementById("btn-reset-mic-1");
  const btnResetMic2 = document.getElementById("btn-reset-mic-2");

  if (btnResetMic1) {
    btnResetMic1.addEventListener("click", () => {
      window.open("/player/1?reset_mic=1", "_blank");
    });
  }
  if (btnResetMic2) {
    btnResetMic2.addEventListener("click", () => {
      window.open("/player/2?reset_mic=1", "_blank");
    });
  }
});
