const anoSelect = document.getElementById('anoFiltro');
populateYearSelect(anoSelect);

async function carregarMeses() {
  const items = await apiGet(`/meses?ano=${anoSelect.value}`);
  const host = document.getElementById('cardsMeses');
  host.innerHTML = '';
  items.forEach(item => {
    const badgeClass = item.situacao === 'Tudo pago' ? 'success' : item.situacao === 'Sem lançamentos' ? 'info' : 'warn';
    const el = document.createElement('article');
    el.className = 'month-card';
    el.innerHTML = `
      <span class="badge ${badgeClass}">${item.situacao}</span>
      <h4>${item.mes_nome}</h4>
      <div class="kpi-line"><span>Ganhos: ${formatMoney(item.ganhos)}</span></div>
      <div class="kpi-line"><span>Gastos: ${formatMoney(item.gastos)}</span></div>
      <div class="kpi-line"><span>Pago: ${formatMoney(item.valor_pago)}</span></div>
      <div class="kpi-line"><span>Pendente: ${formatMoney(item.valor_pendente)}</span></div>
      <div class="kpi-line"><span>Invest.: ${formatMoney(item.investimentos)}</span></div>
    `;
    host.appendChild(el);
  });
}

anoSelect.addEventListener('change', carregarMeses);
carregarMeses().catch(err => toast(err.message));
