let chartFinanceiro;
let chartProjecao;

const anoFiltro = document.getElementById('anoFiltro');
const mesFiltro = document.getElementById('mesFiltro');

populateYearSelect(anoFiltro);
populateMonthSelect(mesFiltro);

async function carregarDashboard() {
  const ano = anoFiltro.value;
  const mes = mesFiltro.value;
  const data = await apiGet(`/dashboard?ano=${ano}&mes=${mes}`);

  document.getElementById('cardPagar').textContent = formatMoney(data.totais.contas_a_pagar);
  document.getElementById('cardPago').textContent = formatMoney(data.totais.contas_pagas);
  document.getElementById('cardInvestimento').textContent = formatMoney(data.totais.investimento);
  document.getElementById('cardGanhos').textContent = formatMoney(data.totais.ganhos);
  document.getElementById('cardSaldoHero').textContent = formatMoney(data.totais.saldo_mes);
  document.getElementById('cardRiscoHero').textContent = formatMoney(data.totais.contas_a_pagar);

  renderChartFinanceiro(data.totais);
  renderProjection(data.projecao_principal);
  renderMonths(data.meses);
}

function renderChartFinanceiro(totais) {
  const ctx = document.getElementById('chartFinanceiro');
  if (chartFinanceiro) chartFinanceiro.destroy();
  chartFinanceiro = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Ganhos', 'Contas pagas', 'Contas a pagar', 'Investimentos'],
      datasets: [{
        data: [totais.ganhos, totais.contas_pagas, totais.contas_a_pagar, totais.investimento],
        borderWidth: 0,
        hoverOffset: 6,
      }]
    },
    options: {
      cutout: '68%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#a4abc0', padding: 18, usePointStyle: true, pointStyle: 'circle' }
        }
      }
    }
  });
}

function renderProjection(item) {
  const summary = document.getElementById('projectionSummary');
  const ctx = document.getElementById('chartProjecao');
  if (chartProjecao) chartProjecao.destroy();

  if (!item) {
    summary.innerHTML = '<div class="notice">Nenhuma projeção cadastrada ainda.</div>';
    return;
  }

  summary.innerHTML = `
    <div><strong>${item.titulo}</strong></div>
    <div>Meta alvo: ${formatMoney(item.valor_meta)}</div>
    <div>Projetado: ${formatMoney(item.valor_projetado)}</div>
    <div>Faltante: ${formatMoney(item.faltante)}</div>
    <div>Progresso visual: ${item.progresso_percentual}%</div>
  `;

  chartProjecao = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Projetado', 'Faltante'],
      datasets: [{ data: [item.valor_projetado, item.faltante], borderWidth: 0, hoverOffset: 6 }]
    },
    options: {
      cutout: '68%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#a4abc0', padding: 18, usePointStyle: true, pointStyle: 'circle' }
        }
      }
    }
  });
}

function renderMonths(items) {
  const host = document.getElementById('listaMeses');
  host.innerHTML = '';
  items.forEach(item => {
    const badgeClass = item.situacao === 'Tudo pago' ? 'success' : item.situacao === 'Sem lançamentos' ? 'info' : 'warn';
    const el = document.createElement('article');
    el.className = 'month-card';
    el.innerHTML = `
      <span class="badge ${badgeClass}">${item.situacao}</span>
      <h4>${item.mes_nome}</h4>
      <div class="kpi-line"><span>Pendente: ${formatMoney(item.valor_pendente)}</span></div>
      <div class="kpi-line"><span>Pago: ${formatMoney(item.valor_pago)}</span></div>
      <div class="kpi-line"><span>Ganhos: ${formatMoney(item.ganhos)}</span></div>
      <div class="kpi-line"><span>Invest.: ${formatMoney(item.investimentos)}</span></div>
    `;
    host.appendChild(el);
  });
}

anoFiltro.addEventListener('change', carregarDashboard);
mesFiltro.addEventListener('change', carregarDashboard);
carregarDashboard().catch(err => toast(err.message));
