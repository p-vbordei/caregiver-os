// Caregiver OS Single Page Application Logic

const API_BASE = '/v1';

// Dictionary of translations
const I18N = {
    en: {
        nav_dashboard: "Dashboard",
        nav_meds: "Medications",
        nav_appts: "Appointments",
        nav_handoff: "Handoff Log",
        nav_careplan: "Care Plan",
        nav_approvals: "AI Approvals",
        nav_settings: "Settings",
        dash_title: "Daily Care State",
        dash_subtitle: "Real-time status and active shift tracking",
        meds_due_today: "Meds Due Today",
        appts_48h: "Appointments (48h)",
        shift_status: "Active Shift",
        incidents_today: "Incidents",
        shift_control: "Shift Operations",
        start_shift_desc: "No active shift. Start a shift to log vitals, meals, and incidents.",
        caregiver_name: "Caregiver Name",
        btn_start_shift: "Start Shift",
        shift_active_label: "Shift active:",
        label_vitals: "Vitals (BP, pulse, temp)",
        label_mood: "Mood",
        label_meals: "Meals",
        label_notes: "Notes / Observations",
        label_report_incident: "Report Incident (Optional)",
        opt_no_incident: "-- No Incident --",
        opt_fall: "Fall",
        opt_confusion: "Confusion",
        opt_missed_meal: "Missed Meal",
        opt_med_refusal: "Medication Refusal",
        opt_other: "Other",
        btn_save_log: "Save Log Entry",
        btn_end_shift: "End Shift",
        up_activities: "Scheduled for Today",
        meds_due: "Medications Due",
        appts_due: "Upcoming Appointments",
        meds_title: "Medication Management",
        meds_subtitle: "Configure medication lists, doses, schedules, and active alerts",
        tbl_name: "Name",
        tbl_dose: "Dose",
        tbl_schedule: "Schedule",
        tbl_instructions: "Instructions",
        tbl_refill: "Refill Alert",
        tbl_status: "Status",
        tbl_actions: "Actions",
        modal_add_med_title: "Add New Medication",
        med_times_label: "Times (comma-separated HH:MM)",
        med_refill_label: "Refill Alert Threshold (Days Left)",
        btn_save: "Save",
        appts_title: "Medical Appointments",
        appts_subtitle: "Coordinate therapy, consults, and clinical visits",
        tbl_date: "Date & Time",
        tbl_provider: "Provider",
        tbl_purpose: "Purpose",
        tbl_location: "Location",
        modal_add_appt_title: "Add Appointment",
        handoff_title: "Handoff Shifts History",
        handoff_subtitle: "Logs of past caregiver shifts and summaries",
        careplan_title: "Patient Care Plan",
        careplan_subtitle: "Shared clinical instructions and protocols",
        approvals_title: "AI Agent Consent Gate",
        approvals_subtitle: "Review and authorize pending write actions requested by the AI Copilot",
        settings_title: "System Settings",
        settings_subtitle: "Configure database connections, calendar subscriptions, and announcement bots",
        set_recipient_title: "Care Recipient Details",
        set_feeds_title: "External Calendar Feeds",
        set_profiles_title: "Care Team Profiles",
        add_team_member: "Add Team Member"
    },
    ro: {
        nav_dashboard: "Tablou de bord",
        nav_meds: "Medicamente",
        nav_appts: "Programări",
        nav_handoff: "Istoric schimburi",
        nav_careplan: "Plan de îngrijire",
        nav_approvals: "Aprobări AI",
        nav_settings: "Setări",
        dash_title: "Starea de îngrijire zilnică",
        dash_subtitle: "Monitorizare în timp real și gestionarea schimburilor active",
        meds_due_today: "Medicamente de luat azi",
        appts_48h: "Programări (48h)",
        shift_status: "Schimb activ",
        incidents_today: "Incidente",
        shift_control: "Operațiuni schimb",
        start_shift_desc: "Nu există un schimb activ. Începeți o tură pentru a înregistra funcțiile vitale, mesele și incidentele.",
        caregiver_name: "Nume îngrijitor",
        btn_start_shift: "Începe schimbul",
        shift_active_label: "Schimb activ pentru:",
        label_vitals: "Vitale (Tensiune, puls, temp)",
        label_mood: "Stare de spirit",
        label_meals: "Mese",
        label_notes: "Note / Observații",
        label_report_incident: "Raportează un incident (Opțional)",
        opt_no_incident: "-- Fără incident --",
        opt_fall: "Căzătură",
        opt_confusion: "Confuzie",
        opt_missed_meal: "Masă ratată",
        opt_med_refusal: "Refuz medicamente",
        opt_other: "Altul",
        btn_save_log: "Salvează intrarea",
        btn_end_shift: "Încheie schimbul",
        up_activities: "Planificat pentru astăzi",
        meds_due: "Medicamente de luat",
        appts_due: "Următoarele programări",
        meds_title: "Gestionare medicamente",
        meds_subtitle: "Configurează listele de medicamente, dozele, programul de administrare și alerte",
        tbl_name: "Nume",
        tbl_dose: "Doză",
        tbl_schedule: "Program",
        tbl_instructions: "Instrucțiuni",
        tbl_refill: "Alertă stoc",
        tbl_status: "Stare",
        tbl_actions: "Acțiuni",
        modal_add_med_title: "Adaugă medicament",
        med_times_label: "Ore administrare (separate prin virgulă, HH:MM)",
        med_refill_label: "Prag alertă stoc (Zile rămase)",
        btn_save: "Salvează",
        appts_title: "Programări medicale",
        appts_subtitle: "Coordonează terapiile, consultațiile și vizitele clinice",
        tbl_date: "Dată și oră",
        tbl_provider: "Medic / Cabinet",
        tbl_purpose: "Scop",
        tbl_location: "Locație",
        modal_add_appt_title: "Adaugă programare",
        handoff_title: "Istoric schimburi",
        handoff_subtitle: "Jurnale de activități pentru schimburile anterioare",
        careplan_title: "Plan de îngrijire",
        careplan_subtitle: "Instrucțiuni clinice și protocoale partajate",
        approvals_title: "Consimțământ acțiuni AI",
        approvals_subtitle: "Verifică și autorizează acțiunile de scriere solicitate de asistentul AI",
        settings_title: "Setări sistem",
        settings_subtitle: "Configurează conexiunea la baza de date, abonamente calendar și boti notificare",
        set_recipient_title: "Detalii beneficiar",
        set_feeds_title: "Fluxuri de calendar extern",
        set_profiles_title: "Profiluri echipă",
        add_team_member: "Adaugă membru echipă"
    }
};

let currentLang = localStorage.getItem('caregiver_lang') || 'en';
let currentProfile = null;
let profiles = [];
let activeShift = null;

// Application State Initializer
document.addEventListener("DOMContentLoaded", () => {
    initApp();
});

function initApp() {
    setupNavigation();
    setupLanguage();
    setupProfileDropdown();
    setupModals();
    setupEventListeners();
    
    // Load initial data
    loadRecipient();
    loadDashboard();
    loadMedications();
    loadAppointments();
    loadHandoffs();
    loadCarePlan();
    loadApprovals();
    loadSettings();
    loadProfiles();
    
    // Periodically poll approvals count
    setInterval(loadApprovals, 10000);
}

// Navigation handling
function setupNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    const views = document.querySelectorAll(".content-view");

    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const targetViewId = item.id.replace("nav-", "view-");
            
            navItems.forEach(n => n.classList.remove("active"));
            views.forEach(v => v.classList.remove("active"));
            
            item.classList.add("active");
            document.getElementById(targetViewId).classList.add("active");
        });
    });
}

// Language system logic
function setupLanguage() {
    document.getElementById("btn-lang-toggle").addEventListener("click", () => {
        currentLang = currentLang === 'en' ? 'ro' : 'en';
        localStorage.setItem('caregiver_lang', currentLang);
        applyTranslations();
        
        // Sync setting with backend default
        fetch(`${API_BASE}/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: 'default_language', value: currentLang })
        });
        
        showToast(currentLang === 'en' ? "Language changed to English" : "Limba a fost schimbată în Română", "info");
    });
    
    applyTranslations();
}

function applyTranslations() {
    document.getElementById("lang-label").innerText = currentLang === 'en' ? 'RO' : 'EN';
    
    // Find all tags with data-i18n and replace content
    const elements = document.querySelectorAll("[data-i18n]");
    elements.forEach(el => {
        const key = el.getAttribute("data-i18n");
        if (I18N[currentLang][key]) {
            el.innerText = I18N[currentLang][key];
        }
    });

    // Translate dynamic text fields that are inputs
    const nameInput = document.getElementById("input-caregiver-name");
    if (nameInput) {
        nameInput.placeholder = currentLang === 'en' ? 'e.g. Alice' : 'ex. Alice';
    }
}

// Active profiles dropdown management
function setupProfileDropdown() {
    const btn = document.getElementById("btn-profile-select");
    const content = document.getElementById("profile-dropdown-content");
    
    btn.addEventListener("click", (e) => {
        e.stopPropagation();
        content.classList.toggle("show");
    });
    
    document.addEventListener("click", () => {
        content.classList.remove("show");
    });
}

// Dialog modals
function setupModals() {
    const modals = [
        { btn: "btn-show-add-med", modal: "modal-add-med", close: "btn-close-med-modal" },
        { btn: "btn-show-add-appt", modal: "modal-add-appt", close: "btn-close-appt-modal" }
    ];
    
    modals.forEach(m => {
        const trigger = document.getElementById(m.btn);
        const modal = document.getElementById(m.modal);
        const closeBtn = document.getElementById(m.close);
        
        if (trigger && modal) {
            trigger.addEventListener("click", () => modal.classList.add("open"));
        }
        if (closeBtn && modal) {
            closeBtn.addEventListener("click", () => modal.classList.remove("open"));
        }
        if (modal) {
            modal.addEventListener("click", (e) => {
                if (e.target === modal) modal.classList.remove("open");
            });
        }
    });

    // Close button for shift summary modal
    const summaryClose = document.getElementById("btn-close-explain-modal");
    const summaryModal = document.getElementById("modal-explain-shift");
    if (summaryClose && summaryModal) {
        summaryClose.addEventListener("click", () => {
            summaryModal.classList.remove("open");
        });
        summaryModal.addEventListener("click", (e) => {
            if (e.target === summaryModal) summaryModal.classList.remove("open");
        });
    }
}

// Add REST Event triggers
function setupEventListeners() {
    // 1. Start Shift
    document.getElementById("btn-start-shift").addEventListener("click", startShift);
    
    // 2. Save log entry
    document.getElementById("btn-save-log").addEventListener("click", saveLogEntry);
    
    // 3. End Shift
    document.getElementById("btn-end-shift").addEventListener("click", endShift);
    
    // 4. Save Medication Form
    document.getElementById("form-add-med").addEventListener("submit", addMedication);

    // 5. Save Appointment Form
    document.getElementById("form-add-appt").addEventListener("submit", addAppointment);

    // 6. Sync iCal
    document.getElementById("btn-sync-ical").addEventListener("click", syncICal);

    // 7. Care Plan Edit lifecycle
    document.getElementById("btn-edit-careplan").addEventListener("click", editCarePlan);
    document.getElementById("btn-cancel-careplan").addEventListener("click", cancelCarePlanEdit);
    document.getElementById("btn-save-careplan").addEventListener("click", saveCarePlan);

    // 8. Settings Forms
    document.getElementById("form-settings-recipient").addEventListener("submit", saveRecipientSettings);
    document.getElementById("form-settings-feeds").addEventListener("submit", saveFeedsSettings);
    document.getElementById("form-settings-telegram").addEventListener("submit", saveTelegramSettings);
    document.getElementById("form-settings-email").addEventListener("submit", saveEmailSettings);
    document.getElementById("form-settings-add-profile").addEventListener("submit", addProfileTeam);
}

// REST Call integrations

// --- Recipient ---
async function loadRecipient() {
    try {
        const res = await fetch(`${API_BASE}/recipient`);
        if (res.ok) {
            const data = await res.json();
            document.getElementById("active-recipient-label").innerText = `${data.name} (${data.age || '?'})`;
            document.getElementById("set-recipient-name").value = data.name;
            document.getElementById("set-recipient-age").value = data.age || '';
            document.getElementById("set-recipient-notes").value = data.notes || '';
        } else {
            document.getElementById("active-recipient-label").innerText = currentLang === 'en' ? 'Setup Required' : 'Necesită configurare';
        }
    } catch (e) {
        console.error(e);
    }
}

// --- Dashboard Stats ---
async function loadDashboard() {
    try {
        const res = await fetch(`${API_BASE}/today`);
        if (!res.ok) return;
        const data = await res.json();
        
        // Count elements
        document.getElementById("dash-meds-count").innerText = data.medications_due.length;
        document.getElementById("dash-appts-count").innerText = data.upcoming_appointments.length;
        document.getElementById("dash-incidents-count").innerText = data.recent_incidents.length;
        
        // Active shift logic
        if (data.open_handoff) {
            activeShift = data.open_handoff;
            document.getElementById("dash-shift-status").innerText = activeShift.caregiver;
            document.getElementById("shift-closed-panel").classList.add("hidden");
            document.getElementById("shift-open-panel").classList.remove("hidden");
            document.getElementById("open-caregiver-label").innerText = activeShift.caregiver;
        } else {
            activeShift = null;
            document.getElementById("dash-shift-status").innerText = currentLang === 'en' ? 'Closed' : 'Închis';
            document.getElementById("shift-closed-panel").classList.remove("hidden");
            document.getElementById("shift-open-panel").classList.add("hidden");
        }

        // Render sched lists
        renderDashboardLists(data);
    } catch (e) {
        console.error(e);
    }
}

function renderDashboardLists(data) {
    // 1. Meds
    const medsList = document.getElementById("dash-meds-list");
    medsList.innerHTML = '';
    if (data.medications_due.length === 0) {
        medsList.innerHTML = `<p class="timeline-desc">${currentLang === 'en' ? 'No medications due today.' : 'Fără medicamente planificate azi.'}</p>`;
    } else {
        data.medications_due.forEach(m => {
            const item = document.createElement("div");
            item.className = "timeline-item";
            item.innerHTML = `
                <div class="timeline-meta">
                    <span class="timeline-title">${m.name}</span>
                    <span class="timeline-desc">${m.dose} — ${m.instructions || ''}</span>
                </div>
                <span class="timeline-time">${m.times.join(', ')}</span>
            `;
            medsList.appendChild(item);
        });
    }

    // 2. Appointments
    const apptsList = document.getElementById("dash-appts-list");
    apptsList.innerHTML = '';
    if (data.upcoming_appointments.length === 0) {
        apptsList.innerHTML = `<p class="timeline-desc">${currentLang === 'en' ? 'No upcoming appointments.' : 'Nu există programări viitoare.'}</p>`;
    } else {
        data.upcoming_appointments.forEach(a => {
            const atDate = new Date(a.at);
            const timeStr = atDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const dateStr = atDate.toLocaleDateString([], { month: 'short', day: 'numeric' });
            
            const item = document.createElement("div");
            item.className = "timeline-item";
            item.innerHTML = `
                <div class="timeline-meta">
                    <span class="timeline-title">${a.provider}</span>
                    <span class="timeline-desc">${a.purpose || ''} @ ${a.location || ''}</span>
                </div>
                <span class="timeline-time">${dateStr} ${timeStr}</span>
            `;
            apptsList.appendChild(item);
        });
    }
}

// --- Shift operations ---
async function startShift() {
    const caregiverName = document.getElementById("input-caregiver-name").value.trim();
    if (!caregiverName) {
        showToast(currentLang === 'en' ? "Please enter caregiver name" : "Introduceți numele îngrijitorului", "error");
        return;
    }

    try {
        const rRes = await fetch(`${API_BASE}/recipient`);
        if (!rRes.ok) {
            showToast("Setup Care Recipient first", "error");
            return;
        }
        const rData = await rRes.json();

        const body = {
            care_recipient_id: rData.id,
            caregiver: caregiverName,
            medications_given: [],
            incidents: []
        };
        const res = await fetch(`${API_BASE}/handoffs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        
        if (res.ok) {
            showToast(currentLang === 'en' ? "Shift started!" : "Schimbul a început!", "success");
            loadDashboard();
            loadHandoffs();
        } else {
            const err = await res.json();
            showToast(err.detail || "Error starting shift", "error");
        }
    } catch (e) {
        console.error(e);
    }
}

async function saveLogEntry() {
    const vitals = document.getElementById("log-vitals").value.trim();
    const mood = document.getElementById("log-mood").value.trim();
    const meals = document.getElementById("log-meals").value.trim();
    const notes = document.getElementById("log-notes").value.trim();
    
    // Incidents
    const incKind = document.getElementById("incident-kind").value;
    const incSeverity = document.getElementById("incident-severity").value;
    const incDesc = document.getElementById("incident-desc").value.trim();
    
    let incidentStr = null;
    if (incKind && incDesc) {
        incidentStr = `${incKind}:${incSeverity}:${incDesc}`;
    }

    try {
        const res = await fetch(`${API_BASE}/handoffs/log`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ vitals, mood, meals, notes, incident: incidentStr })
        });
        
        if (res.ok) {
            showToast(currentLang === 'en' ? "Log updated!" : "Jurnal actualizat!", "success");
            
            // Clear inputs
            document.getElementById("log-vitals").value = '';
            document.getElementById("log-mood").value = '';
            document.getElementById("log-meals").value = '';
            document.getElementById("log-notes").value = '';
            document.getElementById("incident-kind").value = '';
            document.getElementById("incident-desc").value = '';
            
            loadDashboard();
            loadHandoffs();
        } else {
            const err = await res.json();
            showToast(err.detail || "Error saving log", "error");
        }
    } catch (e) {
        console.error(e);
    }
}

async function endShift() {
    if (!activeShift) return;
    
    try {
        const res = await fetch(`${API_BASE}/handoffs/${activeShift.id}/end`, {
            method: 'POST'
        });
        if (res.ok) {
            showToast(currentLang === 'en' ? "Shift ended." : "Schimb închis.", "info");
            loadDashboard();
            loadHandoffs();
        }
    } catch (e) {
        console.error(e);
    }
}

// --- Medications list management ---
async function loadMedications() {
    try {
        const res = await fetch(`${API_BASE}/meds`);
        if (!res.ok) return;
        const data = await res.json();
        
        const tbody = document.getElementById("meds-table-body");
        tbody.innerHTML = '';
        
        data.forEach(m => {
            const tr = document.createElement("tr");
            const statusClass = m.active ? 'active' : 'inactive';
            const statusText = m.active 
                ? (currentLang === 'en' ? 'Active' : 'Activ') 
                : (currentLang === 'en' ? 'Inactive' : 'Inactiv');

            tr.innerHTML = `
                <td><strong>${m.name}</strong></td>
                <td>${m.dose}</td>
                <td><span class="timeline-time">${m.times.join(', ')}</span></td>
                <td>${m.instructions || ''}</td>
                <td>${m.refill_at_days_left} ${currentLang === 'en' ? 'days left' : 'zile rămase'}</td>
                <td><span class="status-pill ${statusClass}">${statusText}</span></td>
                <td>
                    ${m.active ? `<button class="btn btn-danger btn-icon" onclick="deactivateMed('${m.id}')" title="Deactivate">🗑️</button>` : ''}
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error(e);
    }
}

async function addMedication(e) {
    e.preventDefault();
    const name = document.getElementById("med-name").value.trim();
    const dose = document.getElementById("med-dose").value.trim();
    const timesRaw = document.getElementById("med-times").value.trim();
    const instructions = document.getElementById("med-instructions").value.trim();
    const refill = parseInt(document.getElementById("med-refill").value);

    // Convert comma times to array
    const times = timesRaw.split(',').map(t => t.trim()).filter(Boolean);

    try {
        // Find recipient ID first
        const rRes = await fetch(`${API_BASE}/recipient`);
        if (!rRes.ok) {
            showToast("Setup Care Recipient first in Settings", "error");
            return;
        }
        const rData = await rRes.json();

        const body = {
            care_recipient_id: rData.id,
            name,
            dose,
            times,
            instructions,
            refill_at_days_left: refill,
            active: true
        };

        const res = await fetch(`${API_BASE}/meds`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        if (res.ok) {
            showToast(currentLang === 'en' ? "Medication added!" : "Medicament adăugat!", "success");
            document.getElementById("modal-add-med").classList.remove("open");
            document.getElementById("form-add-med").reset();
            loadMedications();
            loadDashboard();
        }
    } catch (err) {
        console.error(err);
    }
}

async function deactivateMed(id) {
    if (!confirm(currentLang === 'en' ? "Deactivate this medication?" : "Dezactivați acest medicament?")) return;
    try {
        const res = await fetch(`${API_BASE}/meds/${id}/deactivate`, { method: 'POST' });
        if (res.ok) {
            showToast(currentLang === 'en' ? "Medication deactivated" : "Medicament dezactivat", "info");
            loadMedications();
            loadDashboard();
        }
    } catch (e) {
        console.error(e);
    }
}

// --- Appointments ---
async function loadAppointments() {
    try {
        const res = await fetch(`${API_BASE}/appointments`);
        if (!res.ok) return;
        const data = await res.json();
        
        const tbody = document.getElementById("appts-table-body");
        tbody.innerHTML = '';
        
        data.sort((x, y) => new Date(x.at) - new Date(y.at));
        
        data.forEach(a => {
            const tr = document.createElement("tr");
            const atDate = new Date(a.at);
            const statusClass = a.completed ? 'inactive' : 'active';
            const statusText = a.completed 
                ? (currentLang === 'en' ? 'Completed' : 'Finalizat') 
                : (currentLang === 'en' ? 'Upcoming' : 'Programat');

            tr.innerHTML = `
                <td><strong>${atDate.toLocaleString()}</strong></td>
                <td><strong>${a.provider}</strong></td>
                <td>${a.purpose || ''}</td>
                <td>${a.location || ''}</td>
                <td><span class="status-pill ${statusClass}">${statusText}</span></td>
                <td>
                    ${!a.completed ? `<button class="btn btn-primary btn-icon" onclick="completeAppt('${a.id}')" title="Complete">✓</button>` : ''}
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error(e);
    }
}

async function addAppointment(e) {
    e.preventDefault();
    const provider = document.getElementById("appt-provider").value.trim();
    const at = document.getElementById("appt-at").value;
    const purpose = document.getElementById("appt-purpose").value.trim();
    const location = document.getElementById("appt-location").value.trim();

    try {
        const rRes = await fetch(`${API_BASE}/recipient`);
        if (!rRes.ok) {
            showToast("Setup Care Recipient first", "error");
            return;
        }
        const rData = await rRes.json();

        const body = {
            care_recipient_id: rData.id,
            provider,
            at,
            purpose,
            location,
            completed: false
        };

        const res = await fetch(`${API_BASE}/appointments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        if (res.ok) {
            showToast(currentLang === 'en' ? "Appointment added!" : "Programare adăugată!", "success");
            document.getElementById("modal-add-appt").classList.remove("open");
            document.getElementById("form-add-appt").reset();
            loadAppointments();
            loadDashboard();
        }
    } catch (err) {
        console.error(err);
    }
}

async function completeAppt(id) {
    try {
        const res = await fetch(`${API_BASE}/appointments/${id}/complete`, { method: 'POST' });
        if (res.ok) {
            showToast(currentLang === 'en' ? "Appointment completed!" : "Programare finalizată!", "success");
            loadAppointments();
            loadDashboard();
        }
    } catch (e) {
        console.error(e);
    }
}

async function syncICal() {
    showToast(currentLang === 'en' ? "Syncing calendars..." : "Se sincronizează calendarele...", "info");
    try {
        const res = await fetch(`${API_BASE}/appointments/sync`, { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        if (res.ok) {
            const data = await res.json();
            showToast(
                currentLang === 'en' 
                    ? `Sync completed. Imported ${data.imported} appointments.` 
                    : `Sincronizare finalizată. S-au importat ${data.imported} programări.`, 
                "success"
            );
            loadAppointments();
            loadDashboard();
        } else {
            showToast(currentLang === 'en' ? "iCal sync failed. Verify feed URL." : "Sincronizare eșuată. Verificați URL-ul.", "error");
        }
    } catch (e) {
        console.error(e);
    }
}

// --- Handoff shift logs history ---
async function loadHandoffs() {
    try {
        const res = await fetch(`${API_BASE}/handoffs`);
        if (!res.ok) return;
        const data = await res.json();
        
        const timeline = document.getElementById("handoff-history-timeline");
        timeline.innerHTML = '';
        
        // Sort newest first
        data.sort((x, y) => new Date(y.shift_start) - new Date(x.shift_start));

        data.forEach(h => {
            const start = new Date(h.shift_start);
            const end = h.shift_end ? new Date(h.shift_end) : null;
            const timeStr = `${start.toLocaleString()} ➔ ${end ? end.toLocaleString() : (currentLang === 'en' ? 'ACTIVE' : 'ACTIVĂ')}`;
            
            const card = document.createElement("div");
            card.className = `history-card ${end ? '' : 'open-shift'}`;
            
            // Build incident badges
            let incBadges = '';
            if (h.incidents && h.incidents.length > 0) {
                incBadges = `<div class="history-incidents">`;
                h.incidents.forEach(inc => {
                    incBadges += `
                        <div class="incident-badge ${inc.severity}">
                            ⚠️ <strong>[${inc.severity.toUpperCase()}] ${inc.kind}</strong>: ${inc.description}
                        </div>
                    `;
                });
                incBadges += `</div>`;
            }

            card.innerHTML = `
                <div class="history-header">
                    <span class="history-title">👤 ${h.caregiver}</span>
                    <span class="history-time">${timeStr}</span>
                </div>
                <div class="history-details-grid">
                    <div class="history-detail-item">
                        <strong>${currentLang === 'en' ? '💓 Vitals' : '💓 Funcții vitale'}</strong>
                        ${h.vitals || '-'}
                    </div>
                    <div class="history-detail-item">
                        <strong>${currentLang === 'en' ? '😊 Mood' : '😊 Stare spirit'}</strong>
                        ${h.mood || '-'}
                    </div>
                    <div class="history-detail-item">
                        <strong>${currentLang === 'en' ? '🍎 Meals' : '🍎 Mese'}</strong>
                        ${h.meals || '-'}
                    </div>
                </div>
                ${h.notes ? `<div class="history-notes"><strong>${currentLang === 'en' ? 'Notes:' : 'Note:'}</strong> ${h.notes}</div>` : ''}
                ${incBadges}
                <div class="mt-3">
                    <button class="btn btn-secondary" onclick="explainShift('${h.id}')">✨ ${currentLang === 'en' ? 'AI Explainer Summary' : 'Sumar explicativ AI'}</button>
                </div>
            `;
            timeline.appendChild(card);
        });
    } catch (e) {
        console.error(e);
    }
}

async function explainShift(id) {
    const textDiv = document.getElementById("ai-summary-text");
    textDiv.innerHTML = `<p>${currentLang === 'en' ? 'Generating shift summary using Gemini...' : 'Se generează rezumatul tura folosind Gemini...'}</p>`;
    document.getElementById("modal-explain-shift").classList.add("open");

    try {
        const res = await fetch(`${API_BASE}/handoffs/${id}/explain?lang=${currentLang}`);
        if (res.ok) {
            const data = await res.json();
            // Convert markdown simple structure to HTML
            textDiv.innerHTML = formatMarkdown(data.summary);
        } else {
            textDiv.innerHTML = `<p class="color-danger">${currentLang === 'en' ? 'API summarization error.' : 'Eroare la generarea rezumatului.'}</p>`;
        }
    } catch (e) {
        textDiv.innerHTML = `<p class="color-danger">Connection error: ${e}</p>`;
    }
}

// Simple markdown formatter
function formatMarkdown(text) {
    if (!text) return '';
    let html = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^\*\* (.*$)/gim, '<strong>$1</strong>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/- (.*$)/gim, '<li>$1</li>')
        .replace(/\n/g, '<br>');
    
    // Wrap lists
    html = html.replace(/(<li>.*<\/li>)/gim, '<ul>$1</ul>');
    return html;
}

// --- Care Plan ---
async function loadCarePlan() {
    try {
        const res = await fetch(`${API_BASE}/careplan`);
        if (!res.ok) return;
        const data = await res.json();
        
        const display = document.getElementById("careplan-display");
        const textarea = document.getElementById("careplan-markdown-input");
        
        if (data.length > 0) {
            // Sort versions to get latest
            data.sort((x, y) => y.version - x.version);
            const latest = data[0];
            
            display.innerHTML = formatMarkdown(latest.markdown);
            textarea.value = latest.markdown;
        } else {
            display.innerHTML = `<p>${currentLang === 'en' ? 'No care plan guidelines uploaded yet.' : 'Nu s-au adăugat linii directoare pentru planul de îngrijire.'}</p>`;
            textarea.value = `# Patient Care Guidelines\n\n- Diet:\n- Activity:\n- Restrictions:`;
        }
    } catch (e) {
        console.error(e);
    }
}

function editCarePlan() {
    document.getElementById("careplan-display").classList.add("hidden");
    document.getElementById("careplan-edit-container").classList.remove("hidden");
}

function cancelCarePlanEdit() {
    document.getElementById("careplan-display").classList.remove("hidden");
    document.getElementById("careplan-edit-container").classList.add("hidden");
}

async function saveCarePlan() {
    const markdown = document.getElementById("careplan-markdown-input").value;
    
    try {
        const rRes = await fetch(`${API_BASE}/recipient`);
        if (!rRes.ok) {
            showToast("Setup Care Recipient first", "error");
            return;
        }
        const rData = await rRes.json();

        // Get latest version index
        const listRes = await fetch(`${API_BASE}/careplan`);
        const list = await listRes.json();
        const nextVersion = list.length + 1;

        const body = {
            care_recipient_id: rData.id,
            version: nextVersion,
            markdown: markdown,
            updated_by: currentProfile ? currentProfile.name : "Caregiver"
        };

        const res = await fetch(`${API_BASE}/careplan`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        if (res.ok) {
            showToast(currentLang === 'en' ? "Care Plan updated!" : "Planul de îngrijire a fost actualizat!", "success");
            cancelCarePlanEdit();
            loadCarePlan();
        }
    } catch (e) {
        console.error(e);
    }
}

// --- AI Approvals / Consent Gate ---
async function loadApprovals() {
    try {
        const res = await fetch(`${API_BASE}/approvals`);
        if (!res.ok) return;
        const data = await res.json();
        
        // Update badge count
        const badge = document.getElementById("badge-pending-count");
        if (data.length > 0) {
            badge.innerText = data.length;
            badge.classList.remove("hidden");
        } else {
            badge.classList.add("hidden");
        }

        const container = document.getElementById("approvals-container");
        if (document.getElementById("view-approvals").classList.contains("active") || container.children.length === 0) {
            container.innerHTML = '';
            if (data.length === 0) {
                container.innerHTML = `<p>${currentLang === 'en' ? 'No pending AI authorization requests.' : 'Nu există solicitări de autorizare AI în așteptare.'}</p>`;
            } else {
                data.forEach(appr => {
                    const card = document.createElement("div");
                    card.className = "approval-card";
                    
                    // Format arguments representation
                    const argsStr = Object.entries(appr.arguments)
                        .map(([k, v]) => `<strong>${k}:</strong> ${v}`)
                        .join(', ');

                    card.innerHTML = `
                        <div class="approval-info">
                            <h4>🤖 Action Request: ${appr.tool_name}</h4>
                            <div class="approval-args">${argsStr}</div>
                            <div class="approval-time">${new Date(appr.created_at).toLocaleString()}</div>
                        </div>
                        <div class="btn-group">
                            <button class="btn btn-primary" onclick="actionApproval('${appr.id}', 'approve')">${currentLang === 'en' ? 'Approve' : 'Aprobă'}</button>
                            <button class="btn btn-danger" onclick="actionApproval('${appr.id}', 'deny')">${currentLang === 'en' ? 'Deny' : 'Respinge'}</button>
                        </div>
                    `;
                    container.appendChild(card);
                });
            }
        }
    } catch (e) {
        console.error(e);
    }
}

async function actionApproval(id, action) {
    try {
        const res = await fetch(`${API_BASE}/approvals/${id}/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action })
        });
        if (res.ok) {
            showToast(
                action === 'approve' 
                    ? (currentLang === 'en' ? 'Action Authorized' : 'Acțiune autorizată')
                    : (currentLang === 'en' ? 'Action Denied' : 'Acțiune respinsă'),
                action === 'approve' ? 'success' : 'info'
            );
            loadApprovals();
            loadDashboard();
            loadMedications();
            loadAppointments();
            loadHandoffs();
        }
    } catch (e) {
        console.error(e);
    }
}

// --- Settings & Profiles ---
async function loadSettings() {
    try {
        const res = await fetch(`${API_BASE}/settings`);
        if (!res.ok) return;
        const data = await res.json();
        
        // Fill Settings
        document.getElementById("set-ical-urls").value = data.ical_urls || '';
        document.getElementById("set-tg-token").value = data.telegram_bot_token || '';
        document.getElementById("set-tg-chat").value = data.telegram_chat_id || '';
        document.getElementById("set-email-host").value = data.email_smtp_host || '';
        document.getElementById("set-email-port").value = data.email_smtp_port || '';
        document.getElementById("set-email-user").value = data.email_smtp_user || '';
        document.getElementById("set-email-from").value = data.email_from || '';
        document.getElementById("set-email-to").value = data.email_to || '';
        
        if (data.default_language) {
            currentLang = data.default_language;
            localStorage.setItem('caregiver_lang', currentLang);
            applyTranslations();
        }
    } catch (e) {
        console.error(e);
    }
}

async function saveRecipientSettings(e) {
    e.preventDefault();
    const name = document.getElementById("set-recipient-name").value.trim();
    const age = parseInt(document.getElementById("set-recipient-age").value) || null;
    const notes = document.getElementById("set-recipient-notes").value.trim();

    try {
        const res = await fetch(`${API_BASE}/recipient`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, age, notes })
        });
        if (res.ok) {
            showToast(currentLang === 'en' ? "Recipient details saved" : "Detaliile beneficiarului au fost salvate", "success");
            loadRecipient();
        }
    } catch (err) {
        console.error(err);
    }
}

async function saveSettingKey(key, value) {
    await fetch(`${API_BASE}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, value })
    });
}

async function saveFeedsSettings(e) {
    e.preventDefault();
    const urls = document.getElementById("set-ical-urls").value.trim();
    await saveSettingKey('ical_urls', urls);
    showToast(currentLang === 'en' ? "Feeds settings saved" : "Setările calendarelor au fost salvate", "success");
}

async function saveTelegramSettings(e) {
    e.preventDefault();
    const token = document.getElementById("set-tg-token").value.trim();
    const chat = document.getElementById("set-tg-chat").value.trim();
    await saveSettingKey('telegram_bot_token', token);
    await saveSettingKey('telegram_chat_id', chat);
    showToast(currentLang === 'en' ? "Telegram details saved" : "Setările Telegram au fost salvate", "success");
}

async function saveEmailSettings(e) {
    e.preventDefault();
    await saveSettingKey('email_smtp_host', document.getElementById("set-email-host").value.trim());
    await saveSettingKey('email_smtp_port', document.getElementById("set-email-port").value.trim());
    await saveSettingKey('email_smtp_user', document.getElementById("set-email-user").value.trim());
    await saveSettingKey('email_smtp_pass', document.getElementById("set-email-pass").value);
    await saveSettingKey('email_from', document.getElementById("set-email-from").value.trim());
    await saveSettingKey('email_to', document.getElementById("set-email-to").value.trim());
    showToast(currentLang === 'en' ? "Email SMTP settings saved" : "Setările SMTP au fost salvate", "success");
}

// --- Team profiles ---
async function loadProfiles() {
    try {
        const res = await fetch(`${API_BASE}/profiles`);
        if (!res.ok) return;
        profiles = await res.json();
        
        // Render selector drop
        const content = document.getElementById("profile-dropdown-content");
        content.innerHTML = '';
        
        profiles.forEach(p => {
            const btn = document.createElement("button");
            btn.innerHTML = `👤 ${p.name} <small>(${p.role})</small>`;
            btn.addEventListener("click", () => switchProfile(p));
            content.appendChild(btn);
        });

        // Set default profile if none
        if (profiles.length > 0 && !currentProfile) {
            switchProfile(profiles[0]);
        }
        
        // Render settings profiles list table
        const tbody = document.getElementById("profiles-settings-table-body");
        tbody.innerHTML = '';
        profiles.forEach(p => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${p.name}</strong></td>
                <td>${p.role}</td>
                <td>${p.language === 'ro' ? 'Română' : 'English'}</td>
                <td>
                    <span class="status-pill active">${currentLang === 'en' ? 'Active' : 'Activ'}</span>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error(e);
    }
}

function switchProfile(p) {
    currentProfile = p;
    document.getElementById("current-profile-label").innerText = p.name;
    
    // Switch language to profile default language if not already set
    if (p.language !== currentLang) {
        currentLang = p.language;
        localStorage.setItem('caregiver_lang', currentLang);
        applyTranslations();
    }
    
    // Autofill name input in shift start
    const nameInput = document.getElementById("input-caregiver-name");
    if (nameInput) {
        nameInput.value = p.name;
    }
}

async function addProfileTeam(e) {
    e.preventDefault();
    const name = document.getElementById("new-profile-name").value.trim();
    const role = document.getElementById("new-profile-role").value;
    const language = document.getElementById("new-profile-lang").value;

    try {
        const res = await fetch(`${API_BASE}/profiles`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, role, language })
        });
        if (res.ok) {
            showToast(currentLang === 'en' ? "Profile created!" : "Profil creat!", "success");
            document.getElementById("new-profile-name").value = '';
            loadProfiles();
        }
    } catch (err) {
        console.error(err);
    }
}

// Toast alerts helper
function showToast(message, type = "success") {
    const toast = document.getElementById("app-toast");
    toast.innerText = message;
    toast.className = `toast ${type}`;
    toast.classList.remove("hidden");
    
    setTimeout(() => {
        toast.classList.add("hidden");
    }, 4000);
}
