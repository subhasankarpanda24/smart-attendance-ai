/* ── Shared state ─────────────────────────────────────────────────────── */
let currentFilter = 'all';

/* ── API helpers ──────────────────────────────────────────────────────── */
function api(url, options = {}) {
  return fetch(url, { headers: { 'Content-Type': 'application/json' }, ...options })
    .then(r => {
      if (r.status === 401 || r.redirected) { window.location.href = '/login'; return null; }
      return r.json();
    });
}

function showToast(msg) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 3000);
}

setInterval(() => {
  const el = document.getElementById('syncTime');
  if (el) el.textContent = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}, 1000);

/* ── Dashboard: Stats ─────────────────────────────────────────────────── */
async function loadStats() {
  const d = await api('/api/stats');
  if (!d) return;
  document.getElementById('sv-att').textContent = d.overall_attendance + '%';
  document.getElementById('sv-att-s').innerHTML = '<span class="up">↑ 2.1%</span> vs last month';
  document.getElementById('sv-risk').textContent = d.at_risk_students;
  document.getElementById('sv-risk-s').innerHTML = '<span class="dn">↑ 8</span> new this week';
  document.getElementById('sv-perf').textContent = d.perfect_attendance;
  document.getElementById('sv-perf-s').innerHTML = '<span class="up">↑ 5</span> since last week';
  document.getElementById('sv-alrt').textContent = d.alerts_today;
  document.getElementById('sv-alrt-s').textContent = 'Email + SMS notified';
  const badge = document.getElementById('alertBadge');
  if (badge) badge.textContent = d.alerts_today;

  // Make stat cards clickable
  document.querySelector('.cr')?.addEventListener('click', () => window.location.href = '/students?risk=high');
  document.querySelector('.cg')?.addEventListener('click', () => window.location.href = '/students?risk=low');
  document.querySelector('.cp')?.addEventListener('click', () => window.location.href = '/alerts');
}

/* ── Dashboard: Chart ────────────────────────────────────────────────── */
async function loadChart() {
  const data = await api('/api/weekly-trend');
  if (!data) return;
  const el = document.getElementById('chartBars');
  if (!el) return;
  el.innerHTML = '';
  const maxH = 143;
  data.forEach(d => {
    const g = document.createElement('div');
    g.className = 'bg';
    g.innerHTML = `
      <div class="bs">
        <div class="b bl" style="height:0" data-h="${(d.late / 100) * maxH}px"    title="Late: ${d.late}%"></div>
        <div class="b ba" style="height:0" data-h="${(d.absent / 100) * maxH}px"  title="Absent: ${d.absent}%"></div>
        <div class="b bp" style="height:0" data-h="${(d.present / 100) * maxH}px" title="Present: ${d.present}%"></div>
      </div>
      <div class="blbl">${d.week}</div>`;
    el.appendChild(g);
  });
  setTimeout(() => {
    el.querySelectorAll('.b').forEach(b => {
      b.style.height = b.getAttribute('data-h');
    });
  }, 50);
}

function switchTab(el) {
  document.querySelectorAll('.ctab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  loadChart();
}

/* ── Dashboard: Risk List ────────────────────────────────────────────── */
async function loadRiskList() {
  const data = await api('/api/students');
  if (!data) return;
  const atRisk = data.filter(s => s.risk !== 'low').slice(0, 5);
  const el = document.getElementById('riskList');
  if (!el) return;
  el.innerHTML = atRisk.map(s => {
    const ini = s.name.split(' ').map(n => n[0]).join('');
    return `<div class="ri ${s.risk}" style="cursor:pointer" onclick="window.location.href='/student/${s.id}'">
      <div class="rav">${ini}</div>
      <div class="rinfo">
        <div class="rname">${s.name}</div>
        <div class="rdet">${s.id} · ${s.risk.toUpperCase()} RISK</div>
      </div>
      <div class="rright">
        <div class="rpct">${s.attendance}%</div>
        <div class="mw"><div class="mf" style="width:${s.attendance}%"></div></div>
      </div>
    </div>`;
  }).join('');
}



/* ── Alert Feed ──────────────────────────────────────────────────────── */
async function loadAlertFeed(targetId = 'alertFeed') {
  const data = await api('/api/alerts');
  if (!data) return;
  const el = document.getElementById(targetId);
  if (!el) return;
  el.innerHTML = data.map(a =>
    `<div class="ai ${a.type}" style="cursor:pointer" onclick="window.location.href='/alerts'">
      <div class="at">${a.time}</div>
      <div class="am">${a.msg}</div>
    </div>`
  ).join('');
}

/* ── Students Table ──────────────────────────────────────────────────── */
async function loadStudents() {
  const search = document.getElementById('searchInput')?.value || '';
  const data = await api(`/api/students?risk=${currentFilter}&search=${encodeURIComponent(search)}`);
  if (!data) return;
  const tbody = document.getElementById('stuTbody');
  if (!tbody) return;
  if (!data.length) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--muted2);padding:30px">No students found</td></tr>';
    return;
  }
  tbody.innerHTML = data.map(s => `
    <tr>
      <td>
        <a href="/student/${s.id}" class="sname" style="color:var(--text); text-decoration:none;">${s.name}</a>
        <div class="sid">${s.id}</div>
        ${s.trend_alert ? `<div style="font-size:10px; color:var(--r); font-weight:700; margin-top:4px;">${s.trend_alert}</div>` : ''}
      </td>
      <td style="color:var(--muted2)">${s.dept} · Year ${s.year}</td>
      <td style="font-size:11px;color:var(--muted2)">
        <div>${s.email || '—'}</div>
        <div>${s.phone || '—'}</div>
      </td>
      <td>
        <div class="att-row">
          <div class="att-track"><div class="att-fill ${s.risk}" style="width:0" data-w="${s.attendance}%"></div></div>
          <span style="font-variant-numeric: tabular-nums; font-size:12px">${s.attendance}%</span>
        </div>
      </td>
      <td><span class="rpill ${s.risk}">${s.risk.toUpperCase()}</span></td>
      <td>
        <div class="action-btns">
          <button class="mbtn" onclick="markAttendance('${s.id}','${s.name}')">✓ Present</button>
          ${(typeof userRole !== 'undefined' && userRole === 'admin') ? `
          <button class="edit-btn" onclick='openEditModal(${JSON.stringify(s)})'>✏️ Edit</button>
          <button class="del-btn" onclick="openDeleteModal('${s.id}','${s.name}')">🗑️</button>
          ` : ''}
        </div>
      </td>
    </tr>`).join('');

  setTimeout(() => {
    tbody.querySelectorAll('.att-fill').forEach(el => el.style.width = el.getAttribute('data-w'));
  }, 50);

  // Handle URL filter param
  const params = new URLSearchParams(window.location.search);
  const riskParam = params.get('risk');
  if (riskParam && riskParam !== currentFilter) {
    const btn = document.querySelector(`.fbtn.f${riskParam[0]}`);
    if (btn) setFilter(riskParam, btn);
  }
}

function setFilter(f, btn) {
  currentFilter = f;
  document.querySelectorAll('.fbtn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  loadStudents();
}

function filterStudents() { loadStudents(); }

async function markAttendance(id, name) {
  const res = await api('/api/mark-attendance', {
    method: 'POST',
    body: JSON.stringify({ student_id: id, status: 'present', subject: 'CS-101' }),
  });
  if (res && res.success) showToast(`✅ ${name} marked present`);
}

/* ── Analytics ───────────────────────────────────────────────────────── */
async function loadSubjectAttendance() {
  const data = await api('/api/subject-attendance');
  if (!data) return;
  const el = document.getElementById('subjBars');
  if (!el) return;
  el.innerHTML = data.map(s => `
    <div class="srow">
      <div class="slbl" title="${s.subject}">${s.subject}</div>
      <div class="strack"><div class="sfill" style="width:0" data-w="${s.present}%"></div></div>
      <div class="spct">${s.present}%</div>
    </div>`).join('');

  setTimeout(() => {
    el.querySelectorAll('.sfill').forEach(el => el.style.width = el.getAttribute('data-w'));
  }, 50);
}

/* ── Alerts Full Page ────────────────────────────────────────────────── */
async function loadAlertsPage() {
  const data = await api('/api/alerts');
  if (!data) return;
  const el = document.getElementById('alertFullFeed');
  if (!el) return;
  const icoMap = { critical: '🚨', warning: '⚠️', info: 'ℹ️', success: '✅' };
  el.innerHTML = data.map(a => `
    <div class="afi ${a.type}">
      <div class="afi-ico">${icoMap[a.type]}</div>
      <div class="afi-body">
        <div class="afi-title">${a.msg}</div>
        <div class="afi-detail">Auto-generated by AttendIQ monitoring engine</div>
        <span class="afi-badge ${a.type}">${a.type.toUpperCase()}</span>
      </div>
      <div class="afi-time">${a.time}</div>
    </div>`).join('');
}

/* ── Add/Edit/Delete Students ────────────────────────────────────────── */
let deleteStudentId = null;

function openAddModal() {
  document.getElementById('modalTitle').textContent = 'Add Student';
  document.getElementById('editStudentId').value = '';
  document.getElementById('fId').value = '';
  document.getElementById('fId').disabled = false;
  document.getElementById('fName').value = '';
  document.getElementById('fDept').value = 'CS';
  document.getElementById('fYear').value = '2';
  document.getElementById('fEmail').value = '';
  document.getElementById('fPhone').value = '';
  document.getElementById('fAttendance').value = '';
  document.getElementById('saveBtn').textContent = 'Save Student';
  document.getElementById('modalOverlay').classList.add('active');
  document.getElementById('studentModal').classList.add('active');
}

function openEditModal(s) {
  document.getElementById('modalTitle').textContent = 'Edit Student';
  document.getElementById('editStudentId').value = s.id;
  document.getElementById('fId').value = s.id;
  document.getElementById('fId').disabled = true;
  document.getElementById('fName').value = s.name;
  document.getElementById('fDept').value = s.dept;
  document.getElementById('fYear').value = s.year;
  document.getElementById('fEmail').value = s.email || '';
  document.getElementById('fPhone').value = s.phone || '';
  document.getElementById('fAttendance').value = s.attendance;
  document.getElementById('saveBtn').textContent = 'Update Student';
  document.getElementById('modalOverlay').classList.add('active');
  document.getElementById('studentModal').classList.add('active');
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('active');
  document.getElementById('studentModal').classList.remove('active');
}

function openDeleteModal(id, name) {
  deleteStudentId = id;
  document.getElementById('deleteStudentName').textContent = name;
  document.getElementById('deleteOverlay').classList.add('active');
  document.getElementById('deleteModal').classList.add('active');
  document.getElementById('confirmDeleteBtn').onclick = confirmDelete;
}

function closeDeleteModal() {
  document.getElementById('deleteOverlay').classList.remove('active');
  document.getElementById('deleteModal').classList.remove('active');
  deleteStudentId = null;
}

async function saveStudent() {
  const editId = document.getElementById('editStudentId').value;
  const data = {
    id: document.getElementById('fId').value.trim(),
    name: document.getElementById('fName').value.trim(),
    dept: document.getElementById('fDept').value.trim(),
    year: document.getElementById('fYear').value,
    email: document.getElementById('fEmail').value.trim(),
    phone: document.getElementById('fPhone').value.trim(),
    attendance: document.getElementById('fAttendance').value,
  };
  if (!data.name || !data.id || !data.attendance) {
    showToast('⚠️ Please fill all required fields'); return;
  }
  let res;
  if (editId) {
    res = await api(`/api/students/update/${editId}`, { method: 'PUT', body: JSON.stringify(data) });
  } else {
    res = await api('/api/students/add', { method: 'POST', body: JSON.stringify(data) });
  }
  if (res && res.success) {
    showToast('✅ ' + res.message);
    closeModal();
    loadStudents();
  } else {
    showToast('❌ ' + (res?.message || 'Something went wrong'));
  }
}

async function confirmDelete() {
  if (!deleteStudentId) return;
  const res = await api(`/api/students/delete/${deleteStudentId}`, { method: 'DELETE' });
  if (res && res.success) {
    showToast('🗑️ ' + res.message);
    closeDeleteModal();
    loadStudents();
  }
}