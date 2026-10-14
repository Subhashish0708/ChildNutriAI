/**
 * ChildNutri AI — Complete Clinical Screening Workflow Controller (v4.0)
 * Integrates: Register/Login -> Dashboard -> Add Child -> Child Profile ->
 *             New Screening (5-Step Wizard) -> AI Inference & Multimodal Fusion ->
 *             Screening Result (WHO + AI + Triage + SHAP + Grad-CAM + Nutrition + Longitudinal + Future Risk + PDF)
 */

const API_BASE = (window.location && window.location.origin && window.location.origin.startsWith("http")) 
  ? (window.location.origin + "/api") 
  : "http://127.0.0.1:8000/api";
let currentUser = null;
let currentChildren = [];
let activeProfileChild = null;
let activeProfileChildId = null;
let activeProfileLatestAssessmentId = null;
let resActiveAssessmentId = null;
let resActiveChildId = null;

// Wizard State
let wizCurrentStep = 1;
let wizSelectedChildId = null;
let wizPhotoFile = null;
let wizWhoData = null;

// ---------------------------------------------------------------------------
// Page Initialization
// ---------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", async function () {
  const token = localStorage.getItem("childnutri_token");
  if (!token) {
    window.location.href = "index.html";
    return;
  }

  await loadCurrentUser();
  await loadDashboardStats();
  await loadRecentAssessments();
  await loadInitialChildren();
  await loadSystemStatus();
});

function getAuthHeaders() {
  const token = localStorage.getItem("childnutri_token");
  return {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`
  };
}

// ---------------------------------------------------------------------------
// User & Cohort Data Loaders
// ---------------------------------------------------------------------------
async function loadCurrentUser() {
  try {
    const res = await fetch(`${API_BASE}/auth/me`, { headers: getAuthHeaders() });
    if (!res.ok) {
      localStorage.removeItem("childnutri_token");
      window.location.href = "index.html";
      return;
    }
    currentUser = await res.json();

    const initial = currentUser.full_name ? currentUser.full_name[0].toUpperCase() : "H";
    const sfAvatar = document.querySelector(".sf-avatar");
    if (sfAvatar) sfAvatar.textContent = initial;
    const sfName = document.getElementById("sidebarUserName");
    if (sfName) sfName.textContent = currentUser.full_name;

    const tbAvatar = document.getElementById("topbarUserAvatar");
    if (tbAvatar) tbAvatar.textContent = initial;
    const tbName = document.getElementById("topbarUserName");
    if (tbName) tbName.textContent = currentUser.full_name;

    const profCardName = document.getElementById("profCardName");
    if (profCardName) profCardName.textContent = currentUser.full_name;
    const profCardEmail = document.getElementById("profCardEmail");
    if (profCardEmail) profCardEmail.textContent = currentUser.email;

  } catch (e) {
    console.error("Error loading user profile:", e);
  }
}

async function loadDashboardStats() {
  try {
    const res = await fetch(`${API_BASE}/users/stats`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const stats = await res.json();

    const el = id => document.getElementById(id);
    if (el("statTotalChildren")) el("statTotalChildren").textContent = stats.total_children;
    if (el("statTotalAssessments")) el("statTotalAssessments").textContent = stats.total_assessments || (stats.total_children * 2);
    if (el("statAtRiskChildren")) el("statAtRiskChildren").textContent = stats.at_risk_count;
    if (el("statFollowUps")) el("statFollowUps").textContent = stats.followups_scheduled;

  } catch (e) {
    console.error("Error loading dashboard stats:", e);
  }
}

async function loadInitialChildren() {
  try {
    const res = await fetch(`${API_BASE}/children`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    currentChildren = await res.json();
    populateWizardChildrenDropdown();
  } catch (e) {
    console.error("Error loading cohort children:", e);
  }
}

async function loadRecentAssessments() {
  try {
    const res = await fetch(`${API_BASE}/assessments/recent?limit=8`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const assessments = await res.json();

    const tbody = document.getElementById("dashRecentAssessmentsBody");
    if (!tbody) return;

    if (assessments.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:24px;color:#718096;">No assessments conducted yet. Click "+ New Screening" above.</td></tr>`;
      return;
    }

    tbody.innerHTML = "";
    renderCohortDonut(assessments);
    assessments.forEach(a => {
      const pred = (a.prediction && a.prediction.prediction) ? a.prediction.prediction : (a.prediction_label || "Prediction unavailable");
      const risk = (a.prediction && a.prediction.risk_score != null) ? a.prediction.risk_score : (a.risk_score != null ? a.risk_score : null);
      
      let badgeClass = pred === "Normal" ? "normal" : (pred === "Prediction unavailable" ? "neutral" : "normal");
      let riskLevel = "low";
      if (pred.includes("SAM") || pred.includes("Severe")) { badgeClass = "severe"; riskLevel = "high"; }
      else if (pred.includes("Stunted")) { badgeClass = "stunted"; riskLevel = "high"; }
      else if (pred.includes("Wasted")) { badgeClass = "wasted"; riskLevel = "medium"; }
      else if (pred.includes("Underweight") || pred.includes("Moderate")) { badgeClass = "underweight"; riskLevel = "medium"; }

      const childName = a.child_name || `Child #${a.child_id}`;
      const initial = childName[0].toUpperCase();
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>
          <div class="child-info">
            <div class="child-avatar" style="background:linear-gradient(135deg,#1a7f5a,#27a872)">${initial}</div>
            <div>
              <div class="child-name">${childName}</div>
              <div class="child-age">${a.age_months} mo &bull; ${a.weight}kg &bull; ${a.height}cm</div>
            </div>
          </div>
        </td>
        <td><span class="badge ${badgeClass}">${pred}</span></td>
        <td>
          <div style="display:flex;align-items:center;gap:8px;">
            <div class="risk-bar"><div class="risk-fill ${riskLevel}" style="width:${risk != null ? Math.min(100, Math.max(12, risk)) : 0}%"></div></div>
            <span style="font-size:0.75rem;font-weight:700;color:#475569;">${risk != null ? Math.round(risk) + '%' : '—'}</span>
          </div>
        </td>
        <td class="td-muted">${a.assessment_date}</td>
        <td>
          <div class="action-row">
            <button class="tbl-btn view" onclick="viewChildProfile(${a.child_id})">Profile</button>
            <button class="tbl-btn report" onclick="viewScreeningResult(${a.id}, ${a.child_id})">Result</button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });

  } catch (e) {
    console.error("Error loading recent assessments:", e);
  }
}

// ---------------------------------------------------------------------------
// Multi-View Navigation (SPA Router)
// ---------------------------------------------------------------------------
function showPage(pageName, el) {
  closeSidebar();

  // Update Nav Item active state
  document.querySelectorAll(".nav-item").forEach(item => item.classList.remove("active"));
  if (el) {
    el.classList.add("active");
  } else {
    // Match by ID
    const navMap = {
      "Dashboard": "navDashboard",
      "Children": "navChildren",
      "Parents": "navParents",
      "New Screening": "navNewScreening",
      "Assessment History": "navHistory",
      "Reports": "navReports",
      "Appointments": "navAppointments",
      "Profile": "navProfile"
    };
    const targetNav = document.getElementById(navMap[pageName]);
    if (targetNav) targetNav.classList.add("active");
  }

  // Update Topbar Title
  const titleEl = document.getElementById("pageTitle");
  if (titleEl) titleEl.textContent = pageName;

  // Hide all views
  document.querySelectorAll(".app-view").forEach(view => view.classList.remove("active"));

  // Activate target view
  if (pageName === "Dashboard") {
    const v = document.getElementById("viewDashboard");
    if (v) v.classList.add("active");
    loadDashboardStats();
    loadRecentAssessments();
  } else if (pageName === "Children") {
    const v = document.getElementById("viewChildren");
    if (v) v.classList.add("active");
    loadChildrenDirectory();
  } else if (pageName === "Parents") {
    const v = document.getElementById("viewParents");
    if (v) v.classList.add("active");
    loadParentsDirectory();
  } else if (pageName === "New Screening") {
    const v = document.getElementById("viewNewScreening");
    if (v) v.classList.add("active");
    initNewScreeningWizard();
  } else if (pageName === "Assessment History") {
    const v = document.getElementById("viewHistory");
    if (v) v.classList.add("active");
    loadFullHistory();
  } else if (pageName === "Reports") {
    const v = document.getElementById("viewReports");
    if (v) v.classList.add("active");
    loadReportsDirectory();
  } else if (pageName === "Appointments") {
    const v = document.getElementById("viewAppointments");
    if (v) v.classList.add("active");
    loadAppointments();
  } else if (pageName === "Profile") {
    const v = document.getElementById("viewProfile");
    if (v) v.classList.add("active");
  }
}

// ---------------------------------------------------------------------------
// VIEW: PARENTS DIRECTORY & DATASET
// ---------------------------------------------------------------------------
async function loadParentsDirectory() {
  const tbody = document.getElementById("parentsTableBody");
  const countBadge = document.getElementById("parentsDatasetCountBadge");
  if (tbody) tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:32px;color:var(--text-muted);">Loading parent dataset...</td></tr>`;
  try {
    const res = await fetch(`${API_BASE}/users/parents`, { headers: getAuthHeaders() });
    if (!res.ok) {
      if (tbody) tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:24px;color:#e53e3e;">Failed to load parent records.</td></tr>`;
      return;
    }
    const parents = await res.json();
    if (countBadge) countBadge.textContent = `${parents.length} Parents`;
    if (!tbody) return;
    if (parents.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:32px;color:var(--text-muted);">No parent accounts registered yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = "";
    parents.forEach(p => {
      const initial = p.full_name ? p.full_name[0].toUpperCase() : "P";
      const regDate = p.created_at ? new Date(p.created_at).toLocaleDateString() : "—";
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>
          <div class="child-info">
            <div class="child-avatar" style="background:linear-gradient(135deg,#3182ce,#2b6cb0)">${initial}</div>
            <div>
              <div class="child-name">${p.full_name}</div>
              <div class="child-age">ID #${p.id} &bull; ${p.role}</div>
            </div>
          </div>
        </td>
        <td>${p.email}</td>
        <td>${p.phone || "—"}</td>
        <td><span class="badge ${p.children_count > 0 ? 'normal' : 'neutral'}">${p.children_count} child${p.children_count === 1 ? '' : 'ren'}</span></td>
        <td class="td-muted">${regDate}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Error loading parents directory:", err);
    if (tbody) tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:24px;color:#e53e3e;">Error loading parents.</td></tr>`;
  }
}

async function exportParentsCsv() {
  try {
    showToast("Generating parent dataset CSV export...", "info");
    const res = await fetch(`${API_BASE}/users/parents/export-csv`, { headers: getAuthHeaders() });
    if (!res.ok) {
      showToast("Failed to export parent dataset CSV", "error");
      return;
    }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "parents_registry.csv";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    showToast("✓ Parent dataset CSV exported successfully!");
  } catch (err) {
    console.error("Error exporting parents CSV:", err);
    showToast("Error exporting parent dataset CSV", "error");
  }
}

// ---------------------------------------------------------------------------
// VIEW 2: CHILDREN DIRECTORY
// ---------------------------------------------------------------------------
async function loadChildrenDirectory() {
  try {
    const res = await fetch(`${API_BASE}/children`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    currentChildren = await res.json();

    renderChildrenTable(currentChildren);
  } catch (e) {
    console.error("Error loading children directory:", e);
  }
}

function renderChildrenTable(childrenList) {
  const tbody = document.getElementById("childrenTableBody");
  if (!tbody) return;

  if (childrenList.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:24px;color:#64748b;">No children found. Click "+ Add New Child" to register one.</td></tr>`;
    return;
  }

  tbody.innerHTML = "";
  childrenList.forEach(child => {
    const latest = child.latest_assessment;
    let lastStatus = "Not assessed";
    let badgeClass = "neutral";

    if (latest && latest.prediction && latest.prediction.prediction) {
      lastStatus = latest.prediction.prediction;
      if (lastStatus.includes("SAM") || lastStatus.includes("Severe")) badgeClass = "severe";
      else if (lastStatus.includes("Stunted")) badgeClass = "stunted";
      else if (lastStatus.includes("Wasted")) badgeClass = "wasted";
      else if (lastStatus.includes("Underweight") || lastStatus.includes("Moderate")) badgeClass = "underweight";
      else if (lastStatus.includes("Normal")) badgeClass = "normal";
    }

    const initial = child.name ? child.name[0].toUpperCase() : "C";
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong style="color:#1a7f5a;">${child.health_id || ('CH' + String(child.id).padStart(3, '0'))}</strong></td>
      <td>
        <div class="child-info" style="cursor:pointer;" onclick="viewChildProfile(${child.id})">
          <div class="child-avatar" style="background:linear-gradient(135deg,#1a7f5a,#27a872)">${initial}</div>
          <div style="font-weight:700;color:#0f172a;">${child.name}</div>
        </div>
      </td>
      <td>${child.age_months || 14} mo</td>
      <td>${child.gender || 'Male'}</td>
      <td><span class="badge ${badgeClass}">${lastStatus}</span></td>
      <td>
        <div class="action-row">
          <button class="tbl-btn view" onclick="viewChildProfile(${child.id})">View Profile</button>
          <button class="tbl-btn report" onclick="startScreeningForChild(${child.id})" style="background:#dcfce7;color:#166534;">+ Screen</button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });

  const countBadge = document.getElementById("childrenCountBadge");
  if (countBadge) countBadge.textContent = `Showing ${childrenList.length} children`;
}

function filterChildrenTable(query) {
  if (!query) {
    renderChildrenTable(currentChildren);
    return;
  }
  const q = query.toLowerCase();
  const filtered = currentChildren.filter(c => 
    (c.name && c.name.toLowerCase().includes(q)) ||
    (c.health_id && c.health_id.toLowerCase().includes(q))
  );
  renderChildrenTable(filtered);
}

function filterHighRiskChildren() {
  showPage('Children');
  const filtered = currentChildren.filter(c => {
    const p = c.latest_assessment && c.latest_assessment.prediction;
    return p && (p.risk_score >= 60 || p.prediction.includes("Severe") || p.prediction.includes("SAM") || p.prediction.includes("Stunted"));
  });
  renderChildrenTable(filtered.length > 0 ? filtered : currentChildren);
}

// ---------------------------------------------------------------------------
// VIEW 3: CHILD PROFILE (THE CENTRAL HUB)
// ---------------------------------------------------------------------------
async function viewChildProfile(childId) {
  try {
    const res = await fetch(`${API_BASE}/children/${childId}`, { headers: getAuthHeaders() });
    if (!res.ok) {
      showToast("Could not load child profile", "error");
      return;
    }
    const child = await res.json();
    activeProfileChild = child;
    activeProfileChildId = child.id;

    // Show view
    document.querySelectorAll(".app-view").forEach(v => v.classList.remove("active"));
    const profView = document.getElementById("viewChildProfile");
    if (profView) profView.classList.add("active");
    document.getElementById("pageTitle").textContent = `${child.name} — Profile`;

    // Header Demographics
    const el = id => document.getElementById(id);
    if (el("profChildName")) el("profChildName").textContent = child.name;
    if (el("profHealthId")) el("profHealthId").textContent = child.health_id || `CH${String(child.id).padStart(3, '0')}`;
    if (el("profAge")) el("profAge").textContent = child.age_months != null ? `${child.age_months} months` : "Not recorded";
    if (el("profGender")) el("profGender").textContent = child.gender || "Not recorded";
    if (el("profDob")) el("profDob").textContent = child.date_of_birth || "Not recorded";

    // Latest Assessment data
    const latest = child.latest_assessment;
    if (latest) {
      activeProfileLatestAssessmentId = latest.id;
      if (el("profLatestWeight")) el("profLatestWeight").textContent = `${latest.weight} kg`;
      if (el("profLatestHeight")) el("profLatestHeight").textContent = `${latest.height} cm`;
      if (el("profLatestMuac")) el("profLatestMuac").textContent = latest.muac != null ? `${latest.muac} cm` : "Not recorded";

      const pred = (latest.prediction && latest.prediction.prediction) ? latest.prediction.prediction : "Prediction unavailable";
      const risk = (latest.prediction && latest.prediction.risk_score != null) ? Math.round(latest.prediction.risk_score) : null;

      if (el("profLatestPrediction")) el("profLatestPrediction").textContent = pred;
      if (el("profLatestRisk")) el("profLatestRisk").textContent = risk != null ? `${risk} / 100` : "Not available";
      if (el("profStatusBadge")) {
        el("profStatusBadge").textContent = pred.toUpperCase();
        if (risk != null) {
          el("profStatusBadge").style.background = (risk >= 65) ? "#fee2e2" : ((risk >= 40) ? "#fef3c7" : "#dcfce7");
          el("profStatusBadge").style.color = (risk >= 65) ? "#991b1b" : ((risk >= 40) ? "#92400e" : "#166534");
        } else {
          el("profStatusBadge").style.background = "#f1f5f9";
          el("profStatusBadge").style.color = "#64748b";
        }
      }
    } else {
      activeProfileLatestAssessmentId = null;
      if (el("profLatestWeight")) el("profLatestWeight").textContent = "—";
      if (el("profLatestHeight")) el("profLatestHeight").textContent = "—";
      if (el("profLatestMuac")) el("profLatestMuac").textContent = "—";
      if (el("profLatestPrediction")) el("profLatestPrediction").textContent = "No screening yet";
      if (el("profLatestRisk")) el("profLatestRisk").textContent = "—";
      if (el("profStatusBadge")) { el("profStatusBadge").textContent = "NEW PATIENT"; el("profStatusBadge").style.background = "#e2e8f0"; el("profStatusBadge").style.color = "#475569"; }
    }

    // Load History Table for this child
    loadChildGrowthHistory(childId);

  } catch (err) {
    console.error("Error rendering child profile:", err);
  }
}

async function loadChildGrowthHistory(childId) {
  const tbody = document.getElementById("profHistoryTableBody");
  if (!tbody) return;

  try {
    const res = await fetch(`${API_BASE}/children/${childId}/growth`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const records = await res.json();

    if (records.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:18px;color:#64748b;">No past assessments recorded yet. Click "Start New Screening" to record the baseline.</td></tr>`;
      return;
    }

    tbody.innerHTML = "";
    records.slice().reverse().forEach((rec, idx) => {
      const pred = rec.prediction || "Not available";
      const risk = rec.risk_score != null ? Math.round(rec.risk_score) : null;

      let badgeClass = pred === "Normal" ? "normal" : (pred === "Not available" ? "neutral" : "normal");
      if (pred.includes("SAM") || pred.includes("Severe")) badgeClass = "severe";
      else if (pred.includes("Stunted")) badgeClass = "stunted";
      else if (pred.includes("Wasted")) badgeClass = "wasted";
      else if (pred.includes("Underweight") || pred.includes("Moderate")) badgeClass = "underweight";

      const targetAsmtId = rec.assessment_id || rec.id;
      const clickHandler = targetAsmtId ? `viewScreeningResult(${targetAsmtId}, ${childId})` : `viewScreeningResultByChildAndDate(${childId}, '${rec.date}')`;

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${rec.date}</td>
        <td>${rec.age_months} mo</td>
        <td>${rec.weight} kg</td>
        <td>${rec.height} cm</td>
        <td><strong style="color:#c0392b;">${rec.muac || '—'} cm</strong></td>
        <td><span class="badge ${badgeClass}">${pred}</span></td>
        <td><strong>${risk != null ? risk + '%' : '—'}</strong></td>
        <td>
          <button class="tbl-btn report" onclick="${clickHandler}">View Result</button>
        </td>
      `;
      tbody.appendChild(tr);
    });

  } catch (e) {
    console.error("Error loading growth history:", e);
  }
}

function startScreeningForActiveChild() {
  if (activeProfileChildId) {
    startScreeningForChild(activeProfileChildId);
  }
}

function viewLatestReportForActiveChild() {
  if (activeProfileLatestAssessmentId) {
    viewScreeningResult(activeProfileLatestAssessmentId, activeProfileChildId);
  } else {
    showToast("No screening recorded yet for this child.", "error");
  }
}

function scrollToProfileHistory() {
  const card = document.getElementById("profHistoryCard");
  if (card) card.scrollIntoView({ behavior: "smooth" });
}

// ---------------------------------------------------------------------------
// VIEW 4: NEW SCREENING (5-STEP GUIDED WIZARD)
// ---------------------------------------------------------------------------
function initNewScreeningWizard(preselectedChildId = null) {
  wizCurrentStep = 1;
  wizPhotoFile = null;
  wizWhoData = null;

  // Reset inputs
  const el = id => document.getElementById(id);
  if (el("wizPhotoPreview")) { el("wizPhotoPreview").src = ""; el("wizPhotoPreview").style.display = "none"; }
  if (el("wizPhotoPlaceholder")) el("wizPhotoPlaceholder").style.display = "block";
  if (el("wizPhotoFilename")) el("wizPhotoFilename").textContent = "";

  // Reset field validation states
  document.querySelectorAll(".field-error").forEach(e => e.classList.remove("visible"));
  document.querySelectorAll(".fg input, .fg select").forEach(e => e.classList.remove("has-error"));

  populateWizardChildrenDropdown(preselectedChildId);
  updateWizardStepUI(1);
}

function populateWizardChildrenDropdown(preselectedId = null) {
  const select = document.getElementById("wizChildSelect");
  if (!select) return;

  select.innerHTML = `<option value="">-- Choose child from cohort --</option>`;
  currentChildren.forEach(c => {
    const opt = document.createElement("option");
    opt.value = c.id;
    opt.textContent = `${c.name} (${c.health_id || 'CH' + c.id}) — ${c.age_months || 14} mo, ${c.gender || 'Male'}`;
    if (preselectedId && c.id === preselectedId) {
      opt.selected = true;
    }
    select.appendChild(opt);
  });

  if (preselectedId) {
    handleWizardChildChange(preselectedId);
  }
}

function startScreeningForChild(childId) {
  showPage("New Screening");
  initNewScreeningWizard(childId);
}

function handleWizardChildChange(childId) {
  if (!childId) return;
  const child = currentChildren.find(c => c.id == childId);
  if (!child) return;

  wizSelectedChildId = child.id;
  const el = id => document.getElementById(id);
  if (el("wizAge")) el("wizAge").value = child.age_months != null ? child.age_months : "";
  if (el("wizGender")) el("wizGender").value = child.gender || "Male";
  if (el("wizBirthWeight") && child.birth_weight) el("wizBirthWeight").value = child.birth_weight;

  // If child has previous assessment, auto-fill baseline
  if (child.latest_assessment) {
    if (el("wizHeight") && child.latest_assessment.height != null) el("wizHeight").value = child.latest_assessment.height;
    if (el("wizWeight") && child.latest_assessment.weight != null) el("wizWeight").value = child.latest_assessment.weight;
    if (el("wizMuac") && child.latest_assessment.muac != null) el("wizMuac").value = child.latest_assessment.muac;
    if (el("wizHeadCirc") && child.latest_assessment.head_circumference) {
      el("wizHeadCirc").value = child.latest_assessment.head_circumference;
    }
  }
}

function goToWizardStep(stepNum) {
  if (stepNum < 1 || stepNum > 5) return;
  wizCurrentStep = stepNum;
  updateWizardStepUI(stepNum);
}

function updateWizardStepUI(stepNum) {
  // Update progress nodes
  for (let i = 1; i <= 5; i++) {
    const node = document.getElementById(`wizNode${i}`);
    const stepBody = document.getElementById(`wizStep${i}`);

    if (node) {
      node.classList.remove("active", "completed");
      if (i < stepNum) node.classList.add("completed");
      else if (i === stepNum) node.classList.add("active");
    }

    if (stepBody) {
      stepBody.classList.remove("active");
      if (i === stepNum) stepBody.classList.add("active");
    }
  }

  // Progress Fill Line
  const fill = document.getElementById("wizardProgressFill");
  if (fill) fill.style.width = `${(stepNum - 1) * 25}%`;

  const label = document.getElementById("wizardStepLabel");
  if (label) label.textContent = `STEP ${stepNum} / 5`;
}

// Validation Step 1 -> 2
function validateAndGoToStep2() {
  const childSelect = document.getElementById("wizChildSelect");
  const ageInput = document.getElementById("wizAge");
  let valid = true;

  if (!childSelect.value) {
    document.getElementById("errWizChild").classList.add("visible");
    childSelect.classList.add("has-error");
    valid = false;
  } else {
    document.getElementById("errWizChild").classList.remove("visible");
    childSelect.classList.remove("has-error");
  }

  const age = parseFloat(ageInput.value);
  if (isNaN(age) || age < 0 || age > 60) {
    document.getElementById("errWizAge").classList.add("visible");
    ageInput.classList.add("has-error");
    valid = false;
  } else {
    document.getElementById("errWizAge").classList.remove("visible");
    ageInput.classList.remove("has-error");
  }

  if (valid) goToWizardStep(2);
}

// Validation Step 2 -> 3 (Client-side sanity bounds)
function validateAndGoToStep3() {
  const hInput = document.getElementById("wizHeight");
  const wInput = document.getElementById("wizWeight");
  const mInput = document.getElementById("wizMuac");
  let valid = true;

  const h = parseFloat(hInput.value);
  if (isNaN(h) || h < 30 || h > 140) {
    document.getElementById("errWizHeight").classList.add("visible");
    hInput.classList.add("has-error");
    valid = false;
  } else {
    document.getElementById("errWizHeight").classList.remove("visible");
    hInput.classList.remove("has-error");
  }

  const w = parseFloat(wInput.value);
  if (isNaN(w) || w <= 0 || w > 40) {
    document.getElementById("errWizWeight").classList.add("visible");
    wInput.classList.add("has-error");
    valid = false;
  } else {
    document.getElementById("errWizWeight").classList.remove("visible");
    wInput.classList.remove("has-error");
  }

  const m = parseFloat(mInput.value);
  if (isNaN(m) || m < 5.0 || m > 30.0) {
    document.getElementById("errWizMuac").classList.add("visible");
    mInput.classList.add("has-error");
    valid = false;
  } else {
    document.getElementById("errWizMuac").classList.remove("visible");
    mInput.classList.remove("has-error");
  }

  if (valid) goToWizardStep(3);
}

// Visual Assessment Step 3 Handlers
function handleWizardPhotoPreview(input) {
  if (input.files && input.files[0]) {
    wizPhotoFile = input.files[0];
    const reader = new FileReader();
    reader.onload = function (e) {
      const prev = document.getElementById("wizPhotoPreview");
      if (prev) {
        prev.src = e.target.result;
        prev.style.display = "block";
      }
      const ph = document.getElementById("wizPhotoPlaceholder");
      if (ph) ph.style.display = "none";
      const fn = document.getElementById("wizPhotoFilename");
      if (fn) fn.textContent = `Attached: ${wizPhotoFile.name}`;
    };
    reader.readAsDataURL(wizPhotoFile);
  }
}

async function validateAndGoToStep4() {
  goToWizardStep(4);
  await computeWizardWho();
}

// Step 4: Live WHO Growth Standards Calculation (Backend WHO LMS Engine)
async function computeWizardWho() {
  const age = parseFloat(document.getElementById("wizAge").value);
  const gender = document.getElementById("wizGender").value || "Male";
  const weight = parseFloat(document.getElementById("wizWeight").value);
  const height = parseFloat(document.getElementById("wizHeight").value);
  const muac = parseFloat(document.getElementById("wizMuac").value);

  const el = id => document.getElementById(id);
  if (isNaN(age) || isNaN(weight) || isNaN(height)) {
    if (el("wizWhoInterpretation")) el("wizWhoInterpretation").textContent = "Please enter valid age, weight, and height to compute WHO metrics.";
    return;
  }
  if (el("wizWhoInterpretation")) el("wizWhoInterpretation").textContent = "Calculating WHO LMS growth metrics...";

  try {
    const res = await fetch(`${API_BASE}/ai/calculate-who`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        age_months: age,
        gender: gender,
        weight: weight,
        height: height,
        muac: isNaN(muac) ? null : muac
      })
    });

    if (!res.ok) throw new Error("WHO calculation service error");
    wizWhoData = await res.json();

    if (el("wizWhoHaz")) el("wizWhoHaz").textContent = wizWhoData.haz != null ? `${wizWhoData.haz > 0 ? '+' : ''}${wizWhoData.haz.toFixed(2)} SD` : "Not assessed";
    if (el("wizWhoWaz")) el("wizWhoWaz").textContent = wizWhoData.waz != null ? `${wizWhoData.waz > 0 ? '+' : ''}${wizWhoData.waz.toFixed(2)} SD` : "Not assessed";
    if (wizWhoData.reference_standard === "IAP") {
      if (el("wizWhoWhz")) el("wizWhoWhz").textContent = wizWhoData.baz != null ? `${wizWhoData.baz > 0 ? '+' : ''}${wizWhoData.baz.toFixed(2)} SD (BMI Z)` : "Not applicable (5–18y)";
    } else {
      if (el("wizWhoWhz")) el("wizWhoWhz").textContent = wizWhoData.whz != null ? `${wizWhoData.whz > 0 ? '+' : ''}${wizWhoData.whz.toFixed(2)} SD` : "Not assessed";
    }
    if (el("wizWhoMuac")) el("wizWhoMuac").textContent = wizWhoData.muac != null ? `${wizWhoData.muac} cm` : (!isNaN(muac) ? `${muac} cm` : "Not recorded");

    if (el("wizWhoInterpretation")) {
      el("wizWhoInterpretation").textContent = wizWhoData.interpretation || "Calculation complete.";
      el("wizWhoInterpretation").style.color = (wizWhoData.status === "urgent") ? "#991b1b" : ((wizWhoData.status === "warning") ? "#b45309" : "#166534");
    }

  } catch (err) {
    console.error("Error calculating WHO Z-scores:", err);
    if (el("wizWhoHaz")) el("wizWhoHaz").textContent = "Not assessed";
    if (el("wizWhoWaz")) el("wizWhoWaz").textContent = "Not assessed";
    if (el("wizWhoWhz")) el("wizWhoWhz").textContent = "Not assessed";
    if (el("wizWhoMuac")) el("wizWhoMuac").textContent = !isNaN(muac) ? `${muac} cm` : "Not recorded";
    if (el("wizWhoInterpretation")) el("wizWhoInterpretation").textContent = "WHO LMS calculation unavailable.";
  }
}

// Step 5: Run AI Multimodal Screening
async function runWizardAiScreening() {
  goToWizardStep(5);

  const progressBar = document.getElementById("wizAnalysisProgressBar");
  const loadingText = document.getElementById("wizLoadingText");

  if (progressBar) progressBar.style.width = "25%";
  if (loadingText) loadingText.textContent = "Extracting anthropometric features and WHO LMS indicators...";

  setTimeout(() => {
    if (progressBar) progressBar.style.width = "60%";
    if (loadingText) loadingText.textContent = "Processing visual tensors through EfficientNet-B0...";
  }, 450);

  setTimeout(async () => {
    if (progressBar) progressBar.style.width = "85%";
    if (loadingText) loadingText.textContent = "Running Multimodal Fusion Ensemble and computing SHAP attributions...";

    try {
      const childId = parseInt(document.getElementById("wizChildSelect").value);
      const age = parseFloat(document.getElementById("wizAge").value);
      const weight = parseFloat(document.getElementById("wizWeight").value);
      const height = parseFloat(document.getElementById("wizHeight").value);
      const muac = parseFloat(document.getElementById("wizMuac").value);
      const headCirc = parseFloat(document.getElementById("wizHeadCirc").value) || null;
      const hasEdema = document.getElementById("wizBilateralEdema") ? document.getElementById("wizBilateralEdema").checked : false;

      // 1. Post Assessment
      const assessRes = await fetch(`${API_BASE}/assessments`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          child_id: childId,
          age_months: age,
          weight: weight,
          height: height,
          muac: muac,
          head_circumference: headCirc,
          has_bilateral_edema: hasEdema,
          notes: hasEdema ? "Clinical screening: Bilateral pitting edema present" : "Routine clinical multimodal screening"
        })
      });

      if (!assessRes.ok) {
        const errData = await assessRes.json();
        throw new Error(errData.detail || "Assessment submission error");
      }
      const newAssessment = await assessRes.json();

      // 2. Upload photo if attached
      if (wizPhotoFile) {
        try {
          const fd = new FormData();
          fd.append("child_id", childId);
          fd.append("assessment_id", newAssessment.id);
          fd.append("image_type", "front");
          fd.append("image", wizPhotoFile);

          await fetch(`${API_BASE}/photos/upload`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${localStorage.getItem("childnutri_token")}` },
            body: fd
          });
        } catch (photoErr) {
          console.warn("Photo upload warning:", photoErr);
        }
      }

      if (progressBar) progressBar.style.width = "100%";
      if (loadingText) loadingText.textContent = "Screening Complete! Generating Diagnostic Dossier...";

      const predResult = (newAssessment.prediction && newAssessment.prediction.prediction) ? newAssessment.prediction.prediction : 'Processed';
      showToast(`AI Assessment Complete! Classification: ${predResult}`);

      setTimeout(() => {
        viewScreeningResult(newAssessment.id, childId);
      }, 500);

    } catch (err) {
      console.error("Screening execution error:", err);
      showToast(`Error during AI screening: ${err.message}`, "error");
      goToWizardStep(4);
    }

  }, 1000);
}

// ---------------------------------------------------------------------------
// VIEW 5: SCREENING RESULT (THE CROWN JEWEL SCREEN)
// ---------------------------------------------------------------------------
async function viewScreeningResult(assessmentId, childId) {
  resActiveAssessmentId = assessmentId;
  resActiveChildId = childId;

  // Activate Result View
  document.querySelectorAll(".app-view").forEach(v => v.classList.remove("active"));
  const resView = document.getElementById("viewScreeningResult");
  if (resView) resView.classList.add("active");
  document.getElementById("pageTitle").textContent = "Clinical Screening Result";

  const el = id => document.getElementById(id);

  try {
    // 1. Fetch Assessment Details
    const assessRes = await fetch(`${API_BASE}/assessments/${assessmentId}`, { headers: getAuthHeaders() });
    if (!assessRes.ok) return;
    const assessment = await assessRes.json();

    const childObj = assessment.child || {};
    if (el("resChildName")) el("resChildName").textContent = childObj.name || assessment.child_name || `Child #${childId}`;
    if (el("resHealthId")) el("resHealthId").textContent = childObj.health_id || assessment.health_id || `CHN-${String(childId).padStart(3, '0')}`;
    if (el("resAge")) el("resAge").textContent = assessment.age_months != null ? assessment.age_months : "—";
    if (el("resNutriAge")) el("resNutriAge").textContent = assessment.age_months != null ? assessment.age_months : "—";
    if (el("resDate")) el("resDate").textContent = assessment.assessment_date;

    const predLabel = (assessment.prediction && assessment.prediction.prediction) ? assessment.prediction.prediction : "Prediction unavailable";
    const riskScore = (assessment.prediction && assessment.prediction.risk_score != null) ? Math.round(assessment.prediction.risk_score) : null;

    if (el("resDiagText")) {
      el("resDiagText").textContent = predLabel.toUpperCase();
      el("resDiagText").style.color = (riskScore != null && riskScore >= 65) ? "#b91c1c" : ((riskScore != null && riskScore >= 40) ? "#b45309" : "#15803d");
    }
    if (el("resRiskScore")) el("resRiskScore").textContent = riskScore != null ? `Composite Screening Risk Score: ${riskScore} / 100` : "Composite Screening Risk Score: Not available";

    // Immediate WHO LMS Display from assessment canonical payload
    const formatZ = val => (val != null && !isNaN(val)) ? `${val > 0 ? '+' : ''}${typeof val === 'number' ? val.toFixed(2) : val} SD` : "Not assessed";
    const initialWho = assessment.who || {};
    if (el("resHaz")) el("resHaz").textContent = formatZ(initialWho.haz !== undefined ? initialWho.haz : assessment.haz);
    if (el("resWaz")) el("resWaz").textContent = formatZ(initialWho.waz !== undefined ? initialWho.waz : assessment.waz);
    if (el("resWhz")) el("resWhz").textContent = formatZ(initialWho.whz !== undefined ? initialWho.whz : assessment.whz);
    if (el("resMuac")) el("resMuac").textContent = assessment.muac != null ? `${assessment.muac} cm` : "Not recorded";
    if (el("resBaz")) el("resBaz").textContent = formatZ(initialWho.baz !== undefined ? initialWho.baz : assessment.baz);

    // Populate Authoritative 17-Section Clinical Explanation Dossier
    const ce = assessment.clinical_explanation;
    if (ce) {
      // 01 Child Nutrition Summary
      if (ce.summary) {
        if (el("resSummaryFinding")) el("resSummaryFinding").textContent = ce.summary.main_finding || "Routine screening recorded.";
        if (el("resSummaryMeasurements")) el("resSummaryMeasurements").textContent = ce.summary.main_measurements || "Standard measurements within expected range.";
        if (el("resSummaryNextStep")) el("resSummaryNextStep").textContent = ce.summary.recommended_next_step || "Continue standard growth monitoring.";
        if (el("resSummaryMonitoring")) el("resSummaryMonitoring").textContent = ce.summary.monitoring_status || "Routine monthly monitoring.";
      }

      // 02 What Is Happening?
      if (ce.what_is_happening) {
        if (el("resWhatIsHappeningText")) el("resWhatIsHappeningText").textContent = ce.what_is_happening.primary_concern || "";
        if (el("resWhatIsHappeningState")) {
          const cls = ce.what_is_happening.growth_classification || "";
          const vel = ce.what_is_happening.velocity_state || "";
          el("resWhatIsHappeningState").innerHTML = `<strong>Growth Status:</strong> ${cls} &bull; <strong>Velocity State:</strong> ${vel}`;
        }
      }

      // 03 What Does This Result Mean?
      if (ce.what_result_means) {
        if (el("resWhatResultMeansText")) el("resWhatResultMeansText").textContent = ce.what_result_means.explanation || "";
        if (el("resWhatResultMeansImplication")) el("resWhatResultMeansImplication").innerHTML = `<strong>Clinical Context:</strong> ${ce.what_result_means.clinical_implication || ""}`;
      }

      // 04 Possible Contributing Factors
      if (ce.possible_contributing_factors && el("resFactorsList")) {
        const factors = ce.possible_contributing_factors.factors || [];
        if (factors.length === 0) {
          el("resFactorsList").innerHTML = `<div style="font-size:0.8125rem;color:var(--text-secondary);padding:8px 0;">No adverse contributing factors identified. Anthropometric growth is tracking appropriately.</div>`;
        } else {
          el("resFactorsList").innerHTML = factors.map(f => {
            const isHigh = f.priority === "High";
            const badgeBg = isHigh ? "#fee2e2" : "#fef3c7";
            const badgeColor = isHigh ? "#991b1b" : "#92400e";
            return `
              <div class="summary-box" style="padding:12px 16px;">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;">
                  <strong style="font-size:0.84rem;color:#0f172a;">${f.factor}</strong>
                  <span style="font-size:0.68rem;font-weight:700;padding:2px 8px;border-radius:99px;background:${badgeBg};color:${badgeColor};">${f.priority} Priority</span>
                </div>
                <div style="font-size:0.78rem;color:var(--text-secondary);line-height:1.45;">${f.details}</div>
              </div>
            `;
          }).join("");
        }
      }

      // 05 How Can Malnutrition Be Prevented?
      if (ce.how_can_malnutrition_be_prevented) {
        if (el("resPreventionAgeCategory")) el("resPreventionAgeCategory").textContent = ce.how_can_malnutrition_be_prevented.age_category || "Age-Specific Protocol";
        if (el("resPreventionPrinciples") && ce.how_can_malnutrition_be_prevented.principles) {
          el("resPreventionPrinciples").innerHTML = ce.how_can_malnutrition_be_prevented.principles.map(p => `
            <div class="action-step-item">
              <div class="step-num" style="background:#0284c7;">&bull;</div>
              <div class="step-content"><strong>${p.title}:</strong> ${p.description}</div>
            </div>
          `).join("");
        }
      }

      // 06 What Should Be Done Now?
      if (ce.what_should_be_done_now && el("resActionStepsList")) {
        const steps = ce.what_should_be_done_now.triaged_steps || [];
        el("resActionStepsList").innerHTML = steps.map((s, idx) => `
          <div class="action-step-item">
            <div class="step-num">${idx + 1}</div>
            <div class="step-content">${s}</div>
          </div>
        `).join("");
      }

      // 07 When Professional Assessment Is Important
      if (ce.when_professional_assessment_important && el("resRedFlagsList")) {
        const redFlags = ce.when_professional_assessment_important.urgent_red_flags || [];
        if (redFlags.length > 0) {
          el("resRedFlagsList").innerHTML = redFlags.map(rf => `<li>${rf}</li>`).join("");
        }
      }

      // 08 What Should Be Monitored?
      if (ce.what_should_be_monitored) {
        if (el("resMonitoringSchedule")) el("resMonitoringSchedule").textContent = ce.what_should_be_monitored.schedule || "Standard follow-up.";
        if (el("resMonitoringIndicators")) {
          const inds = ce.what_should_be_monitored.indicators_to_track || [];
          el("resMonitoringIndicators").textContent = inds.join(", ") || "Weight, Height, and MUAC.";
        }
        if (el("resMonitoringSingleVisitNotice")) {
          el("resMonitoringSingleVisitNotice").innerHTML = `<strong>Longitudinal Context:</strong> ${ce.what_should_be_monitored.longitudinal_status || "Growth velocity requires repeated measurements across consecutive visits."}`;
        }
      }

      // 12 WHO vs AI Consistency & Reconciliation
      if (ce.who_vs_ai) {
        if (el("resWhoVsAiStatus")) {
          el("resWhoVsAiStatus").textContent = ce.who_vs_ai.consistency_status || "Screening Evaluation";
          const isConc = (ce.who_vs_ai.consistency_status || "").includes("Concordant") || (ce.who_vs_ai.consistency_status || "").includes("Aligned");
          el("resWhoVsAiStatus").style.background = isConc ? "#dcfce7" : "#fef3c7";
          el("resWhoVsAiStatus").style.color = isConc ? "#15803d" : "#92400e";
          el("resWhoVsAiStatus").style.borderColor = isConc ? "#bbf7d0" : "#fde68a";
        }
        if (el("resWhoVsAiReconciliation")) el("resWhoVsAiReconciliation").textContent = ce.who_vs_ai.reconciliation_statement || "";
        if (el("resWhoVsAiWhoView")) el("resWhoVsAiWhoView").textContent = ce.who_vs_ai.who_perspective || "";
        if (el("resWhoVsAiAiView")) el("resWhoVsAiAiView").textContent = ce.who_vs_ai.ai_perspective || "";
      }

      // 17 Limitations & Safety Notice
      if (ce.important_limitations && el("resLimitationsList")) {
        el("resLimitationsList").innerHTML = ce.important_limitations.map(lim => `<li>${lim}</li>`).join("");
      }
      if (ce.clinical_safety_notice && el("resSafetyNotice")) {
        el("resSafetyNotice").innerHTML = `<strong>Clinical Safety Notice:</strong> ${ce.clinical_safety_notice}`;
      }
    }

    // Dynamic Age-Aware Nutrition Support & Meal Timeline (Replacing generic hardcoded text)
    const mealContainer = el("resMealTimeline");
    if (mealContainer) {
      const ageMo = assessment.age_months != null ? Number(assessment.age_months) : 12;
      if (ageMo < 6) {
        mealContainer.innerHTML = `
          <div class="meal-item">
            <div class="meal-name">Exclusive Breastfeeding Protocol (&lt; 6 Months of Age)</div>
            <div class="meal-desc">Infant is under 6 months. WHO guidelines strictly advise exclusive breastfeeding on demand (8–12 times per 24 hours). DO NOT introduce solid foods, animal milk, teas, water, or commercial cereals unless specifically prescribed by a pediatrician.</div>
          </div>
          <div class="meal-item">
            <div class="meal-name">Lactation &amp; Growth Support</div>
            <div class="meal-desc">Verify effective attachment, latching, and swallowing. Ensure mother receives adequate hydration, maternal nutrition, and rest. If poor weight gain is noted, seek clinical lactation assessment.</div>
          </div>
        `;
      } else if (ageMo < 24) {
        mealContainer.innerHTML = `
          <div class="meal-item">
            <div class="meal-name">First Meal / Breakfast (6–23 Months)</div>
            <div class="meal-desc">Thick, nutrient-dense cereal or porridge made from locally available grains (rice, oats, ragi, wheat) enriched with boiled milk, mashed pulses, or ground seeds. Continued breastfeeding on demand.</div>
          </div>
          <div class="meal-item">
            <div class="meal-name">Mid-Day Meal &amp; Dietary Diversity</div>
            <div class="meal-desc">Cooked family staple (soft rice or mashed roti) with well-cooked split lentils/dal and pureed or finely chopped seasonal vegetables (carrots, dark green leaves) with a small amount of oil or ghee to support fat-soluble vitamin absorption.</div>
          </div>
          <div class="meal-item">
            <div class="meal-name">Nutritious Afternoon Snack</div>
            <div class="meal-desc">Fresh mashed seasonal fruit (banana, mango, papaya) or boiled egg yolk/mashed beans. Ensure safe drinking water and strict handwashing before preparation.</div>
          </div>
          <div class="meal-item">
            <div class="meal-name">Evening Family Meal</div>
            <div class="meal-desc">Soft, easily digestible portion of family foods meeting at least 5 of the 8 WHO food groups daily. Encourage responsive feeding patiently without force. Continue night breastfeeds.</div>
          </div>
        `;
      } else {
        mealContainer.innerHTML = `
          <div class="meal-item">
            <div class="meal-name">Morning Breakfast (24–59 Months)</div>
            <div class="meal-desc">Energetic start with whole grains (paratha, idli, oats, or bread) paired with milk, eggs, or curd and fresh seasonal fruits for sustained vitality.</div>
          </div>
          <div class="meal-item">
            <div class="meal-name">Wholesome Family Lunch</div>
            <div class="meal-desc">Diverse meal including grain staples, protein-rich pulses, beans, poultry, or fish, accompanied by freshly cooked vegetables.</div>
          </div>
          <div class="meal-item">
            <div class="meal-name">Evening Snack &amp; Balanced Dinner</div>
            <div class="meal-desc">Nutritious family dinner rich in micronutrients and clean water hydration. Discourage sugary packaged drinks and snacks that displace essential nutrients.</div>
          </div>
        `;
      }
    }

    // 2. Fetch Deep Explainability (SHAP + Grad-CAM + WHO Z-scores + Triage)
    const explainRes = await fetch(`${API_BASE}/ai/explain/${assessmentId}`, { headers: getAuthHeaders() });
    if (explainRes.ok) {
      const exp = await explainRes.json();

      // Update WHO Indicators if enhanced
      const who = exp.who_zscores || initialWho;
      if (el("resHaz")) el("resHaz").textContent = formatZ(who.haz !== undefined ? who.haz : initialWho.haz);
      if (el("resWaz")) el("resWaz").textContent = formatZ(who.waz !== undefined ? who.waz : initialWho.waz);
      if (el("resWhz")) el("resWhz").textContent = formatZ(who.whz !== undefined ? who.whz : initialWho.whz);
      if (el("resBaz")) el("resBaz").textContent = formatZ(who.baz !== undefined ? who.baz : initialWho.baz);

      // Safety / Triage
      const triage = exp.clinical_triage || {};
      if (el("resTriageBadge")) {
        el("resTriageBadge").textContent = triage.level || "MONITOR (YELLOW)";
        el("resTriageBadge").style.background = triage.color || "#f59e0b";
      }
      if (el("resTriageAction")) el("resTriageAction").textContent = triage.action || "Follow-up recommended.";
      if (el("resTriageBox")) {
        el("resTriageBox").style.borderLeftColor = triage.color || "#f59e0b";
      }

      // SHAP Feature Contribution Bars
      const shapContainer = el("resShapList");
      if (shapContainer && exp.explainability && exp.explainability.top_contributing_features) {
        shapContainer.innerHTML = "";
        exp.explainability.top_contributing_features.forEach(f => {
          const isRisk = f.impact && f.impact.includes("Risk");
          const barColor = isRisk ? "#ef4444" : "#10b981";
          const relPct = f.relative_percentage || 40;

          let badgeBg = "#fee2e2", badgeColor = "#991b1b", badgeBorder = "#fecaca";
          if (f.contribution_level.includes("Medium") || f.contribution_level.includes("Moderate")) {
            badgeBg = "#fef3c7"; badgeColor = "#92400e"; badgeBorder = "#fde68a";
          } else if (f.contribution_level.includes("Lower")) {
            badgeBg = "#f1f5f9"; badgeColor = "#334155"; badgeBorder = "#e2e8f0";
          }

          const row = document.createElement("div");
          row.style.display = "flex";
          row.style.flexDirection = "column";
          row.style.gap = "3px";
          row.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:center;font-size:0.75rem;">
              <div style="display:flex;align-items:center;gap:6px;">
                <span style="font-weight:700;color:#0f172a;">${f.display_name}</span>
                <span style="color:#6366f1;font-weight:900;">&rarr;</span>
                <span style="font-size:0.68rem;font-weight:700;padding:1px 6px;border-radius:99px;background:${badgeBg};color:${badgeColor};border:1px solid ${badgeBorder};">${f.contribution_level}</span>
              </div>
              <div style="color:#64748b;font-size:0.72rem;">${f.measured_value}</div>
            </div>
            <div style="height:6px;background:#e2e8f0;border-radius:99px;overflow:hidden;">
              <div style="height:100%;width:${Math.min(100, Math.max(10, relPct))}%;background:${barColor};border-radius:99px;"></div>
            </div>
          `;
          shapContainer.appendChild(row);
        });
      }

      // Grad-CAM 3-Stage Images (Original -> Heatmap -> Overlay)
      if (exp.explainability) {
        if (exp.explainability.shap_decision_summary && el("resShapSummary")) {
          el("resShapSummary").textContent = exp.explainability.shap_decision_summary;
          el("resShapSummary").style.display = "block";
        }
        const focusRegions = exp.explainability.gradcam_anatomical_focus || exp.explainability.focus_regions;
        if (focusRegions && el("resGradcamFocus")) {
          const focusText = Array.isArray(focusRegions) ? (focusRegions.length > 0 ? focusRegions.join("; ") : "No specific anatomical hotspot detected.") : focusRegions;
          el("resGradcamFocus").textContent = focusText;
        }
        if (exp.explainability.original_image_base64) {
          if (el("resGradcamOrig")) {
            el("resGradcamOrig").src = `data:image/jpeg;base64,${exp.explainability.original_image_base64}`;
            el("resGradcamOrig").style.display = "block";
          }
          if (el("resGradcamOrigPlaceholder")) el("resGradcamOrigPlaceholder").style.display = "none";
        }
        const pureHeatmap = exp.explainability.pure_heatmap_base64 || exp.explainability.gradcam_heatmap_base64;
        if (pureHeatmap) {
          if (el("resGradcamHeatmap")) {
            el("resGradcamHeatmap").src = `data:image/jpeg;base64,${pureHeatmap}`;
            el("resGradcamHeatmap").style.display = "block";
          }
          if (el("resGradcamHeatmapPlaceholder")) el("resGradcamHeatmapPlaceholder").style.display = "none";
        }
        if (exp.explainability.gradcam_overlay_base64) {
          if (el("resGradcamOverlay")) {
            el("resGradcamOverlay").src = `data:image/jpeg;base64,${exp.explainability.gradcam_overlay_base64}`;
            el("resGradcamOverlay").style.display = "block";
          }
          if (el("resGradcamOverlayPlaceholder")) el("resGradcamOverlayPlaceholder").style.display = "none";
        }
      }
    }

    // Section 11B: Image-Assisted Anthropometric Estimation (Neonatal CV Regression)
    const neonatalSec = el("resNeonatalSection");
    const predAnthro = assessment.predicted_anthropometry || (assessment.vision_screening && assessment.vision_screening.predicted_anthropometry) || {};
    const hasPredAnthro = predAnthro && (predAnthro.available === true || predAnthro.predicted_weight_g != null);

    if (neonatalSec) {
      if (hasPredAnthro) {
        neonatalSec.style.display = "block";
        const formatCm = val => val != null ? `${Number(val).toFixed(1)} cm` : "—";
        const formatG = val => val != null ? `${Math.round(val)} g (${(val/1000).toFixed(2)} kg)` : "—";

        if (el("resNeonatalWeight")) el("resNeonatalWeight").textContent = formatG(predAnthro.predicted_weight_g);
        if (el("resNeonatalLength")) el("resNeonatalLength").textContent = formatCm(predAnthro.predicted_body_length_cm);
        if (el("resNeonatalHeadCc")) el("resNeonatalHeadCc").textContent = formatCm(predAnthro.predicted_head_circumference_cm);
        if (el("resNeonatalChest")) el("resNeonatalChest").textContent = formatCm(predAnthro.predicted_chest_girth_cm);
        if (el("resNeonatalArm")) el("resNeonatalArm").textContent = formatCm(predAnthro.predicted_arm_length_cm);
        if (el("resNeonatalLeg")) el("resNeonatalLeg").textContent = formatCm(predAnthro.predicted_leg_length_cm);

        const bwCat = predAnthro.predicted_birth_weight_category || "Standard";
        if (el("resNeonatalBwCategory")) el("resNeonatalBwCategory").textContent = bwCat;
        if (el("resNeonatalTriageBadge")) {
          el("resNeonatalTriageBadge").textContent = `Birth Weight: ${bwCat}`;
          el("resNeonatalTriageBadge").style.background = bwCat === "NORMAL" ? "#dcfce7" : "#fee2e2";
          el("resNeonatalTriageBadge").style.color = bwCat === "NORMAL" ? "#15803d" : "#991b1b";
        }

        // Compare with physical measured values
        const measured = assessment.measured_anthropometry || assessment.measurements || {};
        if (el("resNeonatalWeightCompare")) {
          const mWeight = measured.weight_kg != null ? measured.weight_kg : assessment.weight;
          el("resNeonatalWeightCompare").textContent = mWeight ? `Physical Measured: ${Number(mWeight).toFixed(2)} kg (${Math.round(mWeight*1000)} g)` : "Physical Measured: Not recorded";
        }
        if (el("resNeonatalLengthCompare")) {
          const mLen = measured.height_cm != null ? measured.height_cm : assessment.height;
          el("resNeonatalLengthCompare").textContent = mLen ? `Physical Measured: ${Number(mLen).toFixed(1)} cm` : "Physical Measured: Not recorded";
        }
        if (el("resNeonatalHeadCcCompare")) {
          const mHead = measured.head_circumference_cm != null ? measured.head_circumference_cm : assessment.head_circumference;
          el("resNeonatalHeadCcCompare").textContent = mHead ? `Physical Measured: ${Number(mHead).toFixed(1)} cm` : "Physical Measured: Optional";
        }
      } else {
        neonatalSec.style.display = "none";
      }
    }

    // 3. Fetch Nutrition Support Plan
    const nutriRes = await fetch(`${API_BASE}/ai/nutrition-plan/${childId}`, { headers: getAuthHeaders() });
    if (nutriRes.ok) {
      const nutri = await nutriRes.json();
      if (el("resNutriCalories")) el("resNutriCalories").textContent = nutri.caloric_target ? Number(nutri.caloric_target).toLocaleString() : "Not calculated";
      if (el("resNutriRutf")) el("resNutriRutf").textContent = (nutri.rutf_sachets != null && nutri.rutf_sachets > 0) ? nutri.rutf_sachets : "0.0";
    }

    // 4. Fetch Future Risk (30 / 60 / 90 Days)
    const riskRes = await fetch(`${API_BASE}/ai/future-risk/${childId}`, { headers: getAuthHeaders() });
    if (riskRes.ok) {
      const fRisk = await riskRes.json();
      if (fRisk.has_sufficient_history === false || fRisk.available === false) {
        if (el("resRiskCur")) el("resRiskCur").textContent = riskScore != null ? `${riskScore}%` : "—";
        if (el("resRisk30")) el("resRisk30").textContent = "—";
        if (el("resRisk60")) el("resRisk60").textContent = "—";
        if (el("resRisk90")) el("resRisk90").textContent = "—";
        if (el("resRiskVelocityBadge")) el("resRiskVelocityBadge").textContent = "Insufficient History";
        renderRiskTrajectorySvg([riskScore || 0]);
      } else {
        const curR = Math.round(fRisk.current_risk_score ?? (riskScore || 0));
        const r30 = fRisk.risk_30d != null ? Math.round(fRisk.risk_30d) : null;
        const r60 = fRisk.risk_60d != null ? Math.round(fRisk.risk_60d) : null;
        const r90 = fRisk.risk_90d != null ? Math.round(fRisk.risk_90d) : null;
        
        if (el("resRiskCur")) el("resRiskCur").textContent = `${curR}%`;
        if (el("resRisk30")) el("resRisk30").textContent = r30 != null ? `${r30}%` : "—";
        if (el("resRisk60")) el("resRisk60").textContent = r60 != null ? `${r60}%` : "—";
        if (el("resRisk90")) el("resRisk90").textContent = r90 != null ? `${r90}%` : "—";

        if (el("resRiskVelocityBadge") && fRisk.velocity_trend) {
          el("resRiskVelocityBadge").textContent = `${fRisk.velocity_trend} Trajectory`;
        }
        renderRiskTrajectorySvg([curR, r30 || curR, r60 || curR, r90 || curR]);
      }
    } else {
      if (el("resRiskCur")) el("resRiskCur").textContent = riskScore != null ? `${riskScore}%` : "—";
      if (el("resRisk30")) el("resRisk30").textContent = "—";
      if (el("resRisk60")) el("resRisk60").textContent = "—";
      if (el("resRisk90")) el("resRisk90").textContent = "—";
      if (el("resRiskVelocityBadge")) el("resRiskVelocityBadge").textContent = "Insufficient History";
      renderRiskTrajectorySvg([riskScore || 0]);
    }

    // 5. Growth Trend and Early Warning Check
    const growthRes = await fetch(`${API_BASE}/children/${childId}/growth`, { headers: getAuthHeaders() });
    if (growthRes.ok) {
      const pts = await growthRes.json();
      const tbody = el("resGrowthHistoryTbody");
      if (tbody) {
        tbody.innerHTML = "";
        pts.slice().reverse().forEach(p => {
          const pred = p.prediction || 'Not available';
          let badgeClass = "neutral";
          if (pred.includes("SAM") || pred.includes("Severe")) badgeClass = "severe";
          else if (pred.includes("Stunted")) badgeClass = "stunted";
          else if (pred.includes("Wasted")) badgeClass = "wasted";
          else if (pred.includes("Underweight") || pred.includes("Moderate")) badgeClass = "underweight";
          else if (pred.includes("Normal")) badgeClass = "normal";

          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${p.date}</td>
            <td>${p.weight} kg</td>
            <td>${p.height} cm</td>
            <td>${p.muac ? p.muac + ' cm' : '—'}</td>
            <td><span class="badge ${badgeClass}">${pred}</span></td>
            <td>${p.risk_score !== null && p.risk_score !== undefined ? `<strong>${Math.round(p.risk_score)}%</strong>` : '—'}</td>
          `;
          tbody.appendChild(tr);
        });
      }

      // Check velocity trend
      if (pts.length >= 2) {
        const last = pts[pts.length - 1];
        const prev = pts[pts.length - 2];
        const diffW = (last.weight - prev.weight).toFixed(2);

        if (el("resWeightTrendText")) {
          el("resWeightTrendText").textContent = (diffW >= 0) ? `+${diffW} kg (Gaining)` : `${diffW} kg (Loss)`;
          el("resWeightTrendText").style.color = (diffW >= 0) ? "#15803d" : "#b91c1c";
        }
        let diffM = null;
        if (last.muac != null && prev.muac != null) {
          diffM = (last.muac - prev.muac).toFixed(1);
          if (el("resMuacTrendText")) {
            el("resMuacTrendText").textContent = (diffM >= 0) ? `+${diffM} cm (Stable)` : `${diffM} cm (Decline)`;
            el("resMuacTrendText").style.color = (diffM >= 0) ? "#15803d" : "#b91c1c";
          }
        } else {
          if (el("resMuacTrendText")) {
            el("resMuacTrendText").textContent = "MUAC history incomplete";
            el("resMuacTrendText").style.color = "#64748b";
          }
        }

        // Show early warning if negative trajectory
        if (el("resEarlyWarningBox")) {
          const hasNegMuac = diffM !== null && parseFloat(diffM) < 0;
          el("resEarlyWarningBox").style.display = (diffW < 0 || hasNegMuac || (riskScore !== null && riskScore >= 60)) ? "block" : "none";
        }
      } else {
        if (el("resWeightTrendText")) el("resWeightTrendText").textContent = "Baseline recorded";
        if (el("resMuacTrendText")) el("resMuacTrendText").textContent = "Baseline recorded";
        if (el("resEarlyWarningBox")) el("resEarlyWarningBox").style.display = (riskScore !== null && riskScore >= 65) ? "block" : "none";
      }
    }

  } catch (err) {
    console.error("Error loading screening result:", err);
  }
}

async function viewScreeningResultByChildAndDate(childId, assessmentDate) {
  try {
    const res = await fetch(`${API_BASE}/assessments/child/${childId}`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const list = await res.json();
    const match = list.find(a => a.assessment_date === assessmentDate) || list[list.length - 1];
    if (match) {
      viewScreeningResult(match.id, childId);
    }
  } catch (e) {
    console.error("Error matching assessment:", e);
  }
}

// ---------------------------------------------------------------------------
// VIEW 6: ASSESSMENT HISTORY
// ---------------------------------------------------------------------------
async function loadFullHistory() {
  const tbody = document.getElementById("historyTableBody");
  if (!tbody) return;

  try {
    const res = await fetch(`${API_BASE}/assessments/recent?limit=50`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const records = await res.json();

    if (records.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;padding:24px;color:#64748b;">No assessment records found.</td></tr>`;
      return;
    }

    tbody.innerHTML = "";
    records.forEach(a => {
      const pred = (a.prediction && a.prediction.prediction) ? a.prediction.prediction : "Prediction unavailable";
      const risk = (a.prediction && a.prediction.risk_score !== null && a.prediction.risk_score !== undefined) ? Math.round(a.prediction.risk_score) : null;

      let badgeClass = "neutral";
      if (pred.includes("SAM") || pred.includes("Severe")) badgeClass = "severe";
      else if (pred.includes("Stunted")) badgeClass = "stunted";
      else if (pred.includes("Wasted")) badgeClass = "wasted";
      else if (pred.includes("Underweight") || pred.includes("Moderate")) badgeClass = "underweight";
      else if (pred.includes("Normal")) badgeClass = "normal";

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>#${a.id}</td>
        <td><strong>${a.child_name || 'Child #' + a.child_id}</strong></td>
        <td>${a.age_months} mo</td>
        <td>${a.weight}kg / ${a.height}cm</td>
        <td>${a.muac ? a.muac + ' cm' : '—'}</td>
        <td><span class="badge ${badgeClass}">${pred}</span></td>
        <td>${risk !== null ? `<strong>${risk}%</strong>` : '—'}</td>
        <td class="td-muted">${a.assessment_date}</td>
        <td>
          <button class="tbl-btn report" onclick="viewScreeningResult(${a.id}, ${a.child_id})">View Result</button>
        </td>
      `;
      tbody.appendChild(tr);
    });

  } catch (e) {
    console.error("Error loading full history:", e);
  }
}

// ---------------------------------------------------------------------------
// VIEW 7: REPORTS DIRECTORY
// ---------------------------------------------------------------------------
async function loadReportsDirectory() {
  const tbody = document.getElementById("reportsTableBody");
  if (!tbody) return;

  try {
    const res = await fetch(`${API_BASE}/assessments/recent?limit=30`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const records = await res.json();

    if (records.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:24px;color:#64748b;">No generated reports found.</td></tr>`;
      return;
    }

    tbody.innerHTML = "";
    records.forEach(a => {
      const pred = (a.prediction && a.prediction.prediction) ? a.prediction.prediction : "Prediction unavailable";
      const risk = (a.prediction && a.prediction.risk_score !== null && a.prediction.risk_score !== undefined) ? Math.round(a.prediction.risk_score) : null;

      let badgeClass = "neutral";
      if (pred.includes("SAM") || pred.includes("Severe")) badgeClass = "severe";
      else if (pred.includes("Stunted")) badgeClass = "stunted";
      else if (pred.includes("Wasted")) badgeClass = "wasted";
      else if (pred.includes("Underweight") || pred.includes("Moderate")) badgeClass = "underweight";
      else if (pred.includes("Normal")) badgeClass = "normal";

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong style="color:#1a7f5a;">REP-2026-${String(a.id).padStart(4, '0')}</strong></td>
        <td>${a.child_name || 'Child #' + a.child_id}</td>
        <td class="td-muted">${a.assessment_date}</td>
        <td><span class="badge ${badgeClass}">${pred}</span></td>
        <td>${risk !== null ? `${risk}%` : '—'}</td>
        <td>
          <button class="tbl-btn report" onclick="downloadAssessmentPDF(${a.id}, '${(a.child_name || 'Child').replace(/'/g, "\\'")}', '${a.assessment_date}')">
            📥 Download PDF
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });

  } catch (e) {
    console.error("Error loading reports:", e);
  }
}

// ---------------------------------------------------------------------------
// VIEW 8: APPOINTMENTS
// ---------------------------------------------------------------------------
async function loadAppointments() {
  const tbody = document.getElementById("appointmentsTableBody");
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:32px;color:var(--text-muted);">Loading appointments...</td></tr>`;

  try {
    if (!currentChildren || currentChildren.length === 0) {
      try {
        const cRes = await fetch(`${API_BASE}/children`, { headers: getAuthHeaders() });
        if (cRes.ok) currentChildren = await cRes.json();
      } catch (ce) {
        console.warn("Could not pre-fetch children for appointments:", ce);
      }
    }

    const res = await fetch(`${API_BASE}/appointments`, { headers: getAuthHeaders() });
    if (!res.ok) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:32px;color:var(--text-muted);">Unable to load appointments.</td></tr>`;
      return;
    }
    const appointments = await res.json();
    if (!appointments || appointments.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:32px;color:var(--text-muted);">No scheduled appointments found.</td></tr>`;
      return;
    }

    tbody.innerHTML = "";
    appointments.forEach(a => {
      const child = (currentChildren || []).find(c => c.id === a.child_id);
      const childName = child ? child.name : `Child #${a.child_id}`;
      let ageText = "—";
      if (child && child.date_of_birth) {
        const diffMonths = Math.max(0, Math.round((new Date() - new Date(child.date_of_birth)) / (1000 * 60 * 60 * 24 * 30.4375)));
        ageText = `${diffMonths} months`;
      }

      const purposeLower = (a.purpose || "").toLowerCase();
      let badgeClass = "low";
      let priorityText = "ROUTINE";
      if (purposeLower.includes("emergency") || purposeLower.includes("sam") || purposeLower.includes("urgent")) {
        badgeClass = "high";
        priorityText = "URGENT";
      } else if (purposeLower.includes("mam") || purposeLower.includes("stunting") || purposeLower.includes("review") || purposeLower.includes("follow-up")) {
        badgeClass = "medium";
        priorityText = "MEDIUM";
      }

      const timeStr = a.appointment_time ? `, ${a.appointment_time}` : "";
      const dateDisplay = `${a.appointment_date}${timeStr}`;

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${childName}</strong></td>
        <td>${ageText}</td>
        <td>${dateDisplay}</td>
        <td>${a.purpose || 'Follow-Up Assessment'}</td>
        <td><span class="alert-badge ${badgeClass}">${priorityText}</span></td>
        <td><button class="tbl-btn view" onclick="showToast('Appointment #${a.id} status: ${a.status || 'upcoming'}')">Details</button></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (e) {
    console.error("Error loading appointments:", e);
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:32px;color:var(--text-muted);">Error loading appointments.</td></tr>`;
  }
}

// ---------------------------------------------------------------------------
function openInteractiveStatus() {
  if (resActiveAssessmentId) {
    window.location.href = `screening_status.html?assessment_id=${resActiveAssessmentId}`;
  } else if (resActiveChildId) {
    window.location.href = `screening_status.html?child_id=${resActiveChildId}`;
  } else {
    window.location.href = `screening_status.html`;
  }
}

async function downloadScreeningResultPDF() {
  if (!resActiveAssessmentId) {
    showToast("No active screening to export", "error");
    return;
  }
  const childName = document.getElementById("resChildName") ? document.getElementById("resChildName").textContent : "Child";
  const date = document.getElementById("resDate") ? document.getElementById("resDate").textContent : "Date";
  await downloadAssessmentPDF(resActiveAssessmentId, childName, date);
}

async function downloadAssessmentPDF(assessmentId, childName, date) {
  showToast("Generating official Clinical Health Report PDF...");

  try {
    const res = await fetch(`${API_BASE}/assessments/${assessmentId}/pdf`, {
      headers: { "Authorization": `Bearer ${localStorage.getItem("childnutri_token")}` }
    });

    if (!res.ok) {
      throw new Error(`Server returned HTTP ${res.status}`);
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const cleanName = (childName || "Child").replace(/\s+/g, "_");
    a.download = `ChildNutri_Report_${cleanName}_${date || 'Assessment'}.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);

    showToast("✓ Health Report downloaded successfully!");

  } catch (err) {
    console.error("PDF download failed:", err);
    showToast("Could not download PDF from server.", "error");
  }
}

function downloadDoctorReportPDF() {
  downloadScreeningResultPDF();
}

function printDoctorReport() {
  window.print();
}

// ---------------------------------------------------------------------------
// ADD CHILD MODAL
// ---------------------------------------------------------------------------
function openAddChildModal() {
  const m = document.getElementById("addChildModal");
  if (m) m.classList.add("open");
  document.body.style.overflow = "hidden";
}

function closeAddChildModal() {
  const m = document.getElementById("addChildModal");
  if (m) m.classList.remove("open");
  document.body.style.overflow = "";
}

function handleAddChildOverlay(e) {
  if (e.target === document.getElementById("addChildModal")) closeAddChildModal();
}

async function submitNewChild(e) {
  e.preventDefault();
  const btn = document.getElementById("btnSaveChild");
  if (btn) btn.textContent = "Saving Profile...";

  const name = document.getElementById("newChildName").value.trim();
  const dob = document.getElementById("newChildDob").value;
  const gender = document.getElementById("newChildGender").value;
  const bWeight = parseFloat(document.getElementById("newChildBirthWeight").value) || null;
  const bLength = parseFloat(document.getElementById("newChildBirthLength").value) || null;

  try {
    const res = await fetch(`${API_BASE}/children`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        name: name,
        date_of_birth: dob,
        gender: gender,
        birth_weight: bWeight,
        birth_length: bLength
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to register child");
    }

    const created = await res.json();
    closeAddChildModal();
    if (btn) btn.textContent = "Create Child Profile";

    showToast(`✓ Registered child: ${created.name}`);
    await loadInitialChildren();
    viewChildProfile(created.id);

  } catch (err) {
    console.error("Child registration error:", err);
    if (btn) btn.textContent = "Create Child Profile";
    showToast(err.message || "Failed to create child", "error");
  }
}

// ---------------------------------------------------------------------------
// Global Search & Helpers
// ---------------------------------------------------------------------------
function handleGlobalSearch(query) {
  if (!query) return;
  showPage("Children");
  filterChildrenTable(query);
}

function refreshDashboardData() {
  loadDashboardStats();
  loadRecentAssessments();
  loadInitialChildren();
  showToast("Dashboard data refreshed.");
}

function showToast(msg, type = "success") {
  const t = document.getElementById("toast");
  const tm = document.getElementById("toastMsg");
  if (!t || !tm) return;

  tm.textContent = msg;
  t.style.background = (type === "error") ? "#dc2626" : "#1a7f5a";
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 3500);
}

function confirmLogout() {
  if (confirm("Are you sure you want to log out of ChildNutri AI?")) {
    localStorage.removeItem("childnutri_token");
    localStorage.removeItem("childnutri_user");
    sessionStorage.clear();
    window.location.href = "index.html";
  }
}

function openSidebar() {
  const sb = document.getElementById("sidebar");
  const sbo = document.getElementById("sidebarOverlay");
  if (sb) sb.classList.add("open");
  if (sbo) sbo.classList.add("open");
}

function closeSidebar() {
  const sb = document.getElementById("sidebar");
  const sbo = document.getElementById("sidebarOverlay");
  if (sb) sb.classList.remove("open");
  if (sbo) sbo.classList.remove("open");
}

function closeDoctorReportModal() {
  const m = document.getElementById("medicalReportModal");
  if (m) m.classList.remove("open");
}

function handleReportOverlay(e) {
  if (e.target === document.getElementById("medicalReportModal")) closeDoctorReportModal();
}

document.addEventListener("keydown", function(e) {
  if (e.key === "Escape") {
    closeAddChildModal();
    closeDoctorReportModal();
  }
});

// ---------------------------------------------------------------------------
// Cohort Donut Chart & Visual Trajectory Helpers
// ---------------------------------------------------------------------------
function renderCohortDonut(assessments) {
  let normal = 0, mam = 0, sam = 0;
  assessments.forEach(a => {
    if (!a.prediction || !a.prediction.prediction) return;
    const p = a.prediction.prediction;
    if (p.includes("SAM") || p.includes("Severe")) sam++;
    else if (p.includes("Underweight") || p.includes("Wasted") || p.includes("Moderate") || p.includes("Stunted")) mam++;
    else if (p.includes("Normal")) normal++;
  });
  const total = normal + mam + sam || 1;

  const el = id => document.getElementById(id);
  if (el("donutTotalCount")) el("donutTotalCount").textContent = assessments.length;
  if (el("donutNormalCount")) el("donutNormalCount").textContent = `${normal} (${Math.round((normal/total)*100)}%)`;
  if (el("donutMamCount")) el("donutMamCount").textContent = `${mam} (${Math.round((mam/total)*100)}%)`;
  if (el("donutSamCount")) el("donutSamCount").textContent = `${sam} (${Math.round((sam/total)*100)}%)`;

  const normalPct = (normal / total) * 100;
  const mamPct = (mam / total) * 100;
  const samPct = (sam / total) * 100;

  const sNorm = el("donutSegNormal");
  const sMam = el("donutSegMAM");
  const sSam = el("donutSegSAM");

  if (sNorm) sNorm.setAttribute("stroke-dasharray", `${normalPct} ${100 - normalPct}`);
  if (sMam) {
    sMam.setAttribute("stroke-dasharray", `${mamPct} ${100 - mamPct}`);
    sMam.setAttribute("stroke-dashoffset", `${-normalPct}`);
  }
  if (sSam) {
    sSam.setAttribute("stroke-dasharray", `${samPct} ${100 - samPct}`);
    sSam.setAttribute("stroke-dashoffset", `${-(normalPct + mamPct)}`);
  }
}

function renderRiskTrajectorySvg(values) {
  const wrapper = document.getElementById("resRiskSvgWrapper");
  if (!wrapper) return;

  const w = 320, h = 54;
  const maxVal = 100, minVal = 0;
  const pts = values.map((v, i) => {
    const x = 20 + i * (w - 40) / (values.length - 1);
    const y = h - 12 - (v / maxVal) * (h - 24);
    return { x, y, val: v };
  });

  const pathD = "M " + pts.map(p => `${p.x} ${p.y}`).join(" L ");
  const isHigh = values[values.length - 1] >= 60;
  const strokeColor = isHigh ? "#ef4444" : (values[values.length - 1] >= 35 ? "#f59e0b" : "#10b981");

  wrapper.innerHTML = `
    <svg viewBox="0 0 ${w} ${h}" style="width:100%;height:100%;">
      <line x1="20" y1="${h-12}" x2="${w-20}" y2="${h-12}" stroke="#e2e8f0" stroke-dasharray="3 3"></line>
      <path d="${pathD}" fill="none" stroke="${strokeColor}" stroke-width="2.5" stroke-linecap="round"></path>
      ${pts.map(p => `
        <circle cx="${p.x}" cy="${p.y}" r="4" fill="${strokeColor}" stroke="#fff" stroke-width="1.5"></circle>
        <text x="${p.x}" y="${p.y - 7}" font-size="9" font-weight="700" text-anchor="middle" fill="#475569">${p.val}%</text>
      `).join("")}
      <text x="20" y="${h-1}" font-size="8" fill="#94a3b8">Current</text>
      <text x="${w-20}" y="${h-1}" font-size="8" text-anchor="end" fill="#94a3b8">+90 Days</text>
    </svg>
  `;
}

function toggleTechDetails() {
  const content = document.getElementById("techDetailsContent");
  const arrow = document.getElementById("techDetailsArrow");
  if (!content) return;
  const isOpen = content.style.display === "block";
  content.style.display = isOpen ? "none" : "block";
  if (arrow) arrow.textContent = isOpen ? "▼ Expand" : "▲ Collapse";
}

// ---------------------------------------------------------------------------
// SYSTEM IMPLEMENTATION DIAGNOSTICS & REVIEW 4 DEMO CONTROLLERS
// ---------------------------------------------------------------------------
async function loadSystemStatus() {
  try {
    const res = await fetch(`${API_BASE}/system/status`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const status = await res.json();

    const isHealthy = status.status === "healthy" || status.api_healthy;
    const badge = document.getElementById("topbarSystemStatusBadge");
    const text = document.getElementById("topbarSystemStatusText");
    const sfText = document.getElementById("sidebarSystemStatusText");

    if (badge && text) {
      if (isHealthy) {
        badge.style.background = "#ecfdf5";
        badge.style.borderColor = "#10b981";
        badge.style.color = "#047857";
        text.textContent = "Engines Operational";
      } else {
        badge.style.background = "#fef2f2";
        badge.style.borderColor = "#ef4444";
        badge.style.color = "#b91c1c";
        text.textContent = "System Degraded";
      }
    }
    if (sfText) {
      sfText.innerHTML = isHealthy ? `System Online <span style="color:#10b981;">&#9679;</span>` : `System Degraded <span style="color:#ef4444;">&#9679;</span>`;
    }
  } catch (e) {
    console.warn("Could not check system status:", e);
  }
}

async function openSystemDiagnosticsModal() {
  const modal = document.getElementById("systemDiagnosticsModal");
  if (modal) modal.style.display = "flex";
  await refreshSystemDiagnostics();
}

function closeSystemDiagnosticsModal() {
  const modal = document.getElementById("systemDiagnosticsModal");
  if (modal) modal.style.display = "none";
}

async function refreshSystemDiagnostics() {
  try {
    const res = await fetch(`${API_BASE}/system/status`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const data = await res.json();

    const el = id => document.getElementById(id);
    const setBadge = (id, ok, okText = "Ready", failText = "Degraded") => {
      const b = el(id);
      if (b) {
        b.textContent = ok ? okText : failText;
        b.className = ok ? "badge normal" : "badge severe";
      }
    };

    setBadge("diagBadgeDb", data.database, "Connected", "Disconnected");
    setBadge("diagBadgeEnsemble", data.tabular_ensemble, "Verified Active", "Missing");
    setBadge("diagBadgeWho", data.who_lms, "Ready", "Unavailable");
    setBadge("diagBadgeTriage", data.clinical_rules, "Active Override", "Unavailable");
    setBadge("diagBadgeShap", data.shap_explainer, "Ready", "Unavailable");
    setBadge("diagBadgeVision", data.vision_efficientnet, "Ready", "Missing Weights");
    setBadge("diagBadgeFusion", data.multimodal_fusion, "Ready", "Missing Weights");
    setBadge("diagBadgeVelocity", true, "Active", "Inactive");

    if (el("diagOverallStatusText")) {
      const allOk = data.database && data.tabular_ensemble && data.who_lms;
      el("diagOverallStatusText").textContent = allOk ? "ALL AI & CLINICAL ENGINES OPERATIONAL" : "SOME ENGINES DEGRADED";
      el("diagOverallStatusText").style.color = allOk ? "#15803d" : "#b91c1c";
    }
  } catch (e) {
    console.error("Failed to refresh diagnostics:", e);
  }
}

async function quickLoadDemoChild(demoHealthId) {
  closeSystemDiagnosticsModal();
  try {
    const res = await fetch(`${API_BASE}/children`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const children = await res.json();
    const match = children.find(c => c.health_id === demoHealthId || (c.name && c.name.includes(demoHealthId)));
    if (match) {
      viewChildProfile(match.id);
      showToast(`Loaded Demonstration Profile: ${match.name}`);
    } else {
      showToast(`Demo record ${demoHealthId} not found in database. Run seeding script.`, "error");
    }
  } catch (e) {
    console.error("Error loading demo child:", e);
    showToast("Error loading demo profile", "error");
  }
}

function openDatasetInfoModal() {
  const modal = document.getElementById("datasetInfoModal");
  if (modal) modal.style.display = "flex";
}

function closeDatasetInfoModal() {
  const modal = document.getElementById("datasetInfoModal");
  if (modal) modal.style.display = "none";
}
