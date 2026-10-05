const API = '/api';
const token = localStorage.getItem('token');
const role = localStorage.getItem('role');
if (!token || (role !== 'gerente' && role !== 'sysadmin')) location.href = '/';

document.getElementById('user-info').innerHTML =
  `<strong>${localStorage.getItem('username')}</strong><br><small>${role}</small>`;

let chartByUser = null;
let chartDaily = null;

async function api(path, opts = {}) {
  opts.headers = { ...(opts.headers || {}), 'Authorization': `Bearer ${token}` };
  if (opts.body && !(opts.body instanceof URLSearchParams)) {
    opts.headers['Content-Type'] = 'application/json';
  }
  const res = await fetch(API + path, opts);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function loadBranding() {
  try {
    const b = await api('/branding/');
    document.getElementById('sidebar-brand').textContent = b.system_name || '🍽️ POS';
    if (b.primary_color) {
      document.documentElement.style.setProperty('--primary', b.primary_color);
    }
  } catch {}
}

document.querySelectorAll('.nav-item').forEach(el => {
  el.addEventListener('click', (e) => {
    e.preventDefault();
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    el.classList.add('active');
    const view = el.dataset.view;
    document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
    document.getElementById(`view-${view}`).classList.remove('hidden');
    if (view === 'dashboard') initDashboard();
    if (view === 'products') loadProducts();
    if (view === 'sales') loadSales();
    if (view === 'sellers') loadSellers();
    if (view === 'cash') loadCash();
  });
});

async function initDashboard() {
  await Promise.all([loadFilterUsers(), loadFilterCash()]);
  await loadDashboard();
}

async function loadFilterUsers() {
  const users = await api('/users/?role=vendedor');
  const sel = document.getElementById('filter-user');
  const current = sel.value;
  sel.innerHTML = '<option value="">Todos</option>' +
    users.map(u => `<option value="${u.id}">${u.full_name || u.username}</option>`).join('');
  sel.value = current;
}

async function loadFilterCash() {
  const cash = await api('/cash/all');
  const sel = document.getElementById('filter-cash');
  const current = sel.value;
  sel.innerHTML = '<option value="">Todas</option>' +
    cash.map(c => `<option value="${c.id}">#${c.id} · user ${c.user_id} · ${c.status}</option>`).join('');
  sel.value = current;
}

function resetFilters() {
  document.getElementById('filter-from').value = '';
  document.getElementById('filter-to').value = '';
  document.getElementById('filter-user').value = '';
  document.getElementById('filter-cash').value = '';
  loadDashboard();
}

async function loadDashboard() {
  const from = document.getElementById('filter-from').value;
  const to = document.getElementById('filter-to').value;
  const userId = document.getElementById('filter-user').value;
  const cashId = document.getElementById('filter-cash').value;

  const params = new URLSearchParams();
  if (from) params.append('date_from', from);
  if (to) params.append('date_to', to);
  if (userId) params.append('user_id', userId);
  if (cashId) params.append('cash_session_id', cashId);

  const sales = await api('/sales/filtered?' + params.toString());
  const total = sales.reduce((a, s) => a + s.total, 0);
  document.getElementById('total-sales').textContent = '$' + total.toFixed(2);
  document.getElementById('count-sales').textContent = sales.length;
  document.getElementById('avg-sales').textContent =
    '$' + (sales.length ? (total / sales.length).toFixed(2) : '0.00');

  document.getElementById('sales-body').innerHTML = sales.slice(0, 10).map(s => `
    <tr>
      <td>#${s.id}</td><td>${s.user_id}</td><td>${s.table_number ?? '-'}</td>
      <td>$${s.total.toFixed(2)}</td><td>${s.status}</td>
      <td>${new Date(s.created_at).toLocaleString()}</td>
      <td><button onclick="openTicket(${s.id})">🖨️</button></td>
    </tr>
  `).join('');

  const byUser = await api('/sales/summary/by-user?' + params.toString());
  const daily = await api('/sales/summary/daily?' + params.toString());
  renderUserChart(byUser);
  renderDailyChart(daily);
}

function renderUserChart(data) {
  const ctx = document.getElementById('chart-by-user');
  if (chartByUser) chartByUser.destroy();
  chartByUser = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.map(d => d.user_name),
      datasets: [{
        label: 'Total vendido ($)',
        data: data.map(d => d.total),
        backgroundColor: '#2563eb',
      }],
    },
    options: { responsive: true, plugins: { legend: { display: false } } },
  });
}

function renderDailyChart(data) {
  const ctx = document.getElementById('chart-daily');
  if (chartDaily) chartDaily.destroy();
  chartDaily = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.map(d => d.date),
      datasets: [{
        label: 'Ventas por día ($)',
        data: data.map(d => d.total),
        borderColor: '#16a34a',
        backgroundColor: 'rgba(22,163,74,0.15)',
        fill: true,
        tension: 0.3,
      }],
    },
    options: { responsive: true, plugins: { legend: { display: false } } },
  });
}

async function loadProducts() {
  const includeInactive = document.getElementById('show-inactive').checked;
  const products = await api(`/products/?include_inactive=${includeInactive}`);
  document.getElementById('products-body').innerHTML = products.map(p => `
    <tr>
      <td>${p.id}</td>
      <td>${p.name}</td>
      <td>${p.category}</td>
      <td>$${p.price.toFixed(2)}</td>
      <td>${p.track_stock ? p.stock + ' ' + p.unit : '—'}</td>
      <td>${p.active ? '✅' : '❌'}</td>
      <td>
        <button onclick='editProduct(${JSON.stringify(p).replace(/'/g, "&apos;")})'>✏️</button>
        ${p.active ? `<button onclick="deleteProduct(${p.id})">🚫</button>` : ''}
      </td>
    </tr>
  `).join('');
}

function openProductModal() {
  document.getElementById('modal-title').textContent = 'Nuevo producto';
  document.querySelector('#product-modal form').reset();
  document.getElementById('product-id').value = '';
  document.getElementById('p-active').checked = true;
  document.getElementById('product-modal').classList.remove('hidden');
}

function editProduct(p) {
  document.getElementById('modal-title').textContent = `Editar #${p.id}`;
  document.getElementById('product-id').value = p.id;
  document.getElementById('p-name').value = p.name;
  document.getElementById('p-price').value = p.price;
  document.getElementById('p-category').value = p.category;
  document.getElementById('p-unit').value = p.unit;
  document.getElementById('p-stock').value = p.stock;
  document.getElementById('p-min-stock').value = p.min_stock;
  document.getElementById('p-track-stock').checked = p.track_stock;
  document.getElementById('p-active').checked = p.active;
  document.getElementById('product-modal').classList.remove('hidden');
}

function closeProductModal() {
  document.getElementById('product-modal').classList.add('hidden');
}

async function saveProduct(e) {
  e.preventDefault();
  const id = document.getElementById('product-id').value;
  const payload = {
    name: document.getElementById('p-name').value,
    price: parseFloat(document.getElementById('p-price').value),
    category: document.getElementById('p-category').value || 'general',
    unit: document.getElementById('p-unit').value || 'unidad',
    stock: parseFloat(document.getElementById('p-stock').value) || 0,
    min_stock: parseFloat(document.getElementById('p-min-stock').value) || 0,
    track_stock: document.getElementById('p-track-stock').checked,
    active: document.getElementById('p-active').checked,
  };
  if (id) await api(`/products/${id}`, { method: 'PUT', body: JSON.stringify(payload) });
  else await api('/products/', { method: 'POST', body: JSON.stringify(payload) });
  closeProductModal();
  loadProducts();
}

async function deleteProduct(id) {
  if (!confirm('¿Desactivar este producto?')) return;
  await api(`/products/${id}`, { method: 'DELETE' });
  loadProducts();
}

async function loadSales() {
  const sales = await api('/sales/all');
  document.getElementById('sales-full-body').innerHTML = sales.map(s => `
    <tr>
      <td>#${s.id}</td><td>${s.user_id}</td><td>${s.table_number ?? '-'}</td>
      <td>$${s.total.toFixed(2)}</td><td>${s.status}</td>
      <td>${new Date(s.created_at).toLocaleString()}</td>
      <td><button onclick="openTicket(${s.id})">🖨️</button></td>
    </tr>
  `).join('');
}

async function loadSellers() {
  const sellers = await api('/users/?role=vendedor');
  document.getElementById('sellers-body').innerHTML = sellers.map(u => `
    <tr>
      <td>${u.id}</td>
      <td>${u.username}</td>
      <td>${u.full_name}</td>
      <td>${u.active ? '✅' : '❌'}</td>
      <td>
        <button onclick='editSeller(${JSON.stringify(u).replace(/'/g, "&apos;")})'>✏️</button>
        ${u.active ? `<button onclick="deactivateSeller(${u.id})">🚫</button>` : ''}
      </td>
    </tr>
  `).join('');
}

function openSellerModal() {
  document.getElementById('seller-modal-title').textContent = 'Nuevo vendedor';
  document.querySelector('#seller-modal form').reset();
  document.getElementById('s-id').value = '';
  document.getElementById('s-active').checked = true;
  document.getElementById('s-pwd-hint').textContent = '(obligatoria al crear)';
  document.getElementById('seller-modal').classList.remove('hidden');
}

function editSeller(u) {
  document.getElementById('seller-modal-title').textContent = `Editar ${u.username}`;
  document.getElementById('s-id').value = u.id;
  document.getElementById('s-username').value = u.username;
  document.getElementById('s-fullname').value = u.full_name;
  document.getElementById('s-password').value = '';
  document.getElementById('s-active').checked = u.active;
  document.getElementById('s-pwd-hint').textContent = '(dejar vacío para no cambiar)';
  document.getElementById('seller-modal').classList.remove('hidden');
}

function closeSellerModal() {
  document.getElementById('seller-modal').classList.add('hidden');
}

async function saveSeller(e) {
  e.preventDefault();
  const id = document.getElementById('s-id').value;
  const payload = {
    username: document.getElementById('s-username').value,
    full_name: document.getElementById('s-fullname').value,
    role: 'vendedor',
    active: document.getElementById('s-active').checked,
  };
  const pwd = document.getElementById('s-password').value;
  if (pwd) payload.password = pwd;
  else if (!id) return alert('La contraseña es obligatoria al crear');

  try {
    if (id) await api(`/users/${id}`, { method: 'PUT', body: JSON.stringify(payload) });
    else await api('/users/', { method: 'POST', body: JSON.stringify(payload) });
    closeSellerModal();
    loadSellers();
  } catch (err) {
    alert('Error: ' + err.message);
  }
}

async function deactivateSeller(id) {
  if (!confirm('¿Desactivar este vendedor?')) return;
  await api(`/users/${id}`, { method: 'DELETE' });
  loadSellers();
}

async function loadCash() {
  const cash = await api('/cash/all');
  document.getElementById('cash-body').innerHTML = cash.map(c => `
    <tr>
      <td>#${c.id}</td><td>${c.user_id}</td>
      <td>${new Date(c.opened_at).toLocaleString()}</td>
      <td>${c.closed_at ? new Date(c.closed_at).toLocaleString() : '—'}</td>
      <td>$${c.opening_amount.toFixed(2)}</td>
      <td>${c.expected_amount != null ? '$' + c.expected_amount.toFixed(2) : '—'}</td>
      <td>${c.closing_amount != null ? '$' + c.closing_amount.toFixed(2) : '—'}</td>
      <td style="color:${c.difference == null ? '#666' : (Math.abs(c.difference) < 0.01 ? '#16a34a' : '#ef4444')}">
        ${c.difference != null ? '$' + c.difference.toFixed(2) : '—'}
      </td>
      <td>${c.status === 'open' ? '🟢 Abierta' : '🔴 Cerrada'}</td>
    </tr>
  `).join('');
}

async function openTicket(saleId) {
  const res = await fetch(`${API}/printing/ticket/${saleId}.pdf`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  if (!res.ok) return alert('No se pudo generar el PDF');
  const blob = await res.blob();
  window.open(URL.createObjectURL(blob), '_blank');
}

function logout() { localStorage.clear(); location.href = '/'; }

loadBranding();
initDashboard();