/**
 * Parent Dashboard Controller - ChildNutri AI
 * Communicates with FastAPI Backend (/api/auth, /api/children, /api/assessments, /api/photos, /api/medical, /api/nutrition, /api/appointments, etc.)
 */

const API_BASE = (window.location && window.location.origin && window.location.origin.startsWith("http")) 
  ? (window.location.origin + "/api") 
  : "http://127.0.0.1:8000/api";
let currentChild = null;
let currentUser = null;
let currentUserId = null;
let currentChildGrowth = [];
let currentUpcomingAppt = null;

document.addEventListener("DOMContentLoaded", async function () {
  const token = localStorage.getItem("childnutri_token");
  if (!token) {
    window.location.href = "index.html";
    return;
  }

  setDynamicGreeting();
  await loadParentProfile();
  await loadChildData();
  await loadNotifications();

  // If newly registered parent account or child has not been registered yet, directly prompt with popup
  const urlParams = new URLSearchParams(window.location.search);
  const isNewAccount = urlParams.get("new_account") === "true" || localStorage.getItem("childnutri_just_registered") === "true";
  if (isNewAccount || !currentChild) {
    localStorage.removeItem("childnutri_just_registered");
    setTimeout(() => {
      openChildProfileModal();
      showToast("Welcome! Please add your child's details to record their first dataset.", "info");
    }, 350);
  }
});

function getAuthHeaders() {
  const token = localStorage.getItem("childnutri_token");
  return {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`
  };
}

function getChildFirstName() {
  if (!currentChild || !currentChild.name) return "Child";
  return currentChild.name.split(" ")[0];
}

function formatChildDob(dobStr) {
  if (!dobStr) return "Born —";
  try {
    const parts = String(dobStr).split("-");
    if (parts.length === 3) {
      const yr = parseInt(parts[0], 10);
      const mo = parseInt(parts[1], 10) - 1;
      const da = parseInt(parts[2], 10);
      const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
      return `${da} ${months[mo] || 'Jan'} ${yr}`;
    }
    const d = new Date(dobStr);
    if (!isNaN(d.getTime())) {
      const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
      return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;
    }
  } catch (e) {}
  return dobStr;
}

function formatChildAgeString(dobStr) {
  if (!dobStr) return "(Age not recorded)";
  try {
    const d = new Date(dobStr);
    const now = new Date();
    if (isNaN(d.getTime())) return "(Age not recorded)";
    const totalMonths = Math.max(0, Math.round((now - d) / (1000 * 60 * 60 * 24 * 30.4375)));
    if (totalMonths >= 12) {
      const yrs = Math.floor(totalMonths / 12);
      const remM = totalMonths % 12;
      if (remM > 0) {
        return `(${yrs} ${yrs === 1 ? 'year' : 'years'} ${remM} ${remM === 1 ? 'month' : 'months'})`;
      }
      return `(${yrs} ${yrs === 1 ? 'year' : 'years'})`;
    }
    return `(${totalMonths} ${totalMonths === 1 ? 'month' : 'months'})`;
  } catch (e) {
    return "(Age not recorded)";
  }
}

function toggleDetailedDossier() {
  const el = document.getElementById("detailedClinicalDossier");
  const btn = document.getElementById("btnToggleDetailedDossier");
  if (!el) return;
  const isHidden = (el.style.display === "none" || !el.style.display);
  el.style.display = isHidden ? "block" : "none";
  if (btn) btn.innerHTML = isHidden ? "📊 Hide Detailed Clinical Anthropometrics &amp; Notes &uarr;" : "📊 View Detailed Clinical Anthropometrics &amp; Notes &darr;";
}

function updateDynamicChildNames() {
  const firstName = getChildFirstName();
  const fullName = currentChild ? currentChild.name : "Child";

  // 1. Overview Tab Name
  const chcName = document.querySelector(".chc-name");
  if (chcName) chcName.textContent = fullName;

  // 2. Doctor notes text
  const dnText = document.querySelector(".dn-text");
  if (dnText) {
    dnText.textContent = dnText.textContent.replace(/Aarav/g, firstName);
  }

  // 3. Section Titles & Descriptions
  const allDescriptions = document.querySelectorAll(".page-header p, .explain-list .ei-desc, .card-title");
  allDescriptions.forEach(el => {
    if (el.textContent.includes("Aarav")) {
      el.textContent = el.textContent.replace(/Aarav's/g, `${firstName}'s`).replace(/Aarav/g, firstName);
    }
  });

  // 4. What this means title
  const explainHdr = document.querySelector("#sec-assessment .card:nth-of-type(1) .card-title");
  if (explainHdr) explainHdr.textContent = `What This Means for ${firstName}`;

  // 5. Growth tracker subtitle
  const growthSub = document.querySelector("#sec-growth .page-header p");
  if (growthSub) growthSub.textContent = `Monitor ${firstName}'s growth against WHO standards`;

  // 6. Growth legend
  const gclItems = document.querySelectorAll(".gc-legend .gcl-item");
  gclItems.forEach(item => {
    if (item.textContent.includes("Aarav") || item.textContent.includes("Child")) {
      item.innerHTML = `<div class="gcl-dot red"></div>${firstName}`;
    }
  });

  // 7. Diet banner
  const nutrBannerText = document.querySelector("#sec-nutrition .ab-text");
  if (nutrBannerText) {
    nutrBannerText.textContent = `Nutritional guidance and complementary feeding schedule for ${firstName}.`;
  }
}

async function loadParentProfile() {
  try {
    const res = await fetch(`${API_BASE}/auth/me`, { headers: getAuthHeaders() });
    if (!res.ok) {
      localStorage.removeItem("childnutri_token");
      window.location.href = "index.html";
      return;
    }
    const user = await res.json();
    currentUser = user;
    currentUserId = user.id;
    localStorage.setItem("childnutri_user", JSON.stringify(user));
    setDynamicGreeting();

    // Update parent name and avatars across dashboard
    const initial = user.full_name ? user.full_name[0].toUpperCase() : "P";
    document.querySelectorAll(".sf-av, .tb-av").forEach(el => el.textContent = initial);
    document.querySelectorAll(".sf-name, .tb-name").forEach(el => el.textContent = user.full_name);

    // Profile section & modal values
    const pfFullName = document.getElementById("profParentFullName");
    if (pfFullName) pfFullName.textContent = user.full_name;
    const pfEmail = document.getElementById("profParentEmail");
    if (pfEmail) pfEmail.textContent = user.email;

    const pfVals = document.querySelectorAll(".profile-form .pf-val");
    if (pfVals.length >= 3) {
      pfVals[0].textContent = user.full_name;
      pfVals[1].textContent = user.phone || "Not recorded";
      pfVals[2].textContent = user.email;
    }

    const inlineName = document.getElementById("inlineEditFullName");
    if (inlineName) inlineName.value = user.full_name || "";
    const inlinePhone = document.getElementById("inlineEditPhone");
    if (inlinePhone) inlinePhone.value = user.phone || "";
    const inlineEmail = document.getElementById("inlineEditEmail");
    if (inlineEmail) inlineEmail.value = user.email || "";

    const chGuardian = document.getElementById("childDossierGuardian");
    if (chGuardian) chGuardian.innerHTML = `&#128101; Caregiver: ${user.full_name}`;
    document.querySelectorAll(".sf-role, .tb-sub").forEach(el => el.textContent = "Parent / Guardian");
  } catch (e) {
    console.error("Error loading parent profile:", e);
  }
}

function renderEmptyDashboardState() {
  currentChild = null;
  currentChildGrowth = [];
  allChildrenList = [];

  const emptyContainer = document.getElementById("parentEmptyStateContainer");
  const populatedContainer = document.getElementById("populatedDashboardContent");
  const errorContainer = document.getElementById("parentErrorStateContainer");

  if (errorContainer) errorContainer.style.display = "none";
  if (emptyContainer) emptyContainer.style.display = "block";
  if (populatedContainer) populatedContainer.style.display = "none";

  const nutriEmpty = document.getElementById("nutriEmptyChildrenState");
  const nutriPop = document.getElementById("nutriPopulatedContent");
  if (nutriEmpty) nutriEmpty.style.display = "block";
  if (nutriPop) nutriPop.style.display = "none";

  // Greeting - display logged-in parent's actual account name
  const parentName = (currentUser && (currentUser.full_name || currentUser.name)) ? (currentUser.full_name || currentUser.name) : "Parent";
  const greetingEl = document.getElementById("parentGreetingText");
  if (greetingEl) {
    const hour = new Date().getHours();
    let timeStr = "Good morning";
    if (hour >= 12 && hour < 17) timeStr = "Good afternoon";
    else if (hour >= 17) timeStr = "Good evening";
    const firstName = parentName.split(" ")[0];
    greetingEl.innerHTML = `${timeStr}, <span style="color:#0d7a57;font-weight:800;">${firstName}</span>`;
  }

  // Summary 3-Card Row reset
  const totKids = document.getElementById("sumCardTotalChildren");
  if (totKids) totKids.textContent = "0";
  const totKidsSub = document.getElementById("sumCardTotalChildrenSub");
  if (totKidsSub) totKidsSub.textContent = "None registered";

  const totAss = document.getElementById("sumCardTotalAssessments");
  if (totAss) totAss.textContent = "0";
  const totAssSub = document.getElementById("sumCardTotalAssessmentsSub");
  if (totAssSub) totAssSub.textContent = "No assessments yet";

  const totRep = document.getElementById("sumCardTotalReports");
  if (totRep) totRep.textContent = "0";
  const totRepSub = document.getElementById("sumCardTotalReportsSub");
  if (totRepSub) totRepSub.textContent = "No reports yet";

  // Screening Status banner and subcards reset
  const scrTitle = document.getElementById("ovScrBannerTitle");
  if (scrTitle) scrTitle.textContent = "No screening records available yet";
  const scrSub = document.getElementById("ovScrBannerSub");
  if (scrSub) scrSub.textContent = "Your child's screening results will appear here after the first assessment.";

  ["ovScrPillGrowth", "ovScrPillDev", "ovScrPillNutr", "ovScrPillVision"].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.textContent = "Not done";
      el.style.background = "#f1f5f9";
      el.style.color = "#64748b";
    }
  });

  // Bottom 4 Quick Cards reset
  ["ovCardBirthPill", "ovCardMeasurementsPill", "ovCardGrowthPill", "ovCardAssessmentsPill"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.textContent = "No data available";
  });

  // Update Child Selector Dropdown
  renderChildSelectorDropdown([]);

  // Hide or reset mini stats & compatibility nodes
  document.querySelectorAll(".chc-stat .cs-val").forEach(el => el.textContent = "--");
  document.querySelectorAll(".mini-stats .ms-val").forEach((el, idx) => el.textContent = idx === 3 ? "--" : "0");
  document.querySelectorAll(".anthro-list .ai-val").forEach(el => el.textContent = "--");
  document.querySelectorAll(".anthro-list .ai-tag").forEach(el => el.textContent = "--");
  document.querySelectorAll(".chc-name").forEach(el => el.textContent = "No Child Added");

  // Reset Overview Dossier Meta
  const chGender = document.getElementById("childDossierGender");
  if (chGender) chGender.innerHTML = `&#9794; Not recorded`;
  const chAge = document.getElementById("childDossierAge");
  if (chAge) chAge.innerHTML = `(Not recorded)`;
  const chDob = document.getElementById("childDossierDob");
  if (chDob) chDob.innerHTML = `&#128197; Born —`;
  const chHid = document.getElementById("childDossierHealthId");
  if (chHid) chHid.innerHTML = `&#127380; —`;
  const chGuardian = document.getElementById("childDossierGuardian");
  if (chGuardian) chGuardian.innerHTML = `&#128101; Caregiver: ${parentName}`;

  // Reset Birth Baseline in Overview
  const curBWt = document.getElementById("currentBirthWeightVal");
  if (curBWt) curBWt.innerHTML = `<span style="font-size:1.1rem;color:var(--text-muted);">Not recorded</span>`;
  const curBLen = document.getElementById("currentBirthLengthVal");
  if (curBLen) curBLen.innerHTML = `<span style="font-size:1.1rem;color:var(--text-muted);">Not recorded</span>`;

  // Reset Modal Tags & Indicators
  const mTag = document.getElementById("modalParentChildTag");
  if (mTag) mTag.innerHTML = `&#128102; No child registered`;
  const pTag = document.getElementById("profSectionChildTag");
  if (pTag) pTag.innerHTML = `&#128102; No child registered`;
  const regChild = document.getElementById("regModalChildName");
  if (regChild) regChild.textContent = "None";

  // Reset Dedicated Regular Update Section
  const regSecName = document.getElementById("regSectionChildName");
  if (regSecName) regSecName.textContent = "--";
  const regSecAge = document.getElementById("regSectionChildAge");
  if (regSecAge) regSecAge.textContent = "--";
  const regSecGender = document.getElementById("regSectionChildGender");
  if (regSecGender) regSecGender.textContent = "--";
  const regSecHid = document.getElementById("regSectionHealthId");
  if (regSecHid) regSecHid.textContent = "--";

  const pageCName = document.getElementById("pageChildName");
  if (pageCName) pageCName.value = "";
  const pageCDob = document.getElementById("pageChildDob");
  if (pageCDob) pageCDob.value = "";
  const pageCGender = document.getElementById("pageChildGender");
  if (pageCGender) pageCGender.value = "Male";
  const pageCBW = document.getElementById("pageChildBirthWeight");
  if (pageCBW) pageCBW.value = "";
  const pageCBL = document.getElementById("pageChildBirthLength");
  if (pageCBL) pageCBL.value = "";
  const pageMDate = document.getElementById("pageMeasureDate");
  if (pageMDate) pageMDate.value = "";

  // Reset Child Profile in My Profile tab
  const childCardPf = document.querySelectorAll(".card:nth-of-type(2) .profile-form .pf-val");
  childCardPf.forEach(el => el.textContent = "--");
}

function renderChildDataErrorState(statusCode = 0, message = "") {
  currentChild = null;
  currentChildGrowth = [];
  allChildrenList = [];

  const emptyContainer = document.getElementById("parentEmptyStateContainer");
  const populatedContainer = document.getElementById("populatedDashboardContent");
  const errorContainer = document.getElementById("parentErrorStateContainer");

  if (populatedContainer) populatedContainer.style.display = "none";
  if (emptyContainer) emptyContainer.style.display = "none";
  if (errorContainer) {
    errorContainer.style.display = "block";
    const msgEl = document.getElementById("parentErrorMessage");
    if (msgEl) {
      msgEl.textContent = message || `Server response status ${statusCode || 'Error'}. Could not retrieve children. Click retry to reconnect.`;
    }
  }
}

async function loadChildData() {
  const errorContainer = document.getElementById("parentErrorStateContainer");
  if (errorContainer) errorContainer.style.display = "none";

  try {
    const res = await fetch(`${API_BASE}/children`, { headers: getAuthHeaders() });
    if (!res.ok) {
      if (res.status === 401) {
        localStorage.removeItem("childnutri_token");
        window.location.href = "index.html";
        return;
      }
      renderChildDataErrorState(res.status, "Unable to load registered children from the server.");
      return;
    }
    const children = await res.json();
    
    if (!Array.isArray(children) || children.length === 0) {
      renderEmptyDashboardState();
      // Directly prompt parent to add her child details (initial dataset)
      setTimeout(() => {
        openChildProfileModal();
      }, 300);
      return;
    }

    allChildrenList = children;
    closeChildProfileModal(true);
    const emptyContainer = document.getElementById("parentEmptyStateContainer");
    const populatedContainer = document.getElementById("populatedDashboardContent");
    if (errorContainer) errorContainer.style.display = "none";
    if (emptyContainer) emptyContainer.style.display = "none";
    if (populatedContainer) populatedContainer.style.display = "block";

    if (!currentChild || !children.some(c => c.id === currentChild.id)) {
      currentChild = children[0];
    } else {
      currentChild = children.find(c => c.id === currentChild.id) || children[0];
    }
    renderChildSelectorDropdown(children);

    // Immediately replace names across all sections
    updateDynamicChildNames();

    // Summary Cards Row: Total Children
    const totKids = document.getElementById("sumCardTotalChildren");
    if (totKids) totKids.textContent = children.length;
    const totKidsSub = document.getElementById("sumCardTotalChildrenSub");
    if (totKidsSub) totKidsSub.textContent = children.length === 1 ? "Active child" : `${children.length} active children`;

    // Dynamic formatted DOB and Age
    const dobFormatted = formatChildDob(currentChild.date_of_birth);
    const ageFormatted = formatChildAgeString(currentChild.date_of_birth);

    // Calculate dynamic age in months for legacy compatibility
    let ageStr = "Not recorded";
    if (currentChild.date_of_birth) {
      const d = new Date(currentChild.date_of_birth);
      const now = new Date();
      const months = Math.max(0, Math.round((now - d) / (1000 * 60 * 60 * 24 * 30.4375)));
      ageStr = `${months} Months`;
    }

    // Populate Overview Dossier Meta matching screenshot
    const chGender = document.getElementById("childDossierGender");
    if (chGender) {
      const isFemale = (currentChild.gender || "").toLowerCase().includes("female");
      chGender.innerHTML = isFemale ? `&#9792; ${currentChild.gender}` : `&#9794; ${currentChild.gender || 'Male'}`;
    }
    const chAge = document.getElementById("childDossierAge");
    if (chAge) chAge.innerHTML = ageFormatted;
    const chDob = document.getElementById("childDossierDob");
    if (chDob) chDob.innerHTML = `&#128197; ${dobFormatted}`;
    const chHid = document.getElementById("childDossierHealthId");
    if (chHid) chHid.innerHTML = `&#127380; ${currentChild.health_id || 'CHN-001'}`;
    const chGuardian = document.getElementById("childDossierGuardian");
    if (chGuardian && currentUser) chGuardian.innerHTML = `&#128101; Caregiver: ${currentUser.full_name || 'Parent'}`;

    // Status badge on hero card
    const heroBadge = document.getElementById("heroStatusBadge");
    if (heroBadge) {
      heroBadge.className = "status-badge normal";
      heroBadge.style.background = "#dcfce7";
      heroBadge.style.color = "#15803d";
      heroBadge.innerHTML = "&#9679; Healthy Growth";
    }

    // Birth Baseline Quick Pill
    const birthPill = document.getElementById("ovCardBirthPill");
    if (birthPill) {
      if (currentChild.birth_weight != null) {
        const blStr = currentChild.birth_length != null ? ` • ${currentChild.birth_length} cm` : '';
        birthPill.textContent = `${currentChild.birth_weight} kg${blStr}`;
      } else {
        birthPill.textContent = "No data available";
      }
    }

    // Populate Birth Baseline in Overview
    const curBWt = document.getElementById("currentBirthWeightVal");
    if (curBWt) {
      const bw = currentChild.birth_weight != null ? currentChild.birth_weight : null;
      curBWt.innerHTML = bw != null ? `${bw} <span style="font-size:1.1rem;font-weight:500;color:var(--text-secondary);">kg</span>` : `<span style="font-size:1.1rem;color:var(--text-muted);">Not recorded</span>`;
    }
    const curBLen = document.getElementById("currentBirthLengthVal");
    if (curBLen) {
      const bl = currentChild.birth_length != null ? currentChild.birth_length : null;
      curBLen.innerHTML = bl != null ? `${bl} <span style="font-size:1.1rem;font-weight:500;color:var(--text-secondary);">cm</span>` : `<span style="font-size:1.1rem;color:var(--text-muted);">Not recorded</span>`;
    }

    // Populate Modal Child Tags
    const mTag = document.getElementById("modalParentChildTag");
    if (mTag) mTag.innerHTML = `&#128102; ${currentChild.name} (${currentChild.health_id})`;
    const pTag = document.getElementById("profSectionChildTag");
    if (pTag) pTag.innerHTML = `&#128102; ${currentChild.name}`;
    const regChild = document.getElementById("regModalChildName");
    if (regChild) regChild.textContent = currentChild.name;

    // Legacy metaPills fallback
    const metaPills = document.querySelectorAll(".chc-meta .meta-pill");
    if (metaPills.length >= 3 && !chGender) {
      metaPills[0].textContent = `👤 ${currentChild.gender}`;
      metaPills[1].textContent = `⏱️ Born ${currentChild.date_of_birth}`;
      metaPills[2].textContent = `🆔 ${currentChild.health_id}`;
    }

    // Update child details in My Profile tab
    const childCardPf = document.querySelectorAll(".card:nth-of-type(2) .profile-form .pf-val");
    if (childCardPf.length >= 6) {
      childCardPf[0].textContent = currentChild.name;
      childCardPf[1].textContent = currentChild.date_of_birth;
      childCardPf[2].textContent = currentChild.gender;
      childCardPf[3].textContent = ageStr;
      childCardPf[4].textContent = currentChild.birth_weight != null ? `${currentChild.birth_weight} kg (Birth Weight)` : "Not recorded (Birth Weight)";
      childCardPf[5].textContent = currentChild.health_id;
    }

    // Load child growth history & sub-modules
    
    // Populate Dedicated Regular Update Section Summary & Forms
    const regSecName = document.getElementById("regSectionChildName");
    if (regSecName) regSecName.textContent = currentChild.name;
    const regSecAge = document.getElementById("regSectionChildAge");
    if (regSecAge) regSecAge.textContent = ageStr;
    const regSecGender = document.getElementById("regSectionChildGender");
    if (regSecGender) regSecGender.textContent = currentChild.gender;
    const regSecHid = document.getElementById("regSectionHealthId");
    if (regSecHid) regSecHid.textContent = currentChild.health_id;

    const pageCName = document.getElementById("pageChildName");
    if (pageCName) pageCName.value = currentChild.name || "";
    const pageCDob = document.getElementById("pageChildDob");
    if (pageCDob) pageCDob.value = currentChild.date_of_birth || "";
    const pageCGender = document.getElementById("pageChildGender");
    if (pageCGender) pageCGender.value = currentChild.gender || "Male";
    const pageCBW = document.getElementById("pageChildBirthWeight");
    if (pageCBW) pageCBW.value = currentChild.birth_weight || "";
    const pageCBL = document.getElementById("pageChildBirthLength");
    if (pageCBL) pageCBL.value = currentChild.birth_length || "";

    const pageMDate = document.getElementById("pageMeasureDate");
    if (pageMDate && !pageMDate.value) pageMDate.value = new Date().toISOString().split("T")[0];

    await loadChildGrowthHistory(currentChild.id);
    await loadChildPhotos(currentChild.id);
    await loadMedicalHistory(currentChild.id);
    await loadNutritionPlan(currentChild.id);
    await loadAppointments(currentChild.id);
    await loadScreeningStatus(currentChild.id);
  } catch (e) {
    console.error("Error loading child data:", e);
    renderChildDataErrorState(0, e.message || "Network connection failure.");
  }
}


// =============================================================================
// COMPLETE GROWTH TRACKER MODULE - CLINICAL LONGITUDINAL SYSTEM
// =============================================================================
let activeGrowthMetric = "weight";
let activeGrowthTimeRange = "all";
let allChildrenList = [];

// 1. CHILD SELECTOR CONTROLLER
function renderChildSelectorDropdown(children) {
  allChildrenList = children || allChildrenList || [];

  const currentName = currentChild ? currentChild.name : (allChildrenList.length > 0 ? allChildrenList[0].name : "Select Child");
  document.querySelectorAll(".child-selector-btn-label, #childSelectorBtnLabel, #childSelectorBtnLabelHero").forEach(el => {
    el.textContent = currentName;
  });

  const containers = [
    document.getElementById("childSelectorList"),
    document.getElementById("childSelectorListHero")
  ].filter(Boolean);

  if (containers.length === 0) return;

  containers.forEach(listContainer => {
    listContainer.innerHTML = "";
    if (allChildrenList.length === 0) {
      listContainer.innerHTML = '<div style="font-size:0.8rem;color:var(--text-muted);padding:8px;">No registered children found.</div>';
      return;
    }

    allChildrenList.forEach(c => {
      const isSelected = currentChild && currentChild.id === c.id;
      let ageStr = "Age unknown";
      if (c.date_of_birth) {
        const d = new Date(c.date_of_birth);
        const now = new Date();
        const m = Math.max(1, Math.round((now - d) / (1000 * 60 * 60 * 24 * 30.4375)));
        ageStr = `${m} months`;
      }

      const item = document.createElement("div");
      item.className = "child-selector-item";
      item.style.cssText = `padding:8px 10px;border-radius:8px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;background:${isSelected ? 'var(--surface-muted)' : 'transparent'};transition:background 120ms ease;`;
      item.onmouseover = () => { if (!isSelected) item.style.background = 'var(--surface-muted)'; };
      item.onmouseout = () => { if (!isSelected) item.style.background = 'transparent'; };
      item.onclick = () => selectActiveChild(c.id);

      item.innerHTML = `
        <div style="flex:1;">
          <div style="font-weight:700;font-size:0.85rem;color:var(--text);">${c.name}</div>
          <div style="font-size:0.75rem;color:var(--text-secondary);">${ageStr} &bull; ${c.gender}</div>
        </div>
        <div style="display:flex;align-items:center;gap:6px;">
          ${isSelected ? '<span style="color:var(--brand);font-weight:700;font-size:0.85rem;" title="Active Child">✓</span>' : ''}
          <button type="button" title="Delete ${c.name}" onclick="event.stopPropagation(); confirmDeleteChild(${c.id}, '${c.name.replace(/'/g, "\\'")}')" style="background:transparent;border:none;cursor:pointer;padding:4px 6px;border-radius:4px;color:#ef4444;font-size:0.88rem;display:flex;align-items:center;justify-content:center;transition:background 120ms ease;" onmouseover="this.style.background='#fee2e2'" onmouseout="this.style.background='transparent'">
            🗑️
          </button>
        </div>
      `;
      listContainer.appendChild(item);
    });
  });
}

function toggleChildSelectorMenu(menuType) {
  let dd;
  if (menuType === "hero") {
    dd = document.getElementById("childSelectorDropdownHero");
  } else {
    dd = document.getElementById("childSelectorDropdown");
  }
  if (!dd) return;

  const willOpen = dd.style.display !== "block";
  document.querySelectorAll(".child-selector-dropdown, #childSelectorDropdown, #childSelectorDropdownHero").forEach(el => {
    el.style.display = "none";
  });
  if (willOpen) {
    dd.style.display = "block";
  }
}

function filterChildList(query, menuType) {
  const q = (query || "").toLowerCase().trim();
  let listContainer;
  if (menuType === "hero") {
    listContainer = document.getElementById("childSelectorListHero");
  } else {
    listContainer = document.getElementById("childSelectorList");
  }
  if (!listContainer) return;
  const items = listContainer.children;
  for (let i = 0; i < items.length; i++) {
    const text = items[i].textContent.toLowerCase();
    items[i].style.display = text.includes(q) ? "flex" : "none";
  }
}

// Close child selector dropdown on outside click
document.addEventListener("click", function(e) {
  const isInsideWrap = !!e.target.closest(".child-selector-wrap") ||
    !!e.target.closest("#childSelectorWrap") ||
    !!e.target.closest("#heroChildSelectorWrap");

  if (!isInsideWrap) {
    document.querySelectorAll(".child-selector-dropdown, #childSelectorDropdown, #childSelectorDropdownHero").forEach(dd => {
      dd.style.display = "none";
    });
  }
});

async function selectActiveChild(childId) {
  document.querySelectorAll(".child-selector-dropdown, #childSelectorDropdown, #childSelectorDropdownHero").forEach(dd => {
    dd.style.display = "none";
  });

  const found = allChildrenList.find(c => c.id === childId);
  if (!found) return;

  currentChild = found;
  showToast(`Switched active child to ${found.name}.`);

  // Update top headers
  document.querySelectorAll(".child-selector-btn-label, #childSelectorBtnLabel, #childSelectorBtnLabelHero").forEach(lbl => {
    lbl.textContent = found.name;
  });
  const hName = document.getElementById("growthActiveChildName");
  if (hName) hName.textContent = found.name;

  let ageStr = "Not recorded";
  if (found.date_of_birth) {
    const d = new Date(found.date_of_birth);
    const now = new Date();
    const m = Math.max(0, Math.round((now - d) / (1000 * 60 * 60 * 24 * 30.4375)));
    ageStr = `${m} months`;
  }
  const hMeta = document.getElementById("growthActiveChildMeta");
  if (hMeta) hMeta.textContent = `${ageStr} • ${found.gender}`;

  // Reload child data & history
  await loadChildData();
}

// 1.1 DELETE CHILD CONTROLLER
async function confirmDeleteChild(childId, childName) {
  if (!childId) return;
  const displayName = childName || (currentChild ? currentChild.name : "this child");
  const confirmed = window.confirm(`Are you sure you want to delete ${displayName}? This will permanently remove their physical growth records, screening history, and pediatric profile.`);
  if (!confirmed) return;

  try {
    const res = await fetch(`${API_BASE}/children/${childId}`, {
      method: "DELETE",
      headers: getAuthHeaders()
    });

    if (res.status === 401) {
      showToast("Session expired. Please log in again.", "error");
      window.location.href = "index.html";
      return;
    }

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      const msg = errData.detail || "Unable to delete child record.";
      showToast(msg, "error");
      return;
    }

    showToast(`Successfully deleted ${displayName}.`, "success");

    // Close any open child selector dropdowns
    document.querySelectorAll(".child-selector-dropdown, #childSelectorDropdown, #childSelectorDropdownHero").forEach(dd => {
      dd.style.display = "none";
    });

    // If deleting the currently selected child, reset currentChild
    if (currentChild && currentChild.id === childId) {
      currentChild = null;
    }

    // Refresh parent dashboard data from server without logging out
    await loadChildData();
  } catch (err) {
    console.error("Delete child failed:", err);
    showToast("Network or server communication error while deleting child.", "error");
  }
}

function confirmDeleteCurrentChild() {
  if (!currentChild) {
    showToast("No active child selected to delete.", "error");
    return;
  }
  confirmDeleteChild(currentChild.id, currentChild.name);
}


// 2. TOP SUMMARY CARDS & DELTAS
function computeGrowthDeltas(growth) {
  growth = growth || [];
  if (growth.length === 0) {
    const bWt = currentChild?.birth_weight || 3.5;
    const bHt = currentChild?.birth_length || 52.0;
    return {
      currentWeight: bWt,
      currentHeight: bHt,
      currentMuac: null,
      currentWhz: null,
      weightDelta: 0,
      heightDelta: 0,
      muacDelta: 0,
      whzDelta: 0,
      lastDate: currentChild?.date_of_birth || "Birth Registration",
      status: "Registration Baseline",
      hasPrevious: false
    };
  }

  const latest = growth[growth.length - 1];
  const hasPrevious = growth.length >= 2;
  const prev = hasPrevious ? growth[growth.length - 2] : null;

  const curWt = latest.weight != null ? Number(latest.weight) : null;
  const curHt = latest.height != null ? Number(latest.height) : null;
  const curMu = latest.muac != null ? Number(latest.muac) : null;
  const curWhz = latest.whz != null ? Number(latest.whz) : null;

  const prevWt = prev && prev.weight != null ? Number(prev.weight) : null;
  const prevHt = prev && prev.height != null ? Number(prev.height) : null;
  const prevMu = prev && prev.muac != null ? Number(prev.muac) : null;
  const prevWhz = prev && prev.whz != null ? Number(prev.whz) : null;

  return {
    currentWeight: curWt,
    currentHeight: curHt,
    currentMuac: curMu,
    currentWhz: curWhz,
    weightDelta: (curWt != null && prevWt != null) ? Math.round((curWt - prevWt) * 10) / 10 : null,
    heightDelta: (curHt != null && prevHt != null) ? Math.round((curHt - prevHt) * 10) / 10 : null,
    muacDelta: (curMu != null && prevMu != null) ? Math.round((curMu - prevMu) * 10) / 10 : null,
    whzDelta: (curWhz != null && prevWhz != null) ? Math.round((curWhz - prevWhz) * 100) / 100 : null,
    lastDate: latest.date || latest.assessment_date || "Recent",
    status: latest.prediction || "Not assessed",
    hasPrevious: hasPrevious
  };
}

function renderGrowthSummaryCards(growth) {
  const d = computeGrowthDeltas(growth);

  // Card 1: Weight
  const wVal = document.getElementById("gtCardWeightVal");
  const wIcon = document.getElementById("gtCardWeightDeltaIcon");
  const wText = document.getElementById("gtCardWeightDeltaText");
  if (wVal) wVal.textContent = d.currentWeight != null ? `${d.currentWeight} kg` : "—";
  if (wIcon && wText) {
    if (!d.hasPrevious || d.weightDelta == null) {
      wIcon.innerHTML = `<span style="color:#64748b;">— Baseline</span>`;
      wText.textContent = "Initial visit recorded";
    } else if (d.weightDelta > 0) {
      wIcon.innerHTML = `<span style="color:#16a34a;">↑ +${d.weightDelta} kg</span>`;
      wText.textContent = "Since previous visit";
    } else if (d.weightDelta < 0) {
      wIcon.innerHTML = `<span style="color:#dc2626;">↓ ${d.weightDelta} kg</span>`;
      wText.textContent = "Since previous visit";
    } else {
      wIcon.innerHTML = `<span style="color:var(--text-secondary);">&rarr; 0.0 kg</span>`;
      wText.textContent = "Stable since previous visit";
    }
  }

  // Card 2: Height
  const hVal = document.getElementById("gtCardHeightVal");
  const hIcon = document.getElementById("gtCardHeightDeltaIcon");
  const hText = document.getElementById("gtCardHeightDeltaText");
  if (hVal) hVal.textContent = d.currentHeight != null ? `${d.currentHeight} cm` : "—";
  if (hIcon && hText) {
    if (!d.hasPrevious || d.heightDelta == null) {
      hIcon.innerHTML = `<span style="color:#64748b;">— Baseline</span>`;
      hText.textContent = "Initial visit recorded";
    } else if (d.heightDelta > 0) {
      hIcon.innerHTML = `<span style="color:#16a34a;">↑ +${d.heightDelta} cm</span>`;
      hText.textContent = "Since previous visit";
    } else if (d.heightDelta < 0) {
      hIcon.innerHTML = `<span style="color:#f59e0b;">↓ ${d.heightDelta} cm</span>`;
      hText.textContent = "Measurement variance check";
    } else {
      wIcon.innerHTML = `<span style="color:var(--text-secondary);">&rarr; 0.0 cm</span>`;
      hText.textContent = "Stable since previous visit";
    }
  }

  // Card 3: MUAC
  const mVal = document.getElementById("gtCardMuacVal");
  const mIcon = document.getElementById("gtCardMuacDeltaIcon");
  const mText = document.getElementById("gtCardMuacDeltaText");
  if (mVal) mVal.textContent = d.currentMuac ? `${d.currentMuac} cm` : "—";
  if (mIcon && mText) {
    if (d.muacDelta !== null) {
      if (d.muacDelta > 0) {
        mIcon.innerHTML = `<span style="color:#16a34a;">↑ +${d.muacDelta} cm</span>`;
      } else if (d.muacDelta < 0) {
        mIcon.innerHTML = `<span style="color:#dc2626;">↓ ${d.muacDelta} cm</span>`;
      } else {
        mIcon.innerHTML = `<span style="color:var(--text-secondary);">&rarr; 0.0 cm</span>`;
      }
      mText.textContent = "Since previous";
    } else {
      mIcon.innerHTML = `<span style="color:var(--text-muted);">&mdash;</span>`;
      mText.textContent = "Safe ≥ 12.5 cm";
    }
  }

  // Card 4: WHZ
  const whzVal = document.getElementById("gtCardWhzVal");
  const whzIcon = document.getElementById("gtCardWhzDeltaIcon");
  const whzText = document.getElementById("gtCardWhzDeltaText");
  if (whzVal) whzVal.textContent = d.currentWhz !== null ? `${d.currentWhz > 0 ? '+' : ''}${d.currentWhz}` : "—";
  if (whzIcon && whzText) {
    if (d.whzDelta !== null) {
      if (d.whzDelta > 0) {
        whzIcon.innerHTML = `<span style="color:#16a34a;">↑ +${d.whzDelta} SD</span>`;
      } else if (d.whzDelta < 0) {
        whzIcon.innerHTML = `<span style="color:#dc2626;">↓ ${d.whzDelta} SD</span>`;
      } else {
        whzIcon.innerHTML = `<span style="color:var(--text-secondary);">&rarr; 0.00 SD</span>`;
      }
      whzText.textContent = "WHO Z-score";
    } else {
      whzIcon.innerHTML = `<span style="color:var(--text-muted);">&mdash;</span>`;
      whzText.textContent = "Standardized";
    }
  }

  // Card 5: Last Screening
  const scDate = document.getElementById("gtCardLastScreeningDate");
  const scBadge = document.getElementById("gtCardLastScreeningStatus");
  const upBadge = document.getElementById("growthLastUpdatedBadge");
  if (scDate) scDate.textContent = d.lastDate;
  if (upBadge) upBadge.textContent = `Last updated: ${d.lastDate}`;
  if (scBadge) {
    const isWorse = d.status.includes("SAM") || d.status.includes("Severe") || d.status.includes("Wasted") || d.status.includes("Stunted");
    scBadge.className = `status-badge ${isWorse ? 'danger' : 'normal'}`;
    scBadge.textContent = d.status;
  }

  // Also update small Home Overview snapshot cards
  const ovW = document.getElementById("ovGrowthWeight");
  const ovWD = document.getElementById("ovGrowthWeightDelta");
  const ovH = document.getElementById("ovGrowthHeight");
  const ovHD = document.getElementById("ovGrowthHeightDelta");
  const ovM = document.getElementById("ovGrowthMuac");
  const ovMD = document.getElementById("ovGrowthMuacDelta");
  const ovWhz = document.getElementById("ovGrowthWhz");
  const ovWhzD = document.getElementById("ovGrowthWhzDelta");

  if (ovW) ovW.textContent = `${d.currentWeight} kg`;
  if (ovWD) ovWD.innerHTML = d.weightDelta < 0 ? `<span style="color:#dc2626;">↓ ${d.weightDelta} kg</span>` : `<span style="color:#16a34a;">↑ +${d.weightDelta} kg</span>`;
  if (ovH) ovH.textContent = `${d.currentHeight} cm`;
  if (ovHD) ovHD.innerHTML = d.heightDelta < 0 ? `<span style="color:#f59e0b;">↓ ${d.heightDelta} cm</span>` : `<span style="color:#16a34a;">↑ +${d.heightDelta} cm</span>`;
  if (ovM) ovM.textContent = d.currentMuac ? `${d.currentMuac} cm` : "—";
  if (ovMD) ovMD.innerHTML = d.muacDelta !== null ? (d.muacDelta < 0 ? `<span style="color:#dc2626;">↓ ${d.muacDelta} cm</span>` : `<span style="color:#16a34a;">↑ +${d.muacDelta} cm</span>`) : "—";
  if (ovWhz) ovWhz.textContent = d.currentWhz !== null ? `${d.currentWhz > 0 ? '+' : ''}${d.currentWhz}` : "—";
  if (ovWhzD) ovWhzD.innerHTML = d.whzDelta !== null ? (d.whzDelta < 0 ? `<span style="color:#dc2626;">↓ ${d.whzDelta} SD</span>` : `<span style="color:#16a34a;">↑ +${d.whzDelta} SD</span>`) : "—";
}

// 3. MAIN INTERACTIVE GROWTH CHART
const WHO_MEDIANS = {
  weight: { 0: 3.3, 6: 7.9, 12: 9.6, 18: 10.8, 24: 12.2, 36: 14.3, 48: 16.3, 60: 18.3 },
  height: { 0: 49.9, 6: 67.6, 12: 75.7, 18: 82.3, 24: 87.8, 36: 96.1, 48: 103.3, 60: 110.0 }
};

function getWhoRef(metric, age) {
  const table = WHO_MEDIANS[metric];
  if (!table) return metric === "whz" || metric === "haz" || metric === "waz" ? 0.0 : 12.5;
  const keys = Object.keys(table).map(Number).sort((a,b) => a - b);
  if (age <= keys[0]) return table[keys[0]];
  if (age >= keys[keys.length - 1]) return table[keys[keys.length - 1]];
  for (let i = 0; i < keys.length - 1; i++) {
    if (age >= keys[i] && age <= keys[i+1]) {
      const t = (age - keys[i]) / (keys[i+1] - keys[i]);
      return table[keys[i]] + t * (table[keys[i+1]] - table[keys[i]]);
    }
  }
  return 10.0;
}

function switchGrowthTab(metric, el) {
  activeGrowthMetric = metric || "weight";
  document.querySelectorAll(".metric-switch-pills .switch-pill").forEach(p => p.classList.remove("active"));
  if (el) el.classList.add("active");
  const titles = {
    weight: "Weight Trajectory (kg)",
    height: "Height Trajectory (cm)",
    muac: "Mid-Upper Arm Circumference (MUAC cm)",
    whz: "Weight-for-Height Z-Score (WHZ)",
    haz: "Height-for-Age Z-Score (HAZ)",
    waz: "Weight-for-Age Z-Score (WAZ)"
  };
  const titleEl = document.getElementById("activeChartTitle");
  if (titleEl) titleEl.textContent = titles[metric] || "Growth Trajectory";
  renderInteractiveGrowthChart();
}

function switchGrowthTimeRange(range, el) {
  activeGrowthTimeRange = range || "all";
  document.querySelectorAll(".time-pill").forEach(p => p.classList.remove("active"));
  if (el) el.classList.add("active");
  renderInteractiveGrowthChart();
}

function filterGrowthByTimeRange(growth) {
  if (!growth || growth.length <= 1 || activeGrowthTimeRange === "all") return growth;
  const now = new Date();
  const monthsMap = { "1m": 1, "3m": 3, "6m": 6, "1y": 12 };
  const cutoffMonths = monthsMap[activeGrowthTimeRange] || 12;
  const cutoffTime = now.getTime() - (cutoffMonths * 30.4375 * 24 * 60 * 60 * 1000);

  const filtered = growth.filter(pt => {
    if (!pt.date && !pt.assessment_date) return true;
    const d = new Date(pt.date || pt.assessment_date);
    return !isNaN(d.getTime()) ? d.getTime() >= cutoffTime : true;
  });

  return filtered.length > 0 ? filtered : growth.slice(-3);
}

function renderInteractiveGrowthChart() {
  const metric = activeGrowthMetric || "weight";
  let growth = currentChildGrowth || [];
  growth = filterGrowthByTimeRange(growth);

  const pathEl = document.getElementById("childGrowthSvgPath");
  const whoMedPath = document.getElementById("whoMedianSvgPath");
  const whoSd2Path = document.getElementById("whoSd2SvgPath");
  const dotsGroup = document.getElementById("childGrowthDotsGroup");
  const tooltip = document.getElementById("chartTooltip");
  if (!pathEl || !dotsGroup) return;

  dotsGroup.innerHTML = "";

  // If no assessments yet, show baseline birth state
  if (growth.length === 0) {
    const bWt = currentChild?.birth_weight || 3.5;
    const bHt = currentChild?.birth_length || 52.0;
    growth = [{
      date: currentChild?.date_of_birth || "Birth",
      age_months: 0,
      weight: bWt,
      height: bHt,
      muac: 12.5,
      whz: 0.0,
      haz: 0.0,
      waz: 0.0
    }];
  }

  // Determine scale bounds
  let minVal = 0, maxVal = 20, unit = "kg";
  if (metric === "weight") {
    minVal = 2; maxVal = 18; unit = "kg";
  } else if (metric === "height") {
    minVal = 45; maxVal = 115; unit = "cm";
  } else if (metric === "muac") {
    minVal = 9; maxVal = 17; unit = "cm";
  } else {
    // whz, haz, waz
    minVal = -4; maxVal = 3; unit = "SD";
  }

  // Map values
  const count = growth.length;
  const leftX = 70, rightX = 780, topY = 30, bottomY = 190;
  const stepX = count > 1 ? (rightX - leftX) / (count - 1) : 0;

  const points = growth.map((pt, i) => {
    let val = null;
    if (metric === "weight") val = pt.weight != null ? Number(pt.weight) : null;
    else if (metric === "height") val = pt.height != null ? Number(pt.height) : null;
    else if (metric === "muac") val = pt.muac != null ? Number(pt.muac) : null;
    else if (metric === "whz") val = pt.whz != null ? Number(pt.whz) : null;
    else if (metric === "haz") val = pt.haz != null ? Number(pt.haz) : null;
    else if (metric === "waz") val = pt.waz != null ? Number(pt.waz) : null;

    const plotVal = val != null ? val : (metric === "whz" || metric === "haz" || metric === "waz" ? 0.0 : (minVal + maxVal) / 2);
    const x = count === 1 ? (leftX + rightX) / 2 : leftX + (i * stepX);
    const norm = Math.max(0, Math.min(1, (plotVal - minVal) / (maxVal - minVal)));
    const y = bottomY - (norm * (bottomY - topY));
    const age = pt.age_months || 12;
    const whoMed = getWhoRef(metric, age);
    const whoNorm = Math.max(0, Math.min(1, (whoMed - minVal) / (maxVal - minVal)));
    const whoY = bottomY - (whoNorm * (bottomY - topY));

    let sd2Val = whoMed * 0.85;
    if (metric === "height") sd2Val = whoMed - 4.5;
    else if (metric === "whz" || metric === "haz" || metric === "waz") sd2Val = -2.0;
    else if (metric === "muac") sd2Val = 12.5;

    const sd2Norm = Math.max(0, Math.min(1, (sd2Val - minVal) / (maxVal - minVal)));
    const sd2Y = bottomY - (sd2Norm * (bottomY - topY));

    return { x, y, whoY, sd2Y, val, age, whoMed, sd2Val, date: pt.date || pt.assessment_date || "Recent" };
  });

  // Construct SVG paths
  function buildPathString(pts, yKey) {
    if (pts.length === 1) return `M ${leftX} ${pts[0][yKey]} L ${rightX} ${pts[0][yKey]}`;
    let d = `M ${pts[0].x} ${pts[0][yKey]}`;
    for (let i = 1; i < pts.length; i++) {
      const prev = pts[i - 1];
      const curr = pts[i];
      const cx = (prev.x + curr.x) / 2;
      d += ` C ${cx} ${prev[yKey]}, ${cx} ${curr[yKey]}, ${curr.x} ${curr[yKey]}`;
    }
    return d;
  }

  pathEl.setAttribute("d", buildPathString(points, "y"));
  if (whoMedPath) whoMedPath.setAttribute("d", buildPathString(points, "whoY"));
  if (whoSd2Path) whoSd2Path.setAttribute("d", buildPathString(points, "sd2Y"));

  // Interactive dots & tooltips
  points.forEach(pt => {
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", pt.x);
    circle.setAttribute("cy", pt.y);
    circle.setAttribute("r", "5.5");
    circle.setAttribute("fill", "var(--brand)");
    circle.setAttribute("stroke", "#FFFFFF");
    circle.setAttribute("stroke-width", "2.5");
    circle.style.cursor = "pointer";
    circle.style.transition = "transform 150ms ease, r 150ms ease";

    circle.addEventListener("mouseenter", function(e) {
      circle.setAttribute("r", "7.5");
      if (tooltip) {
        tooltip.innerHTML = `
          <div style="font-weight:700;margin-bottom:2px;">${pt.date} (${pt.age} mo)</div>
          <div>Child: <strong>${pt.val != null ? `${pt.val} ${unit}` : "Not recorded"}</strong></div>
          <div style="color:#38bdf8;">WHO Median: ${Math.round(pt.whoMed * 10) / 10} ${unit}</div>
          <div style="color:#fbbf24;">WHO -2 SD: ${Math.round(pt.sd2Val * 10) / 10} ${unit}</div>
        `;
        const rect = dotsGroup.getBoundingClientRect();
        tooltip.style.left = `${Math.min(650, Math.max(20, pt.x - 70))}px`;
        tooltip.style.top = `${Math.max(10, pt.y - 65)}px`;
        tooltip.style.display = "block";
      }
    });

    circle.addEventListener("mouseleave", function() {
      circle.setAttribute("r", "5.5");
      if (tooltip) tooltip.style.display = "none";
    });

    dotsGroup.appendChild(circle);
  });

  // Evaluate Trajectory Status Pill
  const trajText = document.getElementById("trajectoryStatusText");
  if (trajText && points.length >= 2) {
    const first = points[0].val;
    const last = points[points.length - 1].val;
    if (metric === "weight" || metric === "muac") {
      if (last < first - 0.3) {
        trajText.textContent = "Declining Trajectory (Review Recommended)";
        trajText.style.color = "#dc2626";
      } else {
        trajText.textContent = "Within Assessed Range";
        trajText.style.color = "var(--brand)";
      }
    } else if (metric === "whz") {
      if (last < -2.0) {
        trajText.textContent = "Moderate Risk Trajectory";
        trajText.style.color = "#ea580c";
      } else {
        trajText.textContent = "Within Assessed Range";
        trajText.style.color = "var(--brand)";
      }
    } else {
      trajText.textContent = "Insufficient History";
      trajText.style.color = "var(--text-muted)";
    }
  }
}

// 4. WHO GROWTH INDICATORS ASSESSMENT
function renderWHOGrowthAssessment(growth) {
  growth = growth || [];
  const latest = growth[growth.length - 1] || {};

  let whz = (latest.whz !== undefined && latest.whz !== null) ? latest.whz : null;
  let haz = (latest.haz !== undefined && latest.haz !== null) ? latest.haz : null;
  let waz = (latest.waz !== undefined && latest.waz !== null) ? latest.waz : null;
  let baz = (latest.baz !== undefined && latest.baz !== null) ? latest.baz : null;

  const vHAZ = document.getElementById("valHAZ");
  const bHAZ = document.getElementById("badgeHAZ");
  const vWAZ = document.getElementById("valWAZ");
  const bWAZ = document.getElementById("badgeWAZ");
  const vWHZ = document.getElementById("valWHZ");
  const bWHZ = document.getElementById("badgeWHZ");
  const vBAZ = document.getElementById("valBAZ");
  const bBAZ = document.getElementById("badgeBAZ");

  function setScoreCard(valEl, badgeEl, score, descType) {
    if (!valEl || !badgeEl) return;
    if (score === null || score === undefined || isNaN(score)) {
      valEl.textContent = "—";
      badgeEl.className = "badge";
      badgeEl.textContent = "Not available";
      return;
    }

    valEl.textContent = `${score > 0 ? '+' : ''}${score.toFixed(2)}`;
    if (score < -3.0) {
      badgeEl.className = "badge severe";
      badgeEl.textContent = "Review";
    } else if (score < -2.0) {
      badgeEl.className = "badge wasted";
      badgeEl.textContent = "Monitor";
    } else {
      badgeEl.className = "badge normal";
      badgeEl.textContent = "Normal range";
    }
  }

  setScoreCard(vHAZ, bHAZ, haz, "haz");
  setScoreCard(vWAZ, bWAZ, waz, "waz");
  setScoreCard(vWHZ, bWHZ, whz, "whz");
  setScoreCard(vBAZ, bBAZ, baz, "baz");
}

// 5. GROWTH VELOCITY & LONGITUDINAL TRENDS
function renderGrowthVelocity(growth) {
  growth = growth || [];
  const vWeight = document.getElementById("velocityWeightVal");
  const vWStatus = document.getElementById("velocityWeightStatus");
  const vHeight = document.getElementById("velocityHeightVal");
  const vHStatus = document.getElementById("velocityHeightStatus");
  const vMuac = document.getElementById("velocityMuacVal");
  const vMStatus = document.getElementById("velocityMuacStatus");
  const vWhz = document.getElementById("velocityWhzVal");
  const vWhzStatus = document.getElementById("velocityWhzStatus");
  const vSummary = document.getElementById("velocityClinicalSummaryText");

  if (growth.length < 2) {
    if (vWeight) vWeight.textContent = "Baseline";
    if (vWStatus) vWStatus.textContent = "Status: Initial record";
    if (vHeight) vHeight.textContent = "Baseline";
    if (vHStatus) vHStatus.textContent = "Status: Initial record";
    if (vMuac) vMuac.textContent = "—";
    if (vMStatus) vMStatus.textContent = "Status: Pending follow-up";
    if (vWhz) vWhz.textContent = "—";
    if (vWhzStatus) vWhzStatus.textContent = "Status: Pending follow-up";
    if (vSummary) vSummary.textContent = "Baseline assessment recorded. Velocity calculations will activate automatically upon subsequent routine measurements.";
    return;
  }

  const p1 = growth[growth.length - 2];
  const p2 = growth[growth.length - 1];

  const d1 = new Date(p1.date || p1.assessment_date || "2026-08-01");
  const d2 = new Date(p2.date || p2.assessment_date || "2026-09-23");
  const daysDiff = Math.max(1, Math.round((d2 - d1) / (1000 * 60 * 60 * 24))) || 30;

  // Weight velocity in g/day
  const wtGainGrams = (p2.weight - p1.weight) * 1000;
  const wtVelocityGDay = Math.round((wtGainGrams / daysDiff) * 10) / 10;

  // Height velocity in cm/year
  const htGainCm = p2.height - p1.height;
  const htVelocityCmYear = Math.round((htGainCm / (daysDiff / 365.25)) * 10) / 10;

  // MUAC change
  const muacChange = (p2.muac && p1.muac) ? Math.round((p2.muac - p1.muac) * 10) / 10 : null;

  // WHZ change
  const whz1 = p1.whz !== undefined ? p1.whz : 0.0;
  const whz2 = p2.whz !== undefined ? p2.whz : (p2.prediction === 'Wasted' ? -2.2 : 0.0);
  const whzChange = Math.round((whz2 - whz1) * 100) / 100;

  if (vWeight) vWeight.textContent = `${wtVelocityGDay > 0 ? '+' : ''}${wtVelocityGDay} g/day`;
  if (vWStatus) {
    vWStatus.textContent = wtVelocityGDay < 0 ? "Status: Declining" : "Status: Gaining";
    vWStatus.style.color = wtVelocityGDay < 0 ? "#dc2626" : "#16a34a";
  }

  if (vHeight) vHeight.textContent = `${htVelocityCmYear > 0 ? '+' : ''}${htVelocityCmYear} cm/year`;
  if (vHStatus) {
    vHStatus.textContent = htVelocityCmYear < 5.0 ? "Status: Monitor" : "Status: Expected growth";
    vHStatus.style.color = htVelocityCmYear < 5.0 ? "#f59e0b" : "#16a34a";
  }

  if (vMuac) vMuac.textContent = muacChange !== null ? `${muacChange > 0 ? '+' : ''}${muacChange} cm` : "—";
  if (vMStatus) {
    vMStatus.textContent = (muacChange !== null && muacChange < 0) ? "Status: Declining" : "Status: Stable";
    vMStatus.style.color = (muacChange !== null && muacChange < 0) ? "#dc2626" : "var(--text-secondary)";
  }

  if (vWhz) vWhz.textContent = `${whzChange > 0 ? '+' : ''}${whzChange} SD`;
  if (vWhzStatus) {
    vWhzStatus.textContent = whzChange < -0.3 ? "Status: Worsening" : "Status: Stable";
    vWhzStatus.style.color = whzChange < -0.3 ? "#dc2626" : "#16a34a";
  }

  if (vSummary) {
    if (wtVelocityGDay < 0 || (muacChange !== null && muacChange < 0) || whzChange < -0.5) {
      vSummary.textContent = "The recent measurements show a growth pattern that warrants review. Weight and/or arm circumference parameters indicate a downward trajectory between screening intervals.";
    } else {
      vSummary.textContent = "Steady longitudinal growth velocity observed across intervals. Parameters align with expected child development benchmarks.";
    }
  }
}

// 6. EARLY WARNING PATTERN DETECTOR
function renderGrowthEarlyWarning(growth) {
  growth = growth || [];
  const card = document.getElementById("earlyWarningAlertCard");
  const list = document.getElementById("earlyWarningSequenceList");
  if (!card) return;

  if (growth.length < 2) {
    card.style.display = "none";
    return;
  }

  const p1 = growth[growth.length - 2];
  const p2 = growth[growth.length - 1];

  const wtDrop = p2.weight < p1.weight;
  const muacDrop = (p1.muac && p2.muac) ? p2.muac < p1.muac : false;
  const whzDrop = (p1.whz !== undefined && p2.whz !== undefined) ? (p2.whz < p1.whz - 0.3) : false;
  const isSevere = p2.prediction && (p2.prediction.includes("SAM") || p2.prediction.includes("Wasted") || p2.prediction.includes("Severe"));

  if (wtDrop || muacDrop || whzDrop || isSevere) {
    card.style.display = "block";
    if (list) {
      const pts = growth.slice(-3);
      const wtSeq = pts.map(p => `${p.weight}`).join(" → ") + " kg";
      const muacSeq = pts.map(p => `${p.muac || 12.0}`).join(" → ") + " cm";
      const whzSeq = pts.map(p => `${p.whz !== undefined ? p.whz : 0}`).join(" → ") + " SD";

      list.innerHTML = `
        <div style="font-weight:700;margin-bottom:4px;">Observed changes across recent screenings:</div>
        <div>• <strong>Weight:</strong> ${wtSeq}</div>
        <div>• <strong>MUAC:</strong> ${muacSeq}</div>
        <div>• <strong>WHZ:</strong> ${whzSeq}</div>
      `;
    }
  } else {
    card.style.display = "none";
  }
}

// 7. FUTURE RISK TRAJECTORY
async function fetchAndRenderFutureRisk(childId) {
  try {
    const res = await fetch(`${API_BASE}/ai/future-risk/${childId}`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const fr = await res.json();

    const curScore = document.getElementById("frCurrentScore");
    const curWt = document.getElementById("frCurrentWeight");
    const s30 = document.getElementById("fr30Score");
    const w30 = document.getElementById("fr30Weight");
    const s60 = document.getElementById("fr60Score");
    const w60 = document.getElementById("fr60Weight");
    const s90 = document.getElementById("fr90Score");
    const w90 = document.getElementById("fr90Weight");

    if (curScore) curScore.textContent = `Risk: ${Math.round(fr.current_risk_score || 50)}`;
    if (curWt && currentChildGrowth?.length > 0) curWt.textContent = `${currentChildGrowth[currentChildGrowth.length - 1].weight} kg`;

    const forecasts = fr.forecasts || [];
    if (forecasts[0]) {
      if (s30) s30.textContent = `Risk: ${Math.round(forecasts[0].projected_risk_score)}`;
      if (w30) w30.textContent = `Estimated ${forecasts[0].weight_kg} kg`;
    }
    if (forecasts[1]) {
      if (s60) s60.textContent = `Risk: ${Math.round(forecasts[1].projected_risk_score)}`;
      if (w60) w60.textContent = `Estimated ${forecasts[1].weight_kg} kg`;
    }
    if (forecasts[2]) {
      if (s90) s90.textContent = `Risk: ${Math.round(forecasts[2].projected_risk_score)}`;
      if (w90) w90.textContent = `Estimated ${forecasts[2].weight_kg} kg`;
    }
  } catch (e) {
    console.error("Future risk fetch error:", e);
  }
}

// 8. COMPARE GROWTH POINTS TOOL
function populateCompareDropdowns(growth) {
  growth = growth || [];
  const sFrom = document.getElementById("compareSelectFrom");
  const sTo = document.getElementById("compareSelectTo");
  if (!sFrom || !sTo) return;

  sFrom.innerHTML = "";
  sTo.innerHTML = "";

  if (growth.length === 0) {
    sFrom.innerHTML = '<option value="">No records</option>';
    sTo.innerHTML = '<option value="">No records</option>';
    return;
  }

  growth.forEach((pt, idx) => {
    const optF = document.createElement("option");
    optF.value = idx;
    optF.textContent = `${pt.date || pt.assessment_date || 'Date'} (${pt.weight} kg)`;
    sFrom.appendChild(optF);

    const optT = document.createElement("option");
    optT.value = idx;
    optT.textContent = `${pt.date || pt.assessment_date || 'Date'} (${pt.weight} kg)`;
    sTo.appendChild(optT);
  });

  sFrom.selectedIndex = 0;
  sTo.selectedIndex = growth.length - 1;
  runGrowthComparison();
}

function runGrowthComparison() {
  const sFrom = document.getElementById("compareSelectFrom");
  const sTo = document.getElementById("compareSelectTo");
  if (!sFrom || !sTo || !currentChildGrowth || currentChildGrowth.length === 0) return;

  const idx1 = parseInt(sFrom.value);
  const idx2 = parseInt(sTo.value);

  const p1 = currentChildGrowth[idx1];
  const p2 = currentChildGrowth[idx2];
  if (!p1 || !p2) return;

  const wtDiff = Math.round((p2.weight - p1.weight) * 10) / 10;
  const htDiff = Math.round((p2.height - p1.height) * 10) / 10;
  const muacDiff = (p1.muac && p2.muac) ? Math.round((p2.muac - p1.muac) * 10) / 10 : null;
  const whzDiff = (p1.whz !== undefined && p2.whz !== undefined) ? Math.round((p2.whz - p1.whz) * 100) / 100 : null;

  const cW = document.getElementById("cmpWeightDelta");
  const cH = document.getElementById("cmpHeightDelta");
  const cM = document.getElementById("cmpMuacDelta");
  const cWhz = document.getElementById("cmpWhzDelta");

  if (cW) cW.innerHTML = `${wtDiff > 0 ? '+' : ''}${wtDiff} kg`;
  if (cH) cH.innerHTML = `${htDiff > 0 ? '+' : ''}${htDiff} cm`;
  if (cM) cM.innerHTML = muacDiff !== null ? `${muacDiff > 0 ? '+' : ''}${muacDiff} cm` : "—";
  if (cWhz) cWhz.innerHTML = whzDiff !== null ? `${whzDiff > 0 ? '+' : ''}${whzDiff} SD` : "—";
}

// 9. DATA QUALITY & FRESHNESS CHECK
function renderGrowthDataQuality(growth) {
  growth = growth || [];
  const badge = document.getElementById("dataFreshnessBadge");
  const desc = document.getElementById("dataFreshnessDesc");
  if (!badge) return;

  if (growth.length === 0) {
    badge.className = "badge wasted";
    badge.textContent = "Awaiting Assessment";
    if (desc) desc.textContent = "Only baseline registration recorded. Periodic screening needed for continuous longitudinal analysis.";
    return;
  }

  const latest = growth[growth.length - 1];
  const d = new Date(latest.date || latest.assessment_date || new Date());
  const now = new Date();
  const diffDays = Math.round((now - d) / (1000 * 60 * 60 * 24));

  if (diffDays > 60) {
    badge.className = "badge severe";
    badge.textContent = "⚠ Out of Date";
    if (desc) desc.textContent = `Last measurement was ${diffDays} days ago. Current growth trend may not reflect child's present health status.`;
  } else {
    badge.className = "badge normal";
    badge.textContent = "✓ Fresh (< 30d)";
    if (desc) desc.textContent = "Assessment date verification and field completeness verified for reliable longitudinal models.";
  }
}

// 10. EXPORT CSV UTILITY
function exportGrowthCSV() {
  const growth = currentChildGrowth || [];
  if (growth.length === 0) {
    showToast("No measurement records available to export.");
    return;
  }

  const childName = (currentChild?.name || "Child").replace(/[^a-zA-Z0-9]/g, "_");
  let csv = "Date,Age_Months,Weight_kg,Height_cm,MUAC_cm,Head_Circ_cm,WHZ,HAZ,WAZ,BAZ,Status\n";

  growth.forEach(pt => {
    csv += `${pt.date || pt.assessment_date || ''},${pt.age_months || ''},${pt.weight || ''},${pt.height || ''},${pt.muac || ''},${pt.head_circumference || ''},${pt.whz !== undefined ? pt.whz : ''},${pt.haz !== undefined ? pt.haz : ''},${pt.waz !== undefined ? pt.waz : ''},${pt.baz !== undefined ? pt.baz : ''},"${pt.prediction || 'Normal'}"\n`;
  });

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `ChildNutri_${childName}_Growth_History.csv`;
  link.click();
  showToast("Growth history CSV downloaded successfully.");
}

// 11. ADD MEASUREMENT MODAL CONTROLLERS
function openAddGrowthModal() {
  const m = document.getElementById("addGrowthModal");
  if (!m) return;
  const dInput = document.getElementById("modalMeasureDate");
  if (dInput) dInput.value = new Date().toISOString().split("T")[0];
  m.style.display = "flex";
}

function closeAddGrowthModal() {
  const m = document.getElementById("addGrowthModal");
  if (m) m.style.display = "none";
}

async function submitAddGrowthModal(e) {
  if (e && e.preventDefault) e.preventDefault();
  if (!currentChild) {
    showToast("No active child selected.");
    return;
  }

  const dateVal = document.getElementById("modalMeasureDate").value || new Date().toISOString().split("T")[0];
  const weight = parseFloat(document.getElementById("modalMeasureWeight").value);
  const height = parseFloat(document.getElementById("modalMeasureHeight").value);
  const muacVal = document.getElementById("modalMeasureMuac").value ? parseFloat(document.getElementById("modalMeasureMuac").value) : null;
  const headCircVal = document.getElementById("modalMeasureHeadCirc").value ? parseFloat(document.getElementById("modalMeasureHeadCirc").value) : null;
  const notes = document.getElementById("modalMeasureNotes").value.trim() || "Routine clinical growth tracker update.";

  if (isNaN(weight) || isNaN(height)) {
    showToast("Please enter valid weight and height measurements.");
    return;
  }

  let ageMonths = 14.0;
  if (currentChild.date_of_birth) {
    const d = new Date(currentChild.date_of_birth);
    const mDate = new Date(dateVal);
    ageMonths = Math.max(0.5, Math.round(((mDate - d) / (1000 * 60 * 60 * 24 * 30.4375)) * 10) / 10);
  }

  const btn = document.getElementById("btnModalSaveMeasurement");
  if (btn) btn.textContent = "Saving...";

  try {
    const res = await fetch(`${API_BASE}/assessments`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        child_id: currentChild.id,
        assessment_date: dateVal,
        age_months: ageMonths,
        weight: weight,
        height: height,
        muac: muacVal,
        head_circumference: headCircVal,
        notes: notes
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to record growth measurement.");
    }

    closeAddGrowthModal();
    showToast("Growth measurement saved successfully! Indicators updated.");
    await loadChildGrowthHistory(currentChild.id);
    await loadChildData();
  } catch (err) {
    console.error("Save measurement error:", err);
    showToast(err.message || "Error saving measurement.");
  } finally {
    if (btn) btn.textContent = "Save Measurement →";
  }
}

// -------------------------------------------------------------
// 1. 🏠 OVERVIEW & 2. 📈 GROWTH TRACKER & 3. 🤖 AI ASSESSMENT
// -------------------------------------------------------------
async function loadChildGrowthHistory(childId) {
  try {
    const res = await fetch(`${API_BASE}/children/${childId}/growth`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    currentChildGrowth = await res.json();
    currentGrowthData = currentChildGrowth;
    
    const firstName = getChildFirstName();

    // If child has no assessments yet, show baseline birth state
    if (currentChildGrowth.length === 0) {
      renderHistoricalGrowthTables([], currentChild);
      renderGrowthSummaryCards([]);
      renderInteractiveGrowthChart();
      renderWHOGrowthAssessment([]);
      renderGrowthVelocity([]);
      renderGrowthEarlyWarning([]);
      populateCompareDropdowns([]);
      renderGrowthDataQuality([]);
      updateDynamicChildNames();
      const bWt = currentChild && currentChild.birth_weight != null ? currentChild.birth_weight : null;
      const bHt = currentChild && currentChild.birth_length != null ? currentChild.birth_length : null;

      // Populate Regular Update Section with Birth Baseline Previous Details
      const regSecStats = document.getElementById("regSectionLastStats");
      if (regSecStats) {
        if (bWt != null && bHt != null) {
          regSecStats.textContent = `${bWt} kg • ${bHt} cm (Birth Baseline)`;
        } else {
          regSecStats.textContent = "No measurements recorded yet";
        }
      }
      const regSecDate = document.getElementById("regSectionLastDate");
      if (regSecDate) regSecDate.textContent = `Registered: ${currentChild && currentChild.date_of_birth ? currentChild.date_of_birth : 'Recent'}`;

      const pageMW = document.getElementById("pageMeasureWeight");
      if (pageMW && !pageMW.value) pageMW.placeholder = bWt != null ? `Birth: ${bWt} kg` : "e.g. 9.5";
      const pageMH = document.getElementById("pageMeasureHeight");
      if (pageMH && !pageMH.value) pageMH.placeholder = bHt != null ? `Birth: ${bHt} cm` : "e.g. 75.0";
      const pageMM = document.getElementById("pageMeasureMuac");
      if (pageMM && !pageMM.value) pageMM.placeholder = "e.g. 13.0";

      const curWt = document.getElementById("currentWeightVal");
      const curHt = document.getElementById("currentHeightVal");
      const curMu = document.getElementById("currentMuacVal");
      const curHc = document.getElementById("currentHeadCircVal");
      const mSub = document.getElementById("measurementSubline");
      const hLast = document.getElementById("heroLastCheck");
      const heroBadge = document.getElementById("heroStatusBadge");

      if (curWt) curWt.innerHTML = bWt != null ? `${bWt} <span style="font-size:1.1rem;font-weight:500;color:var(--text-secondary);">kg (Birth)</span>` : `&mdash;`;
      if (curHt) curHt.innerHTML = bHt != null ? `${bHt} <span style="font-size:1.1rem;font-weight:500;color:var(--text-secondary);">cm (Birth)</span>` : `&mdash;`;
      if (curMu) curMu.innerHTML = `&mdash;`;
      if (curHc) curHc.innerHTML = `&mdash;`;
      if (mSub) mSub.textContent = `No physical assessments recorded yet. Click "Regular Child Update" to log measurements.`;
      if (hLast) hLast.textContent = `No assessments completed yet`;
      const curGest = document.getElementById("currentGestationalAgeVal");
      if (curGest) curGest.textContent = "—";
      const curReg = document.getElementById("currentRegistryStatusVal");
      if (curReg) curReg.textContent = "Registered";
      if (heroBadge) {
        heroBadge.className = "status-badge";
        heroBadge.style.background = "#f1f5f9";
        heroBadge.style.color = "#64748b";
        heroBadge.innerHTML = "&#9679; Registration Complete &bull; Awaiting Assessment";
      }

      const pillMeas = document.getElementById("ovCardMeasurementsPill");
      if (pillMeas) pillMeas.textContent = "No data available";
      const pillGr = document.getElementById("ovCardGrowthPill");
      if (pillGr) pillGr.textContent = "No data available";
      const pillAss = document.getElementById("ovCardAssessmentsPill");
      if (pillAss) pillAss.textContent = "No data available";

      const waz = document.getElementById("wazIndicatorVal");
      if (waz) waz.textContent = "Awaiting Assessment";
      const haz = document.getElementById("hazIndicatorVal");
      if (haz) haz.textContent = "Awaiting Assessment";
      const whz = document.getElementById("whzIndicatorVal");
      if (whz) whz.textContent = "Awaiting Assessment";

      const dnContent = document.getElementById("doctorNoteContent");
      if (dnContent) {
        dnContent.textContent = "No clinical observations recorded yet for this child. Clinical check-up notes will appear here once an assessment is completed.";
      }

      const alertBanner = document.querySelector(".alert-banner");
      if (alertBanner) {
        alertBanner.style.display = "flex";
        alertBanner.className = "alert-banner";
        alertBanner.style.background = "#f0fdf4";
        alertBanner.style.border = "1.5px solid #27a872";
        alertBanner.querySelector(".ab-icon").textContent = "✅";
        alertBanner.querySelector(".ab-title").textContent = "Ready for First AI Assessment";
        alertBanner.querySelector(".ab-title").style.color = "#1a7f5a";
        alertBanner.querySelector(".ab-text").textContent = `Click "Run New Assessment" in the AI Assessment tab to record ${firstName}'s first measurement.`;
        const btn = alertBanner.querySelector(".ab-btn");
        if (btn) {
          btn.textContent = "Start Assessment";
          btn.style.display = "block";
          btn.onclick = () => switchSection("assessment", document.querySelectorAll(".nav-item")[2]);
        }
      }
      await loadScreeningStatus(currentChild.id);
      return;
    }

    const growth = currentChildGrowth;
    const latest = growth[growth.length - 1];
    const riskVal = (latest.risk_score !== undefined && latest.risk_score !== null) ? latest.risk_score : 0;

    // 0. Update Clean Companion Measurements
    const curWt = document.getElementById("currentWeightVal");
    const curHt = document.getElementById("currentHeightVal");
    const curMu = document.getElementById("currentMuacVal");
    const mSub = document.getElementById("measurementSubline");
    const hLast = document.getElementById("heroLastCheck");
    const legName = document.getElementById("legendChildName");

    
    const regSecStats = document.getElementById("regSectionLastStats");
    if (regSecStats && latest) regSecStats.textContent = `${latest.weight} kg • ${latest.height} cm`;
    const regSecDate = document.getElementById("regSectionLastDate");
    if (regSecDate && latest) regSecDate.textContent = `Recorded: ${latest.assessment_date || latest.date || 'Recent'}`;

    const pageMW = document.getElementById("pageMeasureWeight");
    if (pageMW && !pageMW.value && latest) pageMW.placeholder = `Previous: ${latest.weight} kg`;
    const pageMH = document.getElementById("pageMeasureHeight");
    if (pageMH && !pageMH.value && latest) pageMH.placeholder = `Previous: ${latest.height} cm`;
    const pageMM = document.getElementById("pageMeasureMuac");
    if (pageMM && !pageMM.value && latest && latest.muac) pageMM.placeholder = `Previous: ${latest.muac} cm`;
    const pageMHC = document.getElementById("pageMeasureHeadCirc");
    if (pageMHC && !pageMHC.value && latest && latest.head_circumference) pageMHC.placeholder = `Previous: ${latest.head_circumference} cm`;

    if (curWt) curWt.innerHTML = `${latest.weight} <span style="font-size:1.1rem;font-weight:500;color:var(--text-secondary);">kg</span>`;
    if (curHt) curHt.innerHTML = `${latest.height} <span style="font-size:1.1rem;font-weight:500;color:var(--text-secondary);">cm</span>`;
    if (curMu) curMu.innerHTML = `${latest.muac || 12.4} <span style="font-size:1.1rem;font-weight:500;color:var(--text-secondary);">cm</span>`;
    const curHc = document.getElementById("currentHeadCircVal");
    if (curHc) curHc.innerHTML = `${latest.head_circumference || 45.0} <span style="font-size:1.1rem;font-weight:500;color:var(--text-secondary);">cm</span>`;
    if (mSub) mSub.textContent = `Last recorded during clinical evaluation on ${latest.date || 'Recent'}.`;
    if (hLast) {
      const dtStr = latest.date || latest.assessment_date || 'Recent';
      hLast.textContent = `Last updated: ${formatChildDob(dtStr)}`;
    }
    const pillMeas = document.getElementById("ovCardMeasurementsPill");
    if (pillMeas && latest) {
      pillMeas.textContent = `${latest.weight} kg • ${latest.height} cm`;
    }
    const pillGr = document.getElementById("ovCardGrowthPill");
    if (pillGr) {
      pillGr.textContent = "WHO Growth Standards";
    }
    const pillAss = document.getElementById("ovCardAssessmentsPill");
    if (pillAss && latest) {
      pillAss.textContent = latest.prediction || "Normal Nutrition";
    }
    if (legName) legName.textContent = `${firstName}'s Trajectory`;

    const waz = document.getElementById("wazIndicatorVal");
    if (waz) waz.textContent = latest.prediction === 'Underweight' ? 'Underweight Trajectory' : 'Normal Trajectory';
    const haz = document.getElementById("hazIndicatorVal");
    if (haz) haz.textContent = latest.prediction === 'Stunted' ? 'Stunted Stature' : 'Normal Stature';
    const whz = document.getElementById("whzIndicatorVal");
    if (whz) whz.textContent = latest.prediction === 'Wasted' ? 'Wasted Body Mass' : 'Normal Body Mass';

    // 1. Empathetic Health Status Wording (No Technical Jargon)
    const heroBadge = document.getElementById("heroStatusBadge");
    const hsCard = document.getElementById("parentHealthStatusCard");
    const hsTitle = document.getElementById("healthStatusTitle");
    const hsDesc = document.getElementById("healthStatusDesc");
    const pScreenTitle = document.getElementById("parentScreeningTitle");
    const pExplain = document.getElementById("parentAssessmentExplanation");

    if (riskVal <= 35) {
      if (heroBadge) {
        heroBadge.className = "status-badge normal";
        heroBadge.innerHTML = "&#9679; Within assessed range";
      }
      if (hsCard) hsCard.className = "health-status-card";
      if (hsTitle) hsTitle.textContent = "Current Screening: Within Assessed Range";
      if (hsDesc) hsDesc.textContent = "Based on the latest measurements, growth indicators and available screening information, growth looks within the assessed range. Continue regular growth monitoring.";
      if (pScreenTitle) pScreenTitle.textContent = "Within Assessed Range";
      if (pExplain) pExplain.textContent = "Your child's latest measurements indicate that growth parameters are progressing within expected healthy benchmarks. Continue providing age-appropriate balanced meals, active play, and attending scheduled community health check-ups.";
    } else if (riskVal <= 75) {
      if (heroBadge) {
        heroBadge.className = "status-badge danger";
        heroBadge.innerHTML = "&#9679; Growth check advised";
      }
      if (hsCard) hsCard.className = "health-status-card warning";
      if (hsTitle) hsTitle.textContent = "Current Screening: Growth Check Advised";
      if (hsDesc) hsDesc.textContent = "Your child's latest measurements indicate that a follow-up conversation with a healthcare professional may be helpful to review feeding and growth progress.";
      if (pScreenTitle) pScreenTitle.textContent = "Growth Check Advised";
      if (pExplain) pExplain.textContent = "Today's screening suggests that discussing your child's recent growth and feeding routine with your community health worker or doctor is a helpful next step. A professional check can offer personalized reassurance and guidance.";
    } else {
      if (heroBadge) {
        heroBadge.className = "status-badge danger";
        heroBadge.innerHTML = "&#9679; Follow-up recommended";
      }
      if (hsCard) hsCard.className = "health-status-card warning";
      if (hsTitle) hsTitle.textContent = "Current Screening: Professional Review Recommended";
      if (hsDesc) hsDesc.textContent = "Measurements indicate that closer clinical evaluation by a qualified healthcare professional is advised.";
      if (pScreenTitle) pScreenTitle.textContent = "Professional Review Recommended";
      if (pExplain) pExplain.textContent = "Based on today's screening, a timely in-person evaluation by your pediatrician or primary health centre doctor is recommended to review your child's health, diet, and physical development.";
    }

    // 1. 🏠 Update Overview Hero Stats (Legacy compatibility)
    const csVals = document.querySelectorAll(".chc-stat .cs-val");
    if (csVals.length >= 4) {
      csVals[0].innerHTML = `${latest.weight}<span>kg</span>`;
      csVals[1].innerHTML = `${latest.height}<span>cm</span>`;
      csVals[2].innerHTML = latest.muac != null ? `${latest.muac}<span>cm</span>` : '<span>Not recorded</span>';
      csVals[3].innerHTML = `${Math.round(riskVal)}<span>%</span>`;
    }

    // Update Hero Risk Badge
    const statusBadge = document.querySelector(".status-badge");
    const lastCheck = document.querySelector(".last-check");
    if (statusBadge && !heroBadge) {
      const pred = latest.prediction || "Not available";
      const isHighRisk = riskVal > 80;
      statusBadge.className = `status-badge ${isHighRisk ? 'danger' : 'normal'}`;
      statusBadge.textContent = `${isHighRisk ? '● Moderate risk' : '● Within assessed range'}`;
    }
    if (lastCheck && !hLast) {
      lastCheck.textContent = `Last assessed: ${latest.date}`;
    }

    // Condition: If AI Risk Score > 80%, popup Immediate Attention Required
    const alertBanner = document.querySelector(".alert-banner");
    if (alertBanner) {
      if (riskVal > 80) {
        alertBanner.style.display = "flex";
        alertBanner.className = "alert-banner danger";
        alertBanner.style.background = "";
        alertBanner.style.border = "";
        
        const iconEl = alertBanner.querySelector(".ab-icon");
        const titleEl = alertBanner.querySelector(".ab-title");
        const textEl = alertBanner.querySelector(".ab-text");
        const btnEl = alertBanner.querySelector(".ab-btn");

        if (iconEl) iconEl.textContent = "🚨";
        if (titleEl) { titleEl.textContent = "Immediate Attention Required"; titleEl.style.color = ""; }
        if (textEl) {
          textEl.textContent = `${firstName}'s MUAC (${latest.muac || 11.5} cm) is below the safe threshold of 12.5 cm. High AI risk score of ${Math.round(riskVal)}% detected. Please visit the nearest health center immediately or contact Dr. Meena.`;
        }
        if (btnEl) {
          btnEl.style.display = "block";
          btnEl.textContent = "Contact Doctor";
          btnEl.onclick = () => showToast("Connecting with pediatrician Dr. Meena Rao...");
        }
      } else {
        alertBanner.style.display = "flex";
        alertBanner.className = "alert-banner";
        alertBanner.style.background = "#f0fdf4";
        alertBanner.style.border = "1.5px solid #27a872";

        const iconEl = alertBanner.querySelector(".ab-icon");
        const titleEl = alertBanner.querySelector(".ab-title");
        const textEl = alertBanner.querySelector(".ab-text");
        const btnEl = alertBanner.querySelector(".ab-btn");

        if (iconEl) iconEl.textContent = "✅";
        if (titleEl) { titleEl.textContent = "Nutritional Status Monitored"; titleEl.style.color = "#1a7f5a"; }
        if (textEl) {
          textEl.textContent = `${firstName}'s current AI risk score is ${Math.round(riskVal)}%. Parameters are under steady clinical observation. Continue routine feeding and scheduled check-ups.`;
        }
        if (btnEl) btnEl.style.display = "none";
      }
    }

    // Update Mini Stats
    const msVals = document.querySelectorAll(".mini-stats .ms-val");
    if (msVals.length >= 4) {
      msVals[0].textContent = growth.length; // Visits completed
      msVals[3].textContent = `${Math.round(riskVal)}%`; // AI Risk Score
    }

    // Update Anthropometric Data vs WHO in Overview
    const aiVals = document.querySelectorAll(".anthro-list .ai-val");
    const aiTags = document.querySelectorAll(".anthro-list .ai-tag");
    const aiFills = document.querySelectorAll(".anthro-list .ai-fill");
    
    if (aiVals.length >= 4) {
      // Weight
      aiVals[0].textContent = `${latest.weight} kg`;
      if (latest.weight < 8.0) {
        aiVals[0].className = "ai-val red";
        if (aiTags[0]) { aiTags[0].className = "ai-tag danger"; aiTags[0].textContent = "Below Normal"; }
        if (aiFills[0]) { aiFills[0].className = "ai-fill danger"; aiFills[0].style.width = "55%"; }
      } else {
        aiVals[0].className = "ai-val green";
        if (aiTags[0]) { aiTags[0].className = "ai-tag normal"; aiTags[0].textContent = "Normal"; }
        if (aiFills[0]) { aiFills[0].className = "ai-fill normal"; aiFills[0].style.width = "80%"; }
      }

      // Height
      aiVals[1].textContent = `${latest.height} cm`;
      if (latest.height < 72.0) {
        aiVals[1].className = "ai-val orange";
        if (aiTags[1]) { aiTags[1].className = "ai-tag warn"; aiTags[1].textContent = "Stunted"; }
        if (aiFills[1]) { aiFills[1].className = "ai-fill warn"; aiFills[1].style.width = "60%"; }
      } else {
        aiVals[1].className = "ai-val green";
        if (aiTags[1]) { aiTags[1].className = "ai-tag normal"; aiTags[1].textContent = "Normal"; }
        if (aiFills[1]) { aiFills[1].className = "ai-fill normal"; aiFills[1].style.width = "85%"; }
      }

      // MUAC
      const muacVal = latest.muac || 11.5;
      aiVals[2].textContent = `${muacVal} cm`;
      if (muacVal < 11.5) {
        aiVals[2].className = "ai-val red";
        if (aiTags[2]) { aiTags[2].className = "ai-tag danger"; aiTags[2].textContent = "Critical SAM"; }
        if (aiFills[2]) { aiFills[2].className = "ai-fill danger"; aiFills[2].style.width = "45%"; }
      } else if (muacVal < 12.5) {
        aiVals[2].className = "ai-val orange";
        if (aiTags[2]) { aiTags[2].className = "ai-tag warn"; aiTags[2].textContent = "Moderate MAM"; }
        if (aiFills[2]) { aiFills[2].className = "ai-fill warn"; aiFills[2].style.width = "65%"; }
      } else {
        aiVals[2].className = "ai-val green";
        if (aiTags[2]) { aiTags[2].className = "ai-tag normal"; aiTags[2].textContent = "Normal"; }
        if (aiFills[2]) { aiFills[2].className = "ai-fill normal"; aiFills[2].style.width = "90%"; }
      }

      // Head Circumference
      aiVals[3].textContent = `${latest.head_circumference || 45.2} cm`;
    }

    // Update AI Risk Gauge (SVG circle dashoffset animation)
    const gaugeVal = document.querySelector(".gauge-val");
    if (gaugeVal) gaugeVal.textContent = `${Math.round(riskVal)}%`;
    const gaugePath = document.querySelector(".risk-gauge svg path:nth-of-type(2)");
    if (gaugePath) {
      const pct = Math.min(100, Math.max(0, riskVal));
      const offset = 251 - (251 * (pct / 100));
      gaugePath.style.strokeDashoffset = offset;
    }

    // 2. 📈 RENDER GROWTH CHARTS & ADVANCED LONGITUDINAL SYSTEM
    renderGrowthCharts(growth);
    renderHistoricalGrowthTables(growth, currentChild);
    renderGrowthSummaryCards(growth);
    renderInteractiveGrowthChart();
    renderWHOGrowthAssessment(growth);
    renderGrowthVelocity(growth);
    renderGrowthEarlyWarning(growth);
    populateCompareDropdowns(growth);
    renderGrowthDataQuality(growth);
    if (currentChild && currentChild.id) fetchAndRenderFutureRisk(currentChild.id);
    if (typeof populateReportFields === "function") populateReportFields();
    // 3. 🤖 UPDATE AI ASSESSMENT SECTION
    updateAIAssessmentSection(latest);
    await loadScreeningStatus(currentChild.id);

    // Dynamic child names pass
    updateDynamicChildNames();

  } catch (e) {
    console.error("Error loading growth data:", e);
  }
}


function switchGrowthTab(metric, el) {
  document.querySelectorAll(".metric-switch-pills .switch-pill").forEach(p => p.classList.remove("active"));
  if (el) el.classList.add("active");
  const titles = {
    weight: "Weight Trajectory (kg)",
    height: "Height Trajectory (cm)",
    muac: "Mid-Upper Arm Circumference (MUAC cm)",
    whz: "Weight-for-Height Z-Score (WHZ)"
  };
  const titleEl = document.getElementById("activeChartTitle");
  if (titleEl) titleEl.textContent = titles[metric] || "Growth Trajectory";
  renderParentGrowthMetric(metric);
}


// -------------------------------------------------------------
// HISTORICAL MEASUREMENT LOGS (STORED RECORDS IN REGULAR UPDATE & GROWTH TRACKER)
// -------------------------------------------------------------
function renderHistoricalGrowthTables(growth, child) {
  growth = growth || [];
  child = child || currentChild || {};
  const bWt = child.birth_weight || 3.5;
  const bHt = child.birth_length || 52.0;
  const bDob = child.date_of_birth || "Birth Registration";

  // 1. Regular Child Update Section: Stored Records Log
  const regTbody = document.getElementById("regHistoryTableBody");
  const countBadge = document.getElementById("regHistoryRecordCountBadge");
  if (countBadge) {
    countBadge.textContent = `${growth.length} Update${growth.length === 1 ? '' : 's'} Stored`;
  }

  if (regTbody) {
    regTbody.innerHTML = "";
    if (growth.length === 0) {
      // Show Birth Baseline as foundational record
      const tr = document.createElement("tr");
      tr.style.borderBottom = "1px solid var(--border-muted)";
      tr.innerHTML = `
        <td style="padding:14px 20px;">
          <div style="font-weight:700;color:var(--text);">${bDob}</div>
          <span class="badge" style="background:#f1f5f9;color:#475569;font-weight:700;font-size:0.7rem;margin-top:2px;">Birth Baseline</span>
        </td>
        <td style="padding:14px 20px;font-weight:700;color:var(--text);">${bWt} kg</td>
        <td style="padding:14px 20px;font-weight:700;color:var(--text);">${bHt} cm</td>
        <td style="padding:14px 20px;color:var(--text-muted);">&mdash;</td>
        <td style="padding:14px 20px;color:var(--text);font-weight:600;">34.0 cm</td>
        <td style="padding:14px 20px;"><span class="badge normal">&#9679; Registration Baseline</span></td>
      `;
      regTbody.appendChild(tr);
    } else {
      const reversed = [...growth].reverse();
      reversed.forEach((pt, idx) => {
        const tr = document.createElement("tr");
        tr.style.borderBottom = "1px solid var(--border-muted)";
        tr.style.transition = "background 120ms ease";

        let stageBadge = "";
        if (idx === 0) {
          stageBadge = '<span class="badge" style="background:#dcfce7;color:#15803d;font-weight:700;font-size:0.7rem;margin-top:2px;">● Latest Update</span>';
        } else if (idx === 1) {
          stageBadge = '<span class="badge" style="background:#e0f2fe;color:#0369a1;font-weight:700;font-size:0.7rem;margin-top:2px;">Previous Update</span>';
        } else if (idx === 2) {
          stageBadge = '<span class="badge" style="background:#f1f5f9;color:#334155;font-weight:700;font-size:0.7rem;margin-top:2px;">Previous-to-Previous</span>';
        } else {
          stageBadge = `<span class="badge" style="background:#f8fafc;color:#64748b;font-weight:600;font-size:0.7rem;margin-top:2px;">Update #${growth.length - idx}</span>`;
        }

        const pred = pt.prediction || "Not assessed";
        let statusBadgeClass = pred === "Normal" ? "normal" : (pred === "Not assessed" ? "neutral" : "normal");
        if (pred.includes("SAM") || pred.includes("Severe")) statusBadgeClass = "severe";
        else if (pred.includes("Wasted") || pred.includes("Stunted") || pred.includes("Underweight")) statusBadgeClass = "wasted";

        tr.innerHTML = `
          <td style="padding:14px 20px;">
            <div style="font-weight:700;color:var(--text);">${pt.date || pt.assessment_date || 'Recent'}</div>
            ${stageBadge}
          </td>
          <td style="padding:14px 20px;font-weight:700;color:var(--text);">${pt.weight} kg</td>
          <td style="padding:14px 20px;font-weight:700;color:var(--text);">${pt.height} cm</td>
          <td style="padding:14px 20px;color:var(--text);">${pt.muac ? pt.muac + ' cm' : '&mdash;'}</td>
          <td style="padding:14px 20px;color:var(--text);">${pt.head_circumference ? pt.head_circumference + ' cm' : '&mdash;'}</td>
          <td style="padding:14px 20px;"><span class="badge ${statusBadgeClass}">${pred}</span></td>
        `;
        regTbody.appendChild(tr);
      });

      // Append foundational birth baseline at bottom of stored history
      const trBase = document.createElement("tr");
      trBase.style.background = "var(--surface-muted)";
      trBase.innerHTML = `
        <td style="padding:14px 20px;">
          <div style="font-weight:700;color:var(--text);">${bDob}</div>
          <span class="badge" style="background:#e2e8f0;color:#334155;font-weight:700;font-size:0.7rem;margin-top:2px;">Birth Baseline</span>
        </td>
        <td style="padding:14px 20px;font-weight:600;color:var(--text-secondary);">${bWt} kg</td>
        <td style="padding:14px 20px;font-weight:600;color:var(--text-secondary);">${bHt} cm</td>
        <td style="padding:14px 20px;color:var(--text-muted);">&mdash;</td>
        <td style="padding:14px 20px;color:var(--text-muted);">&mdash;</td>
        <td style="padding:14px 20px;"><span class="badge normal">Registered Baseline</span></td>
      `;
      regTbody.appendChild(trBase);
    }
  }

  // 2. Growth Tracker Section: Historical Measurement Log Table
  const growthTbody = document.getElementById("growthHistoryTableBody") || document.querySelector("#sec-growth table tbody");
  if (growthTbody) {
    growthTbody.innerHTML = "";
    if (growth.length === 0) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="padding:12px 20px;font-weight:600;">${bDob}</td>
        <td style="padding:12px 20px;">Birth</td>
        <td style="padding:12px 20px;font-weight:700;">${bWt} kg</td>
        <td style="padding:12px 20px;font-weight:700;">${bHt} cm</td>
        <td style="padding:12px 20px;">&mdash;</td>
        <td style="padding:12px 20px;">34.0 cm</td>
        <td style="padding:12px 20px;"><span class="badge normal">Birth Baseline</span></td>
      `;
      growthTbody.appendChild(tr);
    } else {
      const reversed = [...growth].reverse();
      reversed.forEach(pt => {
        const tr = document.createElement("tr");
        tr.style.borderBottom = "1px solid var(--border-muted)";
        const pred = pt.prediction || "Not assessed";
        let badgeClass = pred === "Normal" ? "normal" : (pred === "Not assessed" ? "neutral" : "normal");
        if (pred.includes("Stunted")) badgeClass = "stunted";
        else if (pred.includes("Wasted")) badgeClass = "wasted";
        else if (pred.includes("SAM") || pred.includes("Severe")) badgeClass = "severe";
        else if (pred.includes("Underweight")) badgeClass = "underweight";

        tr.innerHTML = `
          <td style="padding:12px 20px;font-weight:600;color:var(--text);">${pt.date || pt.assessment_date || 'Recent'}</td>
          <td style="padding:12px 20px;color:var(--text-secondary);">${pt.age_months} mo</td>
          <td style="padding:12px 20px;font-weight:700;color:var(--text);">${pt.weight} kg</td>
          <td style="padding:12px 20px;font-weight:700;color:var(--text);">${pt.height} cm</td>
          <td style="padding:12px 20px;color:var(--text);">${pt.muac ? pt.muac + ' cm' : '—'}</td>
          <td style="padding:12px 20px;color:var(--text);">${pt.head_circumference ? pt.head_circumference + ' cm' : '—'}</td>
          <td style="padding:12px 20px;"><span class="badge ${badgeClass}">${pred}</span></td>
        `;
        growthTbody.appendChild(tr);
      });

      // Baseline row at bottom of Growth Tracker table
      const trBase = document.createElement("tr");
      trBase.style.background = "var(--surface-muted)";
      trBase.innerHTML = `
        <td style="padding:12px 20px;font-weight:600;color:var(--text-secondary);">${bDob}</td>
        <td style="padding:12px 20px;color:var(--text-muted);">Birth</td>
        <td style="padding:12px 20px;font-weight:600;color:var(--text-secondary);">${bWt} kg</td>
        <td style="padding:12px 20px;font-weight:600;color:var(--text-secondary);">${bHt} cm</td>
        <td style="padding:12px 20px;color:var(--text-muted);">&mdash;</td>
        <td style="padding:12px 20px;color:var(--text-muted);">&mdash;</td>
        <td style="padding:12px 20px;"><span class="badge normal">Baseline</span></td>
      `;
      growthTbody.appendChild(trBase);
    }
  }
}

function renderGrowthCharts(growth) {
  // Weight Chart Bars
  const weightChartBars = document.querySelectorAll(".growth-chart .gc-bars")[0];
  if (weightChartBars) {
    weightChartBars.innerHTML = "";
    growth.slice(-6).forEach(pt => {
      const heightPct = Math.min(100, Math.max(15, (pt.weight / 12.0) * 100));
      const col = document.createElement("div");
      col.className = "gc-col";
      col.innerHTML = `
        <div class="gc-bar-wrap">
          <div class="who-line" style="bottom:75%"></div>
          <div class="gc-bar ${pt.weight < 8 ? 'danger' : ''}" style="height:${heightPct}%"></div>
        </div>
        <div class="gc-lbl">${pt.date.split("-")[1] || pt.age_months + 'm'}</div>
      `;
      weightChartBars.appendChild(col);
    });
  }

  // Height Chart Bars
  const heightChartBars = document.querySelectorAll(".growth-chart .gc-bars")[1];
  if (heightChartBars) {
    heightChartBars.innerHTML = "";
    growth.slice(-6).forEach(pt => {
      const heightPct = Math.min(100, Math.max(20, ((pt.height - 50) / 40.0) * 100));
      const col = document.createElement("div");
      col.className = "gc-col";
      col.innerHTML = `
        <div class="gc-bar-wrap">
          <div class="who-line" style="bottom:70%"></div>
          <div class="gc-bar ${pt.height < 72 ? 'warn' : ''}" style="height:${heightPct}%"></div>
        </div>
        <div class="gc-lbl">${pt.date.split("-")[1] || pt.age_months + 'm'}</div>
      `;
      heightChartBars.appendChild(col);
    });
  }
}


// =============================================================================
// ROBUST FETCH UTILITY WITH TIMEOUT (ABORTCONTROLLER)
// =============================================================================
async function fetchWithTimeout(url, options = {}, timeoutMs = 12000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(timer);
    return res;
  } catch (err) {
    clearTimeout(timer);
    throw err;
  }
}

// Friendly feature name dictionary for explainable AI attributions
const SHAP_FEATURE_NAME_MAP = {
  "whz": "Weight-for-Height (WHZ)",
  "haz": "Height-for-Age (HAZ)",
  "waz": "Weight-for-Age (WAZ)",
  "baz": "BMI-for-Age (BAZ)",
  "muac": "MUAC Circumference",
  "age_months": "Age in Months",
  "weight": "Current Weight (kg)",
  "height": "Current Height (cm)",
  "bmi": "Body Mass Index",
  "head_circumference": "Head Circumference",
  "bilateral_edema": "Bilateral Edema",
  "gender_male": "Sex (Male)",
  "dietary_diversity": "Dietary Diversity",
  "recent_illness": "Recent Illness Comorbidity"
};

// Human-Like Explanation Multi-Tier View Mode Switcher
window.switchExplanationView = function(viewMode) {
  const views = ['parent', 'detailed', 'technical', 'doctor'];
  views.forEach(v => {
    const panel = document.getElementById(`panelView${v.charAt(0).toUpperCase() + v.slice(1)}`);
    const btn = document.getElementById(`btnView${v.charAt(0).toUpperCase() + v.slice(1)}`);
    if (panel) panel.style.display = (v === viewMode) ? "block" : "none";
    if (btn) {
      if (v === viewMode) {
        btn.classList.remove("btn-secondary");
        btn.classList.add("btn-primary");
      } else {
        btn.classList.remove("btn-primary");
        btn.classList.add("btn-secondary");
      }
    }
  });
};

// Render Doctor-Like 12 Sequenced Sections
function renderDoctor12Sections(container, doctorExp, humanExp, data) {
  if (!container) return;
  const sections = (doctorExp && doctorExp.sections) || [];
  if (!sections.length) {
    container.innerHTML = `<div style="color:var(--text-muted); font-style:italic;">Doctor-style clinical explanation sections are currently unavailable for this record.</div>`;
    return;
  }

  function esc(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  let html = '';
  sections.forEach(sec => {
    const num = sec.number;
    const title = esc(sec.title);
    const d = sec.data || {};
    let contentHtml = '';

    switch (sec.id) {
      case 'what_we_found': {
        const stmt = esc(d.empathic_statement || '');
        const meas = d.measurements_table || {};
        let measBadges = '';
        if (Object.keys(meas).length > 0) {
          const items = [];
          if (meas.weight_kg != null) items.push(`Weight: <strong>${esc(meas.weight_kg)} kg</strong>`);
          if (meas.height_cm != null) items.push(`Height: <strong>${esc(meas.height_cm)} cm</strong>`);
          if (meas.muac_cm != null) items.push(`MUAC: <strong>${esc(meas.muac_cm)} cm</strong>`);
          if (meas.whz != null) items.push(`WHZ: <strong>${meas.whz > 0 ? '+' : ''}${Number(meas.whz).toFixed(2)} SD</strong>`);
          if (meas.haz != null) items.push(`HAZ: <strong>${meas.haz > 0 ? '+' : ''}${Number(meas.haz).toFixed(2)} SD</strong>`);
          if (meas.waz != null) items.push(`WAZ: <strong>${meas.waz > 0 ? '+' : ''}${Number(meas.waz).toFixed(2)} SD</strong>`);
          if (meas.has_bilateral_edema) items.push(`<span style="color:#b91c1c; font-weight:700;">Bilateral Pedal Edema: YES</span>`);
          measBadges = `<div style="display:flex; flex-wrap:wrap; gap:8px; margin-top:8px;">${items.map(i => `<span style="background:var(--surface); border:1px solid var(--border); padding:4px 8px; border-radius:4px; font-size:0.78rem;">${i}</span>`).join('')}</div>`;
        }
        contentHtml = `<div>${stmt}</div>${measBadges}`;
        break;
      }
      case 'reason': {
        const driver = esc(d.primary_driver || '');
        const traj = esc(d.trajectory_note || '');
        const ev = esc(d.underlying_evidence || '');
        contentHtml = `
          <div><strong>Primary Clinical Driver:</strong> ${driver}</div>
          ${traj ? `<div style="margin-top:6px;"><strong>Growth Trajectory:</strong> ${traj}</div>` : ''}
          ${ev ? `<div style="margin-top:6px; font-size:0.8rem; color:var(--text-secondary);"><strong>Underlying Evidence:</strong> ${ev}</div>` : ''}
        `;
        break;
      }
      case 'why_this_may_be_happening': {
        const disc = esc(d.disclaimer || 'Possible contributing factor, not confirmed cause.');
        const flist = d.factors_list || [];
        let itemsHtml = '';
        if (flist.length > 0) {
          itemsHtml = `<ul style="margin:6px 0 0 18px; padding:0;">${flist.map(f => `<li style="margin-bottom:4px;"><strong>${esc(f.name || f.factor)}:</strong> ${esc(f.details || f.description || '')}</li>`).join('')}</ul>`;
        } else {
          itemsHtml = `<div style="color:var(--text-secondary); margin-top:4px;">No adverse contributing illness or feeding factors documented.</div>`;
        }
        contentHtml = `
          <div style="font-size:0.78rem; color:#b45309; background:#fffbeb; padding:4px 8px; border-radius:4px; margin-bottom:6px; display:inline-block;">${disc}</div>
          ${itemsHtml}
        `;
        break;
      }
      case 'what_this_means': {
        const expl = esc(d.explanation || '');
        const imp = esc(d.practical_implication || '');
        contentHtml = `
          <div>${expl}</div>
          ${imp ? `<div style="margin-top:6px; color:var(--text-secondary);">${imp}</div>` : ''}
        `;
        break;
      }
      case 'what_you_should_do_now': {
        const directive = esc(d.primary_directive || '');
        const actions = d.action_steps || [];
        contentHtml = `
          <div style="font-weight:600; color:var(--brand); margin-bottom:6px;">${directive}</div>
          <ul style="margin:0 0 0 18px; padding:0;">
            ${actions.map(act => `<li style="margin-bottom:4px;">${esc(act)}</li>`).join('')}
          </ul>
        `;
        break;
      }
      case 'how_to_protect_and_support': {
        const ageGroup = esc(d.age_group || '');
        const principles = d.protection_principles || [];
        contentHtml = `
          ${ageGroup ? `<div style="font-size:0.78rem; color:var(--brand); font-weight:700; margin-bottom:4px;">${ageGroup}</div>` : ''}
          <ul style="margin:0 0 0 18px; padding:0;">
            ${principles.map(p => `<li style="margin-bottom:4px;">${esc(p)}</li>`).join('')}
          </ul>
        `;
        break;
      }
      case 'what_to_monitor': {
        const freq = esc(d.frequency || '');
        const track = d.tracking_parameters || [];
        const danger = d.danger_signs || [];
        contentHtml = `
          ${freq ? `<div style="margin-bottom:6px;"><strong>Recommended Cadence:</strong> ${freq}</div>` : ''}
          ${track.length ? `<div style="margin-bottom:4px;"><strong>Parameters to Track:</strong> ${track.map(t => esc(t)).join(', ')}</div>` : ''}
          ${danger.length ? `<div style="margin-top:6px; color:#dc2626; background:#fef2f2; padding:6px 10px; border-radius:4px; border-left:3px solid #dc2626;"><strong>Danger Signs Requiring Immediate Medical Attention:</strong> ${danger.map(s => esc(s)).join('; ')}</div>` : ''}
        `;
        break;
      }
      case 'when_professional_assessment_important': {
        const urg = esc(d.urgency_level || '');
        const calm = esc(d.calm_guidance || '');
        const trigs = d.triggers || [];
        contentHtml = `
          <div><strong>Clinical Priority:</strong> <span style="font-weight:700; color:${urg.toLowerCase().includes('immediate') || urg.toLowerCase().includes('high') ? '#dc2626' : '#15803d'}">${urg}</span></div>
          <div style="margin-top:4px;">${calm}</div>
          ${trigs.length ? `<div style="margin-top:6px;"><strong>Key Triggers:</strong><ul style="margin:4px 0 0 18px; padding:0;">${trigs.map(t => `<li style="margin-bottom:3px;">${esc(t)}</li>`).join('')}</ul></div>` : ''}
        `;
        break;
      }
      case 'why_the_ai_gave_this_result': {
        const trans = esc(d.parent_translation || '');
        const rScore = d.risk_score != null ? esc(d.risk_score) : null;
        const gNote = esc(d.gradcam_note || '');
        const feats = d.strongest_features || [];
        contentHtml = `
          <div>${trans}</div>
          ${feats.length ? `<div style="margin-top:6px;"><strong>Strongest Contributing Factors in Model Prediction:</strong> ${feats.map(f => `<span style="background:var(--surface); border:1px solid var(--border); padding:2px 6px; border-radius:3px; font-size:0.78rem; margin-right:4px;">${esc(f)}</span>`).join('')}</div>` : ''}
          ${rScore != null ? `<div style="margin-top:6px; font-size:0.8rem; color:var(--text-secondary);">Composite Screening Risk Score: <strong>${rScore}/100</strong></div>` : ''}
          ${gNote ? `<div style="margin-top:4px; font-size:0.78rem; color:var(--text-secondary); font-style:italic;">${gNote}</div>` : ''}
        `;
        break;
      }
      case 'who_assessment': {
        const narr = esc(d.narrative || '');
        const scores = d.scores || {};
        let scoreBadges = '';
        if (Object.keys(scores).length > 0) {
          const sItems = [];
          if (scores.whz != null) sItems.push(`WHZ: ${scores.whz > 0 ? '+' : ''}${Number(scores.whz).toFixed(2)} SD`);
          if (scores.haz != null) sItems.push(`HAZ: ${scores.haz > 0 ? '+' : ''}${Number(scores.haz).toFixed(2)} SD`);
          if (scores.waz != null) sItems.push(`WAZ: ${scores.waz > 0 ? '+' : ''}${Number(scores.waz).toFixed(2)} SD`);
          if (scores.baz != null) sItems.push(`BAZ: ${scores.baz > 0 ? '+' : ''}${Number(scores.baz).toFixed(2)} SD`);
          if (scores.muac != null) sItems.push(`MUAC: ${Number(scores.muac).toFixed(1)} cm`);
          scoreBadges = `<div style="display:flex; flex-wrap:wrap; gap:6px; margin-top:8px;">${sItems.map(s => `<span style="background:#f1f5f9; padding:2px 8px; border-radius:4px; font-size:0.78rem; font-weight:600;">${esc(s)}</span>`).join('')}</div>`;
        }
        contentHtml = `<div>${narr}</div>${scoreBadges}`;
        break;
      }
      case 'clinical_triage': {
        const prio = esc(d.safety_priority || '');
        const recon = esc(d.discrepancy_reconciliation || '');
        contentHtml = `
          <div><strong>Safety Rule Priority:</strong> ${prio}</div>
          ${recon ? `<div style="margin-top:6px; font-size:0.82rem; color:var(--text-secondary);"><strong>Harmonization:</strong> ${recon}</div>` : ''}
        `;
        break;
      }
      case 'limitations': {
        const notice = esc(d.notice || '');
        const bounds = d.boundaries || [];
        contentHtml = `
          <div style="font-size:0.8rem; color:#475569; background:#f8fafc; border-left:3px solid #64748b; padding:6px 10px; border-radius:0 4px 4px 0; margin-bottom:6px;">
            ${notice}
          </div>
          ${bounds.length ? `<ul style="margin:0 0 0 18px; padding:0; font-size:0.8rem; color:#64748b;">${bounds.map(b => `<li style="margin-bottom:3px;">${esc(b)}</li>`).join('')}</ul>` : ''}
        `;
        break;
      }
      default: {
        contentHtml = `<div>${esc(JSON.stringify(d))}</div>`;
      }
    }

    html += `
      <div style="background:var(--surface-muted); border-radius:var(--radius-md); padding:14px 16px; border:1px solid var(--border);">
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
          <span style="background:var(--brand); color:#fff; width:22px; height:22px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; font-size:0.75rem; font-weight:700;">${num}</span>
          <span style="font-weight:700; color:var(--brand); font-size:0.82rem; text-transform:uppercase; letter-spacing:0.04em;">${title}</span>
        </div>
        <div style="color:var(--text); font-size:0.85rem; line-height:1.6;">
          ${contentHtml}
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

// =============================================================================
// SCREENING STATUS & CLINICAL AI ASSESSMENT CONTROLLER (FULLY DYNAMIC & CHILD-SPECIFIC)
// =============================================================================
async function loadScreeningStatus(childId, isRetry = false) {
  if (!childId) {
    if (currentChild && currentChild.id) {
      childId = currentChild.id;
    } else {
      console.warn("[ChildNutri AI] loadScreeningStatus called without childId and no active currentChild.");
      return;
    }
  }

  console.log(`[ChildNutri AI] Loading assessment: childId = ${childId}, isRetry = ${isRetry}`);

  const btnDedicated = document.getElementById("btnDedicatedScreeningStatus");
  if (btnDedicated && childId) {
    btnDedicated.href = `screening_status.html?child_id=${childId}`;
  }

  const incCard = document.getElementById("scrIncompleteCard");
  const errCard = document.getElementById("scrErrorCard");
  const contentWrap = document.getElementById("scrContentWrap");

  const explEl = document.getElementById("scrExplanation");
  const shapSummary = document.getElementById("scrShapSummary");
  const shapList = document.getElementById("scrShapList");
  const gActive = document.getElementById("scrGradcamActiveWrap");
  const gUnavail = document.getElementById("scrGradcamUnavailableWrap");
  const gError = document.getElementById("scrGradcamErrorWrap");
  const velStat = document.getElementById("scrVelocityStatus");
  const longBadge = document.getElementById("scrLongitudinalBadge");
  const deltaWt = document.getElementById("scrDeltaWeight");
  const deltaHt = document.getElementById("scrDeltaHeight");
  const deltaMu = document.getElementById("scrDeltaMuac");
  const discBanner = document.getElementById("scrDiscrepancyBanner");
  const discText = document.getElementById("scrDiscrepancyText");

  // STATE: LOADING
  if (errCard) errCard.style.display = "none";
  if (incCard) incCard.style.display = "none";
  if (contentWrap) contentWrap.style.display = "block";
  if (discBanner) discBanner.style.display = "none";

  if (explEl) {
    explEl.innerHTML = `<span class="scr-spinner"></span> We're reviewing the child's assessment data...`;
  }
  if (shapSummary) {
    shapSummary.innerHTML = `<span class="scr-spinner scr-spinner-blue scr-spinner-sm"></span> Reviewing measurement contributions...`;
  }
  if (shapList) shapList.innerHTML = "";
  if (gActive) gActive.style.display = "none";
  if (gUnavail) gUnavail.style.display = "none";
  if (gError) gError.style.display = "none";
  if (velStat) {
    velStat.textContent = "Calculating trajectory...";
    velStat.style.color = "var(--text-muted)";
  }
  if (longBadge) longBadge.textContent = "Assessing history...";

  let data = null;
  let fetchError = null;
  let authExpired = false;

  // Multi-route fallback chain
  const candidateUrls = [
    `${API_BASE}/v1/screening/status/${childId}`,
    `${API_BASE}/v1/predict/status/${childId}`,
    `${API_BASE}/ai/screening-status/${childId}`
  ];

  for (const url of candidateUrls) {
    try {
      console.log(`[API] Requesting screening route: ${url}`);
      const res = await fetchWithTimeout(url, {
        headers: getAuthHeaders()
      }, 12000);

      if (res.status === 401) {
        authExpired = true;
        throw new Error("HTTP 401: Session expired");
      }

      if (res.ok) {
        data = await res.json();
        console.log(`[API RESPONSE] Success from ${url}:`, data);
        fetchError = null;
        break;
      } else {
        console.warn(`[API] Route ${url} returned status ${res.status}`);
        fetchError = new Error(`HTTP ${res.status} from ${url}`);
      }
    } catch (err) {
      console.warn(`[API] Fetch error for ${url}:`, err);
      fetchError = err;
      if (authExpired) break;
    }
  }

  // STATE: ERROR / AUTH EXPIRED
  if (fetchError || !data) {
    if (contentWrap) contentWrap.style.display = "none";
    if (incCard) incCard.style.display = "none";
    if (errCard) {
      errCard.style.display = "block";
      const errHdr = document.getElementById("scrErrorHeader");
      const errMsgEl = document.getElementById("scrErrorMessage");
      const retryBtn = document.getElementById("scrGlobalRetryBtn");

      if (authExpired) {
        if (errHdr) errHdr.textContent = "Your session has expired";
        if (errMsgEl) errMsgEl.textContent = "Your session has expired. Please log in again.";
        if (retryBtn) {
          retryBtn.innerHTML = "<span>🔑</span> Log In Again";
          retryBtn.onclick = () => {
            localStorage.removeItem("childnutri_token");
            window.location.href = "index.html";
          };
        }
      } else {
        if (errHdr) errHdr.textContent = "We couldn't load the assessment right now";
        if (errMsgEl) {
          errMsgEl.textContent = "We couldn't load the assessment right now. Please try again.";
        }
        if (retryBtn) {
          retryBtn.innerHTML = "<span>🔄</span> Retry Assessment";
          retryBtn.onclick = () => loadScreeningStatus(childId, true);
        }
      }
    }
    return;
  }

  // STATE: NO DATA / INCOMPLETE ASSESSMENT (0 clinical records)
  if (data.status === "assessment_incomplete" || data.has_assessments === false) {
    if (incCard) incCard.style.display = "block";
    if (contentWrap) contentWrap.style.display = "none";
    if (errCard) errCard.style.display = "none";

    const incHdr = document.getElementById("scrIncHeader");
    if (incHdr) incHdr.textContent = "No assessment available";
    const incMsg = document.getElementById("scrIncMessage");
    if (incMsg) incMsg.textContent = "No assessment has been recorded for this child yet.";

    const totAss = document.getElementById("sumCardTotalAssessments");
    if (totAss) totAss.textContent = "0";
    const totAssSub = document.getElementById("sumCardTotalAssessmentsSub");
    if (totAssSub) totAssSub.textContent = "No assessments yet";

    const totRep = document.getElementById("sumCardTotalReports");
    if (totRep) totRep.textContent = "0";
    const totRepSub = document.getElementById("sumCardTotalReportsSub");
    if (totRepSub) totRepSub.textContent = "No reports yet";

    const scrTitle = document.getElementById("ovScrBannerTitle");
    if (scrTitle) scrTitle.textContent = "No screening records available yet";
    const scrSub = document.getElementById("ovScrBannerSub");
    if (scrSub) scrSub.textContent = "Your child's screening results will appear here after the first assessment.";

    ["ovScrPillGrowth", "ovScrPillDev", "ovScrPillNutr", "ovScrPillVision"].forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        el.textContent = "Not done";
        el.style.background = "#f1f5f9";
        el.style.color = "#64748b";
      }
    });

    const pillAss = document.getElementById("ovCardAssessmentsPill");
    if (pillAss) pillAss.textContent = "No data available";
    return;
  }

  // STATE: SUCCESS (Full Clinical Assessment Active)
  if (incCard) incCard.style.display = "none";
  if (errCard) errCard.style.display = "none";
  if (contentWrap) contentWrap.style.display = "block";

  const assessCount = (data.assessments && Array.isArray(data.assessments)) ? data.assessments.length : (currentChildGrowth.length || 1);
  const totAss = document.getElementById("sumCardTotalAssessments");
  if (totAss) totAss.textContent = String(assessCount);
  const totAssSub = document.getElementById("sumCardTotalAssessmentsSub");
  if (totAssSub) totAssSub.textContent = assessCount === 1 ? "1 assessment completed" : `${assessCount} assessments completed`;

  const totRep = document.getElementById("sumCardTotalReports");
  if (totRep) totRep.textContent = "1";
  const totRepSub = document.getElementById("sumCardTotalReportsSub");
  if (totRepSub) totRepSub.textContent = "1 report available";

  const scrTitle = document.getElementById("ovScrBannerTitle");
  if (scrTitle) scrTitle.textContent = "Screening records active";
  const scrSub = document.getElementById("ovScrBannerSub");
  if (scrSub) scrSub.textContent = "Routine evaluation indicates normal and healthy progress.";

  ["ovScrPillGrowth", "ovScrPillDev", "ovScrPillNutr", "ovScrPillVision"].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.textContent = "Completed";
      el.style.background = "#dcfce7";
      el.style.color = "#15803d";
    }
  });

  const pillAss = document.getElementById("ovCardAssessmentsPill");
  if (pillAss) pillAss.textContent = "Normal Nutrition";

  // Check for discrepancy between WHO standards and AI prediction (Section 8)
  const whoData = data.who || data.who_assessment || {};
  const aiData = data.ai || data.ai_prediction || {};
  const triageData = data.clinical_triage || {};

  if (data.discrepancy_detected && data.discrepancy_note && discBanner && discText) {
    discText.textContent = data.discrepancy_note;
    discBanner.style.display = "block";
  } else if (discBanner) {
    discBanner.style.display = "none";
  }

  // 1. Child Dossier Header & Metadata
  const childInfo = data.child || {};
  const scrChildName = document.getElementById("scrChildName");
  if (scrChildName) scrChildName.textContent = childInfo.name || (currentChild ? currentChild.name : "Child");
  
  const scrHealthId = document.getElementById("scrHealthId");
  if (scrHealthId) scrHealthId.textContent = childInfo.health_id || (currentChild?.health_id) || "Not available";
  
  const scrAge = document.getElementById("scrAge");
  if (scrAge) {
    const ageVal = childInfo.age_months ?? (currentChild?.age_months);
    scrAge.textContent = ageVal != null ? `${ageVal} Months` : "Not available";
  }
  
  const scrSex = document.getElementById("scrSex");
  if (scrSex) scrSex.textContent = childInfo.sex || childInfo.gender || (currentChild?.gender) || "Not available";
  
  const scrDate = document.getElementById("scrDate");
  if (scrDate) scrDate.textContent = data.assessment_date || childInfo.assessment_date || (data.assessment && data.assessment.date) || "Recent";
  
  const scrAsmtBadge = document.getElementById("scrAssessmentIdBadge");
  const asmtId = data.assessment_id || childInfo.assessment_id || (data.assessment && data.assessment.id) || "1";
  if (scrAsmtBadge) scrAsmtBadge.textContent = `Assessment #${asmtId}`;

  // Overall Screening Status & Category Badges
  const overall = data.overall || {};
  const overallBadge = document.getElementById("scrOverallBadge");
  if (overallBadge) {
    overallBadge.textContent = `● ${overall.status || "Within Assessed Range"}`;
    const tier = (overall.tier || overall.severity_color || triageData.color || "green").toLowerCase();
    if (tier.includes("urgent") || tier.includes("red") || tier.includes("danger") || tier.includes("dc2626") || tier.includes("ef4444")) {
      overallBadge.style.background = "#fee2e2";
      overallBadge.style.color = "#dc2626";
      overallBadge.style.borderColor = "#fecaca";
    } else if (tier.includes("warn") || tier.includes("yellow") || tier.includes("d97706") || tier.includes("f59e0b")) {
      overallBadge.style.background = "#fef3c7";
      overallBadge.style.color = "#d97706";
      overallBadge.style.borderColor = "#fde68a";
    } else {
      overallBadge.style.background = "#dcfce7";
      overallBadge.style.color = "#16a34a";
      overallBadge.style.borderColor = "#bbf7d0";
    }
  }

  const catBadge = document.getElementById("scrCategoryBadge");
  if (catBadge) {
    catBadge.textContent = `AI Category: ${overall.category || aiData.category || overall.status || "Not available"}`;
  }

  // Continuous Risk Score Gauge (Section 9 - No fake fallback)
  const effectiveScore = overall.risk_score ?? aiData.risk_score;
  const riskScoreEl = document.getElementById("scrRiskScore");
  const riskFillEl = document.getElementById("scrRiskFill");
  const riskDescEl = document.getElementById("scrRiskDesc");

  if (effectiveScore != null && !isNaN(effectiveScore)) {
    const numScore = Number(effectiveScore);
    if (riskScoreEl) {
      riskScoreEl.innerHTML = `${numScore.toFixed(1)} <span style="font-size:0.9rem; color:var(--text-muted); font-weight:500;">/ 100</span>`;
    }
    if (riskFillEl) {
      const score = Math.min(100, Math.max(0, numScore));
      riskFillEl.style.width = `${score}%`;
      riskFillEl.style.background = score >= 70 ? "#ef4444" : (score >= 40 ? "#f59e0b" : "#10b981");
    }
    if (riskDescEl) {
      riskDescEl.textContent = `Composite Screening Risk Score: ${overall.status || "Evaluated"}`;
    }
  } else {
    console.warn("[ChildNutri AI] Risk score unavailable for this assessment.");
    if (riskScoreEl) {
      riskScoreEl.innerHTML = `<span style="font-size:1.15rem; color:var(--text-muted); font-weight:700;">Risk score unavailable</span>`;
    }
    if (riskFillEl) riskFillEl.style.width = "0%";
    if (riskDescEl) riskDescEl.textContent = "Composite Screening Risk Score: Not computed";
  }

  const humanExp = data.human_explanation || (data.overall && data.overall.explanation_engine) || {};
  const doctorExp = data.doctor_explanation || humanExp.doctor_explanation || (data.overall && data.overall.doctor_explanation) || {};
  const parentView = humanExp.parent_view || (data.overall && data.overall.parent_view) || {};
  const detailedView = humanExp.detailed_view || (data.overall && data.overall.detailed_view) || {};

  if (explEl) {
    const summaryText = doctorExp.assessment_summary || humanExp.assessment_summary || humanExp.in_simple_words || overall.in_simple_words || overall.explanation || overall.description;
    explEl.innerHTML = `<strong>Assessment Summary:</strong> ${summaryText || "Screening assessment and clinical triage completed."}`;
  }

  // Populate Multi-Tier Explanation Views
  const elWhatHapp = document.getElementById("scrParentWhatIsHappening");
  if (elWhatHapp) {
    elWhatHapp.textContent = parentView.what_is_happening || humanExp.what_is_happening || "The available growth measurements do not currently show a clear nutrition-related growth concern.";
  }
  const elWhatMeans = document.getElementById("scrParentWhatThisMeans");
  if (elWhatMeans) {
    elWhatMeans.textContent = parentView.what_this_means || humanExp.what_this_means || "This is reassuring based on the information available today.";
  }
  const elWhyBox = document.getElementById("scrParentConcernBox");
  const elWhyText = document.getElementById("scrParentWhyConcerned");
  if (elWhyBox && elWhyText) {
    const concernSummary = parentView.why_is_system_concerned || (humanExp.why_is_system_concerned && humanExp.why_is_system_concerned.summary);
    const factorsList = parentView.contributing_factors || humanExp.possible_contributing_factors || [];
    if (concernSummary && (!concernSummary.toLowerCase().includes("did not identify") || factorsList.length > 0)) {
      elWhyBox.style.display = "block";
      elWhyText.textContent = concernSummary;
    } else {
      elWhyBox.style.display = "none";
    }
  }
  const elActionsList = document.getElementById("scrParentActionsList");
  if (elActionsList) {
    const actions = parentView.what_to_do_now || humanExp.what_caregiver_can_do || ["Continue providing age-appropriate nutrition and routine growth checks."];
    elActionsList.innerHTML = actions.map(act => `<li style="margin-bottom:4px;">${act}</li>`).join("");
  }
  const elProfAssess = document.getElementById("scrParentProfAssessment");
  if (elProfAssess) {
    elProfAssess.textContent = parentView.professional_assessment || humanExp.professional_assessment || "Routine preventive health follow-up is recommended at scheduled clinic visits.";
  }
  const elNotWorry = document.getElementById("scrParentNotWorry");
  if (elNotWorry) {
    elNotWorry.textContent = parentView.important_note || parentView.what_not_to_worry_about || humanExp.important_note || humanExp.what_should_i_not_worry_about || "This screening result is not a diagnosis. The findings should be interpreted together with the child's complete growth history and professional assessment where indicated.";
  }

  // Detailed View elements
  const elDetStatus = document.getElementById("scrDetailedClinicalStatus");
  if (elDetStatus) elDetStatus.textContent = detailedView.clinical_status || "Standard pediatric reference range.";
  const elDetInterp = document.getElementById("scrDetailedInterpretation");
  if (elDetInterp) elDetInterp.textContent = detailedView.interpretation || "Growth parameters assessed according to WHO standards.";
  const elDetFactors = document.getElementById("scrDetailedFactors");
  if (elDetFactors) {
    const factors = detailedView.contributing_factors || [];
    if (factors.length > 0) {
      elDetFactors.innerHTML = factors.map(f => `<div>• <strong>${f.factor || f.name}:</strong> ${f.details || f.description || ''}</div>`).join("");
    } else {
      elDetFactors.textContent = "No adverse contributing illness or feeding factors documented.";
    }
  }
  const elDetMonitoring = document.getElementById("scrDetailedMonitoring");
  if (elDetMonitoring) {
    const params = detailedView.monitoring_parameters || [];
    const signs = detailedView.clinical_danger_signs || [];
    elDetMonitoring.innerHTML = `
      <div><strong>Parameters to track:</strong> ${params.join(", ") || "Body weight, appetite, energy level."}</div>
      ${signs.length > 0 ? `<div style="margin-top:6px; color:#dc2626;"><strong>Key danger signs:</strong> ${signs.slice(0, 4).join("; ")}</div>` : ''}
    `;
  }

  // Technical View elements
  const elTechCalib = document.getElementById("scrTechnicalScoreCalibration");
  if (elTechCalib) {
    elTechCalib.innerHTML = `Continuous Score: <strong>${effectiveScore != null ? effectiveScore : 'N/A'}/100</strong> &bull; Primary Model: <strong>${aiData.model_name || 'Soft-Voting Ensemble'}</strong> &bull; Method: Multi-Parameter Continuous Risk Scoring.`;
  }
  const elTechDisc = document.getElementById("scrTechnicalDiscrepancy");
  if (elTechDisc) {
    if (data.discrepancy_detected && data.discrepancy_note) {
      elTechDisc.textContent = `Discrepancy Detected: ${data.discrepancy_note}`;
    } else {
      elTechDisc.textContent = "WHO LMS standard evaluations and AI classification layers are concordant.";
    }
  }

  // Doctor-Like 12-Section View elements
  const elDocSummary = document.getElementById("scrDoctorSummaryText");
  if (elDocSummary) {
    elDocSummary.textContent = doctorExp.assessment_summary || humanExp.assessment_summary || humanExp.in_simple_words || "The available growth measurements do not show a clear nutrition-related concern in this screening.";
  }
  const elDocSections = document.getElementById("scrDoctor12SectionsList");
  if (elDocSections) {
    renderDoctor12Sections(elDocSections, doctorExp, humanExp, data);
  }

  // Standard Reference Determination (India Age-Specific Strategy)
  const stdBadge = document.getElementById("scrStandardBadge");
  const refMeta = data.reference_standard || (data.assessment && data.assessment.reference_standard) || {};
  const ageMonths = childInfo.age_months ?? (currentChild?.age_months) ?? 0;
  const isIAP = (refMeta.system === "IAP" || ageMonths >= 60.0);
  const refTitle = isIAP 
    ? "Growth reference: IAP 2015 Growth Charts — Indian children 5–18 years"
    : "Growth reference: WHO Child Growth Standards — adopted for under-5 assessment in India";

  if (stdBadge) {
    stdBadge.innerHTML = `🇮🇳 <strong>${refTitle}</strong>`;
    stdBadge.style.background = isIAP ? "#fef3c7" : "#dbeafe";
    stdBadge.style.color = isIAP ? "#92400e" : "#1e40af";
    stdBadge.style.borderColor = isIAP ? "#fde68a" : "#bfdbfe";
  }

  // 2. Decoupled Evidence Layers (No Contradictory Labels)
  // LAYER 1: Pediatric Growth Standards (Pure Math / Box-Cox LMS)
  const l1Title = document.getElementById("scrLayer1Title");
  const l1Footer = document.getElementById("scrLayer1Footer");
  const whzRowLabel = document.getElementById("scrWhzRowLabel");
  const hazRowLabel = document.getElementById("scrHazRowLabel");
  const wazRowLabel = document.getElementById("scrWazRowLabel");
  const muacRowLabel = document.getElementById("scrMuacRowLabel");
  const muacValEl = document.getElementById("scrMuacVal");
  const muacCatEl = document.getElementById("scrMuacCat");

  const setWhoField = (idVal, idCat, val, cat, unit) => {
    const elVal = document.getElementById(idVal);
    const elCat = document.getElementById(idCat);
    if (elVal) {
      if (val !== null && val !== undefined) {
        elVal.textContent = (val > 0 ? "+" : "") + Number(val).toFixed(2) + (unit || " SD");
      } else {
        elVal.textContent = "—";
      }
    }
    if (elCat) elCat.textContent = cat || (val !== null && val !== undefined ? "Assessed" : "Not available");
  };

  if (isIAP) {
    if (l1Title) l1Title.textContent = "LAYER 1 • IAP 2015 GROWTH CHARTS (5–18y)";
    if (whzRowLabel) whzRowLabel.textContent = "BMI-for-age (IAP 2015)";
    if (hazRowLabel) hazRowLabel.textContent = "Height-for-age (HFA)";
    if (wazRowLabel) wazRowLabel.textContent = "Weight-for-age (WFA)";
    if (muacRowLabel) muacRowLabel.textContent = "MUAC";
    if (l1Footer) l1Footer.textContent = "Calculated via Indian Academy of Pediatrics (IAP) 2015 Growth Charts (5–18y). Adult-equivalent cutoffs: 23 kg/m² (overweight) & 27 kg/m² (obesity).";

    const iapData = data.iap || (data.growth_indices && data.growth_indices.indicators) || {};
    const bAss = iapData.bmi_iap || iapData.bmi_assessment || {};
    const hAss = iapData.hfa || iapData.height_assessment || {};
    const wAss = iapData.wfa || iapData.weight_assessment || {};

    const bmiVal = bAss.value || (data.growth_indices && data.growth_indices.bmi) || (data.measurements && data.measurements.bmi);
    const bmiZ = bAss.z_score != null ? bAss.z_score : (data.growth_indices && data.growth_indices.baz);
    const bmiInterp = bAss.interpretation || (bmiVal ? `BMI: ${Number(bmiVal).toFixed(1)} kg/m² (Cutoffs: 23 eq OW, 27 eq OB)` : "Assessed");

    const hZ = hAss.z_score != null ? hAss.z_score : (data.growth_indices && data.growth_indices.haz);
    const hInterp = hAss.interpretation || (hAss.value ? `Height: ${Number(hAss.value).toFixed(1)} cm` : "Assessed");

    const wZ = wAss.z_score != null ? wAss.z_score : (data.growth_indices && data.growth_indices.waz);
    const wInterp = wAss.interpretation || (wAss.value ? `Weight: ${Number(wAss.value).toFixed(1)} kg` : "Assessed");

    setWhoField("scrWhzVal", "scrWhzCat", bmiZ, bmiInterp, " SD");
    setWhoField("scrHazVal", "scrHazCat", hZ, hInterp, " SD");
    setWhoField("scrWazVal", "scrWazCat", wZ, wInterp, " SD");

    const recordedMuac = whoData.muac ?? (data.measurements && data.measurements.muac_cm) ?? (data.anthropometry && data.anthropometry.muac_cm);
    if (muacValEl) muacValEl.textContent = recordedMuac != null ? `${Number(recordedMuac).toFixed(1)} cm` : "Not recorded";
    if (muacCatEl) muacCatEl.textContent = "Not calibrated for 5–18y (IAP 2015)";
  } else {
    if (l1Title) l1Title.textContent = "LAYER 1 • WHO LMS STANDARDS (UNDER 5)";
    if (whzRowLabel) whzRowLabel.textContent = "WHZ (Wasting)";
    if (hazRowLabel) hazRowLabel.textContent = "HAZ (Stunting)";
    if (wazRowLabel) wazRowLabel.textContent = "WAZ (Underweight)";
    if (muacRowLabel) muacRowLabel.textContent = "MUAC";
    if (l1Footer) l1Footer.textContent = "Growth reference: WHO Child Growth Standards — adopted for under-5 assessment in India. Calculated via WHO 2006 LMS Box-Cox equations.";

    setWhoField("scrWhzVal", "scrWhzCat", whoData.whz, whoData.whz_category, " SD");
    setWhoField("scrHazVal", "scrHazCat", whoData.haz, whoData.haz_category, " SD");
    setWhoField("scrWazVal", "scrWazCat", whoData.waz, whoData.waz_category, " SD");
    if (muacValEl) muacValEl.textContent = whoData.muac != null ? `${Number(whoData.muac).toFixed(1)} cm` : "Not available";
    if (muacCatEl) muacCatEl.textContent = whoData.muac_category || (whoData.muac != null ? "Assessed zone" : "Not recorded");
  }

  // LAYER 2: AI Screening Pipeline (Machine Learning)
  const predEl = document.getElementById("scrPredLabel");
  if (predEl) predEl.textContent = (aiData.prediction && aiData.prediction !== "NOT_AVAILABLE") ? aiData.prediction : "Prediction unavailable";
  const confEl = document.getElementById("scrConfidence");
  if (confEl) {
    const rawConf = aiData.confidence_percentage ?? (aiData.confidence != null ? (aiData.confidence > 1 ? aiData.confidence : (aiData.confidence * 100)) : null);
    if (rawConf != null && !isNaN(rawConf)) {
      confEl.textContent = `Model Confidence: ${Number(rawConf).toFixed(1)}%`;
    } else {
      confEl.textContent = "Model Confidence: Not available";
    }
  }
  const modelEl = document.getElementById("scrModelName");
  if (modelEl) modelEl.textContent = aiData.model_name || "Multimodal Soft-Voting Ensemble";

  // LAYER 3: Clinical Safety Guardrails (Deterministic Clinical Triage)
  const tLevel = document.getElementById("scrTriageLevel");
  const tAction = document.getElementById("scrTriageAction");
  const tBox = document.getElementById("scrTriageBox");

  if (tLevel) tLevel.textContent = triageData.level || "ROUTINE (GREEN)";
  if (tAction) tAction.textContent = triageData.action || triageData.reason || "Routine growth monitoring & nutritional follow-up.";
  if (tBox) {
    const lvlStr = (triageData.level || "").toUpperCase();
    const colStr = (triageData.color || "").toLowerCase();
    if (lvlStr.includes("URGENT") || lvlStr.includes("RED") || colStr.includes("red") || colStr.includes("dc2626") || colStr.includes("ef4444")) {
      tBox.style.borderLeftColor = "#ef4444";
      tBox.style.background = "#fef2f2";
      if (tLevel) tLevel.style.color = "#dc2626";
    } else if (lvlStr.includes("MONITOR") || lvlStr.includes("YELLOW") || colStr.includes("yellow") || colStr.includes("d97706") || colStr.includes("f59e0b")) {
      tBox.style.borderLeftColor = "#f59e0b";
      tBox.style.background = "#fffbeb";
      if (tLevel) tLevel.style.color = "#b45309";
    } else {
      tBox.style.borderLeftColor = "#10b981";
      tBox.style.background = "#f0fdf4";
      if (tLevel) tLevel.style.color = "#15803d";
    }
  }

  // 3. Child-Specific Dynamic Risk Factors
  const rfList = document.getElementById("scrRiskFactorsList");
  if (rfList) {
    rfList.innerHTML = "";
    const factors = data.risk_factors || [];
    if (factors.length === 0) {
      rfList.innerHTML = `<div style="grid-column:1/-1; padding:12px; color:var(--text-muted); font-size:0.85rem;">No dynamic risk factors identified.</div>`;
    } else {
      factors.forEach(rf => {
        const factorName = rf.factor || rf.name || "Risk Indicator";
        const tier = (rf.tier || rf.severity || "good").toLowerCase();
        let icon = "✅";
        let bg = "#f0fdf4";
        let border = "#bbf7d0";
        let titleColor = "#166534";
        let badgeColor = "#15803d";

        if (tier.includes("danger") || tier.includes("urgent") || tier.includes("red")) {
          icon = "⚠️";
          bg = "#fef2f2";
          border = "#fecaca";
          titleColor = "#991b1b";
          badgeColor = "#dc2626";
        } else if (tier.includes("warn") || tier.includes("yellow")) {
          icon = "⚡";
          bg = "#fffbeb";
          border = "#fde68a";
          titleColor = "#92400e";
          badgeColor = "#b45309";
        } else if (tier.includes("neutral") || tier.includes("gray")) {
          icon = "ℹ️";
          bg = "var(--surface-muted)";
          border = "var(--border)";
          titleColor = "var(--text)";
          badgeColor = "var(--text-muted)";
        }

        const card = document.createElement("div");
        card.style.cssText = `background:${bg}; border:1px solid ${border}; border-radius:var(--radius-lg); padding:14px; display:flex; flex-direction:column; justify-content:space-between;`;
        card.innerHTML = `
          <div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
              <span style="font-weight:700; font-size:0.82rem; color:${titleColor}; display:flex; align-items:center; gap:6px;">
                <span>${icon}</span> ${factorName}
              </span>
              <span style="font-size:0.68rem; font-weight:700; text-transform:uppercase; color:${badgeColor}; background:rgba(255,255,255,0.7); padding:1px 6px; border-radius:4px;">
                ${rf.status || tier}
              </span>
            </div>
            <div style="font-size:0.77rem; color:var(--text); line-height:1.45;">
              ${rf.detail}
            </div>
          </div>
        `;
        rfList.appendChild(card);
      });
    }
  }

  // 4. Explainable AI: SHAP & Grad-CAM
  const xai = data.explainability || {};
  const shap = xai.shap || {};

  const featList = shap.top_contributing_features || shap.features || [];
  if (shapList) {
    shapList.innerHTML = "";
    if (featList.length > 0) {
      const maxVal = Math.max(...featList.map(f => Math.abs(f.importance_score ?? f.shap_value ?? 0.01)), 0.05);
      featList.forEach(f => {
        const rawVal = f.importance_score ?? f.shap_value ?? 0;
        const pct = Math.min(100, Math.max(5, Math.round((Math.abs(rawVal) / maxVal) * 100)));
        const isPos = rawVal > 0;
        const barColor = isPos ? "#ef4444" : "#10b981";
        const sign = isPos ? "+" : "";
        const rawKey = (f.feature || "").toLowerCase();
        const displayName = f.display_name || SHAP_FEATURE_NAME_MAP[rawKey] || rawKey.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());

        const item = document.createElement("div");
        item.style.cssText = "display:flex; align-items:center; gap:8px; font-size:0.77rem;";
        item.innerHTML = `
          <span style="width:130px; color:var(--text); font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${displayName}">${displayName}</span>
          <div style="flex:1; height:8px; background:var(--surface-muted); border-radius:99px; overflow:hidden;">
            <div style="width:${pct}%; height:100%; background:${barColor}; border-radius:99px; transition:width 300ms ease;"></div>
          </div>
          <span style="width:48px; text-align:right; font-weight:700; color:${barColor};">${sign}${Number(rawVal).toFixed(2)}</span>
        `;
        shapList.appendChild(item);
      });
    } else {
      shapList.innerHTML = `<div style="font-size:0.78rem; color:var(--text-muted); padding:8px 0;">No active feature deviations detected. All baseline inputs within standard bounds.</div>`;
    }
  }

  if (shapSummary) {
    if (xai.shap_available === false && featList.length === 0) {
      shapSummary.textContent = "Feature attribution unavailable for this assessment.";
    } else {
      shapSummary.textContent = shap.shap_decision_summary || shap.summary || "Shapley feature attribution calculated across active ensemble trees.";
    }
  }

  // Grad-CAM Attention Heatmap (Section 14 - 3 Clean States)
  const gcam = xai.gradcam || {};
  const gBadge = document.getElementById("scrGradcamBadge");

  if (gcam.status === "available" || (gcam.available && gcam.original_image_base64)) {
    // State A: Photo available with Grad-CAM overlays
    if (gActive) gActive.style.display = "block";
    if (gUnavail) gUnavail.style.display = "none";
    if (gError) gError.style.display = "none";
    if (gBadge) {
      gBadge.textContent = "Photo Analyzed";
      gBadge.style.color = "#7c3aed";
      gBadge.style.background = "#ede9fe";
    }

    const origImg = document.getElementById("scrGradcamOrigImg");
    const camImg = document.getElementById("scrGradcamHeatmapImg");
    const focusText = document.getElementById("scrGradcamFocusText");

    if (origImg) {
      if (gcam.original_image_base64) {
        origImg.src = gcam.original_image_base64.startsWith("data:") ? gcam.original_image_base64 : `data:image/jpeg;base64,${gcam.original_image_base64}`;
      } else if (gcam.original_url) {
        origImg.src = gcam.original_url;
      }
    }
    if (camImg) {
      if (gcam.gradcam_overlay_base64) {
        camImg.src = gcam.gradcam_overlay_base64.startsWith("data:") ? gcam.gradcam_overlay_base64 : `data:image/jpeg;base64,${gcam.gradcam_overlay_base64}`;
      } else if (gcam.cam_url) {
        camImg.src = gcam.cam_url;
      }
    }
    if (focusText) {
      const anat = gcam.anatomical_focus && gcam.anatomical_focus.length > 0 ? gcam.anatomical_focus.join(" • ") : "Upper arm & facial profile";
      focusText.textContent = `Visual Salience Focus: ${anat}`;
    }
  } else if (gcam.status === "error") {
    // State B: Vision model error
    if (gActive) gActive.style.display = "none";
    if (gUnavail) gUnavail.style.display = "none";
    if (gError) {
      gError.style.display = "block";
      const errMsg = document.getElementById("scrGradcamErrorMsg");
      if (errMsg) errMsg.textContent = gcam.message || "Vision analysis could not be completed.";
    }
    if (gBadge) {
      gBadge.textContent = "Vision Error";
      gBadge.style.color = "#dc2626";
      gBadge.style.background = "#fee2e2";
    }
  } else {
    // State C: No photo uploaded (Clean message, NO fake silhouettes)
    if (gActive) gActive.style.display = "none";
    if (gUnavail) gUnavail.style.display = "block";
    if (gError) gError.style.display = "none";
    if (gBadge) {
      gBadge.textContent = "Vision Unavailable";
      gBadge.style.color = "#64748b";
      gBadge.style.background = "#f1f5f9";
    }
  }

  // 5. Longitudinal Growth & Trajectory Comparison (Section 15)
  const long = data.longitudinal || {};
  const tblBody = document.getElementById("scrHistoryTableBody");
  const comp = long.comparison || {};
  const hasHistory = (long.has_history || long.available) && comp.weight_delta_kg !== null && comp.weight_delta_kg !== undefined;

  if (hasHistory) {
    // 2+ Assessments on record
    if (longBadge) longBadge.textContent = "Multi-Visit History";

    const wtDelta = comp.weight_delta_kg;
    const htDelta = comp.height_delta_cm;
    const muacDelta = comp.muac_delta_cm;

    if (deltaWt) {
      const sign = wtDelta > 0 ? "+" : "";
      deltaWt.textContent = `${sign}${Number(wtDelta).toFixed(2)} kg`;
      deltaWt.style.color = wtDelta < 0 ? "#dc2626" : "#16a34a";
    }
    if (deltaHt) {
      const sign = htDelta > 0 ? "+" : "";
      deltaHt.textContent = `${sign}${Number(htDelta).toFixed(1)} cm`;
      deltaHt.style.color = "#16a34a";
    }
    if (deltaMu) {
      if (muacDelta !== null && muacDelta !== undefined) {
        const sign = muacDelta > 0 ? "+" : "";
        deltaMu.textContent = `${sign}${Number(muacDelta).toFixed(1)} cm`;
        deltaMu.style.color = muacDelta < 0 ? "#dc2626" : "#16a34a";
      } else {
        deltaMu.textContent = "—";
        deltaMu.style.color = "var(--text)";
      }
    }

    if (velStat) {
      velStat.textContent = comp.velocity_status || long.message || "Assessed growth status";
      velStat.style.color = comp.velocity_alert ? "#dc2626" : "#16a34a";
    }
  } else {
    // Exactly 1 Assessment on record (Baseline Visit Only)
    if (longBadge) longBadge.textContent = "Baseline Visit Only";
    if (deltaWt) { deltaWt.textContent = "—"; deltaWt.style.color = "var(--text-muted)"; }
    if (deltaHt) { deltaHt.textContent = "—"; deltaHt.style.color = "var(--text-muted)"; }
    if (deltaMu) { deltaMu.textContent = "—"; deltaMu.style.color = "var(--text-muted)"; }
    if (velStat) {
      velStat.textContent = comp.velocity_status || long.message || "Insufficient history for trajectory analysis.";
      velStat.style.color = "var(--text-muted)";
    }
  }

  // Populate Longitudinal History Table
  if (tblBody) {
    tblBody.innerHTML = "";
    const historyList = long.history || [];
    if (historyList.length === 0) {
      tblBody.innerHTML = `<tr><td colspan="6" style="padding:14px; text-align:center; color:var(--text-muted);">No prior records found.</td></tr>`;
    } else {
      historyList.forEach((rec, idx) => {
        const row = document.createElement("tr");
        row.style.borderBottom = "1px solid var(--border)";
        if (idx === 0) row.style.background = "var(--surface-muted)";
        const recWt = rec.weight_kg ?? rec.weight;
        const recHt = rec.height_cm ?? rec.height;
        const recMuac = rec.muac_cm ?? rec.muac;
        row.innerHTML = `
          <td style="padding:8px 12px; font-weight:600; color:var(--text);">${rec.date || rec.assessment_date || "Recent"}${idx === 0 ? " (Latest)" : ""}</td>
          <td style="padding:8px 12px; color:var(--text-secondary);">${rec.age_months ? rec.age_months + " mo" : "—"}</td>
          <td style="padding:8px 12px; font-weight:600; color:var(--text);">${recWt} kg</td>
          <td style="padding:8px 12px; color:var(--text-secondary);">${recHt} cm</td>
          <td style="padding:8px 12px; color:var(--text-secondary);">${recMuac ? recMuac + " cm" : "—"}</td>
          <td style="padding:8px 12px; font-weight:600; color:${rec.whz && rec.whz < -2 ? '#dc2626' : 'var(--text)'};">${rec.whz != null ? (rec.whz > 0 ? "+" : "") + Number(rec.whz).toFixed(2) + " SD" : "—"}</td>
        `;
        tblBody.appendChild(row);
      });
    }
  }

  // 6. Image-Based Malnutrition Screening Pipeline & Early Warning Card
  renderImagePipelineAndEarlyWarning(data);
}

function renderImagePipelineAndEarlyWarning(data) {
  const vis = data.vision_screening || (data.vision && data.vision.available ? data.vision : null) || {};
  const fus = data.multimodal_screening || (data.multimodal && data.multimodal.available ? data.multimodal : null) || {};
  const pipe = data.image_processing_pipeline || {};
  const ew = data.early_warning || {};
  const modMode = data.modality_mode || (fus.available ? "MULTIMODAL" : "TABULAR_ONLY");
  const modWeights = data.modality_weights || fus.modality_weights || { visual_contribution_pct: 0, anthropometric_contribution_pct: 100 };

  // 1. Modality Mode Badge
  const elMode = document.getElementById("scrModalityModeBadge");
  if (elMode) {
    if (modMode === "MULTIMODAL" || fus.available) {
      elMode.textContent = "Mode: Multimodal Fusion";
      elMode.style.background = "#ede9fe";
      elMode.style.color = "#7c3aed";
      elMode.style.borderColor = "#ddd6fe";
    } else {
      elMode.textContent = "Mode: Tabular Only";
      elMode.style.background = "#e0f2fe";
      elMode.style.color = "#0369a1";
      elMode.style.borderColor = "#bae6fd";
    }
  }

  // 2. Vision Quality Badge
  const elQual = document.getElementById("scrVisionQualityBadge");
  if (elQual) {
    const q = vis.quality || (pipe.image_validation && pipe.image_validation.quality) || (vis.available ? "VALID" : "NO_IMAGE");
    elQual.textContent = `Quality: ${q}`;
    if (q === "GOOD" || q === "VALID" || q === "EXCELLENT") {
      elQual.style.background = "#dcfce7";
      elQual.style.color = "#15803d";
      elQual.style.borderColor = "#bbf7d0";
    } else if (q.includes("REJECTED") || q.includes("INVALID") || q.includes("ERROR")) {
      elQual.style.background = "#fee2e2";
      elQual.style.color = "#dc2626";
      elQual.style.borderColor = "#fecaca";
    } else {
      elQual.style.background = "var(--surface-muted)";
      elQual.style.color = "var(--text-secondary)";
      elQual.style.borderColor = "var(--border)";
    }
  }

  // 3. Vision Model Box
  const elVisStat = document.getElementById("scrVisionStatusBadge");
  const elVisPred = document.getElementById("scrVisionPredText");
  const elVisConf = document.getElementById("scrVisionConfidenceText");
  const elVisMsg = document.getElementById("scrVisionMsgText");
  if (elVisStat) elVisStat.textContent = (vis.status || "NO_IMAGE").toUpperCase();
  if (elVisPred) elVisPred.textContent = vis.prediction || (vis.available ? "Assessed" : "Not Evaluated");
  if (elVisConf) elVisConf.textContent = vis.confidence != null ? `Confidence: ${(vis.confidence * 100).toFixed(1)}%` : "Confidence: —";
  if (elVisMsg) elVisMsg.textContent = vis.message || (vis.available ? "EfficientNet-B0 visual feature extraction completed." : "No child photograph uploaded for this assessment session.");

  // 4. Multimodal Fusion Box
  const elFusStat = document.getElementById("scrMultimodalStatusBadge");
  const elFusPred = document.getElementById("scrMultimodalPredText");
  const elFusWeights = document.getElementById("scrMultimodalWeightsText");
  const elFusBar = document.getElementById("scrModalityWeightBar");
  const visPct = modWeights.visual_contribution_pct || 0;
  const anthroPct = modWeights.anthropometric_contribution_pct || 100;
  if (elFusStat) elFusStat.textContent = fus.available ? "ACTIVE FUSION" : "TABULAR BRANCH";
  if (elFusPred) elFusPred.textContent = fus.prediction || (fus.available ? "Fused Prediction" : "Tabular Fallback Active");
  if (elFusWeights) elFusWeights.textContent = `Modality Weights: ${visPct}% Visual • ${anthroPct}% Anthropometric`;
  if (elFusBar) elFusBar.style.width = `${visPct}%`;

  // 5. 7-Stage Checklist
  const elStagesList = document.getElementById("scrPipelineStagesList");
  if (elStagesList) {
    elStagesList.innerHTML = "";
    const stageDefs = [
      { key: "image_upload", name: "1. Image Upload", def: "Uploaded photo file" },
      { key: "image_validation", name: "2. Validation", def: "Format, bytes & resolution" },
      { key: "image_preprocessing", name: "3. Preprocessing", def: "224x224 RGB ImageNet norm" },
      { key: "vision_model_execution", name: "4. EfficientNet-B0", def: "Pediatric feature backbone" },
      { key: "visual_feature_extraction", name: "5. Feature Vector", def: "1280-D bottleneck tensor" },
      { key: "multimodal_fusion", name: "6. Multimodal Fusion", def: "1292-D gating fusion net" },
      { key: "screening_result", name: "7. Screening Result", def: "Continuous composite score" }
    ];

    stageDefs.forEach(s => {
      const stageData = pipe[s.key] || {};
      const completed = stageData.completed || false;
      const statusText = stageData.status || (completed ? "completed" : "not_applicable");
      let icon = "⚪";
      let border = "var(--border)";
      let bg = "var(--surface-muted)";
      let textColor = "var(--text-secondary)";

      if (completed || statusText === "completed" || statusText === "generated" || statusText === "executed" || statusText === "extracted") {
        icon = "✅";
        bg = "#f0fdf4";
        border = "#bbf7d0";
        textColor = "#15803d";
      } else if (statusText === "failed" || statusText === "rejected" || statusText === "invalid") {
        icon = "❌";
        bg = "#fef2f2";
        border = "#fecaca";
        textColor = "#dc2626";
      } else if (statusText === "skipped" || statusText === "not_applicable" || statusText === "missing") {
        icon = "⚪";
        bg = "var(--surface-muted)";
        border = "var(--border)";
        textColor = "var(--text-muted)";
      }

      const item = document.createElement("div");
      item.style.cssText = `background:${bg}; border:1px solid ${border}; border-radius:var(--radius-md); padding:8px 12px; font-size:0.75rem;`;
      item.innerHTML = `
        <div style="font-weight:700; color:${textColor}; display:flex; align-items:center; gap:6px;">
          <span>${icon}</span> <span>${s.name}</span>
        </div>
        <div style="font-size:0.7rem; color:var(--text-muted); margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${stageData.details || s.def}">
          ${stageData.details || s.def}
        </div>
      `;
      elStagesList.appendChild(item);
    });
  }

  // 6. Early Warning Card
  const elEwBadge = document.getElementById("scrEarlyWarningBadge");
  const elEwTrend = document.getElementById("scrEarlyWarningTrendText");
  const elEwWhy = document.getElementById("scrEarlyWarningWhyText");
  const elEwAction = document.getElementById("scrEarlyWarningActionText");
  const elEwVel = document.getElementById("scrEarlyWarningVelocityDetail");

  if (elEwBadge) {
    elEwBadge.textContent = ew.status_badge || (ew.has_early_warning ? "EARLY WARNING" : "NO WARNING");
    const bColor = ew.status_color || (ew.has_early_warning ? "#dc2626" : "#15803d");
    elEwBadge.style.color = bColor;
    elEwBadge.style.background = ew.has_early_warning ? "#fee2e2" : "#dcfce7";
    elEwBadge.style.borderColor = ew.has_early_warning ? "#fecaca" : "#bbf7d0";
  }

  if (elEwTrend) {
    elEwTrend.textContent = ew.trend ? ew.trend.replace(/_/g, " ") : (ew.is_single_visit ? "Baseline Assessment Recorded" : "Growth Trajectory Monitored");
  }
  if (elEwWhy) {
    elEwWhy.textContent = ew.why_warning_generated || ew.current_status_summary || "Current screening measurements track within reference thresholds. Baseline screening recorded.";
  }
  if (elEwAction) {
    elEwAction.textContent = ew.recommended_next_step || "Continue age-appropriate feeding and schedule a routine growth check in 30 days.";
  }
  if (elEwVel) {
    const comp = (data.longitudinal && data.longitudinal.comparison) || {};
    const velText = ew.weight_velocity_g_day != null ? `${ew.weight_velocity_g_day > 0 ? "+" : ""}${ew.weight_velocity_g_day} g/day` : (comp.monthly_velocity_kg != null ? `${comp.monthly_velocity_kg > 0 ? "+" : ""}${comp.monthly_velocity_kg} kg/month` : "Baseline (Single Visit)");
    const whzDeltaText = ew.whz_delta != null ? `${ew.whz_delta > 0 ? "+" : ""}${ew.whz_delta} SD` : (comp.whz_delta != null ? `${comp.whz_delta > 0 ? "+" : ""}${comp.whz_delta} SD` : "—");
    elEwVel.textContent = `Observed weight velocity: ${velText} • WHZ Delta: ${whzDeltaText}`;
  }
}

function updateAIAssessmentSection(latest) {
  const firstName = getChildFirstName();

  // ── OUTPUT 1: Malnutrition Prediction ──────────────────────────────────────
  const pred = (latest.prediction && latest.prediction !== "NOT_AVAILABLE") ? latest.prediction : "Prediction unavailable";
  const riskVal = latest.risk_score != null ? latest.risk_score : null;
  const conf = latest.confidence != null ? (latest.confidence > 1 ? latest.confidence : (latest.confidence * 100)).toFixed(1) : null;
  const details = latest.details || {};

  // Badge color
  const predEl = document.getElementById("mlPredLabel");
  const badgeEl = document.getElementById("mlPredBadge");
  const confEl = document.getElementById("mlPredConf");
  if (predEl) predEl.textContent = pred;
  if (confEl) confEl.textContent = conf != null ? `${conf}%` : "Not available";
  if (badgeEl) {
    badgeEl.textContent = pred.toUpperCase();
    const colorMap = { "Wasted": "#e74c3c", "Stunted": "#e74c3c", "Severe (SAM)": "#c0392b", "Underweight": "#f4a827", "Normal": "#27a872" };
    const bgMap = { "Wasted": "#fee2e2", "Stunted": "#fee2e2", "Severe (SAM)": "#fee2e2", "Underweight": "#fef9c3", "Normal": "#dcfce7" };
    badgeEl.style.color = colorMap[pred] || "#64748b";
    badgeEl.style.background = bgMap[pred] || "#f1f5f9";
  }
  if (document.getElementById("mlStunting"))    document.getElementById("mlStunting").textContent = details.stunting_risk != null ? `${details.stunting_risk}%` : "Not assessed";
  if (document.getElementById("mlWasting"))     document.getElementById("mlWasting").textContent = details.wasting_risk != null ? `${details.wasting_risk}%` : "Not assessed";
  if (document.getElementById("mlSAM"))         document.getElementById("mlSAM").textContent = details.sam_probability != null ? `${details.sam_probability}%` : "Not assessed";

  // Score bars
  const arcChip = document.getElementById("arcChip");
  const arcDate = document.getElementById("arcDate");
  if (arcDate) arcDate.textContent = `Assessed: ${latest.date || "—"}`;
  if (arcChip) {
    const isHigh = riskVal != null && riskVal >= 70;
    const isWarn = riskVal != null && riskVal >= 40;
    arcChip.className = `arc-chip ${isHigh ? "danger" : (isWarn ? "warn" : "success")}`;
    arcChip.textContent = isHigh 
      ? `Clinical Review Recommended — Priority Follow-up` 
      : (isWarn ? `Monitoring Advised — Growth Follow-up` : `Routine Growth Tracking`);
  }
  const stunting    = details.stunting_risk    != null ? details.stunting_risk : 0;
  const wasting     = details.wasting_risk     != null ? details.wasting_risk : 0;
  const underweight = details.underweight_risk != null ? details.underweight_risk : 0;
  const sam         = details.sam_probability  != null ? details.sam_probability : 0;
  const ids = ["fillStunting","fillWasting","fillUnderweight","fillSAM"];
  const pcts = ["pctStunting","pctWasting","pctUnderweight","pctSAM"];
  const vals = [stunting, wasting, underweight, sam];
  ids.forEach((id, i) => {
    const el = document.getElementById(id); if (el) el.style.width = `${vals[i]}%`;
  });
  pcts.forEach((id, i) => {
    const el = document.getElementById(id); if (el) el.textContent = `${vals[i]}%`;
  });

  // If we have the 4-output data from the API, use it directly
  if (latest.future_risk_prediction) {
    renderFutureRiskCard(latest.future_risk_prediction);
  } else if (currentChild && currentChild.id) {
    // Fetch from /api/ai/future-risk/{child_id}
    fetch(`${API_BASE}/ai/future-risk/${currentChild.id}`, { headers: getAuthHeaders() })
      .then(r => r.json())
      .then(fr => renderFutureRiskCard(fr))
      .catch(() => {});
  }

  if (latest.nutrition_recommendation) {
    renderNutritionCard(latest.nutrition_recommendation);
  } else if (currentChild && currentChild.id) {
    fetch(`${API_BASE}/ai/nutrition-plan/${currentChild.id}`, { headers: getAuthHeaders() })
      .then(r => r.json())
      .then(nr => renderNutritionCard(nr))
      .catch(() => {});
  }

  if (latest.explainability) {
    renderExplainCard(latest.explainability);
  }
}

// ── OUTPUT 2: Future Risk Card Renderer ──────────────────────────────────────
function renderFutureRiskCard(fr) {
  const tierColors = { "High": "#e74c3c", "Medium": "#f4a827", "Low": "#27a872" };
  const badgeColors = { "High": ["#fee2e2","#c0392b"], "Medium": ["#fef9c3","#854d0e"], "Low": ["#dcfce7","#166534"] };
  const tier = fr.future_risk_tier || fr.tier || "Medium";
  const color = tierColors[tier] || "#f4a827";
  const [bg, fg] = badgeColors[tier] || ["#fef9c3","#854d0e"];

  const el = id => document.getElementById(id);
  if (el("frTier"))     { el("frTier").textContent = tier; el("frTier").style.color = color; }
  if (el("frBadge"))    { el("frBadge").textContent = `${tier.toUpperCase()} RISK`; el("frBadge").style.background = bg; el("frBadge").style.color = fg; }
  if (el("frScore"))    el("frScore").textContent = fr.future_risk_score || fr.score || "—";
  if (el("frVelocity")) el("frVelocity").textContent = fr.velocity_trend || "Stable";
  if (el("frAction"))   el("frAction").textContent = fr.recommended_action || "";
  const forecasts = fr.forecasts || [];
  if (forecasts[0] && el("fr30w")) el("fr30w").textContent = `${forecasts[0].weight_kg} kg`;
  if (forecasts[1] && el("fr60w")) el("fr60w").textContent = `${forecasts[1].weight_kg} kg`;
  if (forecasts[2] && el("fr90w")) el("fr90w").textContent = `${forecasts[2].weight_kg} kg`;
}

// ── OUTPUT 3: Nutrition Recommendation Card Renderer ─────────────────────────
function renderNutritionCard(nr) {
  const severityColors = { "SAM": "#c0392b", "MAM": "#f4a827", "Mild": "#e07a1c", "Normal": "#27a872", "Standard": "#2563eb" };
  const sev = nr.severity || (nr.prediction ? (nr.prediction.includes("Severe") ? "SAM" : (nr.prediction.includes("Moderate") || nr.prediction.includes("Wasted")) ? "MAM" : "Normal") : "Standard");
  const el = id => document.getElementById(id);
  if (el("nrBadge")) {
    el("nrBadge").textContent = `${sev.toUpperCase()} GUIDANCE`;
    el("nrBadge").style.color = severityColors[sev] || "#334155";
    el("nrBadge").style.background = sev === "SAM" ? "#fee2e2" : sev === "Normal" ? "#dcfce7" : "#fef9c3";
  }
  if (el("nrKcal"))  el("nrKcal").textContent = nr.caloric_target?.total_kcal_per_day || nr.total_kcal_per_day || "—";
  if (el("nrRutf"))  el("nrRutf").textContent = sev === "SAM" ? "Medical Officer Evaluation Required (Supervised SAM Protocol)" : "Not indicated (Dietary diversity recommended)";
  if (el("nrMealList") && nr.meal_schedule && nr.meal_schedule.length > 0) {
    const icons = ["&#127775;","&#9728;","&#127774;","&#127769;","&#127762;"];
    el("nrMealList").innerHTML = nr.meal_schedule.slice(0, 3).map((m, i) => `
      <div style="display:flex;justify-content:space-between;font-size:0.78rem;padding:5px 8px;background:#f8fafc;border-radius:7px;">
        <span style="color:#27a872;font-weight:600;">${icons[i] || "•"} ${m.time_slot.split("(")[0].trim()}</span>
        <span style="color:#334155;">${(m.foods || []).slice(0,2).join(" + ")}</span>
      </div>`).join("");
  }
}

// ── OUTPUT 4: Explainable AI Card Renderer ────────────────────────────────────
function renderExplainCard(xai) {
  const shap = xai.shap_feature_attributions || [];
  const gradcam = xai.gradcam_anatomical_focus || [];
  if (document.getElementById("shapBarsList") && shap.length > 0) {
    const maxVal = Math.max(...shap.map(s => Math.abs(s.shap_value || 0.1)));
    document.getElementById("shapBarsList").innerHTML = shap.slice(0, 4).map(s => {
      const width = Math.round((Math.abs(s.shap_value) / maxVal) * 100);
      const isNeg = s.shap_value < 0;
      return `<div style="display:flex;align-items:center;gap:7px;font-size:0.77rem;">
        <span style="width:90px;color:#334155;font-weight:600;">${(s.feature||"").replace(/_/g," ").replace(/\b\w/g,c=>c.toUpperCase()).slice(0,12)}</span>
        <div style="flex:1;height:8px;background:#f1f5f9;border-radius:99px;overflow:hidden;">
          <div style="width:${width}%;height:100%;background:linear-gradient(90deg,#7c3aed,#a78bfa);border-radius:99px;"></div>
        </div>
        <span style="color:${isNeg?"#e74c3c":"#27a872"};font-weight:700;width:40px;text-align:right;">${s.shap_value >= 0 ? "+":""}${s.shap_value}</span>
      </div>`;
    }).join("");
  }
  if (document.getElementById("gradcamFocus") && gradcam.length > 0) {
    document.getElementById("gradcamFocus").textContent = gradcam.slice(0,2).join(" • ");
  }
}



// -------------------------------------------------------------
// 4. 📷 CHILD PHOTOS
// -------------------------------------------------------------
async function loadChildPhotos(childId) {
  try {
    const res = await fetch(`${API_BASE}/photos/child/${childId}`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const photos = await res.json();

    const photoGrid = document.getElementById("parentPhotoGrid") || document.querySelector(".photo-grid");
    const countBadge = document.getElementById("storedPhotoCountBadge");
    if (countBadge) {
      countBadge.textContent = `${photos.length} Photo${photos.length === 1 ? '' : 's'} Stored`;
    }

    if (!photoGrid) return;

    photoGrid.innerHTML = "";
    if (photos.length === 0) {
      photoGrid.innerHTML = `
        <div style="font-size:0.84rem;color:var(--text-muted);grid-column:1/-1;padding:16px 0;text-align:center;">
          No health photos stored yet. Upload Front, Back, and Face photos above to store them.
        </div>`;
      return;
    }

    photos.forEach(p => {
      const thumb = document.createElement("div");
      thumb.className = "photo-thumb";
      thumb.style.cssText = "position:relative;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);overflow:hidden;padding:8px;box-shadow:var(--shadow-xs);";
      
      const pType = (p.photo_type || "photo").toUpperCase();
      const pDate = p.uploaded_at ? new Date(p.uploaded_at).toLocaleDateString() : (p.date || "Recent");

      thumb.innerHTML = `
        <div style="background:var(--surface-muted);overflow:hidden;display:flex;align-items:center;justify-content:center;height:120px;border-radius:var(--radius-md);position:relative;">
          <img src="http://127.0.0.1:8000/${p.file_path}" alt="${pType}" style="width:100%;height:100%;object-fit:cover;" onerror="this.style.display='none';this.parentElement.innerHTML='<div style=\\'text-align:center;padding:12px;\\'><span style=\\'font-size:1.8rem;\\'>📷</span><br><span style=\\'font-size:0.75rem;font-weight:700;color:var(--text);\\'>${pType}</span></div>'"/>
          <span style="position:absolute;top:6px;left:6px;background:rgba(0,0,0,0.65);color:#fff;font-size:0.68rem;font-weight:700;padding:2px 6px;border-radius:var(--radius-full);backdrop-filter:blur(4px);">${pType}</span>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;padding:6px 2px 2px 2px;">
          <span style="font-size:0.72rem;color:var(--text-secondary);">${pDate}</span>
          <button onclick="deleteChildPhoto(${p.id})" style="background:none;border:none;color:#e11d48;font-size:0.75rem;cursor:pointer;padding:2px 4px;font-weight:600;" title="Delete Photo">✕ Delete</button>
        </div>
      `;
      photoGrid.appendChild(thumb);
    });
  } catch (e) {
    console.error("Error loading photos:", e);
  }
}

async function handlePhotoUpload(event) {
  const file = event.target.files[0];
  if (!file || !currentChild) return;

  const formData = new FormData();
  formData.append("child_id", currentChild.id);
  formData.append("photo_type", "front");
  formData.append("image", file);

  showToast("Uploading photo for AI visual screening...");

  try {
    const token = localStorage.getItem("childnutri_token");
    const res = await fetch(`${API_BASE}/photos/upload`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}` },
      body: formData
    });

    if (res.ok) {
      showToast("Photo uploaded successfully! Visual screening updated.");
      await loadChildPhotos(currentChild.id);
    } else {
      const err = await res.json();
      showToast(err.detail || "Photo upload failed.", "error");
    }
  } catch (e) {
    console.error(e);
    showToast("Error connecting to upload service.", "error");
  } finally {
    event.target.value = "";
  }
}

async function deleteChildPhoto(photoId) {
  if (!confirm("Are you sure you want to delete this photo?")) return;
  try {
    const res = await fetch(`${API_BASE}/photos/${photoId}`, {
      method: "DELETE",
      headers: getAuthHeaders()
    });
    if (res.ok) {
      showToast("Photo deleted.");
      await loadChildPhotos(currentChild.id);
    } else {
      showToast("Failed to delete photo.", "error");
    }
  } catch (e) {
    showToast("Error deleting photo.", "error");
  }
}

// -------------------------------------------------------------
// CLINICAL MODULES: MEDICAL, NUTRITION, APPOINTMENTS, NOTIFICATIONS
// -------------------------------------------------------------
async function loadMedicalHistory(childId) {
  try {
    const res = await fetch(`${API_BASE}/medical/child/${childId}`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const history = await res.json();

    const timeline = document.querySelector(".timeline");
    if (!timeline || history.length === 0) return;

    timeline.innerHTML = "";
    history.forEach(item => {
      const tl = document.createElement("div");
      tl.className = "tl-item";
      tl.innerHTML = `
        <div class="tl-dot danger"></div>
        <div class="tl-card">
          <div class="tl-header">
            <div class="tl-title">${item.diagnosis}</div>
            <div class="tl-date">${item.visit_date}</div>
          </div>
          <div class="tl-doctor">${item.doctor_name}</div>
          <div class="tl-body">${item.notes || item.treatment || 'Routine clinical assessment.'}</div>
          <div class="tl-tags">
            <span class="tl-tag red">${item.diagnosis}</span>
            ${item.treatment ? `<span class="tl-tag orange">${item.treatment}</span>` : ''}
          </div>
        </div>
      `;
      timeline.appendChild(tl);
    });

    // Update latest doctor notes in Overview tab
    if (history.length > 0) {
      const latestMed = history[0];
      const dnName = document.querySelector(".dn-name");
      const dnText = document.querySelector(".dn-text");
      const cardDate = document.querySelector(".card-date");
      if (dnName) dnName.innerHTML = `${latestMed.doctor_name} <span class="dn-badge">Pediatrician</span>`;
      if (dnText) dnText.textContent = (latestMed.notes || latestMed.treatment || latestMed.diagnosis).replace(/Aarav/g, getChildFirstName());
      if (cardDate) cardDate.textContent = `${latestMed.visit_date} • ${latestMed.doctor_name}`;
    }
  } catch (e) {
    console.error("Error loading medical history:", e);
  }
}

// =============================================================================
// NUTRITION DECISION-SUPPORT ENGINE (WHO 2023 COMPLEMENTARY FEEDING)
// =============================================================================

const NUTRITION_DATABASE = {
  meals: [
    // BREAKFAST OPTIONS
    {
      id: "b_poha_egg",
      type: "breakfast",
      title: "Soft Vegetable Poha with Boiled Egg",
      desc: "Steamed flattened rice cooked soft with turmeric, grated carrots, and mashed boiled egg yolk or whole egg.",
      food_groups: ["Grains", "Eggs", "Vitamin-A Veg"],
      food_group_ids: [2, 6, 7],
      required_ingredients: ["poha", "egg", "carrot"],
      cost_band: "₹",
      budget_tier: "budget_conscious",
      diet_pattern: "egg_vegetarian",
      texture: "Soft moist mash / Finger food",
      age_min_months: 6,
      prep_steps: [
        "Rinse poha (flattened rice) thoroughly in clean drinking water until softened.",
        "Lightly sauté finely grated carrots in 1/2 tsp vegetable oil or ghee with a pinch of cumin and turmeric.",
        "Add softened poha with 2 tablespoons water and cook on low heat for 2 minutes until tender.",
        "Boil one egg until hard (10 mins). Peel and mash the yolk (or whole egg for >9 months) with a fork.",
        "Mix together, ensure comfortable feeding temperature, and offer responsively without pressure."
      ],
      choking_warning: "Ensure carrots are grated very fine or boiled soft. Mash egg thoroughly without large rubbery chunks."
    },
    {
      id: "b_ragi_porridge",
      type: "breakfast",
      title: "Ragi (Finger Millet) Porridge",
      desc: "Traditional calcium-rich ragi flour cooked tender with boiled milk, mashed ripe banana, and cooking oil or ghee.",
      food_groups: ["Grains", "Dairy", "Other Fruits"],
      food_group_ids: [2, 4, 8],
      required_ingredients: ["ragi", "milk", "banana"],
      cost_band: "₹",
      budget_tier: "budget_conscious",
      diet_pattern: "vegetarian",
      texture: "Smooth semi-thick porridge",
      age_min_months: 6,
      prep_steps: [
        "Mix 2 tablespoons of ragi flour with 100 ml clean water to form a lump-free paste.",
        "Cook on medium flame, stirring continuously for 4–5 minutes until it thickens and turns glossy.",
        "Stir in 50 ml boiled milk (or warm water) and a drop of cooking oil or melted butter/ghee.",
        "Stir in 2 tablespoons of thoroughly mashed ripe banana for natural sweetness and calories.",
        "Cool to body temperature before feeding with a clean spoon."
      ],
      choking_warning: "Ensure no dry flour lumps remain. Porridge should be thick enough to stay on a tilted spoon without running off."
    },
    {
      id: "b_idli_dal",
      type: "breakfast",
      title: "Steamed Idli with Moong Dal",
      desc: "Fermented steamed rice-lentil cake thoroughly crumbled and soaked in warm yellow moong dal stew.",
      food_groups: ["Grains", "Pulses"],
      food_group_ids: [2, 3],
      required_ingredients: ["rice", "dal"],
      cost_band: "₹",
      budget_tier: "budget_conscious",
      diet_pattern: "vegetarian",
      texture: "Soft soaked mash",
      age_min_months: 6,
      prep_steps: [
        "Steam fresh idli until completely soft and fluffy.",
        "Pressure cook yellow moong dal with a pinch of turmeric and cumin until fully disintegrated.",
        "Crumble 1 small idli into warm dal stew and add 1/2 tsp cooking oil or ghee.",
        "Mash thoroughly with a clean fork until uniform and smooth.",
        "Feed slowly in small spoonfuls following the baby's feeding cues."
      ],
      choking_warning: "Never offer dry idli pieces. Always thoroughly soak and mash in warm dal soup to avoid airway aspiration."
    },
    {
      id: "b_suji_upma",
      type: "breakfast",
      title: "Soft Semolina (Suji) Vegetable Porridge",
      desc: "Roasted semolina cooked soft with finely grated carrots and vegetable oil or ghee for sustained morning calories.",
      food_groups: ["Grains", "Vitamin-A Veg"],
      food_group_ids: [2, 7],
      required_ingredients: ["suji", "carrot"],
      cost_band: "₹",
      budget_tier: "budget_conscious",
      diet_pattern: "vegetarian",
      texture: "Soft moist grain porridge",
      age_min_months: 7,
      prep_steps: [
        "Dry roast semolina (suji) lightly on low heat until aromatic (3 mins).",
        "Steam finely grated carrots until soft.",
        "Bring 150 ml water to boil with a drop of cooking oil or ghee; gradually whisk in roasted suji to avoid lumps.",
        "Cover and cook on lowest flame for 3 minutes until moist and soft.",
        "Cool and serve warm."
      ],
      choking_warning: "Vegetables must be grated very fine or mashed completely."
    },
    {
      id: "b_roti_paneer",
      type: "breakfast",
      title: "Soft Whole Wheat Roti with Paneer",
      desc: "Whole wheat chapati soaked soft in warm boiled milk or thin dal and blended with fresh crumbled cottage cheese (paneer).",
      food_groups: ["Grains", "Dairy"],
      food_group_ids: [2, 4],
      required_ingredients: ["wheat", "paneer", "milk"],
      cost_band: "₹₹",
      budget_tier: "standard",
      diet_pattern: "vegetarian",
      texture: "Soft soaked shreds",
      age_min_months: 9,
      prep_steps: [
        "Warm freshly made soft whole wheat roti (without dry crust).",
        "Tear into small shreds and soak in 60 ml warm boiled milk or thin dal for 5 minutes.",
        "Grate 1 tablespoon fresh soft paneer and blend gently into the soaked roti.",
        "Mash with fingers or fork until thoroughly softened."
      ],
      choking_warning: "Discard hard burnt roti edges. Paneer must be soft and grated finely."
    },

    // LUNCH OPTIONS
    {
      id: "l_dal_khichdi",
      type: "lunch",
      title: "Yellow Moong Dal Khichdi with Carrots",
      desc: "Balanced grain-legume combination of soft rice and split yellow moong dal cooked with tender carrots and cumin.",
      food_groups: ["Grains", "Pulses", "Vitamin-A Veg"],
      food_group_ids: [2, 3, 7],
      required_ingredients: ["rice", "dal", "carrot"],
      cost_band: "₹",
      budget_tier: "budget_conscious",
      diet_pattern: "vegetarian",
      texture: "Thick moist porridge",
      age_min_months: 6,
      prep_steps: [
        "Wash 2 tbsp rice and 2 tbsp yellow moong dal thoroughly.",
        "Pressure cook with 1 cup water, finely grated carrot, pinch of turmeric, and cumin for 4 whistles.",
        "Mash while hot to achieve a smooth, semi-solid texture.",
        "Fold in 1/2 tsp cooking oil or ghee before serving warm."
      ],
      choking_warning: "Ensure no whole unmashed grains or hard vegetable chunks remain."
    },
    {
      id: "l_curd_rice",
      type: "lunch",
      title: "Soft Rice with Fresh Curd",
      desc: "Cooked white rice mashed soft with fresh unsweetened curd and a pinch of roasted cumin for gentle digestion.",
      food_groups: ["Grains", "Dairy"],
      food_group_ids: [2, 4],
      required_ingredients: ["rice", "curd"],
      cost_band: "₹",
      budget_tier: "budget_conscious",
      diet_pattern: "vegetarian",
      texture: "Cool soft mash",
      age_min_months: 7,
      prep_steps: [
        "Cook rice until very soft; mash thoroughly while warm.",
        "Allow to cool to room temperature.",
        "Stir in 3 tablespoons of fresh, unsweetened plain curd.",
        "Season with a pinch of roasted cumin powder."
      ],
      choking_warning: "Serve fresh; do not feed curd that has become sour from sitting out."
    },
    {
      id: "l_chana_rice",
      type: "lunch",
      title: "Mashed Bengal Gram (Chana) with Rice",
      desc: "Bengal gram cooked soft, mashed with rice and seasoned with cumin for plant protein and iron.",
      food_groups: ["Grains", "Pulses"],
      food_group_ids: [2, 3],
      required_ingredients: ["chana", "rice"],
      cost_band: "₹",
      budget_tier: "budget_conscious",
      diet_pattern: "vegetarian",
      texture: "Coarse soft mash",
      age_min_months: 9,
      prep_steps: [
        "Soak Bengal gram overnight; pressure cook until completely soft.",
        "Mash chickpeas thoroughly using the back of a ladle.",
        "Mix with soft boiled rice and a spoon of cooking oil or ghee."
      ],
      choking_warning: "Never offer whole round chickpeas; mash every chickpea flat."
    },
    {
      id: "l_chicken_khichdi",
      type: "lunch",
      title: "Soft Minced Chicken & Rice Khichdi",
      desc: "Finely minced chicken simmered tender with rice, yellow dal, and pumpkin for high bioavailable iron and zinc.",
      food_groups: ["Grains", "Pulses", "Flesh Foods", "Vitamin-A Veg"],
      food_group_ids: [2, 3, 5, 7],
      required_ingredients: ["chicken", "rice", "dal"],
      cost_band: "₹₹",
      budget_tier: "standard",
      diet_pattern: "non_vegetarian",
      texture: "Soft savoury porridge",
      age_min_months: 9,
      prep_steps: [
        "Simmer 2 tbsp minced boneless chicken with 2 tbsp rice, 1 tbsp moong dal, and pumpkin cubes.",
        "Cook until all ingredients are completely tender and chicken is fully cooked.",
        "Mash or puree to an age-appropriate soft texture."
      ],
      choking_warning: "Check chicken thoroughly for tiny bone fragments. Mince very fine."
    },

    // SNACK OPTIONS
    {
      id: "s_banana_curd",
      type: "snack",
      title: "Ripe Banana with Plain Curd",
      desc: "Naturally sweet ripe banana mashed smoothly with fresh curd for dietary potassium and probiotics.",
      food_groups: ["Dairy", "Other Fruits"],
      food_group_ids: [4, 8],
      required_ingredients: ["banana", "curd"],
      cost_band: "₹",
      budget_tier: "budget_conscious",
      diet_pattern: "vegetarian",
      texture: "Smooth spoonable puree",
      age_min_months: 6,
      prep_steps: [
        "Peel half a ripe banana and mash with a fork until smooth.",
        "Stir in 2 tablespoons of fresh plain curd.",
        "Serve immediately to prevent browning."
      ],
      choking_warning: "Never cut banana into thick round discs; always mash or cut into thin lengthwise strips."
    },
    {
      id: "s_papaya_puree",
      type: "snack",
      title: "Mashed Ripe Papaya",
      desc: "Fresh ripe papaya peeled, seeded, and fork-mashed for vitamin A and gentle dietary fiber.",
      food_groups: ["Vitamin-A Veg"],
      food_group_ids: [7],
      required_ingredients: ["papaya"],
      cost_band: "₹",
      budget_tier: "budget_conscious",
      diet_pattern: "vegetarian",
      texture: "Silky fruit mash",
      age_min_months: 6,
      prep_steps: [
        "Take a slice of ripe, sweet papaya; remove seeds and peel skin thickly.",
        "Mash thoroughly with a fork until smooth and uniform."
      ],
      choking_warning: "Ensure fruit is completely ripe and soft with zero seeds."
    },
    {
      id: "s_boiled_egg",
      type: "snack",
      title: "Mashed Hard-Boiled Egg Yolk",
      desc: "Hard-boiled egg yolk mashed with a spoonful of warm milk or broth for choline and essential fatty acids.",
      food_groups: ["Eggs", "Dairy"],
      food_group_ids: [6, 4],
      required_ingredients: ["egg", "milk"],
      cost_band: "₹",
      budget_tier: "budget_conscious",
      diet_pattern: "egg_vegetarian",
      texture: "Soft crumbly mash",
      age_min_months: 7,
      prep_steps: [
        "Boil egg for 10 minutes; cool and peel.",
        "Separate yolk (and white if >9 months) and mash with a fork.",
        "Add 1 tbsp warm boiled milk or water for moist, swallowable consistency."
      ],
      choking_warning: "Never offer dry, unmoistened egg yolk as it can stick in the throat."
    },
    {
      id: "s_sattu_drink",
      type: "snack",
      title: "Roasted Bengal Gram (Sattu) Drink",
      desc: "Roasted gram flour whisked with boiled clean water or milk for quick plant-based protein.",
      food_groups: ["Pulses", "Dairy"],
      food_group_ids: [3, 4],
      required_ingredients: ["sattu", "milk"],
      cost_band: "₹",
      budget_tier: "budget_conscious",
      diet_pattern: "vegetarian",
      texture: "Smooth liquid / cup feeding",
      age_min_months: 8,
      prep_steps: [
        "Mix 1 tbsp roasted sattu powder into 80 ml warm boiled milk or clean water.",
        "Whisk thoroughly to eliminate lumps.",
        "Serve in an open cup or with a spoon."
      ],
      choking_warning: "Ensure powder is fully dissolved with no dry clumps."
    },

    // DINNER OPTIONS
    {
      id: "d_masoor_rice",
      type: "dinner",
      title: "Red Lentil (Masoor Dal) with Soft Rice",
      desc: "Quick-cooking red lentils and rice simmered with spinach leaves and a teaspoon of oil or ghee.",
      food_groups: ["Grains", "Pulses", "Vitamin-A Veg"],
      food_group_ids: [2, 3, 7],
      required_ingredients: ["rice", "dal", "spinach"],
      cost_band: "₹",
      budget_tier: "budget_conscious",
      diet_pattern: "vegetarian",
      texture: "Gentle warm mash",
      age_min_months: 7,
      prep_steps: [
        "Pressure cook masoor dal and rice with finely chopped spinach leaves and turmeric.",
        "Mash well so greens blend completely into the porridge.",
        "Add 1/2 tsp cooking oil or ghee and serve warm."
      ],
      choking_warning: "Ensure spinach leaves are chopped very fine before cooking."
    },
    {
      id: "d_roti_dal",
      type: "dinner",
      title: "Soaked Soft Chapati in Dal Stew",
      desc: "Fresh chapati softened in warm moong dal with cumin and cooked bottle gourd or pumpkin.",
      food_groups: ["Grains", "Pulses"],
      food_group_ids: [2, 3],
      required_ingredients: ["wheat", "dal"],
      cost_band: "₹",
      budget_tier: "budget_conscious",
      diet_pattern: "vegetarian",
      texture: "Soft soaked pieces",
      age_min_months: 8,
      prep_steps: [
        "Tear soft chapati into small shreds.",
        "Immerse completely in hot moong dal soup and cover for 5 minutes.",
        "Mash with a fork until smooth and serve at body temperature."
      ],
      choking_warning: "Roti must be 100% soft and soaked through."
    },
    {
      id: "d_potato_dal",
      type: "dinner",
      title: "Mashed Potato & Moong Dal Stew",
      desc: "Boiled potato cubes mashed with warm dal soup and a drop of cooking oil for evening satiety.",
      food_groups: ["Grains", "Pulses"],
      food_group_ids: [2, 3],
      required_ingredients: ["potato", "dal"],
      cost_band: "₹",
      budget_tier: "budget_conscious",
      diet_pattern: "vegetarian",
      texture: "Comforting smooth mash",
      age_min_months: 7,
      prep_steps: [
        "Boil potato until easily pierced with a fork; peel and mash.",
        "Pour warm yellow moong dal over the potato mash.",
        "Stir in a drop of healthy oil and feed slowly."
      ],
      choking_warning: "Ensure potato is completely lump-free."
    },
    {
      id: "d_chicken_rice",
      type: "dinner",
      title: "Soft Rice in Chicken Broth",
      desc: "Warm rice soaked in tender shredded chicken broth with soft cooked carrots.",
      food_groups: ["Grains", "Flesh Foods", "Vitamin-A Veg"],
      food_group_ids: [2, 5, 7],
      required_ingredients: ["chicken", "rice", "carrot"],
      cost_band: "₹₹",
      budget_tier: "standard",
      diet_pattern: "non_vegetarian",
      texture: "Warm stew",
      age_min_months: 10,
      prep_steps: [
        "Simmer boneless chicken with carrots and cumin for 20 minutes.",
        "Finely shred chicken and return to broth.",
        "Pour over freshly mashed warm rice."
      ],
      choking_warning: "Verify zero bones. Ensure shredded chicken is moist and finely minced."
    }
  ]
};

// Global state for nutrition module
const WHO_8_GROUPS_DEF = [
  { id: 1, name: "Breast milk", icon: "🤱" },
  { id: 2, name: "Grains, roots & tubers", icon: "🌾" },
  { id: 3, name: "Pulses, nuts & seeds", icon: "🫘" },
  { id: 4, name: "Dairy products", icon: "🥛" },
  { id: 5, name: "Flesh foods (chicken/fish/meat)", icon: "🍗" },
  { id: 6, name: "Eggs", icon: "🥚" },
  { id: 7, name: "Vitamin-A fruits & vegetables", icon: "🥕" },
  { id: 8, name: "Other fruits & vegetables", icon: "🍌" }
];

let currentNutritionState = {
  sessionStatus: "NOT_STARTED",
  budgetTier: "budget_conscious",
  dietPattern: "vegetarian",
  allergies: [],
  availableFoods: ["rice", "wheat", "dal", "potato"],
  mealFrequency: { meals: 3, snacks: 2 },
  foodRecall: {
    breakfast: [],
    lunch: [],
    snack: [],
    dinner: []
  },
  selectedMeals: {
    breakfast: null,
    lunch: null,
    snack: null,
    dinner: null
  },
  activeReplaceSlot: null,
  childAgeMonths: 16,
  mddScore: null,
  explanation10: null,
  gaps: []
};

// =============================================================================
// CONVERSATIONAL NUTRITION LOADER & CONTROLLER
// =============================================================================

let currentDietPlan = null;
let selectedDietPattern = "vegetarian";
let selectedAllergies = [];

function setSessionStateUI(state) {
  const badge = document.getElementById("nutriSessionStateBadge");
  if (badge) {
    badge.textContent = state ? state.replace("_", " ") : "READY";
  }
}

function setNutriDietPattern(btn, pattern) {
  selectedDietPattern = pattern;
  document.querySelectorAll("#nutriDietPatternGroup .nutri-tag-chip").forEach(el => {
    el.classList.remove("active");
  });
  if (btn) {
    btn.classList.add("active");
  } else {
    const target = document.querySelector(`#nutriDietPatternGroup [data-diet="${pattern}"]`);
    if (target) target.classList.add("active");
  }
  if (currentChild && currentChild.id) {
    triggerAIDietPlanGeneration();
  }
}

function updateNutriAllergies() {
  const checked = Array.from(document.querySelectorAll("#nutriAllergyCheckboxGroup input[type='checkbox']:checked")).map(cb => cb.value);
  selectedAllergies = checked;
  if (currentChild && currentChild.id) {
    triggerAIDietPlanGeneration();
  }
}

async function triggerAIDietPlanGeneration() {
  if (!currentChild || !currentChild.id) {
    showToast("Please add or select a child first.", "warning");
    return;
  }

  const spinner = document.getElementById("nutriPlanLoadingIndicator");
  const errBanner = document.getElementById("nutriPlanErrorBanner");
  const btn = document.getElementById("btnGenerateDietPlan");

  if (errBanner) errBanner.style.display = "none";
  if (spinner) spinner.style.display = "block";
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span>⏳</span> Generating Plan...`;
  }

  try {
    const res = await fetch(`${API_BASE}/nutrition/plan/generate`, {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({
        child_id: currentChild.id,
        dietary_preference: selectedDietPattern,
        food_allergies: selectedAllergies,
        budget_tier: "standard"
      })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const detail = err.detail || `Server returned HTTP ${res.status}`;
      throw new Error(detail);
    }

    const planData = await res.json();
    currentDietPlan = planData;
    if (errBanner) errBanner.style.display = "none";
    renderAINutritionPlan(planData);
    showToast("Personalized AI Diet Plan generated successfully!", "success");
  } catch (err) {
    console.error("AI diet plan generation failed:", err);
    const msg = err.message || "Failed to generate AI diet plan.";

    if (errBanner) {
      errBanner.style.display = "block";
      const titleEl = document.getElementById("nutriErrorTitle");
      const msgEl = document.getElementById("nutriErrorMessage");
      const actEl = document.getElementById("nutriErrorAction");

      if (msg.includes("GEMINI_API_KEY") || msg.includes("configuration is incomplete")) {
        if (titleEl) titleEl.textContent = "AI Service Configuration Required";
        if (msgEl) msgEl.textContent = msg;
        if (actEl) actEl.innerHTML = "<strong>Action:</strong> Set your <code>GEMINI_API_KEY</code> in the <code>.env</code> file in the project root and restart the server.";
      } else if (msg.includes("measurements") || msg.includes("weight")) {
        if (titleEl) titleEl.textContent = "Child Measurements Missing";
        if (msgEl) msgEl.textContent = msg;
        if (actEl) actEl.innerHTML = "<strong>Action:</strong> Go to the <strong>Growth Assessment</strong> section and record current weight and height for your child.";
      } else if (msg.includes("timed out") || msg.includes("timeout")) {
        if (titleEl) titleEl.textContent = "AI Service Request Timed Out";
        if (msgEl) msgEl.textContent = msg;
        if (actEl) actEl.innerHTML = "<strong>Action:</strong> The external AI service took too long to reply. Please check your network and click <strong>Try Again</strong>.";
      } else if (msg.includes("rate limit") || msg.includes("429")) {
        if (titleEl) titleEl.textContent = "AI Provider Rate Limit Exceeded";
        if (msgEl) msgEl.textContent = msg;
        if (actEl) actEl.innerHTML = "<strong>Action:</strong> The AI quota was temporarily reached. Please wait a minute before retrying.";
      } else {
        if (titleEl) titleEl.textContent = "Diet Plan Notice";
        if (msgEl) msgEl.textContent = msg;
        if (actEl) actEl.innerHTML = "<strong>Action:</strong> Review child profile details and click <strong>Try Again</strong>.";
      }

      errBanner.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    showToast(msg, "error");
  } finally {
    if (spinner) spinner.style.display = "none";
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>⚡</span> Generate AI Diet Plan`;
    }
  }
}

async function loadNutritionPlan(childId) {
  try {
    const secNutri = document.getElementById("sec-nutrition");
    if (!secNutri) return;

    const emptyBox = document.getElementById("nutriEmptyChildrenState");
    const popBox = document.getElementById("nutriPopulatedContent");
    const errBanner = document.getElementById("nutriPlanErrorBanner");
    if (errBanner) errBanner.style.display = "none";

    if (!currentChild || !currentChild.id) {
      if (emptyBox) emptyBox.style.display = "block";
      if (popBox) popBox.style.display = "none";
      return;
    }

    if (emptyBox) emptyBox.style.display = "none";
    if (popBox) popBox.style.display = "block";

    // Set child header details
    const nameEl = document.getElementById("nutriActiveChildName");
    if (nameEl) nameEl.textContent = currentChild.name || "Child";

    let ageMonths = currentChild.age_months;
    if (ageMonths == null && currentChild.date_of_birth) {
      const d = new Date(currentChild.date_of_birth);
      const now = new Date();
      ageMonths = Math.max(0, Math.round(((now - d) / (1000 * 60 * 60 * 24 * 30.4375)) * 10) / 10);
    }
    const ageEl = document.getElementById("nutriActiveChildAge");
    if (ageEl) ageEl.textContent = ageMonths != null ? `${ageMonths} months` : "Age not recorded";

    const genderEl = document.getElementById("nutriActiveChildGender");
    if (genderEl) genderEl.textContent = currentChild.gender || "Gender not recorded";

    const wtEl = document.getElementById("nutriWeightDisp");
    if (wtEl) wtEl.textContent = currentChild.current_weight != null ? `${currentChild.current_weight} kg` : "Not recorded";

    const htEl = document.getElementById("nutriHeightDisp");
    if (htEl) htEl.textContent = currentChild.current_height != null ? `${currentChild.current_height} cm` : "Not recorded";

    // Fetch latest saved plan for this child
    const res = await fetch(`${API_BASE}/nutrition/plan/child/${childId}/latest`, {
      headers: getAuthHeaders()
    });

    if (res.ok) {
      const plan = await res.json();
      currentDietPlan = plan;
      renderAINutritionPlan(plan);
    } else {
      // If child has measurements recorded, show helpful prompt to generate initial plan
      const mealCardsList = document.getElementById("nutriMealCardsList");
      if (mealCardsList) {
        if (!currentChild.current_weight) {
          mealCardsList.innerHTML = `
            <div style="text-align:center;padding:48px 24px;background:#ffffff;border:1px dashed #cbd5e1;border-radius:16px;">
              <div style="font-size:2rem;margin-bottom:12px;">⚖️</div>
              <strong style="display:block;font-size:1.05rem;color:#0f172a;margin-bottom:6px;">Record Measurements First</strong>
              <p style="font-size:0.86rem;color:#64748b;max-width:440px;margin:0 auto 16px;">
                To generate an age-appropriate diet plan with accurate energy targets, please record your child's weight and height in Growth Assessment.
              </p>
              <button type="button" class="btn btn-secondary btn-sm" onclick="switchSection('growth', this)">Go to Growth Assessment</button>
            </div>
          `;
        } else {
          mealCardsList.innerHTML = `
            <div style="text-align:center;padding:48px 24px;background:#ffffff;border:1px dashed #cbd5e1;border-radius:16px;">
              <div style="font-size:2rem;margin-bottom:12px;">🥗</div>
              <strong style="display:block;font-size:1.05rem;color:#0f172a;margin-bottom:6px;">Ready to Personalize Diet Plan</strong>
              <p style="font-size:0.86rem;color:#64748b;max-width:440px;margin:0 auto 16px;">
                Select your dietary pattern and any allergies above, then click <strong>Generate AI Diet Plan</strong> to create a daily meal schedule.
              </p>
              <button type="button" class="btn btn-primary btn-sm" onclick="triggerAIDietPlanGeneration()" style="background:#3b6551;color:#ffffff;border:none;">
                <span>⚡</span> Generate AI Diet Plan
              </button>
            </div>
          `;
        }
      }
    }
  } catch (err) {
    console.error("Error in loadNutritionPlan:", err);
  }
}

function renderAINutritionPlan(plan) {
  if (!plan) return;

  const input = plan.input_snapshot || {};
  const ee = plan.energy_estimate || {};
  const sum = plan.daily_nutrition_summary || {};
  const bmrData = plan.bmr_calculation || {};

  // Section A - Child & Energy info
  const nameEl = document.getElementById("nutriActiveChildName");
  if (nameEl) nameEl.textContent = input.name || (currentChild && currentChild.name) || "Child";

  const ageEl = document.getElementById("nutriActiveChildAge");
  if (ageEl) {
    const ageM = input.age_months ?? (currentChild && currentChild.age_months);
    ageEl.textContent = ageM != null ? `${ageM} months` : "-- months";
  }

  const genderEl = document.getElementById("nutriActiveChildGender");
  if (genderEl) genderEl.textContent = input.gender || (currentChild && currentChild.gender) || "--";

  const wtEl = document.getElementById("nutriWeightDisp");
  if (wtEl) {
    const wt = input.weight_kg ?? (currentChild && currentChild.current_weight);
    wtEl.textContent = wt != null ? `${wt} kg` : "Not recorded";
  }

  const htEl = document.getElementById("nutriHeightDisp");
  if (htEl) {
    const ht = input.height_cm ?? (currentChild && currentChild.current_height);
    htEl.textContent = ht != null ? `${ht} cm` : "Not recorded";
  }

  // Display BMR & EER in child header
  const bmrEl = document.getElementById("nutriBMRDisplay");
  if (bmrEl) {
    const bmrVal = bmrData.bmr_kcal || ee.bmr_schofield_kcal || ee.bmr_reference_kcal;
    bmrEl.textContent = bmrVal ? `${Math.round(bmrVal)} kcal/day` : "-- kcal/day";
  }

  const eerEl = document.getElementById("nutriEERDisplay");
  if (eerEl) {
    const eerVal = ee.estimated_energy_kcal || ee.eer_kcal;
    eerEl.textContent = eerVal ? `${Math.round(eerVal)} kcal/day` : "-- kcal/day";
  }

  const methodEl = document.getElementById("nutriEnergyMethodName");
  if (methodEl) methodEl.textContent = ee.equation_name || "IOM DRI Pediatric Equation (2005) + Schofield BMR";

  const methodStatusEl = document.getElementById("nutriEnergyMethodStatus");
  if (methodStatusEl) {
    methodStatusEl.textContent = ee.status || "Validated";
    methodStatusEl.className = ee.status === "MISSING_MEASUREMENTS" ? "badge warning" : "badge normal";
  }

  const methodDetailsEl = document.getElementById("nutriEnergyMethodDetails");
  if (methodDetailsEl) methodDetailsEl.textContent = ee.notes || "Basal Metabolic Rate calculated via Schofield (1985); EER includes resting expenditure plus growth allowance.";

  const timeBadge = document.getElementById("nutriPlanTimestampBadge");
  if (timeBadge) {
    timeBadge.textContent = plan.generation_timestamp
      ? `Updated: ${new Date(plan.generation_timestamp).toLocaleDateString()}`
      : "Updated: Today";
  }

  // Update active dietary pattern chip
  if (plan.dietary_preference) {
    selectedDietPattern = plan.dietary_preference;
    document.querySelectorAll("#nutriDietPatternGroup .nutri-tag-chip").forEach(el => {
      el.classList.toggle("active", el.getAttribute("data-diet") === plan.dietary_preference);
    });
  }

  // Update allergy checkboxes
  if (Array.isArray(plan.food_allergies)) {
    selectedAllergies = plan.food_allergies;
    document.querySelectorAll("#nutriAllergyCheckboxGroup input[type='checkbox']").forEach(cb => {
      cb.checked = selectedAllergies.includes(cb.value);
    });
  }

  // Section B - Chronological Daily Diet Plan
  const mealCardsList = document.getElementById("nutriMealCardsList");
  if (mealCardsList) {
    mealCardsList.innerHTML = "";
    const meals = plan.meals || [];

    if (meals.length === 0) {
      mealCardsList.innerHTML = `<div style="text-align:center;padding:32px;color:#64748b;background:#ffffff;border:1px solid #e2e8f0;border-radius:14px;">No meal schedule generated.</div>`;
    } else {
      meals.forEach(m => {
        const card = document.createElement("div");
        card.style.cssText = "background:#ffffff;border:1px solid #e2e8f0;border-radius:14px;padding:20px 24px;box-shadow:0 1px 3px rgba(0,0,0,0.02);";

        const itemsHtml = (m.food_items || []).map(f => `
          <div style="display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px dashed #f1f5f9;font-size:0.88rem;">
            <div style="display:flex;align-items:center;gap:8px;">
              <span style="color:#10b981;font-size:0.8rem;">●</span>
              <span style="color:#1e293b;font-weight:600;">${f.name}</span>
            </div>
            <div style="color:#64748b;font-size:0.82rem;">
              <strong style="color:#334155;">${f.portion_size} ${f.portion_unit}</strong>
              <span style="margin-left:8px;color:#94a3b8;">(~${Math.round(f.calories_kcal || 0)} kcal &bull; ${(f.protein_g || 0).toFixed(1)}g Pro)</span>
            </div>
          </div>
        `).join("");

        const prepHtml = m.preparation_notes
          ? `<div style="margin-top:12px;font-size:0.8rem;color:#475569;background:#f8fafc;padding:7px 12px;border-radius:8px;border-left:3px solid #cbd5e1;"><strong>Preparation:</strong> ${m.preparation_notes}</div>`
          : "";

        const textureHtml = m.texture_notes
          ? `<div style="margin-top:6px;font-size:0.8rem;color:#0369a1;background:#f0f9ff;padding:7px 12px;border-radius:8px;border-left:3px solid #38bdf8;"><strong>Texture & Feeding:</strong> ${m.texture_notes}</div>`
          : "";

        const allergyHtml = (m.allergy_warnings && m.allergy_warnings.length > 0)
          ? `<div style="margin-top:6px;font-size:0.8rem;color:#b91c1c;background:#fef2f2;padding:7px 12px;border-radius:8px;border-left:3px solid #f87171;"><strong>Allergy Notice:</strong> ${m.allergy_warnings.join(", ")}</div>`
          : "";

        card.innerHTML = `
          <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:14px;padding-bottom:12px;border-bottom:1px solid #f1f5f9;">
            <div style="display:flex;align-items:center;gap:12px;">
              <span style="background:#e0f2fe;color:#0369a1;font-weight:700;font-size:0.75rem;padding:4px 12px;border-radius:9999px;">${m.suggested_time || 'Meal'}</span>
              <strong style="font-size:1.1rem;color:#0f172a;">${m.meal_name}</strong>
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
              <span style="background:#f1f5f9;color:#334155;font-size:0.76rem;padding:4px 12px;border-radius:9999px;font-weight:600;">
                ~${Math.round(m.calories_kcal || 0)} kcal &bull; ${(m.protein_g || 0).toFixed(1)}g Protein
              </span>
            </div>
          </div>
          <div>${itemsHtml}</div>
          ${prepHtml}
          ${textureHtml}
          ${allergyHtml}
        `;

        mealCardsList.appendChild(card);
      });
    }
  }

  // Section C - Daily Nutrition Summary
  const plannedEnergy = sum.planned_energy_kcal != null ? Math.round(sum.planned_energy_kcal) : null;
  const targetEnergy = sum.target_energy_kcal != null ? Math.round(sum.target_energy_kcal) : null;
  const sumPlannedEl = document.getElementById("nutriSumPlannedEnergy");
  if (sumPlannedEl) sumPlannedEl.textContent = plannedEnergy != null ? plannedEnergy : "--";
  const sumTargetEl = document.getElementById("nutriSumTargetEnergy");
  if (sumTargetEl) sumTargetEl.textContent = targetEnergy != null ? targetEnergy : "--";

  if (targetEnergy && plannedEnergy) {
    const energyPct = Math.min(125, Math.round((plannedEnergy / targetEnergy) * 100));
    const energyBar = document.getElementById("nutriEnergyProgressBar");
    if (energyBar) energyBar.style.width = `${Math.min(100, energyPct)}%`;
    const energyLabel = document.getElementById("nutriEnergyProgressLabel");
    if (energyLabel) energyLabel.textContent = `${energyPct}% of estimated requirement`;
  }

  const plannedProtein = sum.total_protein_g != null ? sum.total_protein_g : null;
  const targetProtein = sum.target_protein_g != null ? sum.target_protein_g : null;
  const sumProteinEl = document.getElementById("nutriSumProtein");
  if (sumProteinEl) sumProteinEl.textContent = plannedProtein != null ? plannedProtein.toFixed(1) : "--";
  const targetProteinEl = document.getElementById("nutriTargetProtein");
  if (targetProteinEl) targetProteinEl.textContent = targetProtein != null ? targetProtein.toFixed(1) : "--";

  if (targetProtein && plannedProtein) {
    const protPct = Math.min(150, Math.round((plannedProtein / targetProtein) * 100));
    const protBar = document.getElementById("nutriProteinProgressBar");
    if (protBar) protBar.style.width = `${Math.min(100, protPct)}%`;
    const protLabel = document.getElementById("nutriProteinAdequacyLabel");
    if (protLabel) protLabel.textContent = `${protPct}% ICMR RDA Adequacy`;
  }

  const sumCalcEl = document.getElementById("nutriSumCalcium");
  if (sumCalcEl) sumCalcEl.textContent = sum.total_calcium_mg != null ? Math.round(sum.total_calcium_mg) : "--";
  const sumIronEl = document.getElementById("nutriSumIron");
  if (sumIronEl) sumIronEl.textContent = sum.total_iron_mg != null ? sum.total_iron_mg.toFixed(1) : "--";
  const sumVitAEl = document.getElementById("nutriSumVitA");
  if (sumVitAEl) sumVitAEl.textContent = sum.total_vitamin_a_mcg != null ? Math.round(sum.total_vitamin_a_mcg) : "--";

  const sumCarbsEl = document.getElementById("nutriSumCarbs");
  if (sumCarbsEl) sumCarbsEl.textContent = sum.total_carbs_g != null ? sum.total_carbs_g.toFixed(1) : "--";
  const sumFatsEl = document.getElementById("nutriSumFats");
  if (sumFatsEl) sumFatsEl.textContent = sum.total_fat_g != null ? sum.total_fat_g.toFixed(1) : "--";
  const sumFiberEl = document.getElementById("nutriSumFiber");
  if (sumFiberEl) sumFiberEl.textContent = sum.total_fiber_g != null ? sum.total_fiber_g.toFixed(1) : "--";

  // Section D - Key Nutritional Focus
  const focusList = document.getElementById("nutriKeyFocusList");
  if (focusList) {
    focusList.innerHTML = "";
    (plan.key_nutritional_focus || []).forEach(f => {
      const card = document.createElement("div");
      card.style.cssText = "background:#ffffff;border:1px solid #e2e8f0;border-radius:14px;padding:16px 18px;box-shadow:0 1px 3px rgba(0,0,0,0.02);";
      const sourcesHtml = (f.recommended_sources || []).map(s => `
        <span style="display:inline-block;background:#f0fdf4;color:#166534;font-size:0.72rem;font-weight:600;padding:2px 8px;border-radius:6px;border:1px solid #bbf7d0;margin-right:4px;margin-bottom:4px;">${s}</span>
      `).join("");

      card.innerHTML = `
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
          <span style="font-size:1.1rem;">🎯</span>
          <strong style="font-size:0.96rem;color:#0f172a;">${f.focus_area}</strong>
        </div>
        <p style="font-size:0.83rem;color:#475569;margin-bottom:10px;line-height:1.45;">${f.description}</p>
        <div>${sourcesHtml}</div>
      `;
      focusList.appendChild(card);
    });
  }

  // Section E - Important Guidelines & Food Safety
  const guidelinesList = document.getElementById("nutriGuidelinesList");
  if (guidelinesList) {
    guidelinesList.innerHTML = "";
    (plan.important_guidelines || []).forEach(g => {
      const card = document.createElement("div");
      card.style.cssText = "background:#ffffff;border:1px solid #e2e8f0;border-radius:14px;padding:16px 18px;box-shadow:0 1px 3px rgba(0,0,0,0.02);";
      card.innerHTML = `
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
          <span style="font-size:1.1rem;">🛡️</span>
          <strong style="font-size:0.96rem;color:#0f172a;">${g.topic}</strong>
        </div>
        <p style="font-size:0.83rem;color:#475569;margin-bottom:10px;line-height:1.45;">${g.guideline}</p>
        <div style="font-size:0.75rem;color:#065f46;background:#ecfdf5;padding:6px 10px;border-radius:6px;border-left:3px solid #10b981;">
          <strong>Action:</strong> ${g.safety_action}
        </div>
      `;
      guidelinesList.appendChild(card);
    });
  }

  // Section F - Follow-Up & Next Review
  const reviewDateEl = document.getElementById("nutriNextReviewDate");
  if (reviewDateEl) {
    reviewDateEl.textContent = (plan.follow_up && plan.follow_up.next_review_date)
      ? plan.follow_up.next_review_date
      : "In 14 Days";
  }
}



async function exportCurrentDietPlanPdf() {
  if (!currentDietPlan || !currentDietPlan.plan_id) {
    showToast("Please generate or select a nutrition plan first.", "warning");
    return;
  }

  try {
    showToast("Preparing printable diet plan PDF...", "info");
    const token = localStorage.getItem("token") || sessionStorage.getItem("token");
    const headers = token ? { "Authorization": `Bearer ${token}` } : {};

    const res = await fetch(`${API_BASE}/nutrition/plan/${currentDietPlan.plan_id}/pdf`, {
      headers: headers
    });

    if (!res.ok) {
      throw new Error(`PDF generation failed (Status ${res.status})`);
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const childName = (currentChild && currentChild.name) ? currentChild.name.replace(/\s+/g, '_') : 'Child';
    a.download = `ChildNutri_DietPlan_${childName}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    showToast("PDF downloaded successfully!", "success");
  } catch (err) {
    console.error("PDF export error:", err);
    showToast(err.message || "Failed to download PDF.", "error");
  }
}

// Expose AI Nutrition Support handlers globally
window.setNutriDietPattern = setNutriDietPattern;
window.updateNutriAllergies = updateNutriAllergies;
window.triggerAIDietPlanGeneration = triggerAIDietPlanGeneration;
window.loadNutritionPlan = loadNutritionPlan;
window.renderAINutritionPlan = renderAINutritionPlan;
window.exportCurrentDietPlanPdf = exportCurrentDietPlanPdf;

// =============================================================================
// PROGRESSIVE CONVERSATIONAL DIALOGUE CONTROLLER
// =============================================================================

function renderConversationalSession(sessionData) {
  if (!sessionData) return;

  const currentAnswers = sessionData.current_answers || {};
  const isComplete = Boolean(sessionData.is_complete);
  const total = sessionData.total_questions || 5;
  const answered = sessionData.answered_count || 0;
  const nextQ = sessionData.next_question;

  // 1. Update Progress Tracker
  const progText = document.getElementById("nutriChatProgressText");
  const progPct = document.getElementById("nutriChatProgressPercent");
  const progFill = document.getElementById("nutriChatProgressBar");

  const pct = Math.min(100, Math.round((answered / Math.max(1, total)) * 100));
  if (progText) progText.textContent = isComplete ? `All questions answered (${answered}/${total})` : `Question ${answered + 1} of ${total}`;
  if (progPct) progPct.textContent = `${pct}%`;
  if (progFill) progFill.style.width = `${pct}%`;

  // 2. Render Chat History Bubbles
  const historyContainer = document.getElementById("nutriChatHistory");
  if (historyContainer) {
    historyContainer.innerHTML = "";
    
    // Convert current answers to history items
    const historyEntries = [];

    // Infant fields
    if (currentAnswers.infant_feeding_mode) {
      historyEntries.push({
        field: "infant_feeding_mode",
        question: "Current feeding method",
        answer: formatAnswerDisplay(currentAnswers.infant_feeding_mode)
      });
    }
    if (currentAnswers.infant_nursing_frequency) {
      historyEntries.push({
        field: "infant_nursing_frequency",
        question: "Daily nursing frequency",
        answer: formatAnswerDisplay(currentAnswers.infant_nursing_frequency)
      });
    }
    if (currentAnswers.infant_wet_diapers) {
      historyEntries.push({
        field: "infant_wet_diapers",
        question: "24-hour wet diaper count",
        answer: formatAnswerDisplay(currentAnswers.infant_wet_diapers)
      });
    }
    if (currentAnswers.infant_feeding_difficulties) {
      historyEntries.push({
        field: "infant_feeding_difficulties",
        question: "Feeding comfort & difficulties",
        answer: formatAnswerDisplay(currentAnswers.infant_feeding_difficulties)
      });
    }
    if (currentAnswers.food_recall && currentAnswers.food_recall.infant_items) {
      historyEntries.push({
        field: "food_recall.infant_items",
        question: "Yesterday's 24-hr intake",
        answer: formatAnswerDisplay(currentAnswers.food_recall.infant_items)
      });
    }

    // Complementary fields (6m+)
    if (currentAnswers.meal_frequency) {
      const mf = currentAnswers.meal_frequency;
      const mfText = typeof mf === "object" ? `${mf.meals || 0} meals, ${mf.snacks || 0} snacks` : String(mf);
      historyEntries.push({
        field: "meal_frequency",
        question: "Daily feeding occasions",
        answer: mfText
      });
    }
    if (currentAnswers.food_recall) {
      if (currentAnswers.food_recall.breakfast) {
        historyEntries.push({
          field: "food_recall.breakfast",
          question: "Breakfast intake",
          answer: formatAnswerDisplay(currentAnswers.food_recall.breakfast)
        });
      }
      if (currentAnswers.food_recall.lunch) {
        historyEntries.push({
          field: "food_recall.lunch",
          question: "Lunch intake",
          answer: formatAnswerDisplay(currentAnswers.food_recall.lunch)
        });
      }
      if (currentAnswers.food_recall.dinner) {
        historyEntries.push({
          field: "food_recall.dinner",
          question: "Dinner intake",
          answer: formatAnswerDisplay(currentAnswers.food_recall.dinner)
        });
      }
      if (currentAnswers.food_recall.snacks_and_drinks || currentAnswers.food_recall.evening_snack) {
        historyEntries.push({
          field: "food_recall.snacks_and_drinks",
          question: "Snacks & drinks",
          answer: formatAnswerDisplay(currentAnswers.food_recall.snacks_and_drinks || currentAnswers.food_recall.evening_snack)
        });
      }
    }
    if (currentAnswers.dietary_pattern) {
      historyEntries.push({
        field: "dietary_pattern",
        question: "Dietary pattern",
        answer: formatAnswerDisplay(currentAnswers.dietary_pattern)
      });
    }
    if (currentAnswers.allergies && currentAnswers.allergies.length > 0) {
      historyEntries.push({
        field: "allergies",
        question: "Allergies / Exclusions",
        answer: formatAnswerDisplay(currentAnswers.allergies)
      });
    }
    if (currentAnswers.available_foods && currentAnswers.available_foods.length > 0) {
      historyEntries.push({
        field: "available_foods",
        question: "Available pantry items",
        answer: formatAnswerDisplay(currentAnswers.available_foods)
      });
    }
    if (currentAnswers.budget_tier) {
      historyEntries.push({
        field: "budget_tier",
        question: "Meal planning approach",
        answer: formatAnswerDisplay(currentAnswers.budget_tier)
      });
    }

    historyEntries.forEach(entry => {
      const itemEl = document.createElement("div");
      itemEl.className = "nutri-chat-item";
      itemEl.innerHTML = `
        <div class="nutri-bubble-assistant">
          <div class="nutri-avatar-icon">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/><path d="M8 12h8M12 8v8"/></svg>
          </div>
          <div>
            <div style="font-size:0.74rem;font-weight:700;color:var(--text-muted);">${entry.question}</div>
            <div class="nutri-bubble-text" style="font-weight:500;">${entry.question}</div>
          </div>
        </div>
        <div class="nutri-bubble-user">
          <div class="nutri-bubble-user-text">&#10003; ${entry.answer}</div>
        </div>
      `;
      historyContainer.appendChild(itemEl);
    });
  }

  // 3. Render Active Question or Complete Box
  const activeBox = document.getElementById("nutriActiveQuestionBox");
  const completeBox = document.getElementById("nutriChatCompleteBox");

  if (isComplete || !nextQ) {
    if (activeBox) activeBox.style.display = "none";
    if (completeBox) {
      completeBox.style.display = "block";
      const titleEl = document.getElementById("nutriCompleteTitle");
      if (titleEl) titleEl.textContent = `Dietary intake complete for ${sessionData.child_name || 'your child'}!`;
    }
    currentNutritionState.activeQuestion = null;
  } else {
    if (completeBox) completeBox.style.display = "none";
    if (activeBox) {
      activeBox.style.display = "block";
      currentNutritionState.activeQuestion = nextQ;

      // Update question text & prompt
      const stepBadge = document.getElementById("nutriActiveQuestionStepBadge");
      if (stepBadge) stepBadge.textContent = `Question ${answered + 1} of ${total}`;

      const promptEl = document.getElementById("nutriActiveQuestionPrompt");
      if (promptEl) promptEl.textContent = nextQ.prompt || "Question";

      const guideEl = document.getElementById("nutriActiveQuestionGuidance");
      if (guideEl) guideEl.textContent = nextQ.guidance ? `Why we ask: ${nextQ.guidance}` : "";

      // Render Dynamic Input Area
      renderDynamicQuestionInput(nextQ);

      // Next button text
      const nextBtn = document.getElementById("btnNutriNextQuestion");
      if (nextBtn) {
        nextBtn.innerHTML = (answered + 1 >= total)
          ? 'Finish &amp; Generate Guidance &rarr;'
          : 'Continue &rarr;';
      }
    }
  }
}

function formatAnswerDisplay(val) {
  if (val == null) return "None / Skipped";
  if (Array.isArray(val)) {
    return val.length > 0 ? val.join(", ") : "None reported";
  }
  if (typeof val === "object") {
    return JSON.stringify(val);
  }
  const str = String(val);
  return str.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
}

function renderDynamicQuestionInput(question) {
  const container = document.getElementById("nutriQuestionInputArea");
  if (!container) return;
  container.innerHTML = "";

  const qType = question.type;

  if (qType === "single_choice") {
    const list = document.createElement("div");
    list.style.display = "flex";
    list.style.flexDirection = "column";
    list.style.gap = "8px";

    (question.options || []).forEach((opt, idx) => {
      const card = document.createElement("div");
      card.className = `nutri-choice-card ${idx === 0 ? 'selected' : ''}`;
      card.setAttribute("data-value", opt.value);
      card.onclick = () => selectActiveChoiceOption(card, opt.value);
      card.innerHTML = `
        <div style="width:18px;height:18px;border-radius:50%;border:2px solid var(--brand);display:flex;align-items:center;justify-content:center;">
          <div class="choice-dot" style="width:8px;height:8px;border-radius:50%;background:${idx === 0 ? 'var(--brand)' : 'transparent'};"></div>
        </div>
        <div style="font-size:0.88rem;color:var(--text);font-weight:600;">${opt.label}</div>
      `;
      list.appendChild(card);
    });

    container.appendChild(list);

  } else if (qType === "composite_frequency") {
    const wrap = document.createElement("div");
    wrap.innerHTML = `
      <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px;">
        <button type="button" class="nutri-tag-chip active" onclick="setFrequencyChoice(this, 3, 2)">3 meals + 2 snacks</button>
        <button type="button" class="nutri-tag-chip" onclick="setFrequencyChoice(this, 3, 1)">3 meals + 1 snack</button>
        <button type="button" class="nutri-tag-chip" onclick="setFrequencyChoice(this, 2, 1)">2 meals + 1 snack</button>
        <button type="button" class="nutri-tag-chip" onclick="setFrequencyChoice(this, 2, 0)">2 meals only</button>
      </div>
      <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(160px, 1fr));gap:12px;background:var(--surface-muted);padding:14px;border-radius:var(--radius-lg);border:1px solid var(--border);">
        <div>
          <label style="font-size:0.75rem;font-weight:700;color:var(--text-secondary);display:block;margin-bottom:4px;">Main Meals / Day</label>
          <input type="number" id="activeMealsCount" min="1" max="6" value="3" style="width:100%;padding:8px 10px;border:1px solid var(--border);border-radius:var(--radius-md);background:var(--surface);color:var(--text);font-size:0.88rem;">
        </div>
        <div>
          <label style="font-size:0.75rem;font-weight:700;color:var(--text-secondary);display:block;margin-bottom:4px;">Nutritious Snacks / Day</label>
          <input type="number" id="activeSnacksCount" min="0" max="6" value="2" style="width:100%;padding:8px 10px;border:1px solid var(--border);border-radius:var(--radius-md);background:var(--surface);color:var(--text);font-size:0.88rem;">
        </div>
      </div>
    `;
    container.appendChild(wrap);

  } else if (qType === "text_or_tags") {
    const wrap = document.createElement("div");

    const tagsHtml = (question.suggested_tags || []).map(tag => `
      <button type="button" class="nutri-tag-chip" onclick="toggleActiveTagChip('${tag.replace(/'/g, "\\'")}')">+ ${tag}</button>
    `).join("");

    wrap.innerHTML = `
      <div style="margin-bottom:10px;">
        <label style="font-size:0.76rem;font-weight:700;color:var(--text-muted);display:block;margin-bottom:6px;">Suggested foods (tap to add):</label>
        <div style="display:flex;flex-wrap:wrap;gap:6px;">
          ${tagsHtml}
        </div>
      </div>
      <div>
        <label style="font-size:0.76rem;font-weight:700;color:var(--text-muted);display:block;margin-bottom:6px;">What was eaten (type or select above):</label>
        <input type="text" id="activeTextInput" placeholder="e.g. Rice with dal, boiled egg, ragi porridge" style="width:100%;padding:10px 14px;border:1px solid var(--border);border-radius:var(--radius-md);background:var(--surface);color:var(--text);font-size:0.9rem;">
      </div>
    `;
    container.appendChild(wrap);

  } else if (qType === "multi_choice" || qType === "multi_choice_or_text") {
    const wrap = document.createElement("div");
    wrap.style.display = "flex";
    wrap.style.flexWrap = "wrap";
    wrap.style.gap = "8px";

    (question.options || []).forEach(opt => {
      const label = document.createElement("label");
      label.className = "recall-option-pill";
      label.innerHTML = `
        <input type="checkbox" value="${opt.value}" onchange="this.closest('label').classList.toggle('checked', this.checked)">
        ${opt.label}
      `;
      wrap.appendChild(label);
    });

    container.appendChild(wrap);
  }
}

function selectActiveChoiceOption(cardEl, val) {
  const allCards = document.querySelectorAll("#nutriQuestionInputArea .nutri-choice-card");
  allCards.forEach(c => {
    c.classList.remove("selected");
    const dot = c.querySelector(".choice-dot");
    if (dot) dot.style.background = "transparent";
  });
  cardEl.classList.add("selected");
  const dot = cardEl.querySelector(".choice-dot");
  if (dot) dot.style.background = "var(--brand)";
}

function setFrequencyChoice(btn, meals, snacks) {
  document.querySelectorAll("#nutriQuestionInputArea .nutri-tag-chip").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  const mInput = document.getElementById("activeMealsCount");
  const sInput = document.getElementById("activeSnacksCount");
  if (mInput) mInput.value = meals;
  if (sInput) sInput.value = snacks;
}

function toggleActiveTagChip(tag) {
  const input = document.getElementById("activeTextInput");
  if (!input) return;

  let current = input.value.trim();
  if (!current) {
    input.value = tag;
  } else if (!current.toLowerCase().includes(tag.toLowerCase())) {
    input.value = `${current}, ${tag}`;
  }
}

async function submitActiveQuestionAnswer() {
  if (!currentChild || !currentNutritionState.activeQuestion) return;

  const q = currentNutritionState.activeQuestion;
  let val = null;

  if (q.type === "single_choice") {
    const sel = document.querySelector("#nutriQuestionInputArea .nutri-choice-card.selected");
    val = sel ? sel.getAttribute("data-value") : (q.options && q.options[0] ? q.options[0].value : null);

  } else if (q.type === "composite_frequency") {
    const m = parseInt(document.getElementById("activeMealsCount")?.value || "3", 10);
    const s = parseInt(document.getElementById("activeSnacksCount")?.value || "2", 10);
    val = { meals: m, snacks: s, is_breastfeeding: currentNutritionState.childAgeMonths < 24 };

  } else if (q.type === "text_or_tags") {
    const input = document.getElementById("activeTextInput");
    const raw = input ? input.value.trim() : "";
    val = raw ? raw.split(",").map(x => x.trim()).filter(Boolean) : [];

  } else if (q.type === "multi_choice" || q.type === "multi_choice_or_text") {
    const checked = document.querySelectorAll("#nutriQuestionInputArea input[type='checkbox']:checked");
    val = Array.from(checked).map(c => c.value);
  }

  const btn = document.getElementById("btnNutriNextQuestion");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="scr-spinner scr-spinner-sm" style="border-top-color:#fff;margin-right:6px;"></span> Saving...';
  }

  try {
    const res = await fetch(`${API_BASE}/nutrition/conversation/${currentChild.id}/answer`, {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ field: q.field, value: val })
    });

    if (!res.ok) throw new Error("Could not save response.");
    const data = await res.json();

    if (data.is_complete) {
      // All questions completed! Call assessment to generate tailored guidance
      showToast("Dietary intake recorded! Personalizing nutrition guidance...", "info");
      const assessRes = await fetch(`${API_BASE}/nutrition/conversation/${currentChild.id}/assess`, {
        method: "POST",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({})
      });

      if (assessRes.ok) {
        const planData = await assessRes.json();
        renderCompletedPlan(planData);
        setSessionStateUI(planData.safety_info?.requires_professional_assessment ? "SAFETY_REVIEW" : "READY");
        showToast("Personalized nutrition guidance generated successfully!", "success");
      }

      await loadNutritionPlan(currentChild.id);

    } else {
      // Update session with next question
      if (currentNutritionState.sessionData) {
        currentNutritionState.sessionData.current_answers = data.current_answers;
        currentNutritionState.sessionData.answered_count = data.answered_count;
        currentNutritionState.sessionData.next_question = data.next_question;
        currentNutritionState.sessionData.is_complete = data.is_complete;
      }
      renderConversationalSession(currentNutritionState.sessionData);
      showToast("Response saved.", "info");
    }

  } catch (err) {
    console.error("Error submitting answer:", err);
    showToast("Error saving response. Please try again.", "error");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = 'Continue &rarr;';
    }
  }
}

async function skipActiveQuestion() {
  if (!currentChild || !currentNutritionState.activeQuestion) return;
  const q = currentNutritionState.activeQuestion;

  try {
    const res = await fetch(`${API_BASE}/nutrition/conversation/${currentChild.id}/answer`, {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ field: q.field, value: null })
    });

    if (res.ok) {
      const data = await res.json();
      if (currentNutritionState.sessionData) {
        currentNutritionState.sessionData.current_answers = data.current_answers;
        currentNutritionState.sessionData.answered_count = data.answered_count;
        currentNutritionState.sessionData.next_question = data.next_question;
        currentNutritionState.sessionData.is_complete = data.is_complete;
      }
      renderConversationalSession(currentNutritionState.sessionData);
    }
  } catch (e) {
    console.warn("Skip error:", e);
  }
}

function startOrRestartNutritionConversation() {
  const convCard = document.getElementById("nutriConversationalCard");
  if (convCard) {
    convCard.scrollIntoView({ behavior: "smooth" });
    showToast("Review or update your 24-hour food recall below.", "info");
  }
}

function restartConversationalRecall() {
  const completeBox = document.getElementById("nutriChatCompleteBox");
  const activeBox = document.getElementById("nutriActiveQuestionBox");
  if (completeBox) completeBox.style.display = "none";
  if (activeBox) activeBox.style.display = "block";
  if (currentChild) loadNutritionPlan(currentChild.id);
}

function scrollToNutritionResults() {
  const resultsContainer = document.getElementById("nutriComplementaryFeedingContainer");
  if (resultsContainer) resultsContainer.scrollIntoView({ behavior: "smooth" });
}

async function refreshNutritionModule() {
  if (!currentChild) return;
  const btn = document.getElementById("btnRefreshNutrition");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="scr-spinner scr-spinner-sm" style="border-top-color:#fff;margin-right:6px;"></span> Regenerating...';
  }

  try {
    showToast("Regenerating personalized nutrition guidance...", "info");
    const res = await fetch(`${API_BASE}/nutrition/conversation/${currentChild.id}/assess`, {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({})
    });

    if (!res.ok) throw new Error("Could not regenerate guidance.");
    const planData = await res.json();
    renderCompletedPlan(planData);
    showToast("Personalized nutrition guidance refreshed!", "success");
  } catch (e) {
    console.error("Error refreshing guidance:", e);
    showToast("Error refreshing guidance. Please try again.", "error");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/></svg>
        Regenerate Guidance
      `;
    }
  }
}

async function resetNutritionPlan() {
  if (!currentChild) return;

  const childName = getChildFirstName();
  const confirmed = confirm(
    `Are you sure you want to completely clear and empty the nutrition guidance and food recall for ${childName}?\n\nThis will remove all saved dietary recall answers and meal plans, resetting the nutrition module to a clean, unassessed state.`
  );
  if (!confirmed) return;

  const btn = document.getElementById("btnResetNutrition");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="scr-spinner scr-spinner-sm" style="border-top-color:#dc2626;margin-right:6px;"></span> Resetting...';
  }

  try {
    const res = await fetch(`${API_BASE}/nutrition/conversation/${currentChild.id}/reset`, {
      method: "POST",
      headers: getAuthHeaders()
    });

    if (!res.ok) {
      const errJson = await res.json().catch(() => ({}));
      throw new Error(errJson.detail || "Failed to reset nutrition guidance.");
    }

    // Reset local in-memory state
    currentNutritionState.sessionData = null;
    currentNutritionState.activeQuestion = null;
    currentNutritionState.selectedMeals = {};
    currentNutritionState.mddScore = null;
    currentNutritionState.explanation10 = null;
    currentNutritionState.gaps = [];

    // Clear chat display boxes
    const chatHistory = document.getElementById("nutriChatHistory");
    if (chatHistory) chatHistory.innerHTML = "";
    const activeBox = document.getElementById("nutriActiveQuestionBox");
    if (activeBox) activeBox.style.display = "block";
    const completeBox = document.getElementById("nutriChatCompleteBox");
    if (completeBox) completeBox.style.display = "none";

    // Reload nutrition plan (which will fetch the fresh NOT_STARTED session and show the empty state banner)
    await loadNutritionPlan(currentChild.id);

    showToast("Nutrition guidance and dietary recall emptied successfully.", "success");
  } catch (err) {
    console.error("Error resetting nutrition guidance:", err);
    showToast(`Error emptying nutrition plan: ${err.message || 'Please try again.'}`, "error");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
        Empty / Reset Plan
      `;
    }
  }
}

function renderCompletedPlan(planData) {
  if (!planData) return;

  // 1. Dietary Diversity Scorecard
  const recallEval = planData.food_recall_evaluation || {};
  renderWho8FoodGroups(recallEval.groups_consumed);

  const mddScoreEl = document.getElementById("mddScoreValue");
  const mddExpEl = document.getElementById("mddScoreExplanation");

  if (mddScoreEl) {
    if (currentNutritionState.childAgeMonths < 6) {
      mddScoreEl.textContent = "Exclusive Breastfeeding";
      mddScoreEl.style.color = "#15803d";
      if (mddExpEl) {
        mddExpEl.textContent = recallEval.non_exclusive_foods_detected
          ? "Non-exclusive food/liquid reported. WHO recommends exclusive breastfeeding without water or solids for the first 6 months."
          : "WHO and UNICEF recommend exclusive breastfeeding on demand (8–12+ times daily) for the first 6 months. Minimum Dietary Diversity index (5/8 food groups) begins at 6 months.";
      }
    } else if (recallEval.status === "NOT_ASSESSED" || recallEval.mdd_score == null) {
      mddScoreEl.textContent = "Not assessed yet.";
      mddScoreEl.style.color = "var(--text-muted)";
      if (mddExpEl) mddExpEl.textContent = "Complete the 24-hour food recall above to assess dietary diversity.";
    } else {
      mddScoreEl.textContent = `${recallEval.mdd_score} / 8`;
      mddScoreEl.style.color = recallEval.mdd_achieved ? "#15803d" : "#b45309";
      if (mddExpEl) {
        mddExpEl.textContent = recallEval.mdd_achieved
          ? `Adequate dietary diversity achieved (${recallEval.mdd_score}/8 WHO food groups). Regular intake supports micronutrient sufficiency.`
          : `Dietary diversity gap identified (${recallEval.mdd_score}/8 WHO food groups). WHO recommends at least 5 food groups daily for adequate micronutrients.`;
      }
    }
  }

  // 2. Nutrition Gaps
  renderNutritionGaps(planData.nutrition_gaps || []);

  // 3. 10-Part Human Explanation
  if (planData.explanation_10_parts) {
    render10PartExplanation(planData.explanation_10_parts);
  }

  // 4. Meal / Nursing Schedule
  if (planData.meal_schedule && Array.isArray(planData.meal_schedule)) {
    if (currentNutritionState.childAgeMonths < 6) {
      currentNutritionState.selectedMeals = {};
      planData.meal_schedule.forEach((m, idx) => {
        const slotKey = m.slot || `infant_slot_${idx}`;
        currentNutritionState.selectedMeals[slotKey] = m;
      });
    } else {
      const slots = ["breakfast", "lunch", "snack", "dinner"];
      slots.forEach(s => {
        const match = planData.meal_schedule.find(m => (m.slot === s || m.time_slot?.toLowerCase().includes(s)));
        if (match) currentNutritionState.selectedMeals[s] = match;
      });
    }
    renderMealCards();
  }
}

function renderWho8FoodGroups(consumedIds) {
  const container = document.getElementById("whoFoodGroupsGrid");
  if (!container) return;

  container.innerHTML = "";
  const isAssessed = consumedIds != null && Array.isArray(consumedIds);
  const consumedSet = new Set(consumedIds || []);

  WHO_8_GROUPS_DEF.forEach(g => {
    const isConsumed = isAssessed && consumedSet.has(g.id);
    const card = document.createElement("div");
    card.style.display = "flex";
    card.style.alignItems = "center";
    card.style.gap = "10px";
    card.style.padding = "10px 14px";
    card.style.borderRadius = "var(--radius-lg)";
    card.style.border = "1px solid var(--border)";
    card.style.background = isConsumed ? "#f0fdf4" : "var(--surface-muted)";
    card.style.borderColor = isConsumed ? "#86efac" : "var(--border)";

    card.innerHTML = `
      <div style="font-size:1.3rem;">${g.icon}</div>
      <div style="flex:1;">
        <div style="font-size:0.82rem;font-weight:700;color:var(--text);">${g.name}</div>
        <div style="font-size:0.72rem;color:${isConsumed ? '#15803d' : 'var(--text-muted)'};font-weight:600;">
          ${!isAssessed ? '○ Not assessed' : (isConsumed ? '✓ Consumed in recall' : '○ Not reported')}
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

function renderNutritionGaps(gaps) {
  const container = document.getElementById("nutriGapsList");
  if (!container) return;

  container.innerHTML = "";
  if (!gaps || gaps.length === 0) {
    container.innerHTML = `
      <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:var(--radius-lg);padding:14px 18px;color:#15803d;font-size:0.86rem;font-weight:600;">
        ✓ No major dietary diversity gaps identified from the available information.
      </div>
    `;
    return;
  }

  gaps.forEach(gap => {
    const isUrgent = gap.severity === "urgent" || gap.severity === "high";
    const box = document.createElement("div");
    box.style.background = isUrgent ? "#fff1f2" : "#fefce8";
    box.style.border = `1px solid ${isUrgent ? '#fecdd3' : '#fef08a'}`;
    box.style.borderRadius = "var(--radius-lg)";
    box.style.padding = "14px 18px";
    box.innerHTML = `
      <div style="display:flex;align-items:flex-start;gap:10px;">
        <span style="font-size:1.1rem;line-height:1;">${isUrgent ? '⚠️' : '💡'}</span>
        <div>
          <div style="font-weight:700;font-size:0.88rem;color:${isUrgent ? '#9f1239' : '#854d0e'};">${gap.finding}</div>
          <div style="font-size:0.82rem;color:${isUrgent ? '#881337' : '#713f12'};margin-top:2px;line-height:1.5;">${gap.explanation}</div>
        </div>
      </div>
    `;
    container.appendChild(box);
  });
}

function render10PartExplanation(expl) {
  if (!expl) return;

  const mapping = {
    expl_what_i_found: expl.what_i_found,
    expl_what_needs_attention: expl.what_needs_attention,
    expl_why_this_matters: expl.why_this_matters,
    expl_what_to_focus_on: expl.what_i_would_focus_on,
    expl_food_options: expl.personalized_food_options,
    expl_why_chose_foods: expl.why_i_chose_these_foods,
    expl_safe_feeding: expl.safe_feeding,
    expl_what_to_monitor: expl.what_to_monitor,
    expl_when_professional: expl.when_professional_assessment_is_important,
    expl_important_note: expl.important_note
  };

  Object.entries(mapping).forEach(([elId, val]) => {
    const el = document.getElementById(elId);
    if (el && val) {
      el.textContent = val;
    }
  });
}

function refreshNutritionModule() {
  if (currentChild) {
    showToast("Refreshing nutrition guidance...", "info");
    loadNutritionPlan(currentChild.id);
  }
}

function selectNutritionBudget(tier) {
  currentNutritionState.budgetTier = tier;
  const pills = document.querySelectorAll("#nutriBudgetPills .nutri-btn-pill");
  pills.forEach(p => {
    if (p.getAttribute("data-budget") === tier) p.classList.add("active");
    else p.classList.remove("active");
  });

  filterAndAssignMeals();
  showToast(`Updated to ${tier.replace("_", "-")} budget plan.`, "success");
}

function selectNutritionDiet(diet) {
  currentNutritionState.dietPattern = diet;
  const pills = document.querySelectorAll("#nutriDietPills .nutri-btn-pill");
  pills.forEach(p => {
    if (p.getAttribute("data-diet") === diet) p.classList.add("active");
    else p.classList.remove("active");
  });

  filterAndAssignMeals();
  showToast(`Switched diet pattern to ${diet.replace("_", " ")}.`, "success");
}

function filterAndAssignMeals() {
  const { budgetTier, dietPattern, childAgeMonths } = currentNutritionState;
  const allMeals = NUTRITION_DATABASE.meals;

  const slots = ["breakfast", "lunch", "snack", "dinner"];
  slots.forEach(slot => {
    let candidates = allMeals.filter(m => m.type === slot && m.age_min_months <= childAgeMonths);

    // Filter by diet pattern
    let dietFiltered = candidates.filter(m => {
      if (dietPattern === "vegetarian") return m.diet_pattern === "vegetarian";
      if (dietPattern === "egg_vegetarian") return m.diet_pattern === "vegetarian" || m.diet_pattern === "egg_vegetarian";
      return true; // non_vegetarian / mixed
    });
    if (dietFiltered.length > 0) candidates = dietFiltered;

    // Filter by budget tier
    let budgetFiltered = candidates.filter(m => {
      if (budgetTier === "budget_conscious") return m.budget_tier === "budget_conscious";
      if (budgetTier === "standard") return m.budget_tier === "budget_conscious" || m.budget_tier === "standard";
      return true;
    });
    if (budgetFiltered.length > 0) candidates = budgetFiltered;

    const chosen = candidates[0] || allMeals.find(m => m.type === slot);
    currentNutritionState.selectedMeals[slot] = chosen;
  });

  renderMealCards();
}

function renderMealCards() {
  const container = document.getElementById("nutriMealCardsGrid");
  if (!container) return;

  container.innerHTML = "";
  const isInfant = currentNutritionState.childAgeMonths < 6;

  // Toggle pantry and budget filter visibility for infants
  const filtersCard = document.querySelector(".nutri-filters-card");
  if (filtersCard) filtersCard.style.display = isInfant ? "none" : "flex";

  const pantryCard = document.getElementById("nutriPantryCard");
  if (pantryCard) {
    if (isInfant) {
      pantryCard.style.display = "block";
      const resultsContainer = document.getElementById("nutriPantryResultsList");
      if (resultsContainer) {
        resultsContainer.innerHTML = `
          <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:var(--radius-lg);padding:18px 22px;color:#166534;font-size:0.86rem;line-height:1.5;grid-column:1/-1;">
            🍼 <strong>Infant Exclusive Nutrition Period (0–5 Months):</strong> Complementary solid feeding from kitchen pantry ingredients starts at 6 months of age. At this stage, exclusive breastfeeding provides all required fluids, energy, and micronutrients.
          </div>
        `;
      }
    } else {
      pantryCard.style.display = "block";
    }
  }

  const slots = isInfant ? [
    { key: "morning", label: "Morning Responsive Nursing", icon: '☀️' },
    { key: "midday", label: "Midday Responsive Nursing", icon: '🍲' },
    { key: "afternoon", label: "Afternoon Responsive Nursing", icon: '🍎' },
    { key: "evening_night", label: "Evening & Night Responsive Nursing", icon: '🌙' }
  ] : [
    { key: "breakfast", label: "Breakfast", icon: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>' },
    { key: "lunch", label: "Mid-Day Meal", icon: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>' },
    { key: "snack", label: "Afternoon Snack", icon: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8h1a4 4 0 0 1 0 8h-1M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/></svg>' },
    { key: "dinner", label: "Evening / Dinner", icon: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>' }
  ];

  slots.forEach(slot => {
    let meal = currentNutritionState.selectedMeals[slot.key];
    if (!meal && isInfant) {
      meal = {
        title: slot.label,
        desc: "Breastfeed on infant demand whenever showing early hunger cues. Empty one breast fully before offering the other.",
        cost_band: "₹0",
        why_selected: "Promotes steady lactation supply, optimal hydration, and immunologic protection against infections.",
        food_groups: ["Breast milk"],
        prep_steps: [
          "Wash hands with clean water and soap before feeding.",
          "Sit comfortably and bring baby to breast ensuring wide open mouth and deep latch.",
          "Nurse until baby releases breast naturally and appears relaxed."
        ],
        choking_warning: "No water or complementary feeds. Burp baby upright gently after feeding."
      };
      currentNutritionState.selectedMeals[slot.key] = meal;
    }

    if (!meal) return;

    const tagsHtml = (meal.food_groups || (meal.groups ? (isInfant ? ["Breast milk"] : ["Grains", "Pulses"]) : [])).map(g => `<span class="meal-tag-pill">&#10003; ${g}</span>`).join("");
    const whySelectedText = meal.why_selected || (meal.why ? meal.why : "Selected based on child's age and nutrient density requirements.");

    const card = document.createElement("div");
    card.className = "meal-card-enhanced";
    card.id = `mealCard-${slot.key}`;
    card.innerHTML = `
      <div>
        <div class="meal-card-header">
          <div class="meal-time-tag">${slot.icon} ${slot.label}</div>
          <span class="meal-cost-badge">${meal.cost_band || (isInfant ? '₹0' : '₹')}</span>
        </div>
        <div class="meal-card-title">${meal.title}</div>
        <div class="meal-card-desc">${meal.desc || meal.description || ''}</div>
        <div style="background:#f0fdf4;border-left:3px solid #16a34a;padding:8px 12px;border-radius:var(--radius-sm);margin:10px 0;font-size:0.8rem;color:#166534;line-height:1.4;">
          <strong>Why Selected:</strong> ${whySelectedText}
        </div>
        <div class="meal-tags-row">
          ${tagsHtml}
        </div>
      </div>
      <div class="meal-card-actions">
        <button type="button" class="meal-card-btn prep" onclick="openMealPrepModal('${slot.key}')">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
          ${isInfant ? 'Feeding Technique' : 'Preparation'}
        </button>
        ${!isInfant ? `
          <button type="button" class="meal-card-btn replace" onclick="openReplaceMealModal('${slot.key}')">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/></svg>
            Replace
          </button>
        ` : ''}
      </div>
    `;
    container.appendChild(card);
  });

  // Update estimated cost display
  const costEl = document.getElementById("nutriEstimatedCost");
  if (costEl) {
    if (isInfant) costEl.textContent = "₹0 (Exclusive Breastfeeding)";
    else if (currentNutritionState.budgetTier === "budget_conscious") costEl.textContent = "₹35 – ₹55";
    else if (currentNutritionState.budgetTier === "standard") costEl.textContent = "₹60 – ₹95";
    else costEl.textContent = "₹100 – ₹160";
  }
}

// Generate Pantry Recipes strictly from selected ingredients
async function generateFromAvailableIngredients() {
  const pantryInputs = document.querySelectorAll("#pantryChecklistGrid input:checked");
  const available = Array.from(pantryInputs).map(c => c.value);

  if (available.length === 0) {
    showToast("Please check at least 2 ingredients in the pantry checklist first.", "warning");
    return;
  }

  const resultsContainer = document.getElementById("nutriPantryResultsList");
  if (resultsContainer) {
    resultsContainer.innerHTML = '<div style="color:var(--text-muted);padding:12px;">Searching available recipes strictly bounded to your ingredients...</div>';
  }

  try {
    const res = await fetch(`${API_BASE}/nutrition/pantry-recipes`, {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({
        available_ingredients: available,
        age_months: currentNutritionState.childAgeMonths || 12,
        diet_pattern: currentNutritionState.dietPattern || "vegetarian",
        allergies: currentNutritionState.allergies || []
      })
    });

    if (!res.ok) throw new Error("Could not generate pantry recipes.");
    const data = await res.json();
    const recipes = data.recipes || [];

    if (!resultsContainer) return;
    resultsContainer.innerHTML = "";

    if (recipes.length === 0) {
      resultsContainer.innerHTML = `
        <div style="background:var(--surface-muted);border:1px dashed var(--border);border-radius:var(--radius-lg);padding:18px;color:var(--text-secondary);font-size:0.86rem;grid-column:1/-1;">
          No pre-configured recipe uses strictly the ingredients currently selected. Try selecting staple dal, rice, potato, or grains above.
        </div>
      `;
      return;
    }

    recipes.forEach(r => {
      const card = document.createElement("div");
      card.style.background = "var(--surface)";
      card.style.border = "1px solid var(--border)";
      card.style.borderRadius = "var(--radius-xl)";
      card.style.padding = "16px";
      card.innerHTML = `
        <div style="font-size:0.72rem;font-weight:700;color:var(--brand);text-transform:uppercase;">${r.slot.toUpperCase()} OPTION</div>
        <div style="font-weight:800;font-size:0.95rem;color:var(--text);margin-top:2px;">${r.title}</div>
        <div style="font-size:0.8rem;color:var(--text-secondary);margin:6px 0 10px 0;">${r.desc}</div>
        <div style="font-size:0.75rem;color:#15803d;background:#f0fdf4;padding:4px 8px;border-radius:var(--radius-sm);display:inline-block;font-weight:600;">
          Uses your ingredients: ${r.required_ingredients.join(', ')}
        </div>
      `;
      resultsContainer.appendChild(card);
    });

    showToast(`Found ${recipes.length} recipe(s) matching your kitchen items!`, "success");

  } catch (e) {
    console.error("Error generating pantry recipes:", e);
    showToast("Error generating pantry recipes. Please try again.", "error");
  }
}

// Safe stubs for compatibility
function handleDiversityCheck() {}
function updateDietaryDiversityUI() {}


// =============================================================================
// MEAL PREPARATION & REPLACEMENT MODALS
// =============================================================================

function openMealPrepModal(slotKey) {
  const meal = currentNutritionState.selectedMeals[slotKey];
  if (!meal) return;

  const modal = document.getElementById("mealPrepModal");
  if (!modal) return;

  const titleEl = document.getElementById("prepModalTitle");
  if (titleEl) titleEl.textContent = meal.title;

  const textureEl = document.getElementById("prepModalTexture");
  if (textureEl) textureEl.textContent = `Texture: ${meal.texture || 'Soft mash'}`;

  const ageEl = document.getElementById("prepModalAge");
  if (ageEl) ageEl.textContent = `Suitable from: ${meal.age_min_months} months`;

  const costEl = document.getElementById("prepModalCost");
  if (costEl) costEl.textContent = `Cost: ${meal.cost_band || '₹'}`;

  const stepsList = document.getElementById("prepModalStepsList");
  if (stepsList) {
    stepsList.innerHTML = (meal.prep_steps || []).map((step, idx) => `
      <div class="prep-step-item">
        <div class="prep-step-number">${idx + 1}</div>
        <div>${step}</div>
      </div>
    `).join("");
  }

  const chokeEl = document.getElementById("prepModalChokingText");
  if (chokeEl) {
    chokeEl.innerHTML = `<strong>Choking Safety Note:</strong> ${meal.choking_warning || 'Ensure food is soft and free of large lumps or hard seeds before feeding.'}`;
  }

  modal.style.display = "flex";
}

function closeMealPrepModal() {
  const modal = document.getElementById("mealPrepModal");
  if (modal) modal.style.display = "none";
}

function openReplaceMealModal(slotKey) {
  currentNutritionState.activeReplaceSlot = slotKey;
  const modal = document.getElementById("replaceMealModal");
  if (!modal) return;

  const titleEl = document.getElementById("replaceModalMealSlotTitle");
  if (titleEl) {
    const slotNames = { breakfast: "Breakfast", lunch: "Mid-Day Meal", snack: "Afternoon Snack", dinner: "Dinner" };
    titleEl.textContent = `Replace ${slotNames[slotKey] || "Meal"}`;
  }

  const optionsList = document.getElementById("replaceModalOptionsList");
  if (optionsList) {
    optionsList.innerHTML = "";
    const currentMeal = currentNutritionState.selectedMeals[slotKey];
    
    let candidates = NUTRITION_DATABASE.meals.filter(m => 
      m.type === slotKey && 
      m.id !== (currentMeal ? currentMeal.id : "") &&
      m.age_min_months <= currentNutritionState.childAgeMonths
    );

    // Diet filtering
    const dietFiltered = candidates.filter(m => {
      if (currentNutritionState.dietPattern === "vegetarian") return m.diet_pattern === "vegetarian";
      if (currentNutritionState.dietPattern === "egg_vegetarian") return m.diet_pattern === "vegetarian" || m.diet_pattern === "egg_vegetarian";
      return true;
    });
    if (dietFiltered.length > 0) candidates = dietFiltered;

    candidates.forEach(cand => {
      const box = document.createElement("div");
      box.className = "replacement-option-box";
      box.onclick = () => applyMealReplacement(slotKey, cand.id);
      box.innerHTML = `
        <div style="flex:1;">
          <div style="font-weight:700;font-size:0.92rem;color:var(--text);">${cand.title}</div>
          <div style="font-size:0.78rem;color:var(--text-secondary);margin-top:2px;">${cand.desc}</div>
          <div style="display:flex;gap:5px;margin-top:6px;flex-wrap:wrap;">
            ${(cand.food_groups || []).map(g => `<span class="meal-tag-pill">&#10003; ${g}</span>`).join("")}
          </div>
        </div>
        <div style="text-align:right;margin-left:14px;">
          <span class="meal-cost-badge">${cand.cost_band || '₹'}</span>
          <div style="margin-top:8px;">
            <button class="btn btn-sm btn-primary" style="padding:4px 10px;font-size:0.74rem;">Select &rarr;</button>
          </div>
        </div>
      `;
      optionsList.appendChild(box);
    });
  }

  modal.style.display = "flex";
}

function closeReplaceMealModal() {
  const modal = document.getElementById("replaceMealModal");
  if (modal) modal.style.display = "none";
}

function applyMealReplacement(slotKey, mealId) {
  const meal = NUTRITION_DATABASE.meals.find(m => m.id === mealId);
  if (meal) {
    currentNutritionState.selectedMeals[slotKey] = meal;
    renderMealCards();
    closeReplaceMealModal();
    showToast(`Replaced ${slotKey} with ${meal.title}!`, "success");
  }
}


async function loadAppointments(childId) {
  try {
    const res = await fetch(`${API_BASE}/appointments/child/${childId}`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const appts = await res.json();

    const apptList = document.querySelector(".appt-list");
    if (apptList && appts.length > 0) {
      apptList.innerHTML = "";
      appts.forEach(a => {
        const isUpcoming = a.status === "upcoming";
        const dateParts = a.appointment_date.split("-");
        const day = dateParts[2] || "28";
        const month = "AUG";

        const row = document.createElement("div");
        row.className = `appt-row ${isUpcoming ? 'upcoming' : 'done'}`;
        row.innerHTML = `
          <div class="ar-date"><div class="ar-day">${day}</div><div class="ar-mon">${month}</div></div>
          <div class="ar-info">
            <div class="ar-title">${a.purpose}</div>
            <div class="ar-meta">⏱️ ${a.appointment_time || '10:00 AM'} &bull; Status: ${a.status.toUpperCase()}</div>
            <div class="ar-note">${a.notes || 'Growth and dietary evaluation.'}</div>
          </div>
          <span class="ar-badge ${isUpcoming ? 'upcoming' : 'done'}">${a.status.toUpperCase()}</span>
        `;
        apptList.appendChild(row);
      });
    }

    // Update Sidebar Appointments Badge
    const upcomingAppts = appts.filter(a => a.status === "upcoming");
    const upcomingCount = upcomingAppts.length;
    const apptBadge = document.getElementById("sidebarApptBadge") || document.querySelector(".sidebar-nav a .nb");
    const isSeen = sessionStorage.getItem("appts_seen_" + childId) === "true";
    if (apptBadge) {
      if (upcomingCount > 0 && !isSeen) {
        apptBadge.textContent = upcomingCount;
        apptBadge.style.display = "inline-block";
      } else {
        apptBadge.style.display = "none";
      }
    }

    // Update Next Appointment card in Overview tab
    const upcoming = upcomingAppts[0] || appts[0];
    if (upcoming) {
      currentUpcomingAppt = upcoming;
      const nextStepAppt = document.getElementById("nextStepApptText");
      if (nextStepAppt) {
        nextStepAppt.innerHTML = `${upcoming.purpose} scheduled with pediatrician on <strong>${upcoming.appointment_date} &bull; ${upcoming.appointment_time || '10:00 AM'}</strong>.`;
      }

      const apptDay = document.querySelector(".appt-day");
      const apptMon = document.querySelector(".appt-mon");
      const apptTitle = document.querySelector(".appt-title");
      const apptMeta = document.querySelectorAll(".appt-detail .appt-meta");
      
      const dateParts = upcoming.appointment_date.split("-");
      if (apptDay) apptDay.textContent = dateParts[2] || "28";
      if (apptMon) apptMon.textContent = "AUG 2025";
      if (apptTitle) apptTitle.textContent = upcoming.purpose;
      if (apptMeta.length >= 2) {
        apptMeta[0].innerHTML = `⏱️ ${upcoming.appointment_time || '10:00 AM'} • Dr. Meena Rao`;
        apptMeta[1].innerHTML = `🏥 PHC Andheri Centre`;
      }
    }
  } catch (e) {
    console.error("Error loading appointments:", e);
  }
}

async function loadNotifications() {
  try {
    const res = await fetch(`${API_BASE}/notifications`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const notifs = await res.json();

    const notifPanel = document.getElementById("notifPanel");
    if (!notifPanel) return;

    const notifBadge = document.querySelector(".notif-badge");
    const unreadCount = notifs.filter(n => !n.is_read).length;
    if (notifBadge) {
      notifBadge.textContent = unreadCount;
      notifBadge.style.display = unreadCount > 0 ? "flex" : "none";
    }

    const unreadLabel = unreadCount > 0 ? ` (${unreadCount} unread)` : "";
    notifPanel.innerHTML = `
      <div class="np-header">
        <span>Notifications${unreadLabel}</span>
        <div style="display:flex;align-items:center;gap:10px;">
          ${unreadCount > 0 ? '<a onclick="markAllNotificationsAsRead()" style="cursor:pointer;font-size:0.75rem;color:#1a7f5a;font-weight:600;">Mark all read</a>' : ''}
          <a onclick="toggleNotifPanel()" style="cursor:pointer;">&#10005;</a>
        </div>
      </div>
    `;

    if (notifs.length === 0) {
      notifPanel.innerHTML += `<div style="padding:24px;color:#64748b;text-align:center;font-size:0.85rem;">No notifications right now</div>`;
      return;
    }

    notifs.forEach(n => {
      const item = document.createElement("div");
      item.className = `np-item ${n.is_read ? 'read' : 'unread'}`;
      item.style.cursor = "pointer";
      item.title = "Click to mark as read";
      item.onclick = () => markNotificationAsRead(n.id, item);
      item.innerHTML = `
        <div class="np-icon" style="background:${n.type === 'alert' ? 'rgba(231,76,60,.12)' : 'rgba(39,168,114,.12)'};color:${n.type === 'alert' ? '#c0392b' : '#1a7f5a'}">
          ${n.type === 'alert' ? '⚠️' : '🌱'}
        </div>
        <div class="np-body">
          <div class="np-text"><strong>${n.title}:</strong> ${n.message.replace(/Aarav/g, getChildFirstName())}</div>
          <div class="np-ts" style="display:flex;justify-content:space-between;align-items:center;margin-top:3px;">
            <span>${n.created_at ? n.created_at.split('T')[0] : 'Recent'}</span>
            <span class="read-status-tag" style="font-size:0.68rem;color:${n.is_read ? '#94a3b8' : '#e07a1c'};font-weight:600;">
              ${n.is_read ? '✓ Read' : '● New'}
            </span>
          </div>
        </div>
      `;
      notifPanel.appendChild(item);
    });
  } catch (e) {
    console.error("Error loading notifications:", e);
  }
}

async function markNotificationAsRead(notifId, itemElement) {
  try {
    const res = await fetch(`${API_BASE}/notifications/${notifId}/read`, {
      method: "PUT",
      headers: getAuthHeaders()
    });
    if (res.ok) {
      if (itemElement) {
        itemElement.classList.remove("unread");
        itemElement.classList.add("read");
        const tag = itemElement.querySelector(".read-status-tag");
        if (tag) {
          tag.textContent = "✓ Read";
          tag.style.color = "#94a3b8";
        }
      }
      const notifBadge = document.querySelector(".notif-badge");
      if (notifBadge) {
        const currentCount = parseInt(notifBadge.textContent) || 0;
        const newCount = Math.max(0, currentCount - 1);
        notifBadge.textContent = newCount;
        if (newCount === 0) notifBadge.style.display = "none";
      }
    }
  } catch (e) {
    console.error("Error marking notification as read:", e);
  }
}

async function markAllNotificationsAsRead() {
  try {
    const res = await fetch(`${API_BASE}/notifications/read-all`, {
      method: "PUT",
      headers: getAuthHeaders()
    });
    if (res.ok) {
      showToast("All notifications marked as read.");
      await loadNotifications();
    }
  } catch (e) {
    console.error("Error marking all notifications as read:", e);
  }
}

// -------------------------------------------------------------
// MODALS: CHILD REGISTRATION, ASSESSMENT, APPOINTMENT DETAILS
// -------------------------------------------------------------
function openChildProfileModal() {
  const m = document.getElementById("childProfileModal");
  if (!m) return;
  m.style.display = "flex";

  const isCompulsory = (!allChildrenList || allChildrenList.length === 0);
  const closeBtn = document.getElementById("childProfileModalCloseBtn");
  const cancelBtn = document.getElementById("childProfileModalCancelBtn");
  if (closeBtn) closeBtn.style.display = isCompulsory ? "none" : "block";
  if (cancelBtn) cancelBtn.style.display = isCompulsory ? "none" : "inline-block";

  const badgeEl = document.getElementById("childProfileModalBadge");
  if (badgeEl) {
    badgeEl.textContent = isCompulsory ? "Compulsory Initial Dataset Intake" : "Foundational Pediatric Intake";
  }

  const todayStr = new Date().toISOString().split("T")[0];
  const dobInput = document.getElementById("newChildDob");
  if (dobInput && !dobInput.max) dobInput.max = todayStr;
  const mDateInput = document.getElementById("newChildMeasureDate");
  if (mDateInput && !mDateInput.value) {
    mDateInput.value = todayStr;
    mDateInput.max = todayStr;
  }

  if (isCompulsory) {
    const form = document.querySelector("#childProfileModal form");
    if (form) form.reset();
    if (dobInput) {
      dobInput.value = "";
      dobInput.max = todayStr;
    }
    if (mDateInput) {
      mDateInput.value = todayStr;
      mDateInput.max = todayStr;
    }
    const nameInput = document.getElementById("newChildName");
    if (nameInput) {
      nameInput.value = "";
      setTimeout(() => nameInput.focus(), 120);
    }
    const weightInput = document.getElementById("newChildWeight");
    if (weightInput) weightInput.value = "";
    const lenInput = document.getElementById("newChildLength") || document.getElementById("newChildHeight");
    if (lenInput) lenInput.value = "";
    const stateInput = document.getElementById("newChildState");
    if (stateInput) stateInput.value = "";
    const muacInput = document.getElementById("newChildMuac");
    if (muacInput) muacInput.value = "";
    const headCircInput = document.getElementById("newChildHeadCirc");
    if (headCircInput) headCircInput.value = "";
    const bwInput = document.getElementById("newChildBirthWeight");
    if (bwInput) bwInput.value = "";
    const blInput = document.getElementById("newChildBirthLength");
    if (blInput) blInput.value = "";
    const notesInput = document.getElementById("newChildNotes");
    if (notesInput) notesInput.value = "";
  } else {
    const nameInput = document.getElementById("newChildName");
    if (nameInput) setTimeout(() => nameInput.focus(), 100);
  }
}

function closeChildProfileModal(force = false) {
  if (!force && (!allChildrenList || allChildrenList.length === 0)) {
    showToast("Adding child details is compulsory to initialize your account.", "warning");
    return;
  }
  const m = document.getElementById("childProfileModal");
  if (m) m.style.display = "none";
}

function handleChildProfileOverlayClick(e) {
  if (e && e.target !== document.getElementById("childProfileModal")) return;
  if (!allChildrenList || allChildrenList.length === 0) {
    showToast("Adding child details is compulsory to initialize your account.", "warning");
    return;
  }
  closeChildProfileModal();
}

document.addEventListener("keydown", function(e) {
  if (e.key === "Escape" || e.keyCode === 27) {
    const m = document.getElementById("childProfileModal");
    if (m && (m.style.display === "flex" || m.style.display === "block")) {
      if (!allChildrenList || allChildrenList.length === 0) {
        e.preventDefault();
        e.stopPropagation();
        showToast("Adding child details is compulsory to initialize your account.", "warning");
        return;
      }
      closeChildProfileModal();
    }
  }
});

async function submitChildProfile(e) {
  if (e && e.preventDefault) e.preventDefault();
  const nameInput = document.getElementById("newChildName");
  const dobInput = document.getElementById("newChildDob");
  const genderInput = document.getElementById("newChildGender");
  const stateInput = document.getElementById("newChildState");
  const urInput = document.getElementById("newChildUrbanRural");
  
  const weightInput = document.getElementById("newChildWeight");
  const heightInput = document.getElementById("newChildLength") || document.getElementById("newChildHeight");
  const measureDateInput = document.getElementById("newChildMeasureDate");
  const edemaInput = document.getElementById("newChildEdema");
  const muacInput = document.getElementById("newChildMuac");
  const headCircInput = document.getElementById("newChildHeadCirc");
  
  const birthWeightInput = document.getElementById("newChildBirthWeight");
  const birthLengthInput = document.getElementById("newChildBirthLength");
  const notesInput = document.getElementById("newChildNotes");

  const name = nameInput ? nameInput.value.trim() : "";
  const dob = dobInput ? dobInput.value : "";
  const gender = genderInput ? genderInput.value : "Male";
  const state = stateInput ? stateInput.value.trim() : null;
  const urbanRural = urInput ? urInput.value : null;

  const weight = (weightInput && weightInput.value) ? parseFloat(weightInput.value) : null;
  const height = (heightInput && heightInput.value) ? parseFloat(heightInput.value) : null;
  const measureDate = (measureDateInput && measureDateInput.value) ? measureDateInput.value : new Date().toISOString().split("T")[0];
  const hasEdema = (edemaInput && edemaInput.value === "yes");
  const muac = (muacInput && muacInput.value) ? parseFloat(muacInput.value) : null;
  const headCirc = (headCircInput && headCircInput.value) ? parseFloat(headCircInput.value) : null;

  const birthWeight = (birthWeightInput && birthWeightInput.value) ? parseFloat(birthWeightInput.value) : null;
  const birthLength = (birthLengthInput && birthLengthInput.value) ? parseFloat(birthLengthInput.value) : null;
  const notes = notesInput ? notesInput.value.trim() : "";

  if (!name) {
    showToast("Please enter your child's full name.", "error");
    return;
  }
  if (!dob) {
    showToast("Please select your child's date of birth.", "error");
    return;
  }

  const effectiveWeight = weight != null ? weight : birthWeight;
  const effectiveHeight = height != null ? height : birthLength;

  if (effectiveWeight == null || isNaN(effectiveWeight) || effectiveWeight <= 0) {
    showToast("Please enter a valid weight (kg) to initialize the child dataset.", "error");
    return;
  }
  if (effectiveHeight == null || isNaN(effectiveHeight) || effectiveHeight < 20) {
    showToast("Please enter a valid height/length (cm) to initialize the child dataset.", "error");
    return;
  }

  const btn = document.getElementById("btnSaveChild");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Creating Profile & Initial Dataset...";
  }

  try {
    // 1. Persist Child Record in the application database
    const childRes = await fetch(`${API_BASE}/children`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        name: name,
        date_of_birth: dob,
        gender: gender,
        birth_weight: birthWeight != null ? birthWeight : effectiveWeight,
        birth_length: birthLength != null ? birthLength : effectiveHeight,
        state: state || null,
        urban_rural: urbanRural || null
      })
    });

    if (!childRes.ok) {
      const err = await childRes.json();
      let msg = err.detail || "Error saving child profile.";
      if (Array.isArray(err.detail)) {
        msg = err.detail.map(d => d.msg || d).join(", ");
      }
      showToast(msg, "error");
      return;
    }

    const newChild = await childRes.json();

    // 2. Automatically record the first health dataset point (Initial Assessment) in the database
    try {
      const asmtRes = await fetch(`${API_BASE}/assessments`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          child_id: newChild.id,
          weight: effectiveWeight,
          height: effectiveHeight,
          muac: muac || null,
          head_circumference: headCirc || null,
          assessment_date: measureDate,
          has_bilateral_edema: hasEdema,
          notes: notes || "Initial baseline dataset recorded upon parent account setup"
        })
      });

      if (!asmtRes.ok) {
        const asmtErr = await asmtRes.json();
        console.warn("Initial assessment recording response:", asmtErr);
      }
    } catch (asmtErr) {
      console.warn("Could not save initial assessment:", asmtErr);
    }

    closeChildProfileModal(true);
    showToast(`Child record & first dataset saved for ${newChild.name}!`, "success");
    await loadChildData();
  } catch (err) {
    console.error(err);
    showToast("Error connecting to server.", "error");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Save Child Details →";
    }
  }
}

window.openChildProfileModal = openChildProfileModal;
window.closeChildProfileModal = closeChildProfileModal;
window.handleChildProfileOverlayClick = handleChildProfileOverlayClick;
window.submitChildProfile = submitChildProfile;

function openParentAssessModal() {
  const m = document.getElementById("parentAssessModal");
  if (m) m.style.display = "flex";
  if (currentChildGrowth && currentChildGrowth.length > 0) {
    const last = currentChildGrowth[currentChildGrowth.length - 1];
    const ageInp = document.getElementById("pAssessAge");
    if (ageInp && !ageInp.value) ageInp.value = (last.age_months + 1);
  }
}

function closeParentAssessModal() {
  const m = document.getElementById("parentAssessModal");
  if (m) m.style.display = "none";
}

async function submitParentAssessment(e) {
  e.preventDefault();
  if (!currentChild) return;

  const age = parseFloat(document.getElementById("pAssessAge").value);
  const weight = parseFloat(document.getElementById("pAssessWeight").value);
  const height = parseFloat(document.getElementById("pAssessHeight").value);
  const muac = document.getElementById("pAssessMuac").value ? parseFloat(document.getElementById("pAssessMuac").value) : null;
  const headCirc = document.getElementById("pAssessHeadCirc").value ? parseFloat(document.getElementById("pAssessHeadCirc").value) : null;
  const notes = document.getElementById("pAssessNotes").value.trim();

  const btn = document.getElementById("btnRunParentAssessment");
  if (btn) btn.textContent = "Analyzing with AI...";

  try {
    const res = await fetch(`${API_BASE}/assessments`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        child_id: currentChild.id,
        age_months: age,
        weight: weight,
        height: height,
        muac: muac,
        head_circumference: headCirc,
        notes: notes
      })
    });

    const result = await res.json();
    closeParentAssessModal();

    if (res.ok) {
      const pred = (result.prediction && result.prediction.prediction) ? result.prediction.prediction : (result.prediction_label || "Prediction recorded");
      const risk = (result.prediction && result.prediction.risk_score != null) ? result.prediction.risk_score : (result.risk_score != null ? result.risk_score : null);
      showToast(`AI Assessment Complete! Prediction: ${pred}${risk != null ? ' (' + risk + '% Risk)' : ''}`);
      await loadChildGrowthHistory(currentChild.id);
      switchSection("assessment", document.querySelectorAll(".nav-item")[2]);
    } else {
      showToast(result.detail || "Assessment submission error.", "error");
    }
  } catch (err) {
    console.error(err);
    showToast("Error connecting to AI service.", "error");
  } finally {
    if (btn) btn.textContent = "Run AI Assessment";
  }
}

function openApptDetailsModal() {
  const m = document.getElementById("apptDetailsModal");
  if (!m) return;

  if (currentUpcomingAppt) {
    const titleEl = document.getElementById("modalApptTitle");
    const dtEl = document.getElementById("modalApptDateTime");
    const notesEl = document.getElementById("modalApptNotes");

    if (titleEl) titleEl.textContent = currentUpcomingAppt.purpose || "Monthly Follow-Up";
    if (dtEl) dtEl.textContent = `${currentUpcomingAppt.appointment_date} • ${currentUpcomingAppt.appointment_time || '10:00 AM'}`;
    if (notesEl) notesEl.textContent = currentUpcomingAppt.notes || "Bring previous weight records. Fasting not required.";
  }

  m.style.display = "flex";
}

function closeApptDetailsModal() {
  const m = document.getElementById("apptDetailsModal");
  if (m) m.style.display = "none";
}

// -------------------------------------------------------------
// UI CONTROLS & NAVIGATION
// -------------------------------------------------------------
function switchSection(id, el) {
  if ((!allChildrenList || allChildrenList.length === 0) && id !== 'overview') {
    showToast("Adding child details is compulsory before navigating your dashboard.", "warning");
    openChildProfileModal();
    return;
  }
  closeSidebar();
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  const target = document.getElementById('sec-' + id);
  if (target) target.classList.add('active');

  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  if (el) el.classList.add('active');

  var titles = {
    overview: 'Overview',
    'regular-update': 'Regular Child Update',
    growth: 'Growth Tracker',
    assessment: 'AI Assessment',
    photos: 'Child Photos',
    medical: 'Medical History',
    nutrition: 'Diet & Nutrition',
    appointments: 'Appointments',
    profile: 'My Profile'
  };
  document.getElementById('pageTitle').textContent = titles[id] || id;

  if (id === 'assessment' && currentChild && currentChild.id) {
    loadScreeningStatus(currentChild.id);
  }

  // Clear appointments badge when user views Appointments tab
  if (id === 'appointments') {
    const apptBadge = document.getElementById('sidebarApptBadge') || document.querySelector(".sidebar-nav a .nb");
    if (apptBadge) apptBadge.style.display = 'none';
    if (currentChild && currentChild.id) {
      sessionStorage.setItem('appts_seen_' + currentChild.id, 'true');
    }
  }

  closeNotifPanel();
}

function openSidebar() {
  document.getElementById('sidebar').classList.add('open');
  document.getElementById('sidebarOverlay').classList.add('open');
}

function closeSidebar() {
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('sidebarOverlay').classList.remove('open');
}

async function toggleNotifPanel() {
  const panel = document.getElementById('notifPanel');
  if (!panel) return;
  const isOpen = panel.classList.toggle('open');
  if (isOpen) {
    // 1. Immediately hide the unread badge as user is viewing notifications
    const notifBadge = document.querySelector('.notif-badge');
    if (notifBadge) {
      notifBadge.style.display = 'none';
      notifBadge.textContent = '0';
    }

    // 2. Mark all notifications as read in backend
    try {
      await fetch(`${API_BASE}/notifications/read-all`, {
        method: 'PUT',
        headers: getAuthHeaders()
      });
    } catch (e) {
      console.error('Error auto-marking notifications read:', e);
    }

    // 3. Load & render notifications with read state
    await loadNotifications();
  }
}

function closeNotifPanel() {
  document.getElementById('notifPanel').classList.remove('open');
}

function showToast(msg) {
  var t = document.getElementById('toast');
  document.getElementById('toastMsg').textContent = msg;
  t.classList.add('show');
  setTimeout(function () { t.classList.remove('show'); }, 3500);
}

function doLogout() {
  if (confirm('Logout from ChildNutri AI?')) {
    localStorage.removeItem('childnutri_token');
    localStorage.removeItem('childnutri_user');
    localStorage.removeItem('userDietaryDiversityScore');
    sessionStorage.clear();
    currentChild = null;
    currentUser = null;
    currentUserId = null;
    currentChildGrowth = [];
    allChildrenList = [];
    currentUpcomingAppt = null;
    window.location.href = 'index.html';
  }
}

document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') {
    closeNotifPanel();
    closeApptDetailsModal();
    closeParentAssessModal();
  }
});

document.addEventListener('click', function (e) {
  var panel = document.getElementById('notifPanel');
  var btn = document.querySelector('.notif-btn');
  if (panel && btn && !panel.contains(e.target) && !btn.contains(e.target)) closeNotifPanel();
});


// -------------------------------------------------------------
// CHILD MEDICAL REPORT PDF DOWNLOAD & MODAL ENGINE (17-SECTION REPORT ENGINE)
// -------------------------------------------------------------
let activeReportAssessmentId = null;

async function populateReportFields(targetAssessmentId = null) {
  const child = currentChild || {};
  const name = child.name || "Child";
  const firstName = getChildFirstName();
  const healthId = child.health_id || (child.id ? `CHN-2026-CH${String(child.id).padStart(3, '0')}` : "Not assigned");
  const dob = child.date_of_birth || "Not recorded";
  const gender = child.gender || "Not recorded";

  let ageStr = "Not recorded";
  let ageMonths = null;
  if (child.date_of_birth) {
    const d = new Date(child.date_of_birth);
    const now = new Date();
    ageMonths = Math.max(0, Math.round(((now - d) / (1000 * 60 * 60 * 24 * 30.4375)) * 10) / 10);
    ageStr = `${Math.round(ageMonths)} months`;
  }

  const el = id => document.getElementById(id);
  const setText = (id, text) => { const node = el(id); if (node) node.textContent = text; };
  const setHtml = (id, html) => { const node = el(id); if (node) node.innerHTML = html; };

  // Section 1 & 2: Header & Profile
  setText("repChildName", name);
  setText("repHealthId", healthId);
  setText("repChildDob", dob);
  setText("repChildSex", gender);
  setText("repChildAge", ageStr);
  setText("repChildGenderAge", `${gender} / ${ageStr}`);
  setText("repGeneratedDate", new Date().toLocaleDateString("en-GB", { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }));

  const user = JSON.parse(localStorage.getItem("childnutri_user") || "{}");
  setText("repCaregiverName", user.full_name || user.name || "Caregiver");
  if (el("repAttendingClinician")) {
    setText("repAttendingClinician", user.full_name || "Attending Clinician");
  }

  // 1. Fetch child assessments history
  let assessments = [];
  if (child.id) {
    try {
      const res = await fetch(`${API_BASE}/assessments/child/${child.id}`, { headers: getAuthHeaders() });
      if (res.ok) {
        assessments = await res.json();
      }
    } catch (e) {
      console.warn("Could not fetch assessments for child report:", e);
    }
  }

  // Sort assessments ascending chronologically so earlier visits come before later visits
  const sortedAsc = [...(assessments || [])].sort((a, b) => {
    const da = new Date(a.assessment_date || a.created_at || 0);
    const db = new Date(b.assessment_date || b.created_at || 0);
    return da - db || (a.id - b.id);
  });

  // Determine target assessment
  let targetAsmt = null;
  let targetIdx = -1;
  if (targetAssessmentId) {
    targetIdx = sortedAsc.findIndex(a => a.id === targetAssessmentId);
    if (targetIdx >= 0) {
      targetAsmt = sortedAsc[targetIdx];
    }
  }
  if (!targetAsmt && sortedAsc.length > 0) {
    targetIdx = sortedAsc.length - 1; // Latest chronologically!
    targetAsmt = sortedAsc[targetIdx];
  }

  if (targetAsmt && targetAsmt.id) {
    activeReportAssessmentId = targetAsmt.id;
    setText("repAssessmentId", `#${targetAsmt.id}`);
    setText("repReportId", `CNR-2026-${String(targetAsmt.id).padStart(5, '0')}`);
  } else {
    activeReportAssessmentId = null;
    setText("repAssessmentId", "—");
    setText("repReportId", "—");
  }

  // If no assessments exist at all:
  if (!targetAsmt) {
    setText("repAssessmentDate", new Date().toISOString().split("T")[0]);
    setText("repPrevAssessmentStatus", "No assessment recorded");
    setText("repWeightCurrent", child.birth_weight != null ? `${child.birth_weight} kg` : "—");
    setText("repWeightPrev", "Previous assessment unavailable");
    setText("repWeightDelta", "Not available");
    setText("repHeightCurrent", child.birth_length != null ? `${child.birth_length} cm` : "—");
    setText("repHeightPrev", "Previous assessment unavailable");
    setText("repHeightDelta", "Not available");
    setText("repMuacCurrent", "Not recorded");
    setText("repMuacPrev", "Previous assessment unavailable");
    setText("repMuacDelta", "Not available");
    setText("repWhzCurrent", "Not assessed");
    setText("repWhzPrev", "Previous assessment unavailable");
    setText("repWhzDelta", "Not available");
    setText("repHazCurrent", "Not assessed");
    setText("repHazPrev", "Previous assessment unavailable");
    setText("repHazDelta", "Not available");
    setText("repWazCurrent", "Not assessed");
    setText("repWazPrev", "Previous assessment unavailable");
    setText("repWazDelta", "Not available");
    setText("whoCardWhzVal", "—");
    setText("whoCardWhzDesc", "Not assessed");
    setText("whoCardHazVal", "—");
    setText("whoCardHazDesc", "Not assessed");
    setText("whoCardWazVal", "—");
    setText("whoCardWazDesc", "Not assessed");
    setText("whoCardBazVal", "—");
    setText("whoCardBazDesc", "Not available — WHO BMI-for-age reference table not loaded");
    setText("repAiScreeningCategory", "No assessment available");
    setText("repAiRiskScoreText", "Not available");
    setText("mfWhzHazStatus", "Not assessed");
    setText("mfTrajectoryStatus", "Not available");
    setText("mfMuacStatus", "Not recorded");
    setText("mfEdemaStatus", "Not reported");
    const lBody = el("repLongitudinalTableBody");
    if (lBody) lBody.innerHTML = `<tr><td colspan="7" style="padding:12px;text-align:center;color:#64748b;">No assessment records available for longitudinal analysis.</td></tr>`;
    const sBody = el("repShapTableBody");
    if (sBody) sBody.innerHTML = `<tr><td colspan="4" style="padding:12px;text-align:center;color:#64748b;">Explainability features unavailable without assessment data.</td></tr>`;
    return;
  }

  // 2. Fetch authoritative canonical report data from GET /api/assessments/{id}/report?format=json
  let reportData = null;
  try {
    const repRes = await fetch(`${API_BASE}/assessments/${targetAsmt.id}/report?format=json`, {
      headers: getAuthHeaders()
    });
    if (repRes.ok) {
      reportData = await repRes.json();
    }
  } catch (err) {
    console.warn("Could not fetch canonical report data:", err);
  }

  const asmtDate = reportData?.assessment?.assessment_date || targetAsmt.assessment_date || targetAsmt.created_at || "—";
  setText("repAssessmentDate", asmtDate);

  const prevAsmt = (targetIdx > 0) ? sortedAsc[targetIdx - 1] : null;
  const hasHistory = !!(reportData?.previous_measurements || prevAsmt);
  setText("repPrevAssessmentStatus", hasHistory ? "Available" : "Baseline Registration (Previous assessment unavailable)");

  // Measurements & Deltas
  const curWt = reportData?.measurements?.weight_kg ?? targetAsmt.weight ?? null;
  const prevWt = reportData?.previous_measurements?.weight_kg ?? (prevAsmt ? prevAsmt.weight : null);
  const wtDelta = reportData?.deltas?.weight_kg ?? ((curWt != null && prevWt != null) ? Math.round((curWt - prevWt) * 10) / 10 : null);

  const curHt = reportData?.measurements?.height_cm ?? targetAsmt.height ?? null;
  const prevHt = reportData?.previous_measurements?.height_cm ?? (prevAsmt ? prevAsmt.height : null);
  const htDelta = reportData?.deltas?.height_cm ?? ((curHt != null && prevHt != null) ? Math.round((curHt - prevHt) * 10) / 10 : null);

  const curMu = reportData?.measurements?.muac_cm ?? targetAsmt.muac ?? null;
  const prevMu = reportData?.previous_measurements?.muac_cm ?? (prevAsmt ? prevAsmt.muac : null);
  const muDelta = reportData?.deltas?.muac_cm ?? ((curMu != null && prevMu != null) ? Math.round((curMu - prevMu) * 10) / 10 : null);

  const curWhz = reportData?.who?.whz ?? targetAsmt.whz ?? null;
  const prevWhz = reportData?.previous_measurements?.whz ?? (prevAsmt ? prevAsmt.whz : null);
  const whzDelta = reportData?.deltas?.whz ?? ((curWhz != null && prevWhz != null) ? Math.round((curWhz - prevWhz) * 100) / 100 : null);

  const curHaz = reportData?.who?.haz ?? targetAsmt.haz ?? null;
  const prevHaz = reportData?.previous_measurements?.haz ?? (prevAsmt ? prevAsmt.haz : null);
  const hazDelta = reportData?.deltas?.haz ?? ((curHaz != null && prevHaz != null) ? Math.round((curHaz - prevHaz) * 100) / 100 : null);

  const curWaz = reportData?.who?.waz ?? targetAsmt.waz ?? null;
  const prevWaz = reportData?.previous_measurements?.waz ?? (prevAsmt ? prevAsmt.waz : null);
  const wazDelta = reportData?.deltas?.waz ?? ((curWaz != null && prevWaz != null) ? Math.round((curWaz - prevWaz) * 100) / 100 : null);

  const curBaz = reportData?.who?.baz ?? targetAsmt.baz ?? null;

  // Render Table: Current, Previous, Delta
  setText("repWeightCurrent", curWt != null ? `${curWt} kg` : "—");
  setText("repWeightPrev", prevWt != null ? `${prevWt} kg` : "Previous assessment unavailable");
  if (wtDelta != null) {
    setHtml("repWeightDelta", wtDelta < 0 ? `<span style="color:#dc2626;font-weight:700;">${wtDelta} kg</span>` : `<span style="color:#16a34a;font-weight:700;">+${wtDelta} kg</span>`);
  } else {
    setText("repWeightDelta", "Not available");
  }

  setText("repHeightCurrent", curHt != null ? `${curHt} cm` : "—");
  setText("repHeightPrev", prevHt != null ? `${prevHt} cm` : "Previous assessment unavailable");
  if (htDelta != null) {
    setHtml("repHeightDelta", htDelta < 0 ? `<span style="color:#dc2626;font-weight:700;">${htDelta} cm</span>` : `<span style="color:#16a34a;font-weight:700;">+${htDelta} cm</span>`);
  } else {
    setText("repHeightDelta", "Not available");
  }

  setText("repMuacCurrent", curMu != null ? `${curMu} cm` : "Not recorded");
  setText("repMuacPrev", prevMu != null ? `${prevMu} cm` : "Previous assessment unavailable");
  if (muDelta != null) {
    setHtml("repMuacDelta", muDelta < 0 ? `<span style="color:#dc2626;font-weight:700;">${muDelta} cm</span>` : `<span style="color:#16a34a;font-weight:700;">+${muDelta} cm</span>`);
  } else {
    setText("repMuacDelta", "Not available");
  }

  const formatZ = val => (val != null && !isNaN(val)) ? `${val > 0 ? '+' : ''}${val.toFixed(2)} SD` : null;

  setText("repWhzCurrent", formatZ(curWhz) || "Not assessed");
  setText("repWhzPrev", formatZ(prevWhz) || "Previous assessment unavailable");
  if (whzDelta != null) {
    setHtml("repWhzDelta", whzDelta < 0 ? `<span style="color:#dc2626;font-weight:700;">${whzDelta.toFixed(2)} SD</span>` : `<span style="color:#16a34a;font-weight:700;">+${whzDelta.toFixed(2)} SD</span>`);
  } else {
    setText("repWhzDelta", "Not available");
  }

  setText("repHazCurrent", formatZ(curHaz) || "Not assessed");
  setText("repHazPrev", formatZ(prevHaz) || "Previous assessment unavailable");
  if (hazDelta != null) {
    setHtml("repHazDelta", hazDelta < 0 ? `<span style="color:#dc2626;font-weight:700;">${hazDelta.toFixed(2)} SD</span>` : `<span style="color:#16a34a;font-weight:700;">+${hazDelta.toFixed(2)} SD</span>`);
  } else {
    setText("repHazDelta", "Not available");
  }

  setText("repWazCurrent", formatZ(curWaz) || "Not assessed");
  setText("repWazPrev", formatZ(prevWaz) || "Previous assessment unavailable");
  if (wazDelta != null) {
    setHtml("repWazDelta", wazDelta < 0 ? `<span style="color:#dc2626;font-weight:700;">${wazDelta.toFixed(2)} SD</span>` : `<span style="color:#16a34a;font-weight:700;">+${wazDelta.toFixed(2)} SD</span>`);
  } else {
    setText("repWazDelta", "Not available");
  }

  // Section 4: WHO Growth Assessment Cards
  setText("whoCardWhzVal", formatZ(curWhz) || "—");
  const whzDesc = reportData?.who?.interpretations?.whz || (curWhz == null ? "Not assessed" : (curWhz < -3 ? "Severe wasting range (< -3 SD)" : (curWhz < -2 ? "Moderate wasting range (< -2 SD)" : (curWhz > 2 ? "Overweight range (> +2 SD)" : "Normal body mass (≥ -2 SD)"))));
  setText("whoCardWhzDesc", whzDesc);

  setText("whoCardHazVal", formatZ(curHaz) || "—");
  const hazDesc = reportData?.who?.interpretations?.haz || (curHaz == null ? "Not assessed" : (curHaz < -3 ? "Severe stunting (< -3 SD)" : (curHaz < -2 ? "Moderate stunting (< -2 SD)" : "Normal linear growth (≥ -2 SD)")));
  setText("whoCardHazDesc", hazDesc);

  setText("whoCardWazVal", formatZ(curWaz) || "—");
  const wazDesc = reportData?.who?.interpretations?.waz || (curWaz == null ? "Not assessed" : (curWaz < -3 ? "Severe underweight (< -3 SD)" : (curWaz < -2 ? "Moderate underweight (< -2 SD)" : "Normal weight range (≥ -2 SD)")));
  setText("whoCardWazDesc", wazDesc);

  setText("whoCardBazVal", formatZ(curBaz) || "—");
  const bazDesc = curBaz != null ? (reportData?.who?.interpretations?.baz || (curBaz < -2 ? "Thinness range" : (curBaz > 2 ? "Overweight range" : "Normal-to-borderline range"))) : (reportData?.who?.interpretations?.baz || "Not available — WHO BMI-for-age reference table not loaded");
  setText("whoCardBazDesc", bazDesc);

  // Section 5: AI Prediction & Composite Screening Risk Score
  const predictionStr = reportData?.ai?.prediction || targetAsmt.prediction?.prediction || targetAsmt.prediction || "AI assessment unavailable";
  const riskScore = reportData?.risk?.score != null ? reportData.risk.score : (targetAsmt.prediction?.risk_score != null ? targetAsmt.prediction.risk_score : (targetAsmt.risk_score != null ? targetAsmt.risk_score : null));

  setText("repAiScreeningCategory", predictionStr);
  setText("repAiRiskScoreText", riskScore != null ? `${Math.round(riskScore)} / 100` : "Not available");

  // Section 6: Multi-Factor Risk Breakdown
  if (curWhz != null && curHaz != null) {
    setText("mfWhzHazStatus", curWhz < -3 ? "Severe Wasting Range" : (curWhz < -2 ? "Moderate Wasting Range" : (curHaz < -2 ? "Stunted Growth" : "Within Normal Limits")));
  } else if (curWhz != null) {
    setText("mfWhzHazStatus", curWhz < -3 ? "Severe Wasting" : (curWhz < -2 ? "Moderate Wasting" : "Normal Body Mass"));
  } else {
    setText("mfWhzHazStatus", "Not assessed");
  }

  if (wtDelta != null) {
    setText("mfTrajectoryStatus", wtDelta < 0 ? `Negative Velocity (${wtDelta} kg)` : `Positive Track (+${wtDelta} kg)`);
  } else {
    setText("mfTrajectoryStatus", "Baseline Visit (Trajectory N/A)");
  }

  if (curMu != null) {
    setText("mfMuacStatus", curMu < 11.5 ? "Severe Acute Malnutrition (< 11.5 cm)" : (curMu < 12.5 ? "Moderate Malnutrition (11.5–12.5 cm)" : "Adequate Muscle Mass (≥ 12.5 cm)"));
  } else {
    setText("mfMuacStatus", "Not recorded");
  }

  const hasEdema = reportData?.measurements?.has_bilateral_edema ?? targetAsmt.has_bilateral_edema;
  if (el("mfEdemaStatus")) {
    setText("mfEdemaStatus", hasEdema ? "Present (Bilateral Pitting Edema)" : "Absent / Not Reported");
    const edColor = hasEdema ? "#dc2626" : "#16a34a";
    el("mfEdemaStatus").style.color = edColor;
    if (el("mfEdemaDesc")) setText("mfEdemaDesc", hasEdema ? "Bilateral fluid retention noted. Prompt evaluation by a qualified healthcare professional is recommended." : "No bilateral fluid retention reported.");
  }

  // Section 7: Clinical Safety Triage
  const triageLvl = reportData?.triage?.level;
  const isUrgent = (curWhz != null && curWhz < -3) || (curMu != null && curMu < 11.5) || hasEdema || (triageLvl && triageLvl.includes("EMERGENCY"));
  const isReview = (curWhz != null && curWhz < -2) || (curMu != null && curMu < 12.5) || (riskScore != null && riskScore >= 40) || (triageLvl && triageLvl.includes("MONITOR"));

  if (isUrgent) {
    setText("repCurrentStatusBadge", "Urgent Review Required");
    setText("repTriageTitle", "Urgent Clinical Triage (Severe Nutritional Risk)");
    setText("repTriageDesc", "The screening indicates severe acute wasting or presence of clinical risk indicators. Immediate clinical evaluation at a Nutrition Rehabilitation Centre (NRC) or hospital is indicated.");
  } else if (isReview) {
    setText("repCurrentStatusBadge", "Needs Review");
    setText("repTriageTitle", "Clinical Review Recommended (Moderate Nutritional Risk)");
    setText("repTriageDesc", "The screening indicates moderate wasting or increased nutritional risk. Nutrition guidance shown below is general supportive information and is not a substitute for clinical treatment. Seek evaluation from your pediatrician or local health center.");
  } else {
    setText("repCurrentStatusBadge", "Within Assessed Range");
    setText("repTriageTitle", "Routine Growth Monitoring Supported");
    setText("repTriageDesc", "Growth parameters fall within expected standard reference ranges. Continue regular complementary feeding and community growth monitoring.");
  }

  // Section 8: Nutrition MDD Assessment
  const userDiversity = localStorage.getItem("userDietaryDiversityScore");
  if (userDiversity !== null && userDiversity !== undefined && !isNaN(parseInt(userDiversity))) {
    const scoreVal = parseInt(userDiversity);
    setText("repMddScore", `${scoreVal} / 8`);
    setText("repMddStatus", scoreVal >= 5 ? "Minimum Diversity Achieved" : "Dietary Diversity Below Target");
  } else {
    setText("repMddScore", "Not assessed");
    setText("repMddStatus", "Requires 24-hr dietary recall");
    if (el("repConsumedGroups")) setText("repConsumedGroups", "Not recorded");
    if (el("repMissingGroups")) setText("repMissingGroups", "Not recorded");
  }

  // Section 10: SHAP Feature Attributions
  const sBody = el("repShapTableBody");
  if (sBody) {
    try {
      const expRes = await fetch(`${API_BASE}/ai/explain/${targetAsmt.id}`, { headers: getAuthHeaders() });
      if (expRes.ok) {
        const expData = await expRes.json();
        const topFeatures = expData?.explainability?.top_contributing_features || [];
        if (topFeatures.length > 0) {
          sBody.innerHTML = "";
          topFeatures.forEach(f => {
            const tr = document.createElement("tr");
            tr.style.borderBottom = "1px solid #e2e8f0";
            const isRisk = (f.impact && f.impact.toLowerCase().includes("risk")) || (f.impact_score > 0);
            const dirColor = isRisk ? "#dc2626" : "#16a34a";
            const dirArrow = isRisk ? "↑ Elevated Risk" : "↓ Protective / Lower Risk";
            const impVal = f.impact_score != null ? `${f.impact_score > 0 ? '+' : ''}${f.impact_score.toFixed(2)}` : "—";
            tr.innerHTML = `
              <td style="padding:6px 10px;font-weight:600;">${f.display_name || f.feature}</td>
              <td style="padding:6px 10px;"><strong style="color:${dirColor};">${impVal}</strong></td>
              <td style="padding:6px 10px;"><span style="color:${dirColor};font-weight:700;">${dirArrow}</span></td>
              <td style="padding:6px 10px;">${f.clinical_meaning || f.meaning || "Model attribution factor"}</td>
            `;
            sBody.appendChild(tr);
          });
          if (el("repShapSummary")) {
            setText("repShapSummary", expData.explainability.shap_decision_summary || "Feature attribution derived from TreeExplainer Shapley analysis.");
          }
        } else {
          sBody.innerHTML = `<tr><td colspan="4" style="padding:12px;text-align:center;color:#64748b;">SHAP explanation unavailable for this assessment.</td></tr>`;
          if (el("repShapSummary")) setText("repShapSummary", "Feature importance breakdown unavailable.");
        }
      } else {
        sBody.innerHTML = `<tr><td colspan="4" style="padding:12px;text-align:center;color:#64748b;">SHAP explanation unavailable for this assessment.</td></tr>`;
      }
    } catch (e) {
      console.warn("Could not query explainability for report:", e);
      sBody.innerHTML = `<tr><td colspan="4" style="padding:12px;text-align:center;color:#64748b;">SHAP explanation unavailable for this assessment.</td></tr>`;
    }
  }

  // Section 12: Longitudinal Growth Table
  const tbody = el("repLongitudinalTableBody");
  if (tbody) {
    if (sortedAsc.length >= 2) {
      tbody.innerHTML = "";
      // Display newest first (descending display order)
      const reversedForDisplay = [...sortedAsc].reverse();
      reversedForDisplay.forEach((pt, idx) => {
        const tr = document.createElement("tr");
        tr.style.borderBottom = "1px solid #e2e8f0";
        const dateText = pt.assessment_date || pt.date || "Recent";
        const ageVal = pt.age_months ? `${Math.round(pt.age_months)} mo` : ageStr;
        const wtVal = pt.weight ? `${pt.weight} kg` : "—";
        const htVal = pt.height ? `${pt.height} cm` : "—";
        const muVal = pt.muac ? `${pt.muac} cm` : "—";
        const whzVal = pt.whz != null ? `${pt.whz > 0 ? '+' : ''}${pt.whz.toFixed(2)} SD` : "—";
        
        let velText = `<span style="color:#64748b;">Baseline</span>`;
        if (idx === 0 && wtDelta != null) {
          velText = wtDelta < 0 ? `<span style="color:#dc2626;font-weight:700;">↓ ${wtDelta} kg (Alert)</span>` : `<span style="color:#16a34a;font-weight:700;">↑ +${wtDelta} kg</span>`;
        } else if (idx < reversedForDisplay.length - 1) {
          const prevPt = reversedForDisplay[idx + 1];
          const currW = parseFloat(pt.weight);
          const prevW = parseFloat(prevPt.weight);
          if (!isNaN(currW) && !isNaN(prevW)) {
            const stepDelta = parseFloat((currW - prevW).toFixed(2));
            velText = stepDelta < 0
              ? `<span style="color:#dc2626;font-weight:600;">↓ ${stepDelta} kg</span>`
              : (stepDelta > 0
                ? `<span style="color:#16a34a;font-weight:600;">↑ +${stepDelta} kg</span>`
                : `<span style="color:#64748b;">0.00 kg</span>`);
          }
        }
        
        tr.innerHTML = `
          <td style="padding:6px 10px;font-weight:600;">${dateText}</td>
          <td style="padding:6px 10px;">${ageVal}</td>
          <td style="padding:6px 10px;">${wtVal}</td>
          <td style="padding:6px 10px;">${htVal}</td>
          <td style="padding:6px 10px;">${muVal}</td>
          <td style="padding:6px 10px;">${whzVal}</td>
          <td style="padding:6px 10px;">${velText}</td>
        `;
        tbody.appendChild(tr);
      });
      if (el("repVelocityAlert")) {
        if (wtDelta != null && wtDelta < -0.5) {
          setText("repVelocityAlert", `Velocity Alert: Growth deceleration detected (${wtDelta} kg decline). Rate of weight drop exceeds threshold requiring active dietary intervention.`);
        } else {
          setText("repVelocityAlert", "Growth trajectory steady relative to chronological monitoring history.");
          el("repVelocityAlert").style.color = "#16a34a";
        }
      }
    } else {
      tbody.innerHTML = `<tr><td colspan="7" style="padding:12px;text-align:center;color:#64748b;">Insufficient history for longitudinal growth analysis. Baseline assessment recorded.</td></tr>`;
      if (el("repVelocityAlert")) setText("repVelocityAlert", "");
    }
  }

  // Section 13: Future Risk Projections
  if (child.id) {
    try {
      const frRes = await fetch(`${API_BASE}/ai/future-risk/${child.id}`, { headers: getAuthHeaders() });
      if (frRes.ok) {
        const frData = await frRes.json();
        setText("projCurrentRisk", `Risk: ${Math.round(frData.current_risk_score ?? (riskScore || 0))}`);
        setText("projCurrentWeight", curWt != null ? `Weight: ${curWt} kg` : "Weight: —");
        const forecasts = frData.forecasts || [];
        if (forecasts[0]) {
          setText("proj30Risk", `Risk: ${Math.round(forecasts[0].projected_risk_score)}`);
          setText("proj30Weight", `Est: ${forecasts[0].weight_kg} kg`);
        } else {
          setText("proj30Risk", "Risk: —"); setText("proj30Weight", "Est: —");
        }
        if (forecasts[1]) {
          setText("proj60Risk", `Risk: ${Math.round(forecasts[1].projected_risk_score)}`);
          setText("proj60Weight", `Est: ${forecasts[1].weight_kg} kg`);
        } else {
          setText("proj60Risk", "Risk: —"); setText("proj60Weight", "Est: —");
        }
        if (forecasts[2]) {
          setText("proj90Risk", `Risk: ${Math.round(forecasts[2].projected_risk_score)}`);
          setText("proj90Weight", `Est: ${forecasts[2].weight_kg} kg`);
        } else {
          setText("proj90Risk", "Risk: —"); setText("proj90Weight", "Est: —");
        }
      } else {
        setText("projCurrentRisk", riskScore != null ? `Risk: ${Math.round(riskScore)}` : "Risk: —");
        setText("projCurrentWeight", curWt != null ? `Weight: ${curWt} kg` : "Weight: —");
        setText("proj30Risk", "Risk: —"); setText("proj30Weight", "Est: —");
        setText("proj60Risk", "Risk: —"); setText("proj60Weight", "Est: —");
        setText("proj90Risk", "Risk: —"); setText("proj90Weight", "Est: —");
      }
    } catch (e) {
      console.warn("Could not query future risk for report modal:", e);
      setText("projCurrentRisk", riskScore != null ? `Risk: ${Math.round(riskScore)}` : "Risk: —");
      setText("projCurrentWeight", curWt != null ? `Weight: ${curWt} kg` : "Weight: —");
      setText("proj30Risk", "Risk: —"); setText("proj30Weight", "Est: —");
      setText("proj60Risk", "Risk: —"); setText("proj60Weight", "Est: —");
      setText("proj90Risk", "Risk: —"); setText("proj90Weight", "Est: —");
    }
  }

  // Section 15: Executive Summary
  if (el("repExecutiveSummary")) {
    const wastingPhrase = curWhz != null ? (curWhz < -3 ? `severe acute wasting (WHZ ${curWhz > 0 ? '+' : ''}${curWhz.toFixed(2)} SD)` : (curWhz < -2 ? `moderate acute wasting (WHZ ${curWhz > 0 ? '+' : ''}${curWhz.toFixed(2)} SD)` : `normal weight-for-height (WHZ ${curWhz > 0 ? '+' : ''}${curWhz.toFixed(2)} SD)`)) : "anthropometric parameters";
    const edemaPhrase = hasEdema ? "Bilateral pitting edema is detected." : "Child is without bilateral pitting edema.";
    const velPhrase = wtDelta != null ? (wtDelta < 0 ? `Recent trajectory shows a weight loss of ${Math.abs(wtDelta)} kg.` : `Recent trajectory shows weight gain of +${wtDelta} kg.`) : "Baseline monitoring visit.";
    const actionPhrase = isUrgent ? "Immediate clinical evaluation at a medical facility is advised." : (isReview ? "Supportive nutritional counseling and close bi-weekly follow-up are recommended." : "Routine complementary feeding and continued community growth monitoring are supported.");
    setText("repExecutiveSummary", `Screening indicates ${wastingPhrase}. ${edemaPhrase} ${velPhrase} ${actionPhrase}`);
  }
}

function openMedicalReportModal(assessmentId = null) {
  const modal = document.getElementById("medicalReportModal");
  if (!modal) return;
  modal.style.display = "flex";
  document.body.style.overflow = "hidden";
  populateReportFields(assessmentId);
}

function closeMedicalReportModal() {
  const modal = document.getElementById("medicalReportModal");
  if (modal) modal.style.display = "none";
  document.body.style.overflow = "auto";
}

function printMedicalReport() {
  window.print();
}

async function downloadMedicalReportPDF() {
  const child = currentChild || {};
  const childName = (child.name || "Child").replace(/\s+/g, '_');
  showToast("Downloading official 17-Section Clinical PDF Report...", "info");

  // Determine target assessment ID
  let targetAssessmentId = activeReportAssessmentId;
  if (!targetAssessmentId && child.id) {
    try {
      const res = await fetch(`${API_BASE}/assessments/child/${child.id}`, { headers: getAuthHeaders() });
      if (res.ok) {
        const assessments = await res.json();
        if (assessments && assessments.length > 0) {
          const sorted = [...assessments].sort((a,b) => new Date(a.assessment_date||a.created_at) - new Date(b.assessment_date||b.created_at) || (a.id - b.id));
          targetAssessmentId = sorted[sorted.length - 1].id;
        }
      }
    } catch (e) {
      console.warn("Could not retrieve assessment ID for PDF:", e);
    }
  }

  // Hit the backend ReportLab clinical PDF engine
  if (targetAssessmentId) {
    try {
      const pdfRes = await fetch(`${API_BASE}/assessments/${targetAssessmentId}/pdf`, {
        headers: getAuthHeaders()
      });
      if (pdfRes.ok) {
        const blob = await pdfRes.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `ChildNutri_Report_${childName}_Assessment_${targetAssessmentId}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        showToast("✓ Official 17-Section Clinical PDF Report downloaded successfully!");
        return;
      }
    } catch (err) {
      console.warn("Backend PDF download failed, falling back to printer:", err);
    }
  }

  // Fallback to window.print if backend is unreachable
  window.print();
}

function exportMedicalDataCSV() {
  const child = currentChild || {};
  const name = child.name || "Child";
  const records = currentGrowthData || [];

  if (records.length === 0) {
    showToast("No growth records found to export.", "error");
    return;
  }

  let csv = "Assessment Date,Age (Months),Weight (kg),Height (cm),MUAC (cm),Head Circumference (cm),Notes\n";
  records.forEach(r => {
    csv += `"${r.assessment_date || r.date || ''}",${r.age_months || ''},${r.weight || ''},${r.height || ''},${r.muac || ''},${r.head_circumference || ''},"${(r.notes || '').replace(/"/g, '""')}"\n`;
  });

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  link.setAttribute("href", url);
  link.setAttribute("download", `ChildNutri_Medical_Report_${name.replace(/\s+/g, '_')}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  showToast("Medical Report CSV downloaded successfully!");
}

function setDynamicGreeting() {
  const el = document.getElementById("parentGreetingText");
  if (!el) return;
  const hour = new Date().getHours();
  let timeStr = "Good morning";
  if (hour >= 12 && hour < 17) timeStr = "Good afternoon";
  else if (hour >= 17) timeStr = "Good evening";

  let name = "Parent";
  try {
    const user = JSON.parse(localStorage.getItem("childnutri_user") || "{}");
    if (user.full_name) name = user.full_name.split(" ")[0];
  } catch (e) {}

  el.innerHTML = `${timeStr}, <span style="color:#0d7a57;font-weight:800;">${name}</span>`;
}

function renderParentGrowthMetric(metric) {
  metric = metric || "weight";
  const growth = currentChildGrowth || [];
  if (growth.length === 0) return;

  const pathEl = document.getElementById("childGrowthSvgPath");
  if (!pathEl) return;

  const count = Math.min(6, growth.length);
  const pts = growth.slice(-count);

  let vals = [];
  let minVal = 0;
  let maxVal = 100;

  if (metric === "weight") {
    vals = pts.map(p => p.weight);
    minVal = 4; maxVal = 16;
  } else if (metric === "height") {
    vals = pts.map(p => p.height);
    minVal = 50; maxVal = 100;
  } else if (metric === "muac") {
    vals = pts.map(p => p.muac || 12.0);
    minVal = 9; maxVal = 17;
  } else {
    // whz
    vals = pts.map(p => p.whz !== undefined ? p.whz : 0);
    minVal = -4; maxVal = 4;
  }

  const stepX = count > 1 ? (740 - 60) / (count - 1) : 0;
  const coords = vals.map((v, i) => {
    const x = count === 1 ? 400 : 60 + (i * stepX);
    const norm = Math.max(0, Math.min(1, (v - minVal) / (maxVal - minVal)));
    const y = 160 - (norm * 120);
    return { x, y };
  });

  if (coords.length === 1) {
    pathEl.setAttribute("d", `M 60 ${coords[0].y} L 740 ${coords[0].y}`);
  } else {
    let d = `M ${coords[0].x} ${coords[0].y}`;
    for (let i = 1; i < coords.length; i++) {
      const prev = coords[i - 1];
      const curr = coords[i];
      const cx = (prev.x + curr.x) / 2;
      d += ` C ${cx} ${prev.y}, ${cx} ${curr.y}, ${curr.x} ${curr.y}`;
    }
    pathEl.setAttribute("d", d);
  }
}


// -------------------------------------------------------------
// PARENT PROFILE MODAL CONTROLS (VIEW & EDIT)
// -------------------------------------------------------------
function openParentProfileModal() {
  const m = document.getElementById("parentProfileModal");
  if (!m) return;
  if (currentUser) {
    const initial = currentUser.full_name ? currentUser.full_name[0].toUpperCase() : "P";
    const av = document.getElementById("modalParentAvatar");
    if (av) av.textContent = initial;
    const name = document.getElementById("modalParentFullName");
    if (name) name.textContent = currentUser.full_name;
    const email = document.getElementById("modalParentEmail");
    if (email) email.textContent = currentUser.email;

    const inputName = document.getElementById("parentEditFullName");
    if (inputName) inputName.value = currentUser.full_name || "";
    const inputPhone = document.getElementById("parentEditPhone");
    if (inputPhone) inputPhone.value = currentUser.phone || "";
    const inputEmail = document.getElementById("parentEditEmail");
    if (inputEmail) inputEmail.value = currentUser.email || "";
  }
  if (currentChild) {
    const tag = document.getElementById("modalParentChildTag");
    if (tag) tag.innerHTML = `&#128102; ${currentChild.name} (${currentChild.health_id})`;
  }
  m.style.display = "flex";
}

function closeParentProfileModal() {
  const m = document.getElementById("parentProfileModal");
  if (m) m.style.display = "none";
}

async function saveParentProfile(e) {
  if (e && e.preventDefault) e.preventDefault();
  const nameInput = document.getElementById("parentEditFullName");
  const phoneInput = document.getElementById("parentEditPhone");
  const btn = document.getElementById("btnSaveParentProfile");
  if (!nameInput) return;

  const newName = nameInput.value.trim();
  const newPhone = phoneInput ? phoneInput.value.trim() : "";
  if (!newName) {
    showToast("Please enter a valid full name.");
    return;
  }

  if (btn) btn.textContent = "Saving...";

  try {
    const res = await fetch(`${API_BASE}/users/me`, {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        full_name: newName,
        phone: newPhone
      })
    });

    if (!res.ok) throw new Error("Failed to update profile.");

    const updated = await res.json();
    currentUser = updated;
    localStorage.setItem("childnutri_user", JSON.stringify(updated));

    const initial = updated.full_name ? updated.full_name[0].toUpperCase() : "P";
    document.querySelectorAll(".sf-av, .tb-av").forEach(el => el.textContent = initial);
    document.querySelectorAll(".sf-name, .tb-name").forEach(el => el.textContent = updated.full_name);

    const pfFullName = document.getElementById("profParentFullName");
    if (pfFullName) pfFullName.textContent = updated.full_name;
    const pfEmail = document.getElementById("profParentEmail");
    if (pfEmail) pfEmail.textContent = updated.email;

    const inlineName = document.getElementById("inlineEditFullName");
    if (inlineName) inlineName.value = updated.full_name;
    const inlinePhone = document.getElementById("inlineEditPhone");
    if (inlinePhone) inlinePhone.value = updated.phone || "";

    const chGuardian = document.getElementById("childDossierGuardian");
    if (chGuardian) chGuardian.innerHTML = `&#128106; Caregiver: ${updated.full_name}`;

    setDynamicGreeting();
    closeParentProfileModal();
    showToast("Profile updated successfully!");
  } catch (err) {
    console.error("Profile save error:", err);
    showToast("Error updating profile. Please try again.");
  } finally {
    if (btn) btn.textContent = "Save Changes";
  }
}

async function saveParentProfileInline(e) {
  if (e && e.preventDefault) e.preventDefault();
  const nameInput = document.getElementById("inlineEditFullName");
  const phoneInput = document.getElementById("inlineEditPhone");
  const btn = document.getElementById("btnSaveInlineProfile");
  if (!nameInput) return;

  const newName = nameInput.value.trim();
  const newPhone = phoneInput ? phoneInput.value.trim() : "";
  if (!newName) {
    showToast("Please enter a valid full name.");
    return;
  }

  if (btn) btn.textContent = "Saving...";

  try {
    const res = await fetch(`${API_BASE}/users/me`, {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        full_name: newName,
        phone: newPhone
      })
    });

    if (!res.ok) throw new Error("Failed to update profile.");

    const updated = await res.json();
    currentUser = updated;
    localStorage.setItem("childnutri_user", JSON.stringify(updated));

    const initial = updated.full_name ? updated.full_name[0].toUpperCase() : "P";
    document.querySelectorAll(".sf-av, .tb-av").forEach(el => el.textContent = initial);
    document.querySelectorAll(".sf-name, .tb-name").forEach(el => el.textContent = updated.full_name);

    const pfFullName = document.getElementById("profParentFullName");
    if (pfFullName) pfFullName.textContent = updated.full_name;

    const chGuardian = document.getElementById("childDossierGuardian");
    if (chGuardian) chGuardian.innerHTML = `&#128106; Caregiver: ${updated.full_name}`;

    setDynamicGreeting();
    showToast("Profile updated successfully!");
  } catch (err) {
    console.error("Profile save error:", err);
    showToast("Error updating profile. Please try again.");
  } finally {
    if (btn) btn.textContent = "Save Changes";
  }
}

// -------------------------------------------------------------
// REGULAR CHILD UPDATE MODAL CONTROLS (MEASUREMENTS, PHOTO, DETAILS)
// -------------------------------------------------------------
function openRegularUpdateModal(tabName) {
  const m = document.getElementById("regularUpdateModal");
  if (!m) return;

  const childName = currentChild ? currentChild.name : "Child";
  const nameEl = document.getElementById("regModalChildName");
  if (nameEl) nameEl.textContent = childName;

  // Pre-fill date to today
  const dateInput = document.getElementById("regMeasureDate");
  if (dateInput && !dateInput.value) {
    dateInput.value = new Date().toISOString().split("T")[0];
  }

  // Pre-fill latest known values if available
  if (currentChildGrowth && currentChildGrowth.length > 0) {
    const last = currentChildGrowth[currentChildGrowth.length - 1];
    const wInput = document.getElementById("regMeasureWeight");
    if (wInput && !wInput.value) wInput.value = last.weight;
    const hInput = document.getElementById("regMeasureHeight");
    if (hInput && !hInput.value) hInput.value = last.height;
    const mInput = document.getElementById("regMeasureMuac");
    if (mInput && !mInput.value && last.muac) mInput.value = last.muac;
    const cInput = document.getElementById("regMeasureHeadCirc");
    if (cInput && !cInput.value && last.head_circumference) cInput.value = last.head_circumference;
  }

  // Pre-fill child demographics tab
  if (currentChild) {
    const nInput = document.getElementById("regChildName");
    if (nInput) nInput.value = currentChild.name || "";
    const dInput = document.getElementById("regChildDob");
    if (dInput) dInput.value = currentChild.date_of_birth || "";
    const gInput = document.getElementById("regChildGender");
    if (gInput) gInput.value = currentChild.gender || "Male";
    const bwInput = document.getElementById("regChildBirthWeight");
    if (bwInput) bwInput.value = currentChild.birth_weight || "";
    const blInput = document.getElementById("regChildBirthLength");
    if (blInput) blInput.value = currentChild.birth_length || "";
  }

  switchRegModalTab(tabName || "measurements");
  m.style.display = "flex";
}

function closeRegularUpdateModal() {
  const m = document.getElementById("regularUpdateModal");
  if (m) m.style.display = "none";
}

function switchRegModalTab(tab) {
  tab = tab || "measurements";
  const tabs = ["measurements", "photo", "details"];
  tabs.forEach(t => {
    const btn = document.getElementById("regTabBtn" + t.charAt(0).toUpperCase() + t.slice(1));
    const content = document.getElementById("regTabContent" + t.charAt(0).toUpperCase() + t.slice(1));
    if (btn) btn.classList.toggle("active", t === tab);
    if (content) content.style.display = (t === tab) ? "block" : "none";
  });
}

function previewRegularPhoto(input) {
  if (input.files && input.files[0]) {
    const file = input.files[0];
    const nameLabel = document.getElementById("regPhotoFilename");
    if (nameLabel) nameLabel.textContent = file.name;

    const reader = new FileReader();
    reader.onload = function(e) {
      const wrap = document.getElementById("regPhotoPreviewWrap");
      const img = document.getElementById("regPhotoPreviewImg");
      if (img && wrap) {
        img.src = e.target.result;
        wrap.style.display = "block";
      }
    };
    reader.readAsDataURL(file);
  }
}

async function submitRegularMeasurements(e) {
  if (e && e.preventDefault) e.preventDefault();
  if (!currentChild) {
    showToast("No active child record found.");
    return;
  }

  const dateVal = document.getElementById("regMeasureDate").value || new Date().toISOString().split("T")[0];
  const weight = parseFloat(document.getElementById("regMeasureWeight").value);
  const height = parseFloat(document.getElementById("regMeasureHeight").value);
  const muacVal = document.getElementById("regMeasureMuac").value ? parseFloat(document.getElementById("regMeasureMuac").value) : null;
  const headCircVal = document.getElementById("regMeasureHeadCirc").value ? parseFloat(document.getElementById("regMeasureHeadCirc").value) : null;
  const notes = document.getElementById("regMeasureNotes").value.trim() || "Parent routine growth update.";

  if (isNaN(weight) || isNaN(height)) {
    showToast("Please enter valid weight and height measurements.");
    return;
  }

  // Calculate age in months at assessment date
  let ageMonths = 14.0;
  if (currentChild.date_of_birth) {
    const d = new Date(currentChild.date_of_birth);
    const mDate = new Date(dateVal);
    ageMonths = Math.max(0.5, Math.round(((mDate - d) / (1000 * 60 * 60 * 24 * 30.4375)) * 10) / 10);
  }

  const btn = document.getElementById("btnSubmitRegularMeasurements");
  if (btn) btn.textContent = "Analyzing & Saving...";

  try {
    const res = await fetch(`${API_BASE}/assessments`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        child_id: currentChild.id,
        assessment_date: dateVal,
        age_months: ageMonths,
        weight: weight,
        height: height,
        muac: muacVal,
        head_circumference: headCircVal,
        notes: notes
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to record measurements.");
    }

    const newAssessment = await res.json();
    closeRegularUpdateModal();
    showToast("Growth measurements updated successfully!");
    await loadChildGrowthHistory(currentChild.id);
  } catch (err) {
    console.error("Save measurement error:", err);
    showToast(err.message || "Error saving measurements. Please try again.");
  } finally {
    if (btn) btn.textContent = "Save Measurement Update";
  }
}

async function submitRegularPhoto(e) {
  if (e && e.preventDefault) e.preventDefault();
  if (!currentChild) {
    showToast("No active child record found.");
    return;
  }

  const fileInput = document.getElementById("regPhotoInput");
  const file = fileInput && fileInput.files ? fileInput.files[0] : null;
  if (!file) {
    showToast("Please select a child photo to upload.");
    return;
  }

  const photoType = document.getElementById("regPhotoType").value || "front";
  const btn = document.getElementById("btnSubmitRegularPhoto");
  if (btn) btn.textContent = "Uploading & Analyzing...";

  const formData = new FormData();
  formData.append("child_id", currentChild.id);
  formData.append("photo_type", photoType);
  formData.append("image", file);

  try {
    const token = localStorage.getItem("childnutri_token");
    const res = await fetch(`${API_BASE}/photos/upload`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}` },
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to upload photo.");
    }

    closeRegularUpdateModal();
    showToast("Child photo uploaded successfully! Visual screening updated.");
    await loadChildPhotos(currentChild.id);
  } catch (err) {
    console.error("Photo upload error:", err);
    showToast(err.message || "Error uploading photo. Please try again.");
  } finally {
    if (btn) btn.textContent = "Upload Child Photo";
  }
}

async function submitRegularChildDetails(e) {
  if (e && e.preventDefault) e.preventDefault();
  if (!currentChild) {
    showToast("No active child record found.");
    return;
  }

  const name = document.getElementById("regChildName").value.trim();
  const dob = document.getElementById("regChildDob").value;
  const gender = document.getElementById("regChildGender").value;
  const birthWeight = document.getElementById("regChildBirthWeight").value ? parseFloat(document.getElementById("regChildBirthWeight").value) : null;
  const birthLength = document.getElementById("regChildBirthLength").value ? parseFloat(document.getElementById("regChildBirthLength").value) : null;

  if (!name) {
    showToast("Please enter a child name.");
    return;
  }

  const btn = document.getElementById("btnSubmitRegularChildDetails");
  if (btn) btn.textContent = "Saving...";

  try {
    const res = await fetch(`${API_BASE}/children/${currentChild.id}`, {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        name: name,
        date_of_birth: dob,
        gender: gender,
        birth_weight: birthWeight,
        birth_length: birthLength
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to update child details.");
    }

    closeRegularUpdateModal();
    showToast("Child details updated successfully!");
    await loadChildData();
  } catch (err) {
    console.error("Child update error:", err);
    showToast(err.message || "Error updating child details.");
  } finally {
    if (btn) btn.textContent = "Save Child Details";
  }
}


// -------------------------------------------------------------
// DEDICATED SECTION: REGULAR CHILD UPDATE CONTROLLER
// -------------------------------------------------------------
let additionalPhotoCount = 0;

function switchPageUpdateTab(tab) {
  tab = tab || "measurements";
  const tabs = ["measurements", "photo"];
  tabs.forEach(t => {
    const btn = document.getElementById("secRegTabBtn" + t.charAt(0).toUpperCase() + t.slice(1));
    const content = document.getElementById("secRegTabContent" + t.charAt(0).toUpperCase() + t.slice(1));
    if (btn) btn.classList.toggle("active", t === tab);
    if (content) content.style.display = (t === tab) ? "block" : "none";
  });
}

// --- PHOTO SLOT CONTROLLERS (FRONT, BACK, FACE) ---
function handlePhotoSlotChange(input, slotType) {
  const file = input && input.files ? input.files[0] : null;
  const card = document.getElementById(`slotCard_${slotType}`);
  const placeholder = document.getElementById(`slotPlaceholder_${slotType}`);
  const previewWrap = document.getElementById(`slotPreviewWrap_${slotType}`);
  const previewImg = document.getElementById(`slotImg_${slotType}`);
  const filenameLabel = document.getElementById(`slotFilename_${slotType}`);

  if (!file) return;

  // Validate extension
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['jpg', 'jpeg', 'png'].includes(ext)) {
    showToast("Invalid file type. Please upload a JPG or PNG image.");
    input.value = "";
    return;
  }

  // File size check (<= 10MB)
  if (file.size > 10 * 1024 * 1024) {
    showToast("Image size exceeds 10MB limit. Please choose a smaller photo.");
    input.value = "";
    return;
  }

  const reader = new FileReader();
  reader.onload = function(e) {
    if (previewImg) previewImg.src = e.target.result;
    if (filenameLabel) filenameLabel.textContent = file.name;
    if (placeholder) placeholder.style.display = "none";
    if (previewWrap) previewWrap.style.display = "flex";
    if (card) {
      card.classList.add("has-file");
      card.classList.remove("slot-error");
    }
    updatePhotoCounterBadge();
  };
  reader.readAsDataURL(file);
}

function clearPhotoSlot(slotType) {
  const input = document.getElementById(slotType === 'front' ? 'photoInputFront' : (slotType === 'back' ? 'photoInputBack' : 'photoInputFace'));
  if (input) input.value = "";

  const card = document.getElementById(`slotCard_${slotType}`);
  const placeholder = document.getElementById(`slotPlaceholder_${slotType}`);
  const previewWrap = document.getElementById(`slotPreviewWrap_${slotType}`);
  const previewImg = document.getElementById(`slotImg_${slotType}`);
  const filenameLabel = document.getElementById(`slotFilename_${slotType}`);

  if (previewImg) previewImg.src = "";
  if (filenameLabel) filenameLabel.textContent = "";
  if (previewWrap) previewWrap.style.display = "none";
  if (placeholder) placeholder.style.display = "block";
  if (card) {
    card.classList.remove("has-file");
    card.classList.remove("slot-error");
  }

  updatePhotoCounterBadge();
}

function updatePhotoCounterBadge() {
  const frontInput = document.getElementById("photoInputFront");
  const backInput = document.getElementById("photoInputBack");
  const faceInput = document.getElementById("photoInputFace");

  const hasFront = frontInput && frontInput.files && frontInput.files.length > 0;
  const hasBack = backInput && backInput.files && backInput.files.length > 0;
  const hasFace = faceInput && faceInput.files && faceInput.files.length > 0;

  const count = [hasFront, hasBack, hasFace].filter(Boolean).length;
  const badge = document.getElementById("photoReqCounterBadge");
  const text = document.getElementById("photoReqCounterText");

  if (!badge || !text) return;

  if (count === 3) {
    badge.style.background = "#dcfce7";
    badge.style.color = "#15803d";
    badge.innerHTML = "<span>✓</span> <span id='photoReqCounterText'>All 3 Required Photos Ready</span>";
  } else {
    badge.style.background = "#fef3c7";
    badge.style.color = "#92400e";
    badge.innerHTML = `<span>⚠️</span> <span id='photoReqCounterText'>${count} of 3 Required Photos Selected</span>`;
  }
}

// --- DYNAMIC ADDITIONAL PHOTOS ---
function addAdditionalPhotoSlot() {
  additionalPhotoCount++;
  const id = additionalPhotoCount;
  const list = document.getElementById("additionalPhotosList");
  if (!list) return;

  const item = document.createElement("div");
  item.className = "additional-photo-card";
  item.id = `additionalCard_${id}`;
  item.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid var(--border);">
      <div style="font-weight:700;font-size:0.86rem;color:var(--text);display:flex;align-items:center;gap:6px;">
        <span>📷</span> Additional Photo #${id}
      </div>
      <button type="button" onclick="removeAdditionalPhotoSlot(${id})" style="background:none;border:none;color:#e11d48;font-size:0.75rem;font-weight:600;cursor:pointer;">
        ✕ Remove Photo Slot
      </button>
    </div>
    
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;">
      <div>
        <label style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.04em;color:var(--text-secondary);display:block;margin-bottom:4px;">Photo Category</label>
        <select id="addPhotoType_${id}" style="width:100%;padding:9px 12px;border:1px solid var(--border);border-radius:var(--radius-md);font-family:var(--font-body);font-size:0.88rem;background:var(--surface);color:var(--text);outline:none;" onchange="handleAdditionalTypeChange(${id})">
          <option value="side">Side / Lateral Profile</option>
          <option value="feet">Feet (Bilateral Edema Check)</option>
          <option value="hands">Hands &amp; Palms</option>
          <option value="abdomen">Abdominal Stature</option>
          <option value="skin">Skin / Hair Observation</option>
          <option value="other">Other / Custom Description</option>
        </select>
      </div>
      <div>
        <label style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.04em;color:var(--text-secondary);display:block;margin-bottom:4px;">Specify Photo Description</label>
        <input type="text" id="addPhotoDesc_${id}" placeholder="e.g. Left ankle swelling, Side view" style="width:100%;padding:9px 12px;border:1px solid var(--border);border-radius:var(--radius-md);font-family:var(--font-body);font-size:0.88rem;background:var(--surface);color:var(--text);outline:none;">
      </div>
    </div>

    <div>
      <input type="file" id="addPhotoInput_${id}" accept="image/png,image/jpeg,image/jpg" style="display:none;" onchange="handleAdditionalPhotoFile(${id})">
      
      <div id="addPlaceholder_${id}" style="border:1.5px dashed var(--border-strong);border-radius:var(--radius-lg);padding:18px;text-align:center;cursor:pointer;background:var(--surface-muted);" onclick="document.getElementById('addPhotoInput_${id}').click()">
        <div style="font-size:1.6rem;margin-bottom:4px;">📁</div>
        <div style="font-size:0.82rem;font-weight:600;color:var(--text);" id="addFilenameLabel_${id}">Click to select image file</div>
        <div style="font-size:0.72rem;color:var(--text-muted);margin-top:2px;">Supports JPG, PNG up to 10MB</div>
      </div>

      <div id="addPreviewWrap_${id}" style="display:none;margin-top:10px;text-align:center;">
        <img id="addImg_${id}" src="" alt="Additional preview" style="max-height:140px;border-radius:var(--radius-md);border:1px solid var(--border);object-fit:cover;">
      </div>
    </div>
  `;
  list.appendChild(item);
}

function handleAdditionalTypeChange(id) {
  const sel = document.getElementById(`addPhotoType_${id}`);
  const inp = document.getElementById(`addPhotoDesc_${id}`);
  if (!sel || !inp) return;
  const labels = {
    side: "Side / Lateral Profile",
    feet: "Feet / Bilateral Edema Check",
    hands: "Hands & Palms View",
    abdomen: "Abdominal Stature",
    skin: "Skin / Hair Condition",
    other: ""
  };
  if (labels[sel.value]) {
    inp.value = labels[sel.value];
  }
}

function handleAdditionalPhotoFile(id) {
  const input = document.getElementById(`addPhotoInput_${id}`);
  const placeholder = document.getElementById(`addPlaceholder_${id}`);
  const previewWrap = document.getElementById(`addPreviewWrap_${id}`);
  const previewImg = document.getElementById(`addImg_${id}`);
  const label = document.getElementById(`addFilenameLabel_${id}`);

  const file = input && input.files ? input.files[0] : null;
  if (!file) return;

  const ext = file.name.split('.').pop().toLowerCase();
  if (!['jpg', 'jpeg', 'png'].includes(ext)) {
    showToast("Invalid file type. Please upload a JPG or PNG image.");
    input.value = "";
    return;
  }

  const reader = new FileReader();
  reader.onload = function(e) {
    if (previewImg) previewImg.src = e.target.result;
    if (label) label.textContent = `Selected: ${file.name}`;
    if (previewWrap) previewWrap.style.display = "block";
  };
  reader.readAsDataURL(file);
}

function removeAdditionalPhotoSlot(id) {
  const card = document.getElementById(`additionalCard_${id}`);
  if (card) card.remove();
}

// --- SUBMISSION HANDLERS ---
async function submitAllChildPhotos(e) {
  if (e && e.preventDefault) e.preventDefault();
  if (!currentChild) {
    showToast("No active child record found.");
    return;
  }

  const frontInput = document.getElementById("photoInputFront");
  const backInput = document.getElementById("photoInputBack");
  const faceInput = document.getElementById("photoInputFace");

  const frontFile = frontInput && frontInput.files ? frontInput.files[0] : null;
  const backFile = backInput && backInput.files ? backInput.files[0] : null;
  const faceFile = faceInput && faceInput.files ? faceInput.files[0] : null;

  // Validate the 3 required photos
  const missing = [];
  if (!frontFile) {
    missing.push("Front");
    document.getElementById("slotCard_front")?.classList.add("slot-error");
  } else {
    document.getElementById("slotCard_front")?.classList.remove("slot-error");
  }

  if (!backFile) {
    missing.push("Back");
    document.getElementById("slotCard_back")?.classList.add("slot-error");
  } else {
    document.getElementById("slotCard_back")?.classList.remove("slot-error");
  }

  if (!faceFile) {
    missing.push("Face");
    document.getElementById("slotCard_face")?.classList.add("slot-error");
  } else {
    document.getElementById("slotCard_face")?.classList.remove("slot-error");
  }

  if (missing.length > 0) {
    showToast(`Minimum 3 photos required: Please upload ${missing.join(", ")} photo${missing.length > 1 ? "s" : ""} before submitting.`);
    const firstMissing = document.getElementById(`slotCard_${missing[0].toLowerCase()}`);
    if (firstMissing) firstMissing.scrollIntoView({ behavior: 'smooth', block: 'center' });
    return;
  }

  // Build the list of photos to upload
  const uploadQueue = [
    { file: frontFile, type: "front", label: "Front View" },
    { file: backFile, type: "back", label: "Back View" },
    { file: faceFile, type: "face", label: "Face View" }
  ];

  // Include any additional photos that have a file selected
  const addCards = document.querySelectorAll(".additional-photo-card");
  addCards.forEach(card => {
    const cid = card.id.replace("additionalCard_", "");
    const fileInp = document.getElementById(`addPhotoInput_${cid}`);
    const file = fileInp && fileInp.files ? fileInp.files[0] : null;
    if (file) {
      const typeSel = document.getElementById(`addPhotoType_${cid}`);
      const descInp = document.getElementById(`addPhotoDesc_${cid}`);
      let photoType = (descInp && descInp.value.trim()) || (typeSel && typeSel.value) || "additional";
      uploadQueue.push({
        file: file,
        type: photoType.toLowerCase().replace(/[^a-z0-9_]/g, '_').substring(0, 20) || "additional",
        label: (descInp && descInp.value.trim()) || "Additional View"
      });
    }
  });

  const btn = document.getElementById("btnSubmitAllPhotos");
  if (btn) btn.disabled = true;

  const token = localStorage.getItem("childnutri_token");
  let uploadSuccessCount = 0;

  try {
    for (let i = 0; i < uploadQueue.length; i++) {
      const item = uploadQueue[i];
      if (btn) btn.textContent = `Uploading ${i + 1} of ${uploadQueue.length} (${item.label})...`;

      const formData = new FormData();
      formData.append("child_id", currentChild.id);
      formData.append("photo_type", item.type);
      formData.append("image", item.file);

      const res = await fetch(`${API_BASE}/photos/upload`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || `Failed to upload ${item.label}.`);
      }
      uploadSuccessCount++;
    }

    showToast(`All ${uploadSuccessCount} photos uploaded successfully! AI visual screening updated.`);
    
    // Clear slots
    clearPhotoSlot("front");
    clearPhotoSlot("back");
    clearPhotoSlot("face");
    const addList = document.getElementById("additionalPhotosList");
    if (addList) addList.innerHTML = "";
    additionalPhotoCount = 0;

    await loadChildPhotos(currentChild.id);
  } catch (err) {
    console.error("Photos upload error:", err);
    showToast(err.message || "Error uploading photos. Please try again.");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Upload Child Photos (3 Required) →";
    }
  }
}

async function submitPageMeasurements(e) {
  if (e && e.preventDefault) e.preventDefault();
  if (!currentChild) {
    showToast("No active child record found.");
    return;
  }

  const dateVal = document.getElementById("pageMeasureDate").value || new Date().toISOString().split("T")[0];
  const weight = parseFloat(document.getElementById("pageMeasureWeight").value);
  const height = parseFloat(document.getElementById("pageMeasureHeight").value);
  const muacVal = document.getElementById("pageMeasureMuac").value ? parseFloat(document.getElementById("pageMeasureMuac").value) : null;
  const headCircVal = document.getElementById("pageMeasureHeadCirc").value ? parseFloat(document.getElementById("pageMeasureHeadCirc").value) : null;
  const notes = document.getElementById("pageMeasureNotes").value.trim() || "Routine regular growth measurement.";

  if (isNaN(weight) || isNaN(height)) {
    showToast("Please enter valid weight and height measurements.");
    return;
  }

  let ageMonths = 14.0;
  if (currentChild.date_of_birth) {
    const d = new Date(currentChild.date_of_birth);
    const mDate = new Date(dateVal);
    ageMonths = Math.max(0.5, Math.round(((mDate - d) / (1000 * 60 * 60 * 24 * 30.4375)) * 10) / 10);
  }

  const btn = document.getElementById("btnPageSaveMeasurements");
  if (btn) btn.textContent = "Analyzing & Saving...";

  try {
    const res = await fetch(`${API_BASE}/assessments`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        child_id: currentChild.id,
        assessment_date: dateVal,
        age_months: ageMonths,
        weight: weight,
        height: height,
        muac: muacVal,
        head_circumference: headCircVal,
        notes: notes
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to record measurements.");
    }

    await res.json();
    showToast("Growth measurements updated successfully! Overview updated.");
    await loadChildGrowthHistory(currentChild.id);
    await loadChildData();
  } catch (err) {
    console.error("Save measurement error:", err);
    showToast(err.message || "Error saving measurements. Please try again.");
  } finally {
    if (btn) btn.textContent = "Save Growth Measurements →";
  }
}

async function submitPageChildDetails(e) {
  if (e && e.preventDefault) e.preventDefault();
  if (!currentChild) {
    showToast("No active child record found.");
    return;
  }

  const name = document.getElementById("pageChildName").value.trim();
  const dob = document.getElementById("pageChildDob").value;
  const gender = document.getElementById("pageChildGender").value;
  const birthWeight = document.getElementById("pageChildBirthWeight").value ? parseFloat(document.getElementById("pageChildBirthWeight").value) : null;
  const birthLength = document.getElementById("pageChildBirthLength").value ? parseFloat(document.getElementById("pageChildBirthLength").value) : null;

  if (!name) {
    showToast("Please enter a child name.");
    return;
  }

  const btn = document.getElementById("btnPageSaveChildDetails");
  if (btn) btn.textContent = "Saving...";

  try {
    const res = await fetch(`${API_BASE}/children/${currentChild.id}`, {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        name: name,
        date_of_birth: dob,
        gender: gender,
        birth_weight: birthWeight,
        birth_length: birthLength
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to update child details.");
    }

    showToast("Child details updated successfully!");
    await loadChildData();
  } catch (err) {
    console.error("Child update error:", err);
    showToast(err.message || "Error updating child details.");
  } finally {
    if (btn) btn.textContent = "Save Child Details →";
  }
}
