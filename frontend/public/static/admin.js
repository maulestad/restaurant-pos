const API = '/api';
const token = localStorage.getItem('token');
if (!token || localStorage.getItem('role') !== 'sysadmin') location.href = '/';

document.getElementById('user-info').innerHTML =
  `<strong>${localStorage.getItem('username')}</strong><br><small>sysadmin</small>`;

async function api(path, opts = {}) {
  opts.headers = { ...(opts.headers || {}), 'Authorization': `Bearer ${token}` };
  if (opts.body && !(opts.body instanceof URLSearchParams)) {
    opts.headers['Content-Type'] = 'application/json';
  }
  const res = await fetch(API + path, opts);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

document.querySelectorAll('.nav-item').forEach(el => {
  el.addEventListener('click', (e) => {
    e.preventDefault();
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    el.classList.add('active');
    const view = el.dataset.view;
    document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
    document.getElementById(`view-${view}`).classList.remove('hidden');
    if (view === 'features') loadFeatures();
    if (view === 'printing') loadPrintingSettings();
    if (view === 'users') loadUsers();
    if (view === 'branding') loadBranding();
  });
});

/* Features */
async function loadFeatures() {
  const features = await api('/admin/features');
  document.getElementById('features').innerHTML = features.map(f => `
    <div class="feature-item">
      <div>
        <strong>${f.name}</strong><br>
        <small style="color:#6b7280">${f.description}</small>
      </div>
      <label class="switch">
        <input type="checkbox" ${f.enabled ? 'checked' : ''} onchange="toggleFeature('${f.name}')">
        <span class="slider"></span>
      </label>
    </div>
  `).join('');
}
async function toggleFeature(name) {
  await api(`/admin/features/${name}/toggle`, { method: 'POST' });
  loadFeatures();
}

/* Impresión */
async function loadPrintingSettings() {
  const settings = await api('/admin/settings');
  const map = Object.fromEntries(settings.map(s => [s.key, s]));
  const mode = map.printer_mode?.value || 'pdf';
  const agentUrl = map.print_agent_url?.value || 'http://localhost:5000';
  const restName = map.restaurant_name?.value || 'Restaurante Demo';

  document.getElementById('printing-settings').innerHTML = `
    <div class="cash-box">
      <label>Modo de impresión
        <select id="printer_mode">
          <option value="pdf" ${mode === 'pdf' ? 'selected' : ''}>PDF</option>
          <option value="escpos_direct" ${mode === 'escpos_direct' ? 'selected' : ''}>Térmica directa</option>
        </select>
      </label>
      <label>URL del Print Agent
        <input id="print_agent_url" value="${agentUrl}" />
      </label>
      <label>Nombre del restaurante en ticket
        <input id="restaurant_name" value="${restName}" />
      </label>
      <button class="btn-primary" onclick="savePrintingSettings()">Guardar</button>
      <p id="printing-msg" style="color:#16a34a"></p>
    </div>`;
}
async function savePrintingSettings() {
  const m = document.getElementById('printer_mode').value;
  const u = document.getElementById('print_agent_url').value;
  const n = document.getElementById('restaurant_name').value;
  await api(`/admin/settings/printer_mode?value=${encodeURIComponent(m)}`, { method: 'POST' });
  await api(`/admin/settings/print_agent_url?value=${encodeURIComponent(u)}`, { method: 'POST' });
  await api(`/admin/settings/restaurant_name?value=${encodeURIComponent(n)}`, { method: 'POST' });
  document.getElementById('printing-msg').textContent = '✅ Guardado';
}

/* Usuarios */
async function loadUsers() {
  const users = await api('/users/');
  document.getElementById('users-body').innerHTML = users.map(u => `
    <tr>
      <td>${u.id}</td>
      <td>${u.username}</td>
      <td>${u.full_name}</td>
      <td>${u.role}</td>
      <td>${u.active ? '✅' : '❌'}</td>
      <td>
        <button onclick='editUser(${JSON.stringify(u).replace(/'/g, "&apos;")})'>✏️</button>
        ${u.active ? `<button onclick="deactivateUser(${u.id})">🚫</button>` : ''}
      </td>
    </tr>
  `).join('');
}

function openUserModal() {
  document.getElementById('user-modal-title').textContent = 'Nuevo usuario';
  document.getElementById('u-id').value = '';
  document.getElementById('u-username').value = '';
  document.getElementById('u-fullname').value = '';
  document.getElementById('u-password').value = '';
  document.getElementById('u-role').value = 'vendedor';
  document.getElementById('u-active').checked = true;
  document.getElementById('u-pwd-hint').textContent = '(obligatoria al crear)';
  document.getElementById('user-modal').classList.remove('hidden');
}

function editUser(u) {
  document.getElementById('user-modal-title').textContent = `Editar ${u.username}`;
  document.getElementById('u-id').value = u.id;
  document.getElementById('u-username').value = u.username;
  document.getElementById('u-fullname').value = u.full_name;
  document.getElementById('u-password').value = '';
  document.getElementById('u-role').value = u.role;
  document.getElementById('u-active').checked = u.active;
  document.getElementById('u-pwd-hint').textContent = '(dejar vacío para no cambiar)';
  document.getElementById('user-modal').classList.remove('hidden');
}

function closeUserModal() {
  document.getElementById('user-modal').classList.add('hidden');
}

async function saveUser(e) {
  e.preventDefault();
  const id = document.getElementById('u-id').value;
  const payload = {
    username: document.getElementById('u-username').value,
    full_name: document.getElementById('u-fullname').value,
    role: document.getElementById('u-role').value,
    active: document.getElementById('u-active').checked,
  };
  const pwd = document.getElementById('u-password').value;
  if (pwd) payload.password = pwd;
  else if (!id) return alert('La contraseña es obligatoria al crear');

  try {
    if (id) await api(`/users/${id}`, { method: 'PUT', body: JSON.stringify(payload) });
    else await api('/users/', { method: 'POST', body: JSON.stringify(payload) });
    closeUserModal();
    loadUsers();
  } catch (err) {
    alert('Error: ' + err.message);
  }
}

async function deactivateUser(id) {
  if (!confirm('¿Desactivar este usuario?')) return;
  await api(`/users/${id}`, { method: 'DELETE' });
  loadUsers();
}

/* Branding */
let currentLogo = '';

async function loadBranding() {
  const b = await api('/branding/');
  document.getElementById('brand-name').value = b.system_name;
  document.getElementById('brand-color').value = b.primary_color;
  currentLogo = b.logo_base64 || '';
  renderBrandPreview();
}

function renderBrandPreview() {
  const div = document.getElementById('brand-preview');
  div.innerHTML = currentLogo
    ? `<img src="${currentLogo}" style="max-height:80px;border-radius:8px" />`
    : '<em>Sin logo</em>';
}

document.getElementById('brand-logo-file').addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (!file) return;
  if (file.size > 200 * 1024) return alert('El logo debe pesar menos de 200KB');
  const reader = new FileReader();
  reader.onload = () => {
    currentLogo = reader.result;
    renderBrandPreview();
  };
  reader.readAsDataURL(file);
});

async function saveBranding() {
  const payload = {
    system_name: document.getElementById('brand-name').value,
    primary_color: document.getElementById('brand-color').value,
    logo_base64: currentLogo,
  };
  await api('/branding/', { method: 'PUT', body: JSON.stringify(payload) });
  document.getElementById('brand-msg').textContent = '✅ Guardado';
  document.getElementById('sidebar-brand').textContent = payload.system_name;
}

function logout() { localStorage.clear(); location.href = '/'; }

loadFeatures();