// Elements
const fileInput = document.getElementById("fileInput");
const preview = document.getElementById("preview");
const video = document.getElementById("video");
const overlay = document.getElementById("overlay");
const guidanceText = document.getElementById("guidanceText");

// Step elements
const stepChoice = document.getElementById("step-choice");
const stepUpload = document.getElementById("step-upload");
const stepCamera = document.getElementById("step-camera");
const stepPreview = document.getElementById("step-preview");

// Choice buttons
const chooseUpload = document.getElementById("chooseUpload");
const chooseCamera = document.getElementById("chooseCamera");

// Upload elements
const backFromUpload = document.getElementById("backFromUpload");

// Camera elements
const startCameraBtn = document.getElementById("startCameraBtn");
const stopCameraBtn = document.getElementById("stopCameraBtn");
const captureBtn = document.getElementById("captureBtn");
const backFromCamera = document.getElementById("backFromCamera");

// Preview elements
const confirmUpload = document.getElementById("confirmUpload");
const retryPhoto = document.getElementById("retryPhoto");

// State
let mediaStream = null;
let animationId = null;
let currentPhotoData = null;
let currentMethod = null; // 'upload' or 'camera'

// Step management
function showStep(stepId) {
  document
    .querySelectorAll(".step")
    .forEach((step) => step.classList.remove("active"));
  document.getElementById(stepId).classList.add("active");
}

// Photo data management
function setPhotoData(dataUrl, method) {
  currentPhotoData = dataUrl;
  currentMethod = method;
  preview.innerHTML = `<img src="${dataUrl}" alt="Preview">`;
}

function clearPhotoData() {
  currentPhotoData = null;
  currentMethod = null;
  preview.innerHTML = "";
}

// Step 1: Choice
chooseUpload.addEventListener("click", () => {
  showStep("step-upload");
});

chooseCamera.addEventListener("click", async () => {
  showStep("step-camera");
  // Auto-start camera when choosing camera option
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user" },
    });
    video.srcObject = mediaStream;
    enable(captureBtn, true);
    enable(stopCameraBtn, true);
    startOverlayLoop();
  } catch (err) {
    alert("Camera access denied or unavailable");
  }
});

// Step 2: Upload
backFromUpload.addEventListener("click", () => {
  showStep("step-choice");
  clearPhotoData();
});

fileInput.addEventListener("change", () => {
  if (fileInput.files && fileInput.files[0]) {
    const reader = new FileReader();
    reader.onload = (e) => {
      setPhotoData(e.target.result, "upload");
      showStep("step-preview");
    };
    reader.readAsDataURL(fileInput.files[0]);
  }
});

// Step 2: Camera
backFromCamera.addEventListener("click", () => {
  stopCamera();
  showStep("step-choice");
  clearPhotoData();
});

// Camera starts automatically when choosing camera option, so this is no longer needed

stopCameraBtn.addEventListener("click", () => {
  stopCamera();
});

function stopCamera() {
  if (animationId) cancelAnimationFrame(animationId);
  if (overlay) {
    const ctx = overlay.getContext("2d");
    ctx && ctx.clearRect(0, 0, overlay.width, overlay.height);
  }
  if (mediaStream) {
    mediaStream.getTracks().forEach((t) => t.stop());
    mediaStream = null;
  }
  enable(captureBtn, false);
  enable(stopCameraBtn, false);
}

captureBtn.addEventListener("click", () => {
  if (!video || !mediaStream) return;
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext("2d");

  // Flip the captured image horizontally to match the mirrored preview
  ctx.scale(-1, 1);
  ctx.drawImage(video, -canvas.width, 0, canvas.width, canvas.height);

  const dataUrl = canvas.toDataURL("image/jpeg", 0.92);

  setPhotoData(dataUrl, "camera");
  stopCamera();
  showStep("step-preview");
});

// Step 3: Preview and confirm
confirmUpload.addEventListener("click", async () => {
  if (!currentPhotoData) return;

  try {
    let blob;
    if (currentMethod === "upload") {
      // Use the original file for upload
      blob = fileInput.files[0];
    } else {
      // Convert data URL to blob for camera capture
      blob = await (await fetch(currentPhotoData)).blob();
    }

    const formData = new FormData();
    formData.append(
      "image",
      blob,
      currentMethod === "camera" ? "captured.jpg" : fileInput.files[0].name
    );

    const res = await fetch("/upload", { method: "POST", body: formData });
    if (res.ok) {
      const data = await res.json();
      alert(data.message || "Photo uploaded successfully!");
      // Reset to start
      clearPhotoData();
      fileInput.value = "";
      showStep("step-choice");
    } else {
      const error = await res.text();
      alert(`Upload failed: ${error}`);
    }
  } catch (err) {
    alert("Upload failed: " + err.message);
  }
});

retryPhoto.addEventListener("click", () => {
  if (currentMethod === "upload") {
    showStep("step-upload");
  } else {
    showStep("step-camera");
  }
});

// Helper functions
function enable(el, on) {
  el.disabled = !on;
}

// Simple oval guide overlay
function startOverlayLoop() {
  const ctx = overlay.getContext("2d");
  function resizeOverlayToVideo() {
    const rect = video.getBoundingClientRect();
    overlay.width = rect.width * devicePixelRatio;
    overlay.height = rect.height * devicePixelRatio;
    overlay.style.width = rect.width + "px";
    overlay.style.height = rect.height + "px";
  }
  resizeOverlayToVideo();
  window.addEventListener("resize", resizeOverlayToVideo);
  video.addEventListener("loadedmetadata", resizeOverlayToVideo);

  function draw() {
    animationId = requestAnimationFrame(draw);
    const w = overlay.width,
      h = overlay.height;
    ctx.clearRect(0, 0, w, h);

    // Draw framing guide (central oval)
    const cx = w / 2,
      cy = h / 2;
    const rx = Math.min(w, h) * 0.28;
    const ry = Math.min(w, h) * 0.38;
    ctx.save();
    ctx.beginPath();
    ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
    ctx.lineWidth = Math.max(2, Math.min(w, h) * 0.006);
    ctx.strokeStyle = "rgba(255,255,255,0.9)";
    ctx.stroke();
    ctx.restore();

    guidanceText.textContent =
      "Center your face in the oval and capture when ready";
  }
  draw();
}
