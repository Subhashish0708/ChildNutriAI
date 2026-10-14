/* ─── ChildNutri AI — App Logic ─────────────────────────────────────────── */

/* ══════════════════════ DASHBOARD ════════════════════════════════════════ */
async function loadDashboard() {
  const user = await requireUser();
  const nameEl = document.getElementById('welcome-name');
  if (nameEl) nameEl.textContent = user.full_name || user.email;

  const children = await API.get('/api/children').catch(() => []);
  const count = document.getElementById('children-count');
  if (count) count.textContent = children.length;
  const kpiC = document.getElementById('kpi-children');
  if (kpiC) kpiC.textContent = children.length;

  // Fetch all assessment counts (approximate via history)
  let totalA = 0, atRisk = 0;
  for (const child of children) {
    const hist = await API.get(`/api/assessments/child/${child.id}/history`).catch(() => []);
    totalA += hist.length;
    atRisk += hist.filter(h => h.tier === 'WATCH' || h.tier === 'HIGH').length;
  }
  const kpiA = document.getElementById('kpi-assessments');
  if (kpiA) kpiA.textContent = totalA;
  const kpiR = document.getElementById('kpi-risk');
  if (kpiR) kpiR.textContent = atRisk;

  renderChildren(children);
}

function renderChildren(children) {
  const list = document.getElementById('children-list');
  if (!list) return;

  if (!children.length) {
    list.innerHTML = `
      <div class="empty-state">
        <span class="empty-icon">👶</span>
        <h3>No children yet</h3>
        <p>Add the first profile to begin screening.</p>
      </div>`;
    return;
  }

  list.innerHTML = children.map(child => {
    const initials = child.name.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase();
    return `
      <article class="card" style="display:flex;gap:14px;align-items:flex-start;margin-bottom:12px;">
        <div style="width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,var(--green),var(--cyan));display:grid;place-items:center;font-weight:800;color:#031a13;flex-shrink:0;font-size:14px;">${initials}</div>
        <div style="flex:1;min-width:0;">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;flex-wrap:wrap;">
            <h3 style="font-size:15px;">${child.name}</h3>
            <span class="badge neutral">${child.sex}</span>
          </div>
          <p class="muted" style="font-size:12px;">Born ${fmtDate(child.date_of_birth)} · ID ${child.health_id}</p>
          <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;">
            <a class="btn sm primary" href="/assess.html?child=${child.id}">Screen →</a>
            <a class="btn sm" href="/result.html?child=${child.id}">History</a>
          </div>
        </div>
      </article>`;
  }).join('');
}

function bindChildForm() {
  const form = document.getElementById('child-form');
  if (!form) return;
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const btn = document.getElementById('child-btn');
    const msg = document.getElementById('child-msg');
    btn.disabled = true; btn.textContent = 'Saving…';
    const data = Object.fromEntries(new FormData(form));
    data.birth_weight_kg = data.birth_weight_kg ? +data.birth_weight_kg : null;
    data.birth_length_cm = data.birth_length_cm ? +data.birth_length_cm : null;
    try {
      await API.post('/api/children', data);
      form.reset();
      msg.className = 'message success';
      msg.textContent = 'Child profile saved!';
      await loadDashboard();
    } catch (err) {
      msg.className = 'message error';
      msg.textContent = err.message;
    } finally {
      btn.disabled = false; btn.textContent = 'Save profile';
    }
  });
}

/* ══════════════════════ ASSESSMENT WIZARD ═════════════════════════════════ */
let currentStep = 0;
const TOTAL_STEPS = 6;

function showStep(idx) {
  currentStep = Math.max(0, Math.min(idx, TOTAL_STEPS - 1));
  document.querySelectorAll('.step-tab').forEach((t, i) => {
    t.classList.toggle('active', i === currentStep);
    if (i < currentStep) t.classList.add('done');
    else t.classList.remove('done');
  });
  document.querySelectorAll('.step-panel').forEach((p, i) => {
    p.classList.toggle('active', i === currentStep);
  });
  const pf = document.getElementById('progress-fill');
  if (pf) pf.style.width = `${((currentStep + 1) / TOTAL_STEPS) * 100}%`;

  // Update review summary on last step
  if (currentStep === TOTAL_STEPS - 1) updateReviewSummary();
}

function updateReviewSummary() {
  const form = document.getElementById('assessment-form');
  if (!form) return;
  const f = new FormData(form);
  const el = document.getElementById('review-summary');
  if (!el) return;
  const child = document.getElementById('child-select');
  const childName = child ? child.options[child.selectedIndex]?.text : '—';
  el.innerHTML = `
    <div class="ocr-field"><span class="ocr-key">Child</span><span class="ocr-val">${childName}</span></div>
    <div class="ocr-field"><span class="ocr-key">Date</span><span class="ocr-val">${f.get('measurement_date') || '—'}</span></div>
    <div class="ocr-field"><span class="ocr-key">Weight</span><span class="ocr-val">${f.get('weight_kg') || '—'} kg</span></div>
    <div class="ocr-field"><span class="ocr-key">Height</span><span class="ocr-val">${f.get('height_cm') || '—'} cm</span></div>
    <div class="ocr-field"><span class="ocr-key">MUAC</span><span class="ocr-val">${f.get('muac_cm') || 'not entered'} cm</span></div>
    <div class="ocr-field"><span class="ocr-key">Breastfed</span><span class="ocr-val">${f.get('breastfed') === 'true' ? 'Yes' : 'No'}</span></div>
  `;
}

async function bindAssessmentWizard() {
  const form = document.getElementById('assessment-form');
  if (!form) return;
  await requireUser();

  // Populate child select
  const childSel = document.getElementById('child-select');
  const children = await API.get('/api/children').catch(() => []);
  if (!children.length) {
    childSel.innerHTML = '<option disabled>No children — add one in the Dashboard first</option>';
  } else {
    childSel.innerHTML = children.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    const preselect = qs('child');
    if (preselect) childSel.value = preselect;
  }
  const measDate = document.getElementById('meas-date');
  if (measDate) measDate.valueAsDate = new Date();

  // Apply prefill if coming from OCR scan
  const prefillRaw = sessionStorage.getItem('childnutri_prefill');
  if (prefillRaw) {
    try {
      const data = JSON.parse(prefillRaw);
      sessionStorage.removeItem('childnutri_prefill');

      if (data.child_name && children.length) {
        const match = children.find(c => 
          c.name.toLowerCase().includes(data.child_name.toLowerCase()) || 
          data.child_name.toLowerCase().includes(c.name.toLowerCase())
        );
        if (match) childSel.value = match.id;
      }
      if (data.measurement_date && form.elements['measurement_date']) form.elements['measurement_date'].value = data.measurement_date;
      if (data.weight_kg != null && form.elements['weight_kg']) form.elements['weight_kg'].value = data.weight_kg;
      if (data.height_cm != null && form.elements['height_cm']) form.elements['height_cm'].value = data.height_cm;
      if (data.muac_cm != null && form.elements['muac_cm']) form.elements['muac_cm'].value = data.muac_cm;
      if (data.head_circ_cm != null && form.elements['head_circ_cm']) form.elements['head_circ_cm'].value = data.head_circ_cm;
      if (data.how_measured && form.elements['how_measured']) form.elements['how_measured'].value = data.how_measured;
      if (data.bilateral_edema != null && form.elements['bilateral_edema']) form.elements['bilateral_edema'].checked = !!data.bilateral_edema;
      if (data.breastfed != null && form.elements['breastfed']) form.elements['breastfed'].value = String(data.breastfed);
      if (data.appetite && form.elements['appetite']) form.elements['appetite'].value = data.appetite;
      if (data.food_groups_yesterday != null && form.elements['food_groups_yesterday']) form.elements['food_groups_yesterday'].value = data.food_groups_yesterday;
      if (data.meals_per_day != null && form.elements['meals_per_day']) form.elements['meals_per_day'].value = data.meals_per_day;
      if (data.diarrhoea_2w != null && form.elements['diarrhoea_2w']) form.elements['diarrhoea_2w'].checked = !!data.diarrhoea_2w;
      if (data.fever_2w != null && form.elements['fever_2w']) form.elements['fever_2w'].checked = !!data.fever_2w;
      if (data.vaccination_status && form.elements['vaccination_status']) form.elements['vaccination_status'].value = data.vaccination_status;
      if (data.mother_education && form.elements['mother_education']) form.elements['mother_education'].value = data.mother_education;
      if (data.mother_age != null && form.elements['mother_age']) form.elements['mother_age'].value = data.mother_age;
      if (data.wealth_score != null && form.elements['wealth_score']) form.elements['wealth_score'].value = data.wealth_score;
      if (data.rural_urban && form.elements['rural_urban']) form.elements['rural_urban'].value = data.rural_urban;
      if (data.food_preference && form.elements['food_preference']) form.elements['food_preference'].value = data.food_preference;

      const banner = document.createElement('div');
      banner.className = 'alert healthy mb';
      banner.style.marginBottom = '16px';
      banner.innerHTML = '<span>✓</span><div><strong>Health Card Scanned:</strong> Measurements and health context were pre-filled. Please review and verify.</div>';
      const firstPanel = form.querySelector('.step-panel');
      if (firstPanel) firstPanel.prepend(banner);
    } catch (e) {
      console.warn('OCR prefill failed', e);
    }
  }

  // Apply photo screening indication if coming from Photo AI
  let cachedPhotoScreen = null;
  const photoRaw = sessionStorage.getItem('childnutri_photo_screen');
  if (photoRaw) {
    try {
      const pData = JSON.parse(photoRaw);
      cachedPhotoScreen = pData;
      sessionStorage.removeItem('childnutri_photo_screen');
      const pBanner = document.createElement('div');
      const isInconclusive = pData.status && (pData.status.includes('inconclusive') || pData.status.includes('unsupported'));
      const isCritical = pData.verdict && pData.verdict.includes('Severe');
      pBanner.className = `alert ${isCritical ? 'warning' : 'info'} mb`;
      pBanner.style.marginBottom = '16px';
      
      if (isInconclusive) {
        pBanner.innerHTML = `<span>📸</span><div><strong>Photo AI Screening (${pData.verdict}):</strong> Visual screening was inconclusive due to clothing obstruction or age criteria. Proceed with verified physical measurements (weight, height, and MUAC) below for clinical evaluation.</div>`;
      } else {
        pBanner.innerHTML = `<span>📸</span><div><strong>Photo AI Screening (${pData.verdict} · ${pData.confidence_pct}%):</strong> Preliminary visual screening noted. Please complete the anthropometric measurements below to establish verified WHO Z-scores and clinical care plan.</div>`;
      }
      const firstPanel = form.querySelector('.step-panel');
      if (firstPanel) firstPanel.prepend(pBanner);
    } catch (pe) {
      console.warn('Photo screen banner failed', pe);
    }
  }

  // Step tab clicks
  document.querySelectorAll('.step-tab[data-step]').forEach(btn => {
    btn.addEventListener('click', () => showStep(+btn.dataset.step));
  });

  // Next / Back buttons
  document.querySelectorAll('[data-next]').forEach(btn => btn.addEventListener('click', () => showStep(currentStep + 1)));
  document.querySelectorAll('[data-back]').forEach(btn => btn.addEventListener('click', () => showStep(currentStep - 1)));

  // Submit
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const btn = document.getElementById('submit-btn');
    const msg = document.getElementById('assess-msg');
    btn.disabled = true; btn.textContent = 'Running…';
    msg.className = 'message info'; msg.textContent = 'Running WHO rules, future-risk scoring, and diet plan…';

    const f = new FormData(form);
    const body = {
      child_id: +f.get('child_id'),
      measurement_date: f.get('measurement_date'),
      measurement: {
        weight_kg: +f.get('weight_kg'),
        height_cm: +f.get('height_cm'),
        muac_cm: f.get('muac_cm') ? +f.get('muac_cm') : null,
        head_circ_cm: f.get('head_circ_cm') ? +f.get('head_circ_cm') : null,
        bilateral_edema: f.get('bilateral_edema') === 'on',
        how_measured: f.get('how_measured'),
      },
      feeding: {
        breastfed: f.get('breastfed') === 'true',
        food_groups_yesterday: f.get('food_groups_yesterday') ? +f.get('food_groups_yesterday') : null,
        meals_per_day: f.get('meals_per_day') ? +f.get('meals_per_day') : null,
        appetite: f.get('appetite'),
      },
      health: {
        diarrhoea_2w: f.get('diarrhoea_2w') === 'on',
        fever_2w: f.get('fever_2w') === 'on',
        vaccination_status: f.get('vaccination_status'),
        known_illness: f.get('known_illness') || null,
        food_allergy: f.get('food_allergy') || null,
      },
      home: {
        mother_education: f.get('mother_education'),
        mother_age: f.get('mother_age') ? +f.get('mother_age') : null,
        wealth_score: f.get('wealth_score') ? +f.get('wealth_score') : null,
        rural_urban: f.get('rural_urban'),
        food_preference: f.get('food_preference'),
      },
    };
    if (cachedPhotoScreen) {
      body.photo_screening_result = cachedPhotoScreen;
    }

    try {
      const result = await API.post('/api/assessments', body);
      location.href = `/result.html?id=${result.id}`;
    } catch (err) {
      msg.className = 'message error'; msg.textContent = err.message;
      btn.disabled = false; btn.textContent = 'Run assessment ✓';
    }
  });
}

/* ══════════════════════ RESULT / HISTORY ══════════════════════════════════ */
async function loadResult() {
  const resultView = document.getElementById('result-view');
  const historyView = document.getElementById('history-view');
  if (!resultView && !historyView) return;
  await requireUser();

  const id = qs('id');
  const childId = qs('child');

  if (!id && childId) {
    // History view
    historyView && historyView.classList.remove('hidden');
    const link = document.getElementById('new-assess-link');
    if (link) link.href = `/assess.html?child=${childId}`;
    const history = await API.get(`/api/assessments/child/${childId}/history`).catch(() => []);
    renderHistory(history, childId);
    return;
  }

  if (!id) {
    const msg = document.getElementById('global-msg');
    if (msg) { msg.className = 'message error'; msg.textContent = 'No assessment ID provided.'; }
    return;
  }

  resultView && resultView.classList.remove('hidden');
  const assessment = await API.get(`/api/assessments/${id}`).catch(err => { throw err; });
  renderResult(assessment);

  // Load growth chart history
  if (assessment.child_id) {
    const history = await API.get(`/api/assessments/child/${assessment.child_id}/history`).catch(() => []);
    if (history.length > 1) renderGrowthChart(history, assessment.id);
  }
}

function severityClass(sev) {
  const map = {
    'healthy': 'healthy', 'normal': 'healthy',
    'moderate': 'watch', 'watch': 'watch',
    'severe': 'high', 'sam': 'high', 'critical': 'high',
    'mam': 'watch', 'stunted': 'watch', 'underweight': 'watch',
    'overweight': 'watch'
  };
  return map[(sev || '').toLowerCase()] || 'neutral';
}

function renderResult(assessment) {
  const r = assessment.result_json || {};
  const sn = r.status_now || {};
  const fr = r.future_risk || {};
  const zs = r.zscores || {};
  const diet = r.diet_plan || {};

  const sevClass = severityClass(sn.severity || sn.headline);
  const tierClass = severityClass(fr.tier);

  // Orb
  const orb = document.getElementById('result-orb');
  if (orb) orb.className = `orb status-${tierClass}`;

  // Badge + headline
  const badge = document.getElementById('result-badge');
  if (badge) { badge.className = `badge ${sevClass}`; badge.innerHTML = `<span class="badge-dot"></span>${sn.headline || 'Result'}`; }

  const headline = document.getElementById('result-headline');
  if (headline) headline.textContent = sn.headline || '—';

  const conf = document.getElementById('result-confidence');
  if (conf) conf.textContent = `Data confidence: ${r.data_confidence || '—'}`;

  const expl = document.getElementById('result-explanation');
  if (expl) expl.textContent = Object.values(sn.explanation || {}).join(' ') || '';

  // PDF link - programmatic download ensuring proper filename and auth cookies
  const pdf = document.getElementById('pdf-link');
  if (pdf) {
    pdf.href = '#';
    pdf.onclick = async (e) => {
      e.preventDefault();
      const origText = pdf.textContent;
      try {
        pdf.textContent = 'Generating PDF…';
        const res = await fetch(`/api/assessments/${assessment.id}/pdf`, { credentials: 'include' });
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || `Server error (HTTP ${res.status})`);
        }
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ChildNutriAI_Report_${assessment.id}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      } catch (err) {
        alert('Could not download PDF report: ' + err.message);
      } finally {
        pdf.textContent = origText;
      }
    };
  }

  // Z-scores
  const zDisplay = document.getElementById('zscore-display');
  if (zDisplay) {
    const zRows = [
      { label: 'Weight-for-age (WAZ)', i18n: 'weight_for_age', val: zs.waz, ref: '-2 to +2' },
      { label: 'Height-for-age (HAZ)', i18n: 'height_for_age', val: zs.haz, ref: '-2 to +2' },
      { label: 'Weight-for-height (WHZ)', i18n: 'weight_for_height', val: zs.whz, ref: '-2 to +2' },
    ];
    zDisplay.innerHTML = zRows.map(({ label, i18n, val }) => {
      const v = val ?? null;
      const cls = v === null ? '' : v < -3 ? 'red' : v < -2 ? 'amber' : v > 2 ? 'amber' : 'green';
      return `<div class="ocr-field">
        <span class="ocr-key" style="font-size:12px;" data-i18n="${i18n}">${label}</span>
        <span class="ocr-val ${cls}">${v !== null ? v.toFixed(2) : 'N/A'}</span>
      </div>`;
    }).join('');
  }

  // Future risk
  const frDisplay = document.getElementById('future-risk-display');
  if (frDisplay) {
    frDisplay.innerHTML = `
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
        <span class="badge ${tierClass}" style="font-size:14px;padding:6px 16px;">${fr.tier || '—'}</span>
        <span class="muted" style="font-size:13px;">${fr.total_points || 0} pts</span>
      </div>
      <p class="muted" style="font-size:13px;">${fr.horizon || ''}</p>
      <div class="mt-sm" style="font-size:12px;">
        <div class="ocr-field"><span class="ocr-key">Trend</span><span class="ocr-val">${fr.breakdown?.trend ?? 0} pts</span></div>
        <div class="ocr-field"><span class="ocr-key">Closeness</span><span class="ocr-val">${fr.breakdown?.closeness ?? 0} pts</span></div>
        <div class="ocr-field"><span class="ocr-key">ML model</span><span class="ocr-val">${fr.breakdown?.model ?? 0} pts</span></div>
      </div>`;
  }

  // Risk reasons
  const reasons = document.getElementById('risk-reasons');
  if (reasons) {
    const list = fr.reasons || ['No significant risk factors identified'];
    reasons.innerHTML = list.map(r => `<li>${r}</li>`).join('');
  }

  // Diet accordion
  const acc = document.getElementById('diet-accordion');
  if (acc && diet) {
    const sections = [
      { key: 'what_this_means', title: 'What this means', i18n: 'what_this_means' },
      { key: 'how_to_feed', title: 'How to feed', i18n: 'how_to_feed' },
      { key: 'foods_that_help', title: 'Foods that help', i18n: 'foods_that_help', isList: true },
      { key: 'when_to_return', title: 'When to return / follow-up' },
      { key: 'government_help', title: 'Government support (India)', i18n: 'govt_support' },
      { key: 'red_flags', title: '🚩 Red flags — seek care immediately', i18n: 'red_flags', isList: true },
    ];
    acc.innerHTML = sections.map((s, i) => {
      const val = diet[s.key];
      if (!val || (Array.isArray(val) && !val.length)) return '';
      const body = s.isList && Array.isArray(val)
        ? `<ul class="list-bullet">${val.map(x => `<li>${x}</li>`).join('')}</ul>`
        : `<p style="font-size:14px;color:var(--text-2);line-height:1.7;">${val}</p>`;
      const i18nAttr = s.i18n ? ` data-i18n="${s.i18n}"` : '';
      return `
        <div class="accordion-item${i === 0 ? ' open' : ''}">
          <button class="accordion-toggle" onclick="toggleAccordion(this)">
            <span${i18nAttr}>${s.title}</span>
            <span class="chevron">▼</span>
          </button>
          <div class="accordion-body">${body}</div>
        </div>`;
    }).join('');
  }

  if (typeof applyTranslations === 'function') {
    applyTranslations(currentLang);
  }
}

function toggleAccordion(btn) {
  const item = btn.closest('.accordion-item');
  item.classList.toggle('open');
}

function renderHistory(history, childId) {
  const link = document.getElementById('new-assess-link');
  if (link) link.href = `/assess.html?child=${childId}`;

  const list = document.getElementById('history-list');
  if (!list) return;

  if (!history.length) {
    list.innerHTML = `<div class="empty-state"><span class="empty-icon">📋</span><h3>No assessments yet</h3><p>Start the first screening for this child.</p><a class="btn primary mt" href="/assess.html?child=${childId}">Start screening</a></div>`;
    return;
  }

  list.innerHTML = history.map(item => {
    const sevClass = severityClass(item.tier || item.status);
    return `
      <div class="tl-item">
        <div class="tl-dot">✓</div>
        <div class="tl-body">
          <p class="tl-date">${fmtDate(item.date)}</p>
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap;">
            <span class="badge ${sevClass}">${item.status || '—'}</span>
            <span class="badge ${sevClass}">${item.tier || '—'} risk</span>
          </div>
          <p class="muted" style="font-size:12px;">WAZ ${item.waz?.toFixed(2) ?? '—'} · HAZ ${item.haz?.toFixed(2) ?? '—'} · WHZ ${item.whz?.toFixed(2) ?? '—'}</p>
          <a class="btn sm mt-sm" href="/result.html?id=${item.id}">View result</a>
        </div>
      </div>`;
  }).join('');

  // Chart
  renderHistoryChart(history);
}

function renderHistoryChart(history) {
  const canvas = document.getElementById('history-chart');
  if (!canvas || typeof Chart === 'undefined') return;
  if (!history.length) return;

  const sorted = [...history].sort((a, b) => a.date.localeCompare(b.date));
  const labels = sorted.map(h => fmtDate(h.date));
  const wazData = sorted.map(h => h.waz ?? null);
  const hazData = sorted.map(h => h.haz ?? null);

  new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [
        { label: 'WAZ', data: wazData, borderColor: '#34d399', backgroundColor: 'rgba(52,211,153,0.1)', tension: 0.4, pointRadius: 5, borderWidth: 2 },
        { label: 'HAZ', data: hazData, borderColor: '#22d3ee', backgroundColor: 'rgba(34,211,238,0.1)', tension: 0.4, pointRadius: 5, borderWidth: 2 },
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#7fada0', font: { size: 12 } } } },
      scales: {
        x: { ticks: { color: '#7fada0' }, grid: { color: 'rgba(255,255,255,0.06)' } },
        y: { ticks: { color: '#7fada0' }, grid: { color: 'rgba(255,255,255,0.06)' },
          title: { display: true, text: 'Z-score', color: '#7fada0' },
          min: -4, max: 4 }
      }
    }
  });
}

function renderGrowthChart(history, currentId) {
  const wrap = document.getElementById('growth-chart-wrap');
  const canvas = document.getElementById('growth-chart');
  if (!wrap || !canvas || typeof Chart === 'undefined') return;
  if (history.length < 2) return;

  wrap.style.display = '';
  const sorted = [...history].sort((a, b) => a.date.localeCompare(b.date));
  const labels = sorted.map(h => fmtDate(h.date));

  new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [
        { label: 'WAZ', data: sorted.map(h => h.waz ?? null), borderColor: '#34d399', tension: 0.4, pointRadius: 5, borderWidth: 2 },
        { label: 'HAZ', data: sorted.map(h => h.haz ?? null), borderColor: '#22d3ee', tension: 0.4, pointRadius: 5, borderWidth: 2 },
        { label: 'WHZ', data: sorted.map(h => h.whz ?? null), borderColor: '#a78bfa', tension: 0.4, pointRadius: 5, borderWidth: 2 },
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#7fada0', font: { size: 12 } } } },
      scales: {
        x: { ticks: { color: '#7fada0' }, grid: { color: 'rgba(255,255,255,0.06)' } },
        y: { ticks: { color: '#7fada0' }, grid: { color: 'rgba(255,255,255,0.06)' },
          min: -4, max: 4,
          title: { display: true, text: 'Z-score', color: '#7fada0' }
        }
      }
    }
  });
}

/* ══════════════════════ INIT ══════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  const page = document.body.dataset.page;

  if (page === 'dashboard') {
    loadDashboard().then(bindChildForm).catch(err => {
      const msg = document.getElementById('global-msg');
      if (msg) { msg.className = 'message error'; msg.textContent = err.message; }
    });
  }

  if (document.getElementById('assessment-form')) {
    bindAssessmentWizard().catch(err => {
      const msg = document.getElementById('assess-msg');
      if (msg) { msg.className = 'message error'; msg.textContent = err.message; }
    });
  }

  if (document.getElementById('result-view') || document.getElementById('history-view')) {
    loadResult().catch(err => {
      const msg = document.getElementById('global-msg');
      if (msg) { msg.className = 'message error'; msg.textContent = err.message; }
    });
  }
});
