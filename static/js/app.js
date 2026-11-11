/* ==========================================
   MEDI-MIND CDSS - MAIN FRONTEND APPLICATION
   ========================================== */

let allSymptoms = [];
let selectedSymptomCodes = new Set(['SYM_043', 'SYM_044', 'SYM_045']); // Default demo: Nose Bleeding, Nasal Congestion, Sinus Pressure
let currentPatientPage = 1;
let lastDiagnosisResult = null;
let currentSpecialists = [];

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    loadSymptoms();
    loadDbSchema();
    loadPatientRecords(1);
    loadDataMiningVisualizations();

    // Default pre-select symptom cards
    setTimeout(() => {
        updateSymptomCardSelections();
        runSimForecast();
    }, 400);
});

// Tab Navigation
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.getAttribute('data-tab');
            switchTab(target);
        });
    });
}

function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

    const btn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
    const pane = document.getElementById(tabId);

    if (btn) btn.classList.add('active');
    if (pane) pane.classList.add('active');

    // If switching to database tab, refresh patient list to see new inserts
    if (tabId === 'tab-database') {
        loadPatientRecords(1);
        loadDbSchema();
    }

    // If switching to simulator tab, run forecast recalculation
    if (tabId === 'tab-simulator') {
        runSimForecast();
    }
}

// Toast Notification
function showToast(message, isSuccess = true) {
    const toast = document.getElementById('toast-notification');
    const msgEl = document.getElementById('toast-message');
    if (!toast || !msgEl) return;

    msgEl.innerHTML = message;
    toast.classList.remove('hidden');

    setTimeout(() => {
        toast.classList.add('hidden');
    }, 4500);
}

// Load Symptoms List
async function loadSymptoms() {
    try {
        const res = await fetch('/api/symptoms');
        const data = await res.json();
        if (data.status === 'success') {
            allSymptoms = data.symptoms;
            renderSymptomsGrid(allSymptoms);
        }
    } catch (err) {
        console.error("Failed to load symptoms:", err);
    }
}

function renderSymptomsGrid(symptoms) {
    const grid = document.getElementById('symptoms-selector-grid');
    if (!grid) return;

    if (symptoms.length === 0) {
        grid.innerHTML = '<div style="color: var(--text-dim); padding: 12px; grid-column: 1/-1;">No matching symptoms found.</div>';
        return;
    }

    grid.innerHTML = symptoms.map(s => `
        <div class="symptom-card ${selectedSymptomCodes.has(s.code) ? 'selected' : ''}" 
             data-code="${s.code}" onclick="toggleSymptom('${s.code}')">
            <span>${s.name}</span>
            <input type="checkbox" ${selectedSymptomCodes.has(s.code) ? 'checked' : ''} onclick="event.stopPropagation(); toggleSymptom('${s.code}')">
        </div>
    `).join('');
}

function filterSymptomCategory(cat) {
    document.querySelectorAll('#symptom-category-pills .pill-btn').forEach(b => b.classList.remove('active'));
    if (event && event.target) {
        event.target.classList.add('active');
    }

    const searchVal = (document.getElementById('symptom-search-box').value || '').trim().toLowerCase();

    let filtered = allSymptoms;
    if (cat !== 'all') {
        filtered = filtered.filter(s => s.category.toLowerCase().includes(cat.toLowerCase()));
    }
    if (searchVal) {
        filtered = filtered.filter(s => s.name.toLowerCase().includes(searchVal));
    }

    renderSymptomsGrid(filtered);
}

function searchSymptomsInline() {
    const searchVal = (document.getElementById('symptom-search-box').value || '').trim().toLowerCase();
    const activePill = document.querySelector('#symptom-category-pills .pill-btn.active');
    const activeCategory = activePill ? activePill.innerText : 'All';

    let filtered = allSymptoms;
    if (!activeCategory.includes('All')) {
        const catKey = activeCategory.split(' ')[0];
        filtered = filtered.filter(s => s.category.toLowerCase().includes(catKey.toLowerCase()));
    }
    if (searchVal) {
        filtered = filtered.filter(s => s.name.toLowerCase().includes(searchVal));
    }

    renderSymptomsGrid(filtered);
}

function toggleSymptom(code) {
    if (selectedSymptomCodes.has(code)) {
        selectedSymptomCodes.delete(code);
    } else {
        selectedSymptomCodes.add(code);
    }
    updateSymptomCardSelections();
}

function clearSelectedSymptoms() {
    selectedSymptomCodes.clear();
    updateSymptomCardSelections();
}

function updateSymptomCardSelections() {
    document.querySelectorAll('.symptom-card').forEach(card => {
        const code = card.getAttribute('data-code');
        const isSel = selectedSymptomCodes.has(code);
        const chk = card.querySelector('input');
        if (isSel) {
            card.classList.add('selected');
            if (chk) chk.checked = true;
        } else {
            card.classList.remove('selected');
            if (chk) chk.checked = false;
        }
    });
}

// Quick Preset Cases
function loadCasePreset(type) {
    selectedSymptomCodes.clear();

    if (type === 'epistaxis') {
        document.getElementById('patient-full-name').value = "Rahul Sharma";
        document.getElementById('vital-age').value = 38;
        document.getElementById('vital-gender').value = "Male";
        document.getElementById('vital-bmi').value = 25.4;
        document.getElementById('vital-bp-sys').value = 138;
        document.getElementById('vital-bp-dia').value = 88;
        document.getElementById('vital-glucose').value = 108;
        selectedSymptomCodes.add('SYM_043'); // Nose Bleeding
        selectedSymptomCodes.add('SYM_044'); // Nasal Congestion
        selectedSymptomCodes.add('SYM_045'); // Facial Pain / Sinus Pressure
        selectedSymptomCodes.add('SYM_041'); // Mild Fever
    } else if (type === 'cold_fever') {
        document.getElementById('patient-full-name').value = "Pooja Verma";
        document.getElementById('vital-age').value = 27;
        document.getElementById('vital-gender').value = "Female";
        document.getElementById('vital-bmi').value = 22.1;
        document.getElementById('vital-bp-sys').value = 118;
        document.getElementById('vital-bp-dia').value = 76;
        document.getElementById('vital-glucose').value = 92;
        selectedSymptomCodes.add('SYM_041'); // Mild / Basic Fever
        selectedSymptomCodes.add('SYM_026'); // Runny Nose
        selectedSymptomCodes.add('SYM_027'); // Sneezing
        selectedSymptomCodes.add('SYM_025'); // Sore Throat
    } else if (type === 'cardiac') {
        document.getElementById('patient-full-name').value = "Amitabh Sen";
        document.getElementById('vital-age').value = 61;
        document.getElementById('vital-gender').value = "Male";
        document.getElementById('vital-bmi').value = 29.8;
        document.getElementById('vital-bp-sys').value = 155;
        document.getElementById('vital-bp-dia').value = 95;
        document.getElementById('vital-glucose').value = 142;
        selectedSymptomCodes.add('SYM_001'); // Chest Pain
        selectedSymptomCodes.add('SYM_002'); // SOB
        selectedSymptomCodes.add('SYM_021'); // Palpitations
        selectedSymptomCodes.add('SYM_048'); // Chest tightness
    } else if (type === 'gastro') {
        document.getElementById('patient-full-name').value = "Neha Kapoor";
        document.getElementById('vital-age').value = 32;
        document.getElementById('vital-gender').value = "Female";
        document.getElementById('vital-bmi').value = 23.5;
        document.getElementById('vital-bp-sys').value = 110;
        document.getElementById('vital-bp-dia').value = 72;
        document.getElementById('vital-glucose').value = 88;
        selectedSymptomCodes.add('SYM_049'); // Vomiting
        selectedSymptomCodes.add('SYM_050'); // Watery Diarrhea
        selectedSymptomCodes.add('SYM_028'); // Abdominal Pain
        selectedSymptomCodes.add('SYM_020'); // Nausea
    }

    updateSymptomCardSelections();
    showToast(`Loaded preset case: <strong>${type.toUpperCase()}</strong>. Click Execute CDSS to evaluate.`);
}

// Execute CDSS Diagnosis
async function runDiagnosis() {
    if (selectedSymptomCodes.size === 0) {
        alert("Please select at least one symptom from the list.");
        return;
    }

    const patientName = (document.getElementById('patient-full-name').value || '').trim() || "Anonymous Patient";
    const age = parseInt(document.getElementById('vital-age').value) || 45;
    const gender = document.getElementById('vital-gender').value;
    const bmi = parseFloat(document.getElementById('vital-bmi').value) || 24.5;
    const bpSys = parseInt(document.getElementById('vital-bp-sys').value) || 120;
    const bpDia = parseInt(document.getElementById('vital-bp-dia').value) || 80;
    const glucose = parseFloat(document.getElementById('vital-glucose').value) || 100;
    const cholesterol = parseFloat(document.getElementById('vital-cholesterol').value) || 185;
    const smoking = document.getElementById('vital-smoking').value;
    const activity = document.getElementById('vital-activity').value;

    // Collect Medical History
    const history = [];
    document.querySelectorAll('#history-tags-container input:checked').forEach(chk => {
        history.push(chk.value);
    });

    const payload = {
        patient_name: patientName,
        symptoms: Array.from(selectedSymptomCodes),
        vitals: {
            age: age,
            gender: gender,
            bmi: bmi,
            bp_sys: bpSys,
            bp_dia: bpDia,
            glucose: glucose,
            cholesterol: cholesterol,
            smoking: smoking,
            activity: activity
        },
        medical_history: history
    };

    try {
        const res = await fetch('/api/cdss/diagnose', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (data.status === 'success') {
            lastDiagnosisResult = data.result;
            currentSpecialists = data.result.specialists || [];
            displayDiagnosisResult(data.result, payload, data.saved_patient_id);
            showToast(`Patient <strong>${patientName}</strong> evaluated & saved to SQLite Database (Record #${data.saved_patient_id})!`);
        } else {
            alert("Error: " + data.message);
        }
    } catch (err) {
        console.error("Diagnosis request failed:", err);
        alert("Diagnosis request failed. Ensure the Python web server is running.");
    }
}

function displayDiagnosisResult(result, payload, savedPatientId) {
    document.getElementById('cdss-welcome-state').classList.add('hidden');
    document.getElementById('cdss-results-container').classList.remove('hidden');

    // Stored DB banner
    const dbBanner = document.getElementById('db-saved-banner');
    const dbText = document.getElementById('db-saved-banner-text');
    if (savedPatientId) {
        dbText.innerHTML = `<strong>Patient Record Registered:</strong> Stored in SQLite Database as <strong>Patient #${savedPatientId} (${payload.patient_name})</strong> with diagnosed condition <em>${result.diagnosis.primary_disease}</em>.`;
    }

    // Triage Banner
    const triage = result.triage;
    const banner = document.getElementById('triage-banner');
    const badge = document.getElementById('triage-badge-text');
    badge.innerText = triage.badge;
    badge.style.backgroundColor = triage.color;
    document.getElementById('triage-title').innerText = `${triage.level} Assessment`;
    document.getElementById('triage-message').innerText = triage.message;
    banner.style.borderColor = triage.color;

    // Red Flags
    const redFlagsBox = document.getElementById('red-flags-box');
    const redFlagsList = document.getElementById('red-flags-list');
    if (triage.red_flags && triage.red_flags.length > 0) {
        redFlagsBox.classList.remove('hidden');
        redFlagsList.innerHTML = triage.red_flags.map(f => `<li>${f}</li>`).join('');
    } else {
        redFlagsBox.classList.add('hidden');
    }

    // Primary Diagnosis Card
    const diag = result.diagnosis;
    document.getElementById('diag-category').innerText = diag.category;
    document.getElementById('diag-icd').innerText = `ICD-10: ${diag.icd10_code}`;
    document.getElementById('diag-disease-name').innerText = diag.primary_disease;
    document.getElementById('diag-description').innerText = diag.description;
    document.getElementById('diag-confidence-val').innerText = `${diag.confidence}%`;
    document.getElementById('diag-confidence-bar').style.width = `${Math.min(diag.confidence, 100)}%`;

    // Differential Table
    const diffTbody = document.getElementById('differential-tbody');
    diffTbody.innerHTML = diag.differential.map((item, idx) => `
        <tr>
            <td><strong>#${idx + 1}</strong></td>
            <td>${item.disease}</td>
            <td><strong style="color: var(--primary-cyan);">${item.probability}%</strong></td>
            <td>
                <div class="progress-bar-track" style="width: 120px;">
                    <div class="progress-bar-fill" style="width: ${item.probability}%;"></div>
                </div>
            </td>
        </tr>
    `).join('');

    // Recommended Diagnostic Tests
    const testsGrid = document.getElementById('recommended-tests-grid');
    testsGrid.innerHTML = result.diagnostic_tests.map(t => `
        <div class="test-card">
            <h5><i class="fa-solid fa-flask"></i> ${t.name}</h5>
            <p>${t.purpose}</p>
            <span class="badge-line" style="margin-top: 6px; display: inline-block;">${t.urgency} Urgency</span>
        </div>
    `).join('');

    // Populate Tab 2 Medications & Prevention
    renderMedications(result.medications);
    renderPreventiveMeasures(result.preventive_measures);
    renderSpecialists(result.specialists);

    // Populate Tab 5 Medical Report Sheet
    renderPrintableReport(result, payload, savedPatientId);
}

function renderMedications(meds) {
    const container = document.getElementById('medications-container');
    if (!meds || meds.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No specific medications found for this condition.</p></div>';
        return;
    }

    container.innerHTML = meds.map(m => `
        <div class="med-card">
            <div class="med-header">
                <div>
                    <h4><i class="fa-solid fa-capsule"></i> ${m.name}</h4>
                    <span style="font-size: 0.76rem; color: var(--primary-cyan);">${m.category}</span>
                </div>
                <span class="badge-line">${m.line_of_treatment}</span>
            </div>

            <div style="font-size: 0.82rem; color: #a5f3fc; margin: 4px 0;">
                <i class="fa-solid fa-circle-info"></i> <strong>Indication:</strong> ${m.indication || 'Clinical therapeutic use'}
            </div>

            <div class="med-dosage">
                <i class="fa-solid fa-clock"></i> <strong>Standard Dosage:</strong> ${m.standard_dosage}
            </div>

            <div style="font-size: 0.8rem; color: var(--text-muted); margin: 3px 0;">
                <i class="fa-solid fa-utensils"></i> <strong>Directions:</strong> ${m.timing_instructions || 'Take with water.'}
            </div>

            <p style="font-size: 0.78rem; color: var(--text-dim); margin-top: 4px;">
                <i class="fa-solid fa-chart-line"></i> Efficacy Score: ${m.efficacy_score} | Potential Side Effects: ${m.side_effects || 'None common'}
            </p>
            
            ${m.safety_alert ? `
                <div class="safety-alert-badge">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                    <span>${m.safety_alert}</span>
                </div>
            ` : ''}
        </div>
    `).join('');
}

function renderPreventiveMeasures(measures) {
    const container = document.getElementById('preventive-container');
    if (!measures || measures.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No preventive protocols available.</p></div>';
        return;
    }

    container.innerHTML = measures.map(p => `
        <div class="test-card" style="border-left: 4px solid var(--primary-teal); margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h5 style="color: #fff;"><i class="fa-solid fa-shield"></i> ${p.type} Measure</h5>
                <span class="badge-tag" style="background: rgba(255, 255, 255, 0.1);">${p.priority} Priority</span>
            </div>
            <p style="margin-top: 6px; color: var(--text-muted);">${p.description}</p>
        </div>
    `).join('');
}

function renderSpecialists(specialists) {
    const grid = document.getElementById('specialists-grid');
    if (!specialists || specialists.length === 0) return;

    grid.innerHTML = specialists.map((d, idx) => `
        <div class="doctor-card">
            <div class="doctor-card-top">
                <div class="doctor-avatar">
                    <i class="fa-solid fa-user-doctor"></i>
                </div>
                <div class="doctor-card-meta">
                    <h4>${d.name}</h4>
                    <div class="doctor-qual">${d.qualifications || 'MD / Specialist'}</div>
                    <div class="doctor-hospital">${d.specialty} | ${d.hospital}</div>
                    
                    <div class="google-rating-line">
                        <span class="google-stars"><i class="fa-solid fa-star"></i> ${d.rating}</span>
                        <span class="google-reviews">(${d.reviews_count || 320} Google Reviews)</span>
                    </div>
                </div>
            </div>

            <div class="doctor-card-details">
                <div><i class="fa-solid fa-location-dot"></i> ${d.location}</div>
                <div><i class="fa-solid fa-clock"></i> ${d.timings || 'Mon - Sat: 10am - 4pm'}</div>
                <div><i class="fa-solid fa-tag"></i> Fee: <strong>${d.consultation_fee || '$65 / ₹1,000'}</strong></div>
            </div>

            <div class="doctor-card-actions">
                <button class="btn-doc-details" onclick="openDoctorModal(${idx})">
                    <i class="fa-solid fa-circle-info"></i> Check Doctor Details
                </button>
                <a class="btn-doc-google" href="${d.google_query_url || ('https://www.google.com/search?q=' + encodeURIComponent(d.name + ' ' + d.specialty))}" target="_blank" rel="noopener noreferrer">
                    <i class="fa-brands fa-google"></i> Google
                </a>
            </div>
        </div>
    `).join('');
}

// Doctor Details Modal
function openDoctorModal(index) {
    const doc = currentSpecialists[index];
    if (!doc) return;

    const modalBody = document.getElementById('doctor-modal-body');
    const modal = document.getElementById('doctor-modal');

    modalBody.innerHTML = `
        <div class="modal-profile-header">
            <div class="modal-avatar"><i class="fa-solid fa-user-doctor"></i></div>
            <div class="modal-doc-info">
                <h3>${doc.name}</h3>
                <div style="color: var(--primary-cyan); font-weight: 600;">${doc.qualifications}</div>
                <div style="color: var(--text-muted); font-size: 0.88rem;">${doc.specialty} Specialist | ${doc.hospital}</div>
                <div class="google-rating-line" style="margin-top: 6px;">
                    <span class="google-stars"><i class="fa-solid fa-star"></i> ${doc.rating} Rating</span>
                    <span class="google-reviews">(${doc.reviews_count} Verified Google Patient Reviews)</span>
                </div>
            </div>
        </div>

        <div class="modal-bio-text">
            <strong>About Specialist:</strong><br>
            ${doc.bio || 'Experienced clinical specialist committed to evidence-based healthcare delivery and patient recovery.'}
        </div>

        <div class="modal-details-grid">
            <div class="modal-detail-item">
                <span>Clinical Experience</span>
                <strong>${doc.experience}</strong>
            </div>
            <div class="modal-detail-item">
                <span>Consultation Fee</span>
                <strong>${doc.consultation_fee}</strong>
            </div>
            <div class="modal-detail-item">
                <span>Clinic / Hospital Location</span>
                <strong>${doc.location}</strong>
            </div>
            <div class="modal-detail-item">
                <span>Direct Contact Phone</span>
                <strong>${doc.contact}</strong>
            </div>
            <div class="modal-detail-item" style="grid-column: 1/-1;">
                <span>Available Consultation Hours</span>
                <strong>${doc.timings}</strong>
            </div>
        </div>

        <div class="modal-actions">
            <a class="btn-action-primary" style="text-decoration: none; flex: 1;" href="${doc.google_query_url}" target="_blank" rel="noopener noreferrer">
                <i class="fa-brands fa-google"></i> Open Doctor Profile on Google
            </a>
            <button class="btn-secondary" style="flex: 1;" onclick="simulateBooking('${doc.name.replace(/'/g, "\\'")}')">
                <i class="fa-solid fa-calendar-check"></i> Book Consultation
            </button>
        </div>
    `;

    modal.classList.remove('hidden');
}

function closeDoctorModal(e) {
    const modal = document.getElementById('doctor-modal');
    if (modal) modal.classList.add('hidden');
}

function simulateBooking(doctorName) {
    alert(`Appointment Simulation:\n\nYour consultation request with ${doctorName} has been queued! In a live hospital deployment, this synchronizes with the clinic appointment calendar.`);
    closeDoctorModal();
}

// Load DB Schema Cards & Patient Records
async function loadDbSchema() {
    try {
        const res = await fetch('/api/database/schema');
        const data = await res.json();
        if (data.status === 'success') {
            const container = document.getElementById('db-schema-cards');
            container.innerHTML = Object.keys(data.schema).map(t => `
                <div class="schema-card">
                    <h4>${t}</h4>
                    <div class="count">${data.schema[t].count}</div>
                    <span style="font-size: 0.72rem; color: var(--text-dim);">${data.schema[t].columns.length} Columns</span>
                </div>
            `).join('');
        }
    } catch (err) {
        console.error("Failed to load schema:", err);
    }
}

async function loadPatientRecords(page = 1) {
    currentPatientPage = page;
    const search = document.getElementById('patient-search-input') ? document.getElementById('patient-search-input').value : '';
    try {
        const res = await fetch(`/api/patients?page=${page}&limit=12&search=${encodeURIComponent(search)}`);
        const data = await res.json();
        if (data.status === 'success') {
            renderPatientTable(data.patients);
            document.getElementById('page-indicator').innerText = `Page ${data.page} of ${Math.max(1, Math.ceil(data.total / data.limit))}`;
        }
    } catch (err) {
        console.error("Failed to load patients:", err);
    }
}

function renderPatientTable(patients) {
    const tbody = document.getElementById('patients-tbody');
    if (!tbody) return;

    if (!patients || patients.length === 0) {
        tbody.innerHTML = '<tr><td colspan="11" style="text-align:center; padding: 20px;">No patient records found.</td></tr>';
        return;
    }

    tbody.innerHTML = patients.map(p => `
        <tr>
            <td>#${p.id}</td>
            <td><strong>${p.name}</strong></td>
            <td>${p.age} yrs / ${p.gender}</td>
            <td>${p.bmi}</td>
            <td>${p.blood_pressure_sys}/${p.blood_pressure_dia}</td>
            <td>${p.glucose_level} mg/dL</td>
            <td>${p.cholesterol} mg/dL</td>
            <td>${p.smoking_status} / ${p.activity_level}</td>
            <td>
                <span class="badge-tag" style="background: ${p.risk_category === 'High Risk' ? '#ef4444' : p.risk_category === 'Moderate Risk' ? '#f59e0b' : '#10b981'};">
                    ${p.risk_category}
                </span>
            </td>
            <td><strong style="color: var(--primary-cyan);">${p.diagnosed_condition || 'Under CDSS'}</strong></td>
            <td>
                <button class="btn-link" onclick="loadPatientIntoCdss(${p.id}, '${p.name.replace(/'/g, "\\'")}', ${p.age}, '${p.gender}', ${p.bmi}, ${p.blood_pressure_sys}, ${p.blood_pressure_dia}, ${p.glucose_level})">
                    Load into CDSS
                </button>
            </td>
        </tr>
    `).join('');
}

function loadPatientIntoCdss(id, name, age, gender, bmi, bpSys, bpDia, glucose) {
    document.getElementById('patient-full-name').value = name;
    document.getElementById('vital-age').value = age;
    document.getElementById('vital-gender').value = gender;
    document.getElementById('vital-bmi').value = bmi;
    document.getElementById('vital-bp-sys').value = bpSys;
    document.getElementById('vital-bp-dia').value = bpDia;
    document.getElementById('vital-glucose').value = glucose;
    switchTab('tab-cdss');
    showToast(`Loaded patient #${id} (${name}) into CDSS form.`);
}

function searchPatients() {
    loadPatientRecords(1);
}

function changePatientPage(dir) {
    const newPage = currentPatientPage + dir;
    if (newPage >= 1) {
        loadPatientRecords(newPage);
    }
}

// SQL Query Sandbox
function setSqlPreset(presetNum) {
    const input = document.getElementById('sql-query-input');
    if (presetNum === 1) {
        input.value = "SELECT id, name, age, gender, diagnosed_condition, risk_category, created_at FROM patients ORDER BY id DESC LIMIT 15;";
    } else if (presetNum === 2) {
        input.value = "SELECT d.name as DiseaseName, d.category as Category, COUNT(ds.symptom_id) as SymptomCount FROM diseases d JOIN disease_symptoms ds ON d.id = ds.disease_id GROUP BY d.id;";
    } else if (presetNum === 3) {
        input.value = "SELECT name, age, bmi, blood_pressure_sys, glucose_level, diagnosed_condition FROM patients WHERE risk_category = 'High Risk' ORDER BY blood_pressure_sys DESC LIMIT 15;";
    } else if (presetNum === 4) {
        input.value = "SELECT name, specialty, hospital, rating, reviews_count, consultation_fee, location FROM doctor_specialists ORDER BY rating DESC;";
    }
}

async function runCustomSqlQuery() {
    const query = document.getElementById('sql-query-input').value;
    try {
        const res = await fetch('/api/database/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });
        const data = await res.json();
        if (data.status === 'success') {
            displaySqlResults(data.columns, data.rows);
        } else {
            alert("SQL Error: " + data.message);
        }
    } catch (err) {
        alert("Execution failed: " + err);
    }
}

function displaySqlResults(columns, rows) {
    const container = document.getElementById('sql-results-container');
    container.classList.remove('hidden');
    document.getElementById('sql-result-count').innerText = `Query Results (${rows.length} rows returned):`;

    const thead = document.getElementById('sql-thead');
    const tbody = document.getElementById('sql-tbody');

    thead.innerHTML = `<tr>${columns.map(c => `<th>${c}</th>`).join('')}</tr>`;
    tbody.innerHTML = rows.map(r => `
        <tr>${columns.map(c => `<td>${r[c]}</td>`).join('')}</tr>
    `).join('');
}

// Data Mining Visualizations
async function loadDataMiningVisualizations() {
    // 1. Apriori Rules
    try {
        const aprioriRes = await fetch('/api/mining/apriori');
        const aprioriData = await aprioriRes.json();
        if (aprioriData.status === 'success') {
            const tbody = document.getElementById('apriori-tbody');
            tbody.innerHTML = aprioriData.rules.map(r => `
                <tr>
                    <td><strong style="color: var(--primary-cyan);">${r.antecedent.join(', ')}</strong></td>
                    <td><strong style="color: var(--primary-emerald);">${r.consequent.join(', ')}</strong></td>
                    <td>${r.support}%</td>
                    <td>${r.confidence}%</td>
                    <td><span class="badge-tag">${r.lift}</span></td>
                </tr>
            `).join('');
        }
    } catch (err) {
        console.error("Apriori load failed:", err);
    }

    // 2. ML Benchmark Chart
    try {
        const benchRes = await fetch('/api/mining/benchmark');
        const benchData = await benchRes.json();
        if (benchData.status === 'success') {
            renderBenchmarkChart(benchData.benchmark);
            if (benchData.benchmark['Random Forest']) {
                document.getElementById('rf-acc-text').innerText = `${benchData.benchmark['Random Forest'].accuracy}%`;
            }
            if (benchData.benchmark['KNN']) {
                document.getElementById('knn-acc-text').innerText = `${benchData.benchmark['KNN'].accuracy}%`;
            }
        }
    } catch (err) {
        console.error("Benchmark load failed:", err);
    }

    // 3. K-Means Clusters
    try {
        const clusterRes = await fetch('/api/mining/clusters');
        const clusterData = await clusterRes.json();
        if (clusterData.status === 'success') {
            renderClusterScatterChart(clusterData.data);
            renderClusterSummaries(clusterData.data.cluster_summaries);
        }
    } catch (err) {
        console.error("Cluster load failed:", err);
    }
}

function renderClusterSummaries(summaries) {
    const container = document.getElementById('cluster-summaries-container');
    if (!summaries || !container) return;

    container.innerHTML = summaries.map(s => `
        <div class="cluster-item">
            <h4>${s.name}</h4>
            <p><strong>${s.count} Patients</strong> | Avg Age: ${s.avg_age} | Avg BMI: ${s.avg_bmi}</p>
            <p>Avg BP Sys: ${s.avg_bp_sys} mmHg | Avg Glucose: ${s.avg_glucose} mg/dL</p>
        </div>
    `).join('');
}

async function retrainModels() {
    try {
        showToast("Retraining Machine Learning models on updated parameters...");
        const res = await fetch('/api/retrain', { method: 'POST' });
        const data = await res.json();
        if (data.status === 'success') {
            renderBenchmarkChart(data.benchmark);
            showToast("Models retrained successfully! Benchmark metrics updated.");
        }
    } catch (err) {
        alert("Retrain failed: " + err);
    }
}

// Render Printable Consultation Summary Report
function renderPrintableReport(result, payload, savedPatientId) {
    document.getElementById('report-date').innerText = new Date().toISOString().split('T')[0];
    document.getElementById('rpt-patient-id').innerText = savedPatientId ? `#CDSS-P${savedPatientId}` : '#CDSS-P1001';
    document.getElementById('rpt-patient-name').innerText = payload.patient_name || 'Anonymous Patient';
    document.getElementById('rpt-patient-age-gender').innerText = `${payload.vitals.age} yrs / ${payload.vitals.gender}`;
    document.getElementById('rpt-patient-bmi').innerText = `${payload.vitals.bmi} kg/m²`;
    document.getElementById('rpt-patient-bp').innerText = `${payload.vitals.bp_sys}/${payload.vitals.bp_dia} mmHg`;
    document.getElementById('rpt-patient-glucose').innerText = `${payload.vitals.glucose} mg/dL`;
    document.getElementById('rpt-medical-history').innerText = payload.medical_history.join(', ') || 'No prior conditions noted';

    const triage = result.triage;
    const triageEl = document.getElementById('rpt-triage-level');
    triageEl.innerText = triage.badge;
    triageEl.style.color = triage.color;

    const diag = result.diagnosis;
    document.getElementById('rpt-diag-name').innerText = diag.primary_disease;
    document.getElementById('rpt-diag-icd').innerText = diag.icd10_code;
    document.getElementById('rpt-diag-conf').innerText = `${diag.confidence}%`;
    document.getElementById('rpt-diag-cat').innerText = diag.category;

    // Active Symptoms List
    const symNames = payload.symptoms.map(code => {
        const found = allSymptoms.find(s => s.code === code);
        return found ? found.name : code;
    });
    document.getElementById('rpt-symptoms-list').innerText = symNames.join(', ');

    // Meds Table
    const rptMedsTbody = document.getElementById('rpt-meds-tbody');
    rptMedsTbody.innerHTML = result.medications.map(m => `
        <tr>
            <td><strong>${m.name}</strong> (${m.category})</td>
            <td>${m.standard_dosage}</td>
            <td>${m.timing_instructions || 'Take with water.'}</td>
            <td>${m.safety_alert || 'Cleared standard safety checks'}</td>
        </tr>
    `).join('');

    // Preventive List
    document.getElementById('rpt-preventive-list').innerHTML = result.preventive_measures.map(p => `
        <li><strong>[${p.type} - ${p.priority} Priority]:</strong> ${p.description}</li>
    `).join('');

    // Diagnostic Tests List
    document.getElementById('rpt-tests-list').innerHTML = result.diagnostic_tests.map(t => `
        <li><strong>${t.name}</strong>: ${t.purpose}</li>
    `).join('');
}

/* ===================================================
   PROGNOSTIC DIGITAL HEALTH TWIN & SIMULATOR CONTROLLER
   =================================================== */

let simDebounceTimer = null;

function updateSimValue(param, val) {
    if (param === 'age') document.getElementById('sim-val-age').innerText = `${val} Years`;
    if (param === 'bmi') document.getElementById('sim-val-bmi').innerText = `${val} kg/m²`;
    if (param === 'bpsys') document.getElementById('sim-val-bpsys').innerText = `${val} mmHg`;
    if (param === 'glucose') document.getElementById('sim-val-glucose').innerText = `${val} mg/dL`;
    if (param === 'cholesterol') document.getElementById('sim-val-cholesterol').innerText = `${val} mg/dL`;

    clearTimeout(simDebounceTimer);
    simDebounceTimer = setTimeout(() => {
        runSimForecast();
    }, 250);
}

function syncSimulatorWithCdss() {
    const age = document.getElementById('vital-age').value || 45;
    const bmi = document.getElementById('vital-bmi').value || 25.0;
    const bpSys = document.getElementById('vital-bp-sys').value || 128;
    const glucose = document.getElementById('vital-glucose').value || 105;
    const cholesterol = document.getElementById('vital-cholesterol').value || 190;
    const smoking = document.getElementById('vital-smoking').value || 'Never';
    const activity = document.getElementById('vital-activity').value || 'Moderate';

    document.getElementById('sim-range-age').value = age;
    document.getElementById('sim-range-bmi').value = bmi;
    document.getElementById('sim-range-bpsys').value = bpSys;
    document.getElementById('sim-range-glucose').value = glucose;
    document.getElementById('sim-range-cholesterol').value = cholesterol;
    document.getElementById('sim-select-smoking').value = smoking;
    document.getElementById('sim-select-activity').value = activity;

    document.getElementById('sim-val-age').innerText = `${age} Years`;
    document.getElementById('sim-val-bmi').innerText = `${bmi} kg/m²`;
    document.getElementById('sim-val-bpsys').innerText = `${bpSys} mmHg`;
    document.getElementById('sim-val-glucose').innerText = `${glucose} mg/dL`;
    document.getElementById('sim-val-cholesterol').innerText = `${cholesterol} mg/dL`;

    runSimForecast();
    showToast("Synced Health Twin with current patient intake vitals!");
}

async function runSimForecast() {
    const age = parseFloat(document.getElementById('sim-range-age') ? document.getElementById('sim-range-age').value : 45);
    const bmi = parseFloat(document.getElementById('sim-range-bmi') ? document.getElementById('sim-range-bmi').value : 28.4);
    const bpSys = parseFloat(document.getElementById('sim-range-bpsys') ? document.getElementById('sim-range-bpsys').value : 145);
    const glucose = parseFloat(document.getElementById('sim-range-glucose') ? document.getElementById('sim-range-glucose').value : 130);
    const cholesterol = parseFloat(document.getElementById('sim-range-cholesterol') ? document.getElementById('sim-range-cholesterol').value : 220);
    const smoking = document.getElementById('sim-select-smoking') ? document.getElementById('sim-select-smoking').value : 'Current';
    const activity = document.getElementById('sim-select-activity') ? document.getElementById('sim-select-activity').value : 'Sedentary';

    const payload = {
        vitals: {
            age: age,
            bmi: bmi,
            bp_sys: bpSys,
            glucose: glucose,
            cholesterol: cholesterol,
            smoking: smoking,
            activity: activity,
            gender: 'Male'
        }
    };

    try {
        const res = await fetch('/api/simulator/forecast', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (data.status === 'success') {
            displaySimForecast(data.forecast);
        }
    } catch (err) {
        console.error("Simulation forecast failed:", err);
    }
}

function displaySimForecast(fc) {
    // 1. Biological Health Age
    const bioAgeEl = document.getElementById('twin-bio-age-val');
    const ageDiffBadge = document.getElementById('twin-age-diff-badge');
    if (bioAgeEl && ageDiffBadge) {
        bioAgeEl.innerText = `${fc.biological_age} Yrs`;
        if (fc.age_differential > 2) {
            ageDiffBadge.className = "twin-badge badge-danger";
            ageDiffBadge.innerText = `+${fc.age_differential} Yrs Older (Vascular Stiffening)`;
        } else if (fc.age_differential < -1) {
            ageDiffBadge.className = "twin-badge badge-success";
            ageDiffBadge.innerText = `${Math.abs(fc.age_differential)} Yrs Younger (Optimal Vitals)`;
        } else {
            ageDiffBadge.className = "twin-badge badge-warning";
            ageDiffBadge.innerText = "Approx. Matches Chronological Age";
        }
    }

    // 2. 10-Year CVD Risk
    const cvdVal = document.getElementById('twin-cvd-risk-val');
    const cvdBadge = document.getElementById('twin-cvd-badge');
    if (cvdVal && cvdBadge) {
        cvdVal.innerText = `${fc.ten_year_cvd_risk}%`;
        if (fc.ten_year_cvd_risk >= 30) {
            cvdBadge.className = "twin-badge badge-danger";
            cvdBadge.innerText = "High Cardiovascular Risk";
        } else if (fc.ten_year_cvd_risk >= 15) {
            cvdBadge.className = "twin-badge badge-warning";
            cvdBadge.innerText = "Moderate Risk";
        } else {
            cvdBadge.className = "twin-badge badge-success";
            cvdBadge.innerText = "Low / Favorable Risk";
        }
    }

    // 3. 5-Year Diabetes Risk
    const diabVal = document.getElementById('twin-diab-risk-val');
    const diabBadge = document.getElementById('twin-diab-badge');
    if (diabVal && diabBadge) {
        diabVal.innerText = `${fc.five_year_diab_risk}%`;
        if (fc.five_year_diab_risk >= 30) {
            diabBadge.style.background = "rgba(239, 68, 68, 0.2)";
            diabBadge.style.color = "#ef4444";
            diabBadge.innerText = "High Metabolic Risk";
        } else if (fc.five_year_diab_risk >= 15) {
            diabBadge.style.background = "rgba(245, 158, 11, 0.2)";
            diabBadge.style.color = "#fbbf24";
            diabBadge.innerText = "Borderline Insulin Resistance";
        } else {
            diabBadge.style.background = "rgba(16, 185, 129, 0.2)";
            diabBadge.style.color = "#10b981";
            diabBadge.innerText = "Optimal Glycemic Trajectory";
        }
    }

    // 4. Potential Risk Reduction & Life Years Gained
    const gainVal = document.getElementById('twin-gain-val');
    const yearsGainedBadge = document.getElementById('twin-years-gained-badge');
    if (gainVal && yearsGainedBadge) {
        gainVal.innerText = `-${fc.risk_reduction_pct}%`;
        yearsGainedBadge.innerText = `+${fc.life_years_gained} Healthy Yrs Gained`;
    }

    // 5. Prescriptive Actions List
    const actionsList = document.getElementById('prescriptive-actions-list');
    if (actionsList && fc.prescriptive_actions) {
        actionsList.innerHTML = fc.prescriptive_actions.map(act => `
            <div class="prescriptive-item">
                <strong><i class="fa-solid fa-check"></i> [${act.category}]: ${act.target}</strong>
                <p>${act.impact}</p>
            </div>
        `).join('');
    }

    // 6. 10-Year Comparative Trajectory Chart
    if (typeof renderTrajectoryChart === 'function') {
        renderTrajectoryChart(fc.years, fc.trajectory_baseline, fc.trajectory_optimized);
    }
}

