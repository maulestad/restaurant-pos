const API = '/api';
const token = localStorage.getItem('token');
if (!token) location.href = '/';

document.getElementById('user-info').innerHTML =
  `<strong>${localStorage.getItem('username')}</strong><br><small>${localStorage.getItem('role')}</small>`;

let products = [];
let cart = [];
let inventoryOn = false;
let printMode = 'pdf';
let printAgentUrl = 'http://localhost:5000';

async function api(path, opts = {}) {
  opts.headers = { ...(opts.headers || {}), 'Authorization': `Bearer ${token}` };
  if (opts.body && !(opts.body instanceof URLSearchParams)) {
    opts.headers['Content-Type'] = 'application/json';
  }
  const res = await fetch(API + path, opts);
  if (res.status === 401) { logout(); throw new Error('No autorizado'); }
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
    if (view === 'orders') loadOrders();
    if (view === 'cash') loadCash();
  });
});

async function loadConfig() {
  try { inventoryOn = (await api('/inventory/status')).enabled; } catch {}
  try { printMode = (await api('/printing/mode')).mode; } catch {}
}

async function loadProducts() {
  products = await api('/products/');
  const grid = document.getElementById('products');
  grid.innerHTML = '';
  products.forEach(p => {
    const card = document.createElement('div');
    card.className = 'product-card';
    const stockBadge = (inventoryOn && p.track_stock)
      ? `<div class="stock ${p.stock <= p.min_stock ? 'low' : ''}">Stock: ${p.stock} ${p.unit}</div>`
      : '';
    card.innerHTML = `
      <div class="name">${p.name}</div>
      <div class="price">$${p.price.toFixed(2)}</div>
      ${stockBadge}
    `;
    card.onclick = () => addToCart(p);
    grid.appendChild(card);
  });
}

function addToCart(p) {
  const ex = cart.find(i => i.product_id === p.id);
  if (ex) ex.quantity++;
  else cart.push({ product_id: p.id, name: p.name, price: p.price, quantity: 1 });
  renderCart();
}

function renderCart() {
  const body = document.getElementById('cart-body');
  body.innerHTML = '';
  let total = 0;
  cart.forEach((item, idx) => {
    const sub = item.price * item.quantity;
    total += sub;
    body.innerHTML += `
      <tr>
        <td>${item.name}</td>
        <td>${item.quantity}</td>
        <td>$${sub.toFixed(2)}</td>
        <td><button onclick="removeItem(${idx})">✕</button></td>
      </tr>`;
  });
  document.getElementById('total').textContent = total.toFixed(2);
}

function removeItem(idx) { cart.splice(idx, 1); renderCart(); }

async function confirmSale() {
  if (cart.length === 0) return alert('El pedido está vacío');

  const cash = await api('/cash/current');
  if (!cash.open) {
    alert('Debes abrir tu caja antes de vender. Ve a "Mi caja".');
    return;
  }

  const table_number = document.getElementById('table_number').value || null;
  const payload = {
    items: cart.map(i => ({ product_id: i.product_id, quantity: i.quantity })),
    table_number: table_number ? parseInt(table_number) : null,
  };
  try {
    const sale = await api('/sales/', { method: 'POST', body: JSON.stringify(payload) });
    const result = await printTicket(sale);
    document.getElementById('msg').textContent =
      `✅ Venta #${sale.id} — $${sale.total.toFixed(2)} · ${result}`;
    cart = [];
    renderCart();
    document.getElementById('table_number').value = '';
  } catch (e) {
    alert('Error: ' + e.message);
  }
}

async function printTicket(sale) {
  if (printMode === 'pdf') {
    const res = await fetch(`${API}/printing/ticket/${sale.id}.pdf`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('No se pudo generar el PDF');
    const blob = await res.blob();
    window.open(URL.createObjectURL(blob), '_blank');
    return 'PDF abierto';
  }
  try {
    const res = await fetch(`${printAgentUrl}/print`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        header: `Restaurante Demo\nVenta #${sale.id}  Mesa: ${sale.table_number ?? '-'}`,
        items: sale.items.map(i => ({ name: i.product_name, price: i.subtotal })),
        total: sale.total,
      }),
    });
    if (!res.ok) throw new Error();
    return 'Ticket enviado';
  } catch {
    return '⚠️ Print Agent no disponible, venta registrada';
  }
}

async function loadOrders() {
  const sales = await api('/sales/my');
  document.getElementById('orders-body').innerHTML = sales.map(s => `
    <tr>
      <td>#${s.id}</td>
      <td>${s.table_number ?? '-'}</td>
      <td>$${s.total.toFixed(2)}</td>
      <td>${s.status}</td>
      <td>${new Date(s.created_at).toLocaleString()}</td>
      <td><button onclick="openTicket(${s.id})">🖨️</button></td>
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

async function loadCash() {
  const current = await api('/cash/current');
  const panel = document.getElementById('cash-panel');

  if (!current.open) {
    panel.innerHTML = `
      <div class="cash-box">
        <h3>Abrir caja</h3>
        <p>No tienes una caja abierta.</p>
        <label>Monto inicial en efectivo
          <input type="number" step="0.01" id="opening-amount" value="0" />
        </label>
        <label>Notas (opcional)
          <input type="text" id="opening-notes" />
        </label>
        <button class="btn-primary" onclick="openCash()">Abrir caja</button>
      </div>`;
  } else {
    const s = current.session;
    panel.innerHTML = `
      <div class="cash-box">
        <h3>Caja abierta desde ${new Date(s.opened_at).toLocaleString()}</h3>
        <div class="kpi" style="grid-template-columns:repeat(3,1fr)">
          <div class="kpi-card"><h3>Apertura</h3><p>$${s.opening_amount.toFixed(2)}</p></div>
          <div class="kpi-card"><h3>Ventas (${current.sales_count})</h3><p>$${current.total_sales.toFixed(2)}</p></div>
          <div class="kpi-card"><h3>Esperado en caja</h3><p>$${current.expected_amount.toFixed(2)}</p></div>
        </div>
        <hr style="margin:16px 0">
        <h3>Cerrar caja</h3>
        <label>Monto contado en efectivo
          <input type="number" step="0.01" id="closing-amount" value="${current.expected_amount.toFixed(2)}" />
        </label>
        <label>Notas (opcional)
          <input type="text" id="closing-notes" />
        </label>
        <button class="btn-primary" onclick="closeCash()">Cerrar caja</button>
      </div>`;
  }

  const history = await api('/cash/history');
  document.getElementById('cash-history-body').innerHTML = history.map(c => `
    <tr>
      <td>#${c.id}</td>
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

async function openCash() {
  const amount = parseFloat(document.getElementById('opening-amount').value) || 0;
  const notes = document.getElementById('opening-notes').value;
  await api('/cash/open', { method: 'POST', body: JSON.stringify({ opening_amount: amount, notes }) });
  loadCash();
}

async function closeCash() {
  const amount = parseFloat(document.getElementById('closing-amount').value) || 0;
  const notes = document.getElementById('closing-notes').value;
  if (!confirm('¿Cerrar la caja?')) return;
  await api('/cash/close', { method: 'POST', body: JSON.stringify({ closing_amount: amount, notes }) });
  loadCash();
}

function logout() { localStorage.clear(); location.href = '/'; }

(async () => {
  await loadBranding();
  await loadConfig();
  await loadProducts();
})();