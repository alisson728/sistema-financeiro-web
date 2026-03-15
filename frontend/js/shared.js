const API = `${window.location.origin}/api`;

const MONTHS = [
  'Janeiro',
  'Fevereiro',
  'Março',
  'Abril',
  'Maio',
  'Junho',
  'Julho',
  'Agosto',
  'Setembro',
  'Outubro',
  'Novembro',
  'Dezembro'
];

function formatMoney(value) {
  return Number(value || 0).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  });
}

function formatNumber(value, decimals = 2) {
  return Number(value || 0).toLocaleString('pt-BR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
}

function populateYearSelect(
  select,
  start = new Date().getFullYear() - 5,
  end = new Date().getFullYear() + 5,
  selected = new Date().getFullYear()
) {
  if (!select) return;

  select.innerHTML = '';

  for (let year = start; year <= end; year++) {
    const option = document.createElement('option');
    option.value = year;
    option.textContent = year;

    if (Number(year) === Number(selected)) {
      option.selected = true;
    }

    select.appendChild(option);
  }
}

function populateMonthSelect(select, selected = new Date().getMonth() + 1, withAll = false) {
  if (!select) return;

  select.innerHTML = '';

  if (withAll) {
    const allOption = document.createElement('option');
    allOption.value = '';
    allOption.textContent = 'Todos os meses';
    select.appendChild(allOption);
  }

  MONTHS.forEach((name, idx) => {
    const option = document.createElement('option');
    option.value = idx + 1;
    option.textContent = name;

    if (Number(idx + 1) === Number(selected)) {
      option.selected = true;
    }

    select.appendChild(option);
  });
}

async function apiGet(path) {
  const response = await fetch(`${API}${path}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  });

  let data = null;
  try {
    data = await response.json();
  } catch (_) {
    data = null;
  }

  if (!response.ok) {
    throw new Error(data?.message || data?.error || 'Falha ao buscar dados da API.');
  }

  return data;
}

async function apiSend(path, method = 'POST', body = null) {
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json'
    }
  };

  if (body !== null) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`${API}${path}`, options);

  let data = null;
  try {
    data = await response.json();
  } catch (_) {
    data = null;
  }

  if (!response.ok) {
    throw new Error(data?.message || data?.error || 'Falha ao enviar dados para a API.');
  }

  return data;
}

function toast(message) {
  alert(message);
}

function getCurrentYear() {
  return new Date().getFullYear();
}

function getCurrentMonth() {
  return new Date().getMonth() + 1;
}

function getMonthName(monthNumber) {
  return MONTHS[Number(monthNumber) - 1] || '';
}

function qs(selector, scope = document) {
  return scope.querySelector(selector);
}

function qsa(selector, scope = document) {
  return Array.from(scope.querySelectorAll(selector));
}

function safeValue(value, fallback = 0) {
  if (value === null || value === undefined || value === '') return fallback;
  const n = Number(value);
  return Number.isNaN(n) ? fallback : n;
}
