// ChildNutriAI — shared front-end logic
// Each block guards on the element it needs, so this one file can be
// safely included on every page without throwing on missing elements.

const STORAGE_KEY = 'childnutriai_child';

/* ---------------- Register page ---------------- */
const registerForm = document.getElementById('registerForm');
if (registerForm) {
  registerForm.addEventListener('submit', function (e) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.target).entries());
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    const note = document.getElementById('savedNote');
    if (note) note.classList.add('visible');
    setTimeout(() => { window.location.href = 'upload.html'; }, 700);
  });
}

/* ---------------- Upload page ---------------- */
function wireUpload(inputId, boxId, statusClass) {
  const input = document.getElementById(inputId);
  const box = document.getElementById(boxId);
  if (!input || !box) return;
  input.addEventListener('change', () => {
    const file = input.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      box.classList.add('has-image');
      box.innerHTML = `<img src="${e.target.result}" alt="${inputId} preview">`;
      updateUploadState();
    };
    reader.readAsDataURL(file);
  });
}

function updateUploadState() {
  const face = document.getElementById('faceInput');
  const body = document.getElementById('bodyInput');
  const uploadBtn = document.getElementById('uploadBtn');
  const nextBtn = document.getElementById('nextBtn');
  if (!uploadBtn || !nextBtn) return;
  const bothChosen = face?.files?.length && body?.files?.length;
  uploadBtn.disabled = !bothChosen;
}

const faceInputEl = document.getElementById('faceInput');
const bodyInputEl = document.getElementById('bodyInput');
if (faceInputEl && bodyInputEl) {
  wireUpload('faceInput', 'faceBox');
  wireUpload('bodyInput', 'bodyBox');
  updateUploadState();

  const uploadBtn = document.getElementById('uploadBtn');
  const nextBtn = document.getElementById('nextBtn');
  const uploadStatus = document.getElementById('uploadStatus');

  uploadBtn?.addEventListener('click', () => {
    uploadBtn.textContent = 'Uploading…';
    uploadBtn.disabled = true;
    setTimeout(() => {
      uploadBtn.textContent = 'Uploaded ✓';
      if (uploadStatus) {
        uploadStatus.textContent = 'Both images uploaded successfully.';
        uploadStatus.classList.add('visible');
      }
      nextBtn.disabled = false;
    }, 900);
  });

  nextBtn?.addEventListener('click', () => {
    window.location.href = 'processing.html';
  });
}

/* ---------------- Processing page ---------------- */
const progressBar = document.getElementById('progressBar');
const countdownEl = document.getElementById('countdown');
if (progressBar && countdownEl) {
  const totalMs = 4000;
  const stepMs = 100;
  let elapsed = 0;

  const timer = setInterval(() => {
    elapsed += stepMs;
    const pct = Math.min(100, (elapsed / totalMs) * 100);
    progressBar.style.width = pct + '%';
    const secondsLeft = Math.max(0, Math.ceil((totalMs - elapsed) / 1000));
    countdownEl.textContent = secondsLeft;

    if (elapsed >= totalMs) {
      clearInterval(timer);
      window.location.href = 'dashboard.html';
    }
  }, stepMs);
}

/* ---------------- Dashboard page ---------------- */
const childNameEl = document.getElementById('childName');
if (childNameEl) {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) {
    try {
      const c = JSON.parse(saved);
      if (c.childName) {
        childNameEl.textContent = c.childName;
        const initialEl = document.getElementById('childInitial');
        if (initialEl) initialEl.textContent = c.childName.trim().charAt(0).toUpperCase() || 'R';
      }
      const ageEl = document.getElementById('childAge');
      const genderEl = document.getElementById('childGender');
      if (ageEl && c.age) ageEl.textContent = c.age;
      if (genderEl && c.gender) {
        genderEl.textContent = c.gender.charAt(0).toUpperCase() + c.gender.slice(1);
      }
    } catch (e) { /* keep defaults */ }
  }

  // Animate the confidence ring on load
  window.addEventListener('load', () => {
    const ring = document.querySelector('.ring-fg');
    if (!ring) return;
    const circumference = 2 * Math.PI * 70;
    const confidence = parseFloat(document.getElementById('confidenceValue')?.dataset.value || '0.94');
    requestAnimationFrame(() => {
      ring.style.strokeDashoffset = circumference * (1 - confidence);
    });
  });

  // Download report as a simple text file (stand-in for a PDF export)
  const downloadBtn = document.getElementById('downloadReportBtn');
  downloadBtn?.addEventListener('click', () => {
    const name = childNameEl.textContent.trim();
    const age = document.getElementById('childAge')?.textContent.trim() || '3';
    const gender = document.getElementById('childGender')?.textContent.trim() || 'Male';
    const report = `ChildNutriAI — Assessment Report
================================
Child Information
  Name   : ${name}
  Age    : ${age} Years
  Gender : ${gender}

Prediction
  Moderate Malnutrition
  Confidence: 94%

Nutrition Recommendation
  - Milk
  - Eggs
  - Green vegetables
  - Protein rich food

Risk: Medium
Growth Status: Healthy progress

--------------------------------
Generated by ChildNutriAI (demo build — prediction is placeholder data)
`;
    const blob = new Blob([report], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${name.replace(/\s+/g, '_') || 'child'}_report.txt`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  });
}
