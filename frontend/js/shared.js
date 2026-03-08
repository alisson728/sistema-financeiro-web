const API = '/api';
const MONTHS = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'];

function formatMoney(value) {
  return Number(value || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function populateYearSelect(select, start = new Date().getFullYear() - 5, end = new Date().getFullYear() + 5, selected = new Date().getFullYear()) {
  if (!select) return;
  select.innerHTML = '';
  for (let year = start; year <= end; year++) {
    const option = document.createElement('option');
    option.value = year;
    option.textContent = year;
    if (year === selected) option.selected = true;
    select.appendChild(option);
  }
}

function populateMonthSelect(select, selected = new Date().getMonth() + 1, withAll = false) {
  if (!select) return;
  select.innerHTML = '';
  if (withAll) {
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = 'Todos os meses';
    select.appendChild(opt);
  }
  MONTHS.forEach((name, idx) => {
    const option = document.createElement('option');
    option.value = idx + 1;
    option.textContent = name;
    if (idx + 1 === selected) option.selected = true;
    select.appendChild(option);
  });
}

async function apiGet(path) {
  const resp = await fetch(`${API}${path}`);
  if (!resp.ok) throw new Error('Falha na API');
  return resp.json();
}

async function apiSend(path, method = 'POST', body = null) {
  const resp = await fetch(`${API}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : null,
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.message || 'Falha na API');
  return data;
}

function toast(message) {
  let host = document.querySelector('.toast-host');
  if (!host) {
    host = document.createElement('div');
    host.className = 'toast-host';
    document.body.appendChild(host);
  }

  const item = document.createElement('div');
  item.className = 'toast-item';
  item.textContent = message;
  host.appendChild(item);

  requestAnimationFrame(() => item.classList.add('show'));
  setTimeout(() => {
    item.classList.remove('show');
    setTimeout(() => item.remove(), 260);
  }, 2600);
}
