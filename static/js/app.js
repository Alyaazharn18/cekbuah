/*
 * CekBuah — frontend flow: unggah gambar -> analisis -> hasil.
 *
 * DEMO_MODE = true  => hasil contoh dibuat di browser (backend belum dipakai).
 * DEMO_MODE = false => hasil diambil dari endpoint /predict (Flask + model CNN).
 */
const DEMO_MODE = false;
const DEMO_DELAY = 1100;

const FRUIT_NAMES = { Apple: "Apel", Banana: "Pisang", Orange: "Jeruk" };

const input = document.getElementById("imageInput");
const dropZone = document.getElementById("dropZone");
const preview = document.getElementById("imagePreview");
const previewBackdrop = document.getElementById("previewBackdrop");
const placeholder = document.getElementById("previewPlaceholder");
const removeButton = document.getElementById("removeImage");
const predictButton = document.getElementById("predictButton");
const buttonLabel = predictButton.querySelector(".btn-label");
const statusMessage = document.getElementById("statusMessage");
const resultBadge = document.getElementById("resultBadge");
const badgeText = document.getElementById("badgeText");
const resultDescription = document.getElementById("resultDescription");
const confidenceValue = document.getElementById("confidenceValue");
const confidenceFill = document.getElementById("confidenceFill");
const resultCard = document.getElementById("resultCard");
const resultIconUse = document.querySelector("#resultIcon use");
const steps = Array.from(document.querySelectorAll(".step"));
const stepLines = Array.from(document.querySelectorAll(".step-line"));

let selectedFile = null;
let previewUrl = null;
let dragDepth = 0;

/* ---------- Status & langkah ---------- */
function setStatus(message, type = "info") {
  statusMessage.textContent = message;
  statusMessage.classList.toggle("is-error", type === "error");
  statusMessage.classList.toggle("is-success", type === "success");
}

function setSteps(activeStep) {
  steps.forEach((step) => {
    const number = Number(step.dataset.step);
    step.classList.toggle("is-active", number === activeStep);
    step.classList.toggle("is-done", number < activeStep);
  });
  stepLines.forEach((line) => {
    line.classList.toggle("is-done", Number(line.dataset.line) < activeStep);
  });
}

function setBadge(text, variant) {
  badgeText.textContent = text;
  resultBadge.className = `result-badge ${variant}`;
}

/* ---------- Upload ---------- */
function showFile(file) {
  if (!file) return;
  const allowed = ["image/jpeg", "image/png"];
  if (!allowed.includes(file.type)) {
    setStatus("Format file harus JPG, JPEG, atau PNG.", "error");
    return;
  }
  if (file.size > 5 * 1024 * 1024) {
    setStatus("Ukuran gambar maksimal 5 MB.", "error");
    return;
  }

  selectedFile = file;
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = URL.createObjectURL(file);
  preview.src = previewUrl;
  previewBackdrop.style.backgroundImage = `url("${previewUrl}")`;
  preview.hidden = false;
  placeholder.hidden = true;
  removeButton.hidden = false;
  predictButton.disabled = false;

  setBadge("Siap Dianalisis", "neutral");
  resultDescription.textContent = "Tekan tombol Prediksi untuk mengetahui kondisi buah.";
  confidenceValue.textContent = "—";
  confidenceFill.style.width = "0%";
  resultCard.classList.remove("is-fresh", "is-rotten");
  resultIconUse.setAttribute("href", "#i-image");
  setSteps(2);
  setStatus("Gambar berhasil dipilih.", "success");
}

input.addEventListener("change", (event) => showFile(event.target.files[0]));

["dragenter", "dragover"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    if (eventName === "dragenter") dragDepth += 1;
    dropZone.classList.add("dragover");
  });
});
["dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    if (eventName === "dragleave") dragDepth = Math.max(0, dragDepth - 1);
    if (dragDepth === 0) dropZone.classList.remove("dragover");
  });
});
dropZone.addEventListener("drop", (event) => {
  dragDepth = 0;
  dropZone.classList.remove("dragover");
  showFile(event.dataTransfer.files[0]);
});

/* ---------- Hapus gambar / reset ---------- */
function clearImage() {
  selectedFile = null;
  input.value = "";
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = null;
  preview.removeAttribute("src");
  previewBackdrop.style.backgroundImage = "";
  preview.hidden = true;
  placeholder.hidden = false;
  removeButton.hidden = true;
  predictButton.disabled = true;

  setBadge("Menunggu Prediksi", "neutral");
  resultDescription.textContent = "Hasil analisis akan ditampilkan di sini.";
  confidenceValue.textContent = "—";
  confidenceFill.style.width = "0%";
  resultCard.classList.remove("is-fresh", "is-rotten");
  resultIconUse.setAttribute("href", "#i-info");
  setSteps(1);
  setStatus("Pilih gambar buah terlebih dahulu untuk memulai prediksi.");
}
removeButton.addEventListener("click", clearImage);
window.addEventListener("beforeunload", () => {
  if (previewUrl) URL.revokeObjectURL(previewUrl);
});

/* ---------- Prediksi ---------- */
function startLoading() {
  predictButton.disabled = true;
  predictButton.classList.add("is-loading");
  buttonLabel.textContent = "Menganalisis...";
  setSteps(2);
  setStatus("Sedang menganalisis gambar. Mohon tunggu.");
  resultCard.style.opacity = ".55";
}

function stopLoading() {
  predictButton.classList.remove("is-loading");
  buttonLabel.textContent = "Prediksi";
  predictButton.disabled = !selectedFile;
  resultCard.style.opacity = "";
}

function showResult(label, confidence, result = {}) {
  const isFresh = label === "Segar";
  const fruit = FRUIT_NAMES[result.fruit] || result.fruit;
  const condition = isFresh ? "segar" : "busuk";

  resultCard.classList.toggle("is-fresh", isFresh);
  resultCard.classList.toggle("is-rotten", !isFresh);
  setBadge(isFresh ? "Segar" : "Busuk", isFresh ? "fresh" : "rotten");
  resultIconUse.setAttribute("href", isFresh ? "#i-check" : "#i-x");
  resultDescription.textContent = fruit
    ? `Buah teridentifikasi sebagai ${fruit} dalam kondisi ${condition}.`
    : `Buah teridentifikasi dalam kondisi ${condition}.`;
  confidenceValue.textContent = `${confidence}%`;

  // Animasikan meter dari 0 ke nilai confidence.
  confidenceFill.style.width = "0%";
  requestAnimationFrame(() => { confidenceFill.style.width = `${Math.min(100, Math.max(0, confidence))}%`; });

  setSteps(3);
  setStatus(
    result.is_uncertain
      ? "Keyakinan model masih rendah. Coba gunakan foto buah yang lebih jelas."
      : "Analisis berhasil diselesaikan.",
    result.is_uncertain ? "info" : "success"
  );
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Contoh hasil untuk keperluan demo frontend. Nama file mengandung
// "busuk"/"rotten" akan menampilkan kondisi Busuk, selain itu Segar.
function demoPrediction(file) {
  const name = file.name.toLowerCase();
  const isRotten = /busuk|rotten|spoiled/.test(name);
  const seed = (name.length * 7 + (file.size % 53)) % 14;
  const confidence = Number((84.2 + seed + 0.3).toFixed(1));
  return { label: isRotten ? "Busuk" : "Segar", confidence };
}

predictButton.addEventListener("click", async () => {
  if (!selectedFile) return;

  const formData = new FormData();
  formData.append("image", selectedFile);

  startLoading();

  try {
    let result;
    if (DEMO_MODE) {
      await wait(DEMO_DELAY);
      result = demoPrediction(selectedFile);
    } else {
      const response = await fetch("/predict", { method: "POST", body: formData });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Prediksi gagal.");
      result = data;
    }
    showResult(result.label, Number(result.confidence), result);
  } catch (error) {
    setStatus(error.message, "error");
    setSteps(2);
  } finally {
    stopLoading();
  }
});
