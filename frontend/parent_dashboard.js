/**
 * Parent Dashboard Controller - ChildNutri AI
 * Communicates with FastAPI Backend (/api/auth, /api/children, /api/assessments, /api/photos, /api/medical, /api/nutrition, /api/appointments, etc.)
 */

const API_BASE = "http://127.0.0.1:8000/api";
let currentChild = null;
let currentUserId = null;
let currentChildGrowth = [];
let currentUpcomingAppt = null;

document.addEventListener("DOMContentLoaded", async function () {
  const token = localStorage.getItem("childnutri_token");
  if (!token) {
    window.location.href = "index.html";
    return;
  }

  await loadParentProfile();
  await loadChildData();
  await loadNotifications();
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
    nutrBannerText.textContent = `${firstName} is on RUTF (Ready-to-Use Therapeutic Food) therapy. Follow the prescribed feeding schedule strictly.`;
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
    currentUserId = user.id;

    // Update parent name in DOM
    const initial = user.full_name ? user.full_name[0].toUpperCase() : "P";
    const sfAv = document.querySelector(".sf-av");
    if (sfAv) sfAv.textContent = initial;
    const sfName = document.querySelector(".sf-name");
    if (sfName) sfName.textContent = user.full_name;

    const tbAv = document.querySelector(".tb-av");
    if (tbAv) tbAv.textContent = initial;
    const tbName = document.querySelector(".tb-name");
    if (tbName) tbName.textContent = user.full_name;

    // Profile form
    const pfVals = document.querySelectorAll(".profile-form .pf-val");
    if (pfVals.length >= 3) {
      pfVals[0].textContent = user.full_name;
      pfVals[1].textContent = user.phone || "+91 98765 43210";
      pfVals[2].textContent = user.email;
    }
  } catch (e) {
    console.error("Error loading parent profile:", e);
  }
}

async function loadChildData() {
  try {
    const res = await fetch(`${API_BASE}/children`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const children = await res.json();
    
    if (children.length === 0) {
      // Step 3: Progressive Onboarding - prompt parent to complete child profile
      openChildProfileModal();
      return;
    }

    closeChildProfileModal();
    currentChild = children[0];

    // Immediately replace names across all sections
    updateDynamicChildNames();

    // Populate Overview Hero Card Meta
    const metaPills = document.querySelectorAll(".chc-meta .meta-pill");
    if (metaPills.length >= 3) {
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
      childCardPf[3].textContent = "14 Months";
      childCardPf[4].textContent = `${currentChild.birth_weight || 2.8} kg (Birth Weight)`;
      childCardPf[5].textContent = currentChild.health_id;
    }

    // Load child growth history & sub-modules
    await loadChildGrowthHistory(currentChild.id);
    await loadChildPhotos(currentChild.id);
    await loadMedicalHistory(currentChild.id);
    await loadNutritionPlan(currentChild.id);
    await loadAppointments(currentChild.id);
  } catch (e) {
    console.error("Error loading child data:", e);
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
    
    const firstName = getChildFirstName();

    // If child has no assessments yet, show neutral state
    if (currentChildGrowth.length === 0) {
      updateDynamicChildNames();
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
      return;
    }

    const growth = currentChildGrowth;
    const latest = growth[growth.length - 1];
    const riskVal = latest.risk_score !== undefined ? latest.risk_score : 82;

    // 1. 🏠 Update Overview Hero Stats
    const csVals = document.querySelectorAll(".chc-stat .cs-val");
    if (csVals.length >= 4) {
      csVals[0].innerHTML = `${latest.weight}<span>kg</span>`;
      csVals[1].innerHTML = `${latest.height}<span>cm</span>`;
      csVals[2].innerHTML = `${latest.muac || 11.5}<span>cm</span>`;
      csVals[3].innerHTML = `${Math.round(riskVal)}<span>%</span>`;
    }

    // Update Hero Risk Badge
    const statusBadge = document.querySelector(".status-badge");
    const lastCheck = document.querySelector(".last-check");
    if (statusBadge) {
      const pred = latest.prediction || "Normal";
      const isHighRisk = riskVal > 80;
      statusBadge.className = `status-badge ${isHighRisk ? 'danger' : 'normal'}`;
      statusBadge.textContent = `⚠️ ${pred} — ${isHighRisk ? 'High Risk' : 'Monitoring'}`;
    }
    if (lastCheck) {
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

    // 2. 📈 RENDER GROWTH CHARTS
    renderGrowthCharts(growth);

    // Populate Measurements Table in Growth Tracker
    const tbody = document.querySelector("#sec-growth table tbody");
    if (tbody) {
      tbody.innerHTML = "";
      [...growth].reverse().forEach(pt => {
        const tr = document.createElement("tr");
        const pred = pt.prediction || "Normal";
        let badgeClass = "normal";
        if (pred.includes("Stunted")) badgeClass = "stunted";
        else if (pred.includes("Wasted")) badgeClass = "wasted";
        else if (pred.includes("SAM") || pred.includes("Severe")) badgeClass = "severe";
        else if (pred.includes("Underweight")) badgeClass = "underweight";

        tr.innerHTML = `
          <td>${pt.date}</td>
          <td>${pt.age_months} mo</td>
          <td class="${pt.weight < 8 ? 'val-bad' : 'val-ok'}">${pt.weight} kg</td>
          <td class="${pt.height < 72 ? 'val-bad' : 'val-ok'}">${pt.height} cm</td>
          <td class="${(pt.muac && pt.muac < 12.5) ? 'val-bad' : 'val-ok'}">${pt.muac || 12.0} cm</td>
          <td class="val-ok">${pt.head_circumference || 45.0} cm</td>
          <td><span class="badge ${badgeClass}">${pred}</span></td>
        `;
        tbody.appendChild(tr);
      });
    }

    // 3. 🤖 UPDATE AI ASSESSMENT SECTION
    updateAIAssessmentSection(latest);

    // Dynamic child names pass
    updateDynamicChildNames();

  } catch (e) {
    console.error("Error loading growth data:", e);
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

function updateAIAssessmentSection(latest) {
  const arcChip = document.querySelector(".arc-chip");
  const arcDate = document.querySelector(".arc-date");
  if (arcDate) arcDate.textContent = `Assessed: ${latest.date}`;
  
  const riskVal = latest.risk_score !== undefined ? latest.risk_score : 82;
  const isHighRisk = riskVal > 80;
  
  if (arcChip) {
    arcChip.className = `arc-chip ${isHighRisk ? 'danger' : 'success'}`;
    arcChip.textContent = isHighRisk ? `⚠️ HIGH RISK: ${latest.prediction.toUpperCase()}` : `✅ NORMAL NUTRITIONAL STATUS`;
  }

  // Risk Score Bars
  const arcPcts = document.querySelectorAll(".arc-pct");
  const arcFills = document.querySelectorAll(".arc-fill");
  
  const stunting = Math.min(100, latest.height < 72 ? 82 : 18);
  const wasting = Math.min(100, (latest.muac && latest.muac < 12.5) ? 65 : 22);
  const underweight = Math.min(100, latest.weight < 8 ? 74 : 15);
  const sam = Math.min(100, (latest.muac && latest.muac < 11.5) ? 85 : 20);

  if (arcPcts.length >= 4 && arcFills.length >= 4) {
    arcPcts[0].textContent = `${stunting}%`;
    arcFills[0].style.width = `${stunting}%`;

    arcPcts[1].textContent = `${wasting}%`;
    arcFills[1].style.width = `${wasting}%`;

    arcPcts[2].textContent = `${underweight}%`;
    arcFills[2].style.width = `${underweight}%`;

    arcPcts[3].textContent = `${sam}%`;
    arcFills[3].style.width = `${sam}%`;
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

    const photoGrid = document.querySelector(".photo-grid");
    if (!photoGrid) return;

    photoGrid.innerHTML = "";
    photos.forEach(p => {
      const thumb = document.createElement("div");
      thumb.className = "photo-thumb";
      thumb.style.position = "relative";
      thumb.innerHTML = `
        <div class="pt-placeholder green" style="background:#eaf8f1;overflow:hidden;display:flex;align-items:center;justify-content:center;height:110px;border-radius:12px;">
          <img src="http://127.0.0.1:8000/${p.file_path}" alt="${p.photo_type}" style="width:100%;height:100%;object-fit:cover;" onerror="this.style.display='none';this.parentElement.innerHTML='📷<br><span>${p.photo_type.toUpperCase()}</span>'"/>
        </div>
        <div class="pt-date" style="display:flex;justify-content:space-between;align-items:center;padding:4px 2px;">
          <span>${p.photo_type.toUpperCase()}</span>
          <button onclick="deleteChildPhoto(${p.id})" style="background:none;border:none;color:#e74c3c;font-size:.75rem;cursor:pointer;" title="Delete Photo">🗑️</button>
        </div>
      `;
      photoGrid.appendChild(thumb);
    });

    const addMore = document.createElement("div");
    addMore.className = "photo-thumb add-more";
    addMore.onclick = () => document.getElementById("photoFileInput").click();
    addMore.innerHTML = `<div class="pt-add">+</div><div class="pt-date">Add Photo</div>`;
    photoGrid.appendChild(addMore);
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

async function loadNutritionPlan(childId) {
  try {
    const res = await fetch(`${API_BASE}/nutrition/child/${childId}`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const plans = await res.json();
    if (plans.length === 0) return;

    const plan = plans[0];
    const alertTitle = document.querySelector("#sec-nutrition .ab-title");
    if (alertTitle) alertTitle.textContent = plan.plan_title;
    const alertText = document.querySelector("#sec-nutrition .ab-text");
    if (alertText && plan.description) {
      alertText.textContent = plan.description.replace(/Aarav/g, getChildFirstName());
    }
  } catch (e) {
    console.error("Error loading nutrition plan:", e);
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

    // Update Next Appointment card in Overview tab
    const upcoming = appts.find(a => a.status === "upcoming") || appts[0];
    if (upcoming) {
      currentUpcomingAppt = upcoming;
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
    if (notifBadge) notifBadge.textContent = unreadCount;

    notifPanel.innerHTML = `<div class="np-header"><span>Notifications (${unreadCount} unread)</span><a onclick="toggleNotifPanel()">&#10005;</a></div>`;
    notifs.forEach(n => {
      const item = document.createElement("div");
      item.className = `np-item ${n.is_read ? '' : 'unread'}`;
      item.innerHTML = `
        <div class="np-icon" style="background:rgba(231,76,60,.12);color:#c0392b">⚠️</div>
        <div class="np-body">
          <div class="np-text"><strong>${n.title}:</strong> ${n.message.replace(/Aarav/g, getChildFirstName())}</div>
          <div class="np-ts">${n.created_at ? n.created_at.split('T')[0] : 'Recent'}</div>
        </div>
      `;
      notifPanel.appendChild(item);
    });
  } catch (e) {
    console.error("Error loading notifications:", e);
  }
}

// -------------------------------------------------------------
// MODALS: CHILD REGISTRATION, ASSESSMENT, APPOINTMENT DETAILS
// -------------------------------------------------------------
function openChildProfileModal() {
  const m = document.getElementById("childProfileModal");
  if (m) m.style.display = "flex";
}

function closeChildProfileModal() {
  const m = document.getElementById("childProfileModal");
  if (m) m.style.display = "none";
}

async function submitChildProfile(e) {
  e.preventDefault();
  const name = document.getElementById("newChildName").value.trim();
  const dob = document.getElementById("newChildDob").value;
  const gender = document.getElementById("newChildGender").value;
  const birthWeight = document.getElementById("newChildWeight").value ? parseFloat(document.getElementById("newChildWeight").value) : null;
  const birthLength = document.getElementById("newChildLength").value ? parseFloat(document.getElementById("newChildLength").value) : null;

  const btn = document.getElementById("btnSaveChild");
  if (btn) btn.textContent = "Creating Profile...";

  try {
    const res = await fetch(`${API_BASE}/children`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        name: name,
        date_of_birth: dob,
        gender: gender,
        birth_weight: birthWeight,
        birth_length: birthLength
      })
    });

    if (res.ok) {
      const newChild = await res.json();
      closeChildProfileModal();
      showToast(`Child profile created for ${newChild.name}! Initializing dashboard...`);
      await loadChildData();
    } else {
      const err = await res.json();
      showToast(err.detail || "Error saving child profile.", "error");
    }
  } catch (err) {
    console.error(err);
    showToast("Error connecting to server.", "error");
  } finally {
    if (btn) btn.textContent = "Save Child Profile & Continue";
  }
}

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
      const pred = result.prediction ? result.prediction.prediction : "Normal";
      const risk = result.prediction ? result.prediction.risk_score : 0;
      showToast(`AI Assessment Complete! Prediction: ${pred} (${risk}% Risk)`);
      
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
  closeSidebar();
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  const target = document.getElementById('sec-' + id);
  if (target) target.classList.add('active');

  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  if (el) el.classList.add('active');

  var titles = {
    overview: 'Overview',
    growth: 'Growth Tracker',
    assessment: 'AI Assessment',
    photos: 'Child Photos',
    medical: 'Medical History',
    nutrition: 'Diet & Nutrition',
    appointments: 'Appointments',
    profile: 'My Profile'
  };
  document.getElementById('pageTitle').textContent = titles[id] || id;
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

function toggleNotifPanel() {
  document.getElementById('notifPanel').classList.toggle('open');
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
// CHILD MEDICAL REPORT PDF DOWNLOAD & MODAL ENGINE
// -------------------------------------------------------------
async function populateReportFields() {
  const child = currentChild || {};
  const name = child.name || "Visheshwar Yadav";
  const firstName = getChildFirstName();
  const healthId = child.health_id || "CHN-2026-E0FD0";
  const dob = child.date_of_birth || "15 May 2025";
  const gender = child.gender || "Male";
  const bWt = child.birth_weight ? `${child.birth_weight} kg` : "2.4 kg";
  const bHt = child.birth_length ? `${child.birth_length} cm` : "67.5 cm";

  let ageStr = "14 Months";
  if (child.date_of_birth) {
    const d = new Date(child.date_of_birth);
    const now = new Date();
    const months = Math.max(1, Math.round((now - d) / (1000 * 60 * 60 * 24 * 30.4375)));
    ageStr = `${months} Months`;
  }

  const el = id => document.getElementById(id);
  if (el("repChildName")) el("repChildName").textContent = name;
  if (el("repHealthId")) el("repHealthId").textContent = healthId;
  if (el("repChildDob")) el("repChildDob").textContent = dob;
  if (el("repChildGenderAge")) el("repChildGenderAge").textContent = `${gender} / ${ageStr}`;
  if (el("repBirthStats")) el("repBirthStats").textContent = `${bWt} / ${bHt}`;
  if (el("repGeneratedDate")) el("repGeneratedDate").textContent = new Date().toLocaleDateString("en-GB", { day: '2-digit', month: 'short', year: 'numeric' });

  const user = JSON.parse(localStorage.getItem("childnutri_user") || "{}");
  if (el("repParentName")) el("repParentName").textContent = user.full_name || user.name || "Rahul Kumar";
  if (el("repParentPhone")) el("repParentPhone").textContent = user.phone || "+91 98765 43210";

  if (currentGrowthData && currentGrowthData.length > 0) {
    const latest = currentGrowthData[currentGrowthData.length - 1];
    if (el("repWeight")) el("repWeight").textContent = `${latest.weight} kg`;
    if (el("repHeight")) el("repHeight").textContent = `${latest.height} cm`;
    if (el("repMuac") && latest.muac) el("repMuac").textContent = `${latest.muac} cm`;
  }

  // Populate dynamic AI evaluation summary
  if (el("repAiSummaryText")) {
    el("repAiSummaryText").textContent = `${firstName} exhibits nutritional deficit with active therapeutic intervention. Anthropometric monitoring indicates steady response to supplementary feeding.`;
  }

  // Load and populate medical history records in table
  if (child.id) {
    try {
      const res = await fetch(`${API_BASE}/medical/child/${child.id}`, { headers: getAuthHeaders() });
      if (res.ok) {
        const history = await res.json();
        const tbody = el("repMedicalTableBody");
        if (tbody && history.length > 0) {
          tbody.innerHTML = "";
          history.forEach(item => {
            const tr = document.createElement("tr");
            tr.style.borderBottom = "1px solid #e2e8f0";
            const tagColor = item.diagnosis.toLowerCase().includes("sam") || item.diagnosis.toLowerCase().includes("stunt") ? "#e74c3c" : "#f4a827";
            tr.innerHTML = `
              <td style="padding:7px 10px;font-weight:600;">${item.visit_date}</td>
              <td style="padding:7px 10px;">${item.doctor_name}</td>
              <td style="padding:7px 10px;"><span style="color:${tagColor};font-weight:700;">${item.diagnosis}</span></td>
              <td style="padding:7px 10px;">${(item.notes || item.treatment || 'Routine clinical assessment.').replace(/Aarav/g, firstName)}</td>
            `;
            tbody.appendChild(tr);
          });
        }
      }
    } catch (e) {
      console.warn("Could not refresh medical table for report:", e);
    }
  }
}

function openMedicalReportModal() {
  const modal = document.getElementById("medicalReportModal");
  if (!modal) return;
  populateReportFields();
  modal.style.display = "flex";
  document.body.style.overflow = "hidden";
}

function closeMedicalReportModal() {
  const modal = document.getElementById("medicalReportModal");
  if (modal) modal.style.display = "none";
  document.body.style.overflow = "auto";
}

function printMedicalReport() {
  window.print();
}

function downloadMedicalReportPDF() {
  populateReportFields();
  const child = currentChild || {};
  const childName = (child.name || "Child").replace(/\s+/g, '_');
  const filename = `ChildNutri_Medical_Report_${childName}.pdf`;

  showToast("Generating official PDF report...", "info");

  const element = document.getElementById("printableReportArea");
  if (!element) {
    window.print();
    return;
  }

  // Check if html2pdf is available
  if (typeof html2pdf !== "undefined") {
    const opt = {
      margin:       [8, 8, 8, 8],
      filename:     filename,
      image:        { type: 'jpeg', quality: 0.98 },
      html2canvas:  { scale: 2, useCORS: true, letterRendering: true, logging: false },
      jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };

    html2pdf().set(opt).from(element).save().then(() => {
      showToast("Medical Report PDF downloaded successfully!");
    }).catch(err => {
      console.warn("html2pdf fallback to print:", err);
      window.print();
    });
  } else {
    // Graceful fallback to browser print/save as PDF
    window.print();
  }
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
