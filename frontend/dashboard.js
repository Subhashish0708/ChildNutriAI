/**
 * Health Worker Dashboard Controller - ChildNutri AI
 * Communicates with FastAPI Backend (/api/auth, /api/users/stats, /api/children, /api/assessments, etc.)
 */

const API_BASE = "http://127.0.0.1:8000/api";
let currentUser = null;
let currentChildren = [];

// Check Authentication & Load Dashboard Data on page load
document.addEventListener("DOMContentLoaded", async function () {
  const token = localStorage.getItem("childnutri_token");
  if (!token) {
    window.location.href = "index.html";
    return;
  }

  await loadCurrentUser();
  await loadDashboardStats();
  await loadRecentAssessments();
  await loadNotifications();
  await loadUpcomingFollowUps();
});

function getAuthHeaders() {
  const token = localStorage.getItem("childnutri_token");
  return {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`
  };
}

async function loadCurrentUser() {
  try {
    const res = await fetch(`${API_BASE}/auth/me`, { credentials: "omit", headers: getAuthHeaders() });
    if (!res.ok) {
      localStorage.removeItem("childnutri_token");
      window.location.href = "index.html";
      return;
    }
    currentUser = await res.json();

    // Populate user profile info in DOM
    const initial = currentUser.full_name ? currentUser.full_name[0].toUpperCase() : "H";
    const sfAvatar = document.querySelector(".sf-avatar");
    if (sfAvatar) sfAvatar.textContent = initial;
    const sfName = document.querySelector(".sf-name");
    if (sfName) sfName.textContent = currentUser.full_name;

    const tbAvatar = document.querySelector(".tb-avatar");
    if (tbAvatar) tbAvatar.textContent = initial;
    const tbName = document.querySelector(".tb-name");
    if (tbName) tbName.textContent = currentUser.full_name;

    const greetingName = document.querySelector(".greeting-bar h2 span");
    if (greetingName) greetingName.textContent = currentUser.full_name;
  } catch (e) {
    console.error("Error loading user profile:", e);
  }
}

async function loadDashboardStats() {
  try {
    const res = await fetch(`${API_BASE}/users/stats`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const stats = await res.json();

    // Update Stat Cards
    const statCards = document.querySelectorAll(".stat-card .sc-val");
    if (statCards.length >= 4) {
      statCards[0].textContent = stats.total_children;
      statCards[1].textContent = stats.at_risk_count;
      statCards[2].textContent = stats.normal_count;
      statCards[3].textContent = stats.followups_scheduled;
    }

    // Update Donut Center Number
    const donutNum = document.querySelector(".donut-num");
    if (donutNum) donutNum.textContent = stats.total_children;

    // Update Legend Values
    const legendVals = document.querySelectorAll(".legend-val");
    if (legendVals.length >= 4 && stats.status_distribution) {
      legendVals[0].textContent = stats.status_distribution["Normal"] || 0;
      legendVals[1].textContent = stats.status_distribution["Stunted"] || 0;
      legendVals[2].textContent = stats.status_distribution["Wasted"] || 0;
      legendVals[3].textContent = stats.status_distribution["Severe SAM"] || 0;
    }
  } catch (e) {
    console.error("Error loading stats:", e);
  }
}

async function loadRecentAssessments() {
  try {
    const res = await fetch(`${API_BASE}/assessments/recent?limit=6`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const assessments = await res.json();

    const tbody = document.querySelector(".tbl-wrap tbody");
    if (!tbody) return;

    if (assessments.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:24px;color:#718096;">No assessments conducted yet. Click "+ New Assessment" above.</td></tr>`;
      return;
    }

    tbody.innerHTML = "";
    assessments.forEach(a => {
      const pred = a.prediction ? a.prediction.prediction : "Normal";
      const risk = a.prediction ? a.prediction.risk_score : 10;
      
      let badgeClass = "normal";
      let riskLevel = "low";
      if (pred.includes("SAM") || pred.includes("Severe")) { badgeClass = "severe"; riskLevel = "high"; }
      else if (pred.includes("Stunted")) { badgeClass = "stunted"; riskLevel = "high"; }
      else if (pred.includes("Wasted")) { badgeClass = "wasted"; riskLevel = "medium"; }
      else if (pred.includes("Underweight")) { badgeClass = "underweight"; riskLevel = "medium"; }

      const childName = `Child #${a.child_id}`;
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>
          <div class="child-info">
            <div class="child-avatar" style="background:linear-gradient(135deg,#1a7f5a,#27a872)">${childName[0]}</div>
            <div>
              <div class="child-name">${childName}</div>
              <div class="child-age">${a.age_months} months &bull; ${a.weight}kg &bull; ${a.height}cm</div>
            </div>
          </div>
        </td>
        <td><span class="badge ${badgeClass}">${pred}</span></td>
        <td><div class="risk-bar"><div class="risk-fill ${riskLevel}" style="width:${Math.min(100, risk)}%"></div></div></td>
        <td class="td-muted">${a.assessment_date}</td>
        <td>
          <div class="action-row">
            <button class="tbl-btn view" onclick="showToast('Viewing assessment #${a.id} details...')">View</button>
            <button class="tbl-btn report" onclick="showToast('Assessment report for Child #${a.child_id} generated.')">Report</button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (e) {
    console.error("Error loading recent assessments:", e);
  }
}

async function loadNotifications() {
  try {
    const res = await fetch(`${API_BASE}/notifications`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const notifs = await res.json();

    const notifList = document.querySelector(".notif-list");
    if (!notifList) return;

    if (notifs.length === 0) {
      notifList.innerHTML = `<div style="padding:16px;color:#718096;text-align:center;">No new notifications</div>`;
      return;
    }

    notifList.innerHTML = "";
    notifs.slice(0, 5).forEach(n => {
      const item = document.createElement("div");
      item.className = "notif-item";
      item.innerHTML = `
        <div class="notif-dot-i ${n.is_read ? 'read' : 'unread'}"></div>
        <div class="notif-body">
          <div class="notif-text"><strong>${n.title}</strong> &mdash; ${n.message}</div>
          <div class="notif-ts">${n.created_at ? n.created_at.split('T')[0] : 'Today'}</div>
        </div>
      `;
      notifList.appendChild(item);
    });
  } catch (e) {
    console.error("Error loading notifications:", e);
  }
}

async function loadUpcomingFollowUps() {
  try {
    const res = await fetch(`${API_BASE}/appointments?status_filter=upcoming`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const appts = await res.json();

    const alertGrid = document.querySelector(".alert-grid");
    if (!alertGrid || appts.length === 0) return;

    alertGrid.innerHTML = "";
    appts.slice(0, 4).forEach(appt => {
      const item = document.createElement("div");
      item.className = "alert-item medium";
      item.innerHTML = `
        <div class="alert-icon">&#128197;</div>
        <div class="alert-body">
          <div class="alert-name">${appt.purpose} (Child #${appt.child_id})</div>
          <div class="alert-detail">${appt.notes || 'Routine pediatric monitoring and growth check'}</div>
          <div class="alert-time">Date: ${appt.appointment_date} &bull; ${appt.appointment_time || '10:00 AM'}</div>
        </div>
        <span class="alert-badge medium">UPCOMING</span>
      `;
      alertGrid.appendChild(item);
    });
  } catch (e) {
    console.error("Error loading follow-ups:", e);
  }
}

async function submitAssessment(e) {
  e.preventDefault();
  const childName = document.getElementById("assessChildName").value.trim();
  const dob = document.getElementById("assessDob").value;
  const gender = document.getElementById("assessGender").value || "Male";
  const ageMonths = parseFloat(document.getElementById("assessAge").value);
  const weight = parseFloat(document.getElementById("assessWeight").value);
  const height = parseFloat(document.getElementById("assessHeight").value);
  const muac = document.getElementById("assessMuac").value ? parseFloat(document.getElementById("assessMuac").value) : null;
  const headCirc = document.getElementById("assessHeadCirc").value ? parseFloat(document.getElementById("assessHeadCirc").value) : null;
  const notes = document.getElementById("assessNotes").value.trim();

  const btn = document.getElementById("btnRunAssessment");
  if (btn) btn.textContent = "Running AI Analysis...";

  try {
    // 1. Create or find child
    let childRes = await fetch(`${API_BASE}/children`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        name: childName,
        date_of_birth: dob,
        gender: gender,
        birth_weight: weight,
        birth_length: height
      })
    });
    
    let childData = await childRes.json();
    const childId = childData.id;

    // 2. Submit assessment
    const assessRes = await fetch(`${API_BASE}/assessments`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        child_id: childId,
        age_months: ageMonths,
        weight: weight,
        height: height,
        muac: muac,
        head_circumference: headCirc,
        notes: notes
      })
    });

    const result = await assessRes.json();
    closeModal();
    if (btn) btn.textContent = "Run AI Assessment";

    if (assessRes.ok) {
      const pred = result.prediction ? result.prediction.prediction : "Assessment Saved";
      const risk = result.prediction ? result.prediction.risk_score : 0;
      showToast(`AI Assessment Complete! Result: ${pred} (${risk}% Risk)`);
      
      // Refresh dashboard metrics
      await loadDashboardStats();
      await loadRecentAssessments();
    } else {
      showToast(result.detail || "Assessment submission error.", "error");
    }
  } catch (err) {
    console.error(err);
    if (btn) btn.textContent = "Run AI Assessment";
    showToast("Error connecting to AI service.", "error");
  }
}

// UI Sidebar & Navigation Controls
function openSidebar() {
  document.getElementById("sidebar").classList.add("open");
  document.getElementById("sidebarOverlay").classList.add("open");
}

function closeSidebar() {
  document.getElementById("sidebar").classList.remove("open");
  document.getElementById("sidebarOverlay").classList.remove("open");
}

function showPage(name, el) {
  closeSidebar();
  document.querySelectorAll(".nav-item").forEach(function(i){ i.classList.remove("active"); });
  if (el) el.classList.add("active");
  document.getElementById("pageTitle").textContent = name;
  showToast("Viewing " + name);
}

function openModal() {
  document.getElementById("assessModal").classList.add("open");
  document.body.style.overflow = "hidden";
}

function closeModal() {
  document.getElementById("assessModal").classList.remove("open");
  document.body.style.overflow = "";
}

function handleOverlay(e) {
  if (e.target === document.getElementById("assessModal")) closeModal();
}

function showToast(msg) {
  var t = document.getElementById("toast");
  document.getElementById("toastMsg").textContent = msg;
  t.classList.add("show");
  setTimeout(function(){ t.classList.remove("show"); }, 3500);
}

function confirmLogout() {
  if (confirm("Are you sure you want to logout?")) {
    localStorage.removeItem("childnutri_token");
    localStorage.removeItem("childnutri_user");
    window.location.href = "index.html";
  }
}

document.addEventListener("keydown", function(e) {
  if (e.key === "Escape") closeModal();
});
