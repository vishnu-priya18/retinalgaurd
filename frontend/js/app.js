let currentLanguage = 'en';
let selectedFile = null;
let currentScreeningResult = null;
let currentViewerMode = 'annotated';

document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  loadDashboardStats();
});

function setupEventListeners() {
  document.getElementById('lang-selector').addEventListener('change', (e) => {
    currentLanguage = e.target.value;
    updateLanguageTexts();
  });

  const dropzone = document.getElementById('dropzone');
  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.style.backgroundColor = '#dbeafe';
  });
  dropzone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    dropzone.style.backgroundColor = '#eff6ff';
  });
  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.style.backgroundColor = '#eff6ff';
    if (e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  });
}

function updateLanguageTexts() {
  const dict = UI_TRANSLATIONS[currentLanguage] || UI_TRANSLATIONS['en'];
  document.getElementById('txt-app-title').innerText = dict.app_title;
  document.getElementById('txt-app-subtitle').innerText = dict.app_subtitle;
  document.getElementById('txt-nav-dashboard').innerText = dict.nav_dashboard;
  document.getElementById('txt-nav-screening').innerText = dict.nav_new_screening;
  document.getElementById('txt-nav-history').innerText = dict.nav_history;
  document.getElementById('txt-disclaimer').innerText = dict.disclaimer;

  document.getElementById('lbl-step1').innerText = dict.step1;
  document.getElementById('lbl-step2').innerText = dict.step2;
  document.getElementById('lbl-step3').innerText = dict.step3;
  document.getElementById('lbl-step4').innerText = dict.step4;
  document.getElementById('lbl-step5').innerText = dict.step5;

  document.getElementById('btn-to-step2').innerText = dict.btn_next;
  document.getElementById('btn-run-analysis').innerText = dict.btn_analyze;
}

function switchView(viewName) {
  document.getElementById('view-dashboard').style.display = 'none';
  document.getElementById('view-new-screening').style.display = 'none';
  document.getElementById('view-history').style.display = 'none';
  document.getElementById('view-validation').style.display = 'none';

  document.getElementById('tab-dashboard').classList.remove('active');
  document.getElementById('tab-screening').classList.remove('active');
  document.getElementById('tab-history').classList.remove('active');
  document.getElementById('tab-validation').classList.remove('active');

  if (viewName === 'dashboard') {
    document.getElementById('view-dashboard').style.display = 'block';
    document.getElementById('tab-dashboard').classList.add('active');
    loadDashboardStats();
  } else if (viewName === 'new-screening') {
    document.getElementById('view-new-screening').style.display = 'block';
    document.getElementById('tab-screening').classList.add('active');
  } else if (viewName === 'history') {
    document.getElementById('view-history').style.display = 'block';
    document.getElementById('tab-history').classList.add('active');
    loadHistory();
  } else if (viewName === 'validation') {
    document.getElementById('view-validation').style.display = 'block';
    document.getElementById('tab-validation').classList.add('active');
  }
}

function goToStep(stepNum) {
  if (stepNum === 2) {
    document.getElementById('wizard-step1').style.display = 'none';
    document.getElementById('wizard-step2').style.display = 'block';
    document.getElementById('lbl-step2').style.color = '#2563eb';
  }
}

function handleFileSelect(event) {
  if (event.target.files.length > 0) {
    handleFile(event.target.files[0]);
  }
}

function handleFile(file) {
  if (!file.type.startsWith('image/')) {
    alert('Please upload a valid image file (JPG or PNG).');
    return;
  }

  selectedFile = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    document.getElementById('upload-preview-img').src = e.target.result;
    document.getElementById('upload-file-info').innerText = `${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
    document.getElementById('upload-preview-container').style.display = 'block';
    document.getElementById('btn-run-analysis').style.display = 'inline-flex';
  };
  reader.readAsDataURL(file);
}

async function runFullPipeline() {
  if (!selectedFile) {
    alert('Please upload a retinal image first.');
    return;
  }

  document.getElementById('wizard-step2').style.display = 'none';
  document.getElementById('wizard-step3-4').style.display = 'block';
  document.getElementById('loading-spinner').style.display = 'block';
  document.getElementById('quality-fail-container').style.display = 'none';
  document.getElementById('analysis-success-container').style.display = 'none';

  const formData = new FormData();
  formData.append('file', selectedFile);
  formData.append('patient_id', document.getElementById('input-patient-id').value || 'ANONYMOUS');
  formData.append('patient_name', document.getElementById('input-patient-name').value || 'N/A');
  formData.append('age', document.getElementById('input-age').value || '');
  formData.append('sex', document.getElementById('input-sex').value);
  formData.append('hba1c', document.getElementById('input-hba1c').value || '');
  formData.append('diabetes_duration_years', document.getElementById('input-duration').value || '');
  formData.append('has_hypertension', document.getElementById('input-hypertension').checked);
  formData.append('lang', currentLanguage);

  try {
    const response = await fetch('/api/v1/screen', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Server returned status ${response.status}`);
    }

    const data = await response.json();
    currentScreeningResult = data;
    document.getElementById('loading-spinner').style.display = 'none';

    if (data.quality_assessment.quality_status === 'FAIL') {
      renderQualityFail(data);
    } else {
      renderAnalysisSuccess(data);
    }
  } catch (err) {
    document.getElementById('loading-spinner').style.display = 'none';
    alert(`Error processing image: ${err.message}`);
  }
}

function renderQualityFail(data) {
  document.getElementById('quality-fail-container').style.display = 'block';
  const listEl = document.getElementById('fail-reasons-list');
  listEl.innerHTML = '';
  data.quality_assessment.failure_reasons.forEach((reason) => {
    const li = document.createElement('li');
    li.innerText = reason;
    listEl.appendChild(li);
  });

  document.getElementById('fail-guidance-text').innerText = data.quality_assessment.recapture_guidance;
}

function renderAnalysisSuccess(data) {
  document.getElementById('analysis-success-container').style.display = 'block';
  document.getElementById('val-qscore').innerText = data.quality_assessment.overall_score;

  // Reliability Badge
  const relBadge = document.getElementById('badge-reliability');
  const relStatus = data.dr_analysis ? (data.dr_analysis.reliability_status || 'Reliable') : 'Uncertain';
  relBadge.innerText = `Reliability: ${relStatus}`;
  if (relStatus === 'Reliable') {
    relBadge.className = 'badge badge-pass';
  } else if (relStatus === 'Review Recommended') {
    relBadge.className = 'badge badge-warning';
  } else {
    relBadge.className = 'badge badge-fail';
  }

  setViewerMode('annotated');

  // Render DR Severity & Confidence
  const dr = data.dr_analysis;
  if (dr && dr.predicted_class_id !== -1) {
    document.getElementById('res-icdr-grade').innerText = `${dr.icdr_grade} - ${dr.predicted_class_name}`;
    document.getElementById('res-confidence').innerText = `${dr.confidence_score}%`;
    document.getElementById('res-uncertainty').innerText = dr.uncertainty_index;
  } else {
    document.getElementById('res-icdr-grade').innerText = 'AI classification unavailable — model validation required';
    document.getElementById('res-confidence').innerText = '0%';
    document.getElementById('res-uncertainty').innerText = '1.0';
  }

  // Render "Why This Severity?" Rationale
  document.getElementById('res-why-text').innerText = data.why_this_severity || 'Classified based on feature activation pattern.';

  // Render Lesion Findings List & Bounding Boxes
  renderLesionsList(data.lesions_analysis);

  // Render Triage Recommendation
  const tr = data.triage;
  document.getElementById('res-urgency').innerText = tr.urgency_level;
  document.getElementById('res-timeline').innerText = tr.recommended_timeline;
  document.getElementById('res-summary').innerText = tr.clinical_summary;

  // Populate Debug Panel Fields
  if (dr && dr.debug_info) {
    const dbg = dr.debug_info;
    document.getElementById('dbg-md5').innerText = dbg.md5_hash || '-';
    document.getElementById('dbg-shape').innerText = JSON.stringify(dbg.input_tensor_shape) || '-';
    document.getElementById('dbg-model').innerText = dbg.model_name || '-';
    document.getElementById('dbg-weights').innerText = dbg.model_loaded ? `${dbg.weights_path} (LOADED)` : 'MISSING / UNVALIDATED';
    document.getElementById('dbg-latency').innerText = `${dbg.inference_time_ms} ms`;
    document.getElementById('dbg-logits').innerText = JSON.stringify(dbg.raw_logits);
    document.getElementById('dbg-probs').innerText = JSON.stringify(dr.class_probabilities, null, 2);
  }
}

function setViewerMode(mode) {
  currentViewerMode = mode;
  document.getElementById('vbtn-annotated').classList.remove('active');
  document.getElementById('vbtn-heatmap').classList.remove('active');
  document.getElementById('vbtn-original').classList.remove('active');

  const opacityBox = document.getElementById('opacity-control-box');
  const imgOverlay = document.getElementById('img-canvas-overlay');
  const imgBase = document.getElementById('img-canvas-base');

  if (!currentScreeningResult) return;
  const exp = currentScreeningResult.explainability;
  const les = currentScreeningResult.lesions_analysis;

  if (mode === 'annotated') {
    document.getElementById('vbtn-annotated').classList.add('active');
    opacityBox.style.display = 'none';
    imgOverlay.style.display = 'none';
    imgBase.src = les.annotated_image_b64 || exp.original_image_b64;
  } else if (mode === 'heatmap') {
    document.getElementById('vbtn-heatmap').classList.add('active');
    opacityBox.style.display = 'block';
    imgOverlay.style.display = 'block';
    imgBase.src = exp.original_image_b64;
    imgOverlay.src = exp.heatmap_only_b64;
  } else if (mode === 'original') {
    document.getElementById('vbtn-original').classList.add('active');
    opacityBox.style.display = 'none';
    imgOverlay.style.display = 'none';
    imgBase.src = exp.original_image_b64;
  }
}

function renderLesionsList(lesionsAnalysis) {
  const container = document.getElementById('lesion-findings-list');
  container.innerHTML = '';

  if (!lesionsAnalysis || !lesionsAnalysis.lesions || lesionsAnalysis.lesions.length === 0) {
    document.getElementById('txt-lesion-count').innerText = '0';
    container.innerHTML = `<div style="font-size: 0.8rem; color: #94a3b8; font-style: italic;">No specific focal lesions detected. Microvascular structure appears intact.</div>`;
    return;
  }

  const lesions = lesionsAnalysis.lesions;
  document.getElementById('txt-lesion-count').innerText = lesions.length.toString();

  lesions.forEach((l) => {
    const item = document.createElement('div');
    item.className = 'lesion-item';
    item.onclick = () => inspectLesion(l);

    let badgeColor = l.type === 'Hard Exudate' ? '#f59e0b' : (l.type === 'Cotton-Wool Spot' ? '#06b6d4' : '#dc2626');
    item.innerHTML = `
      <div>
        <strong style="color: ${badgeColor};">${l.id} (${l.type})</strong>
        <div style="font-size: 0.75rem; color: #64748b;">Region: ${l.quadrant} | Box: [${l.bbox.join(', ')}]</div>
      </div>
      <span style="font-size: 0.75rem; font-weight: 600; color: #475569;">${Math.round(l.confidence * 100)}% Conf</span>
    `;
    container.appendChild(item);
  });
}

function inspectLesion(lesion) {
  alert(`FINDING DETECTED: ${lesion.type} (${lesion.id})\n` +
        `----------------------------------------\n` +
        `Anatomical Region: ${lesion.quadrant}\n` +
        `Bounding Box [X, Y, W, H]: [${lesion.bbox.join(', ')}]\n` +
        `Model Confidence: ${Math.round(lesion.confidence * 100)}%\n` +
        `Clinical Context: ${lesion.description}\n\n` +
        `Note: This detected region contributed to the AI screening evaluation.`);
}

function updateOpacity(val) {
  document.getElementById('val-opacity').innerText = `${val}%`;
  document.getElementById('img-canvas-overlay').style.opacity = (val / 100).toString();
}

function resetWizard() {
  selectedFile = null;
  currentScreeningResult = null;
  document.getElementById('file-input').value = '';
  document.getElementById('upload-preview-container').style.display = 'none';
  document.getElementById('btn-run-analysis').style.display = 'none';

  document.getElementById('wizard-step3-4').style.display = 'none';
  document.getElementById('wizard-step2').style.display = 'none';
  document.getElementById('wizard-step1').style.display = 'block';
  document.getElementById('lbl-step2').style.color = '#64748b';
}

function downloadCurrentPDF() {
  if (currentScreeningResult && currentScreeningResult.screening_id) {
    window.open(`/api/v1/report/pdf/${currentScreeningResult.screening_id}`, '_blank');
  }
}

async function loadDashboardStats() {
  try {
    const res = await fetch('/api/v1/dashboard');
    if (res.ok) {
      const data = await res.json();
      document.getElementById('stat-total').innerText = data.total_screenings;
      document.getElementById('stat-grade0').innerText = data.grade0_count;
      document.getElementById('stat-grade1').innerText = data.grade1_count;
      document.getElementById('stat-grade2').innerText = data.grade2_count;
      document.getElementById('stat-grade3').innerText = data.grade3_count;
      document.getElementById('stat-grade4').innerText = data.grade4_count;
      document.getElementById('stat-rechecks').innerText = data.recheck_cases;
    }
  } catch (e) {
    console.error('Could not load dashboard stats:', e);
  }

  // Load Recent Dashboard Table
  try {
    const res = await fetch('/api/v1/history');
    if (res.ok) {
      const rows = await res.json();
      const tbody = document.getElementById('dashboard-recent-tbody');
      tbody.innerHTML = '';
      if (rows.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #94a3b8;">No stored screening records found. Click "+ Start New Screening" to run an analysis.</td></tr>`;
        return;
      }
      rows.slice(0, 5).forEach((r) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><b>${r.screening_id}</b></td>
          <td>${r.patient_id}</td>
          <td>${r.created_at}</td>
          <td><span class="badge ${r.quality_status==='PASS'?'badge-pass':'badge-fail'}">${r.quality_status}</span></td>
          <td><b>${r.icdr_grade}</b> (${r.predicted_class_name})</td>
          <td>${r.urgency_level}</td>
          <td><a href="/api/v1/report/pdf/${r.screening_id}" target="_blank" class="btn" style="padding: 0.2rem 0.5rem; font-size: 0.75rem;">📄 PDF</a></td>
        `;
        tbody.appendChild(tr);
      });
    }
  } catch (e) {
    console.error('Could not load recent table:', e);
  }
}

async function loadHistory() {
  const search = document.getElementById('history-search').value;
  const filter = document.getElementById('history-filter').value;
  try {
    const res = await fetch(`/api/v1/history?search=${encodeURIComponent(search)}&filter=${encodeURIComponent(filter)}`);
    if (res.ok) {
      const rows = await res.json();
      const tbody = document.getElementById('history-tbody');
      tbody.innerHTML = '';
      if (rows.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #94a3b8;">No matching records found.</td></tr>`;
        return;
      }
      rows.forEach((r) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><b>${r.screening_id}</b></td>
          <td>${r.patient_id}</td>
          <td>${r.created_at}</td>
          <td><span class="badge ${r.quality_status==='PASS'?'badge-pass':'badge-fail'}">${r.quality_status}</span></td>
          <td><b>${r.icdr_grade}</b> (${r.predicted_class_name})</td>
          <td>${r.urgency_level}</td>
          <td><a href="/api/v1/report/pdf/${r.screening_id}" target="_blank" class="btn" style="padding: 0.2rem 0.5rem; font-size: 0.75rem;">📄 PDF</a></td>
        `;
        tbody.appendChild(tr);
      });
    }
  } catch (e) {
    console.error('Could not load history table:', e);
  }
}
