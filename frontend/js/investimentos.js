let chartMeta;
const formProj = document.getElementById('formProjecao');

async function carregarProjecoes() {
  const items = await apiGet('/projecoes');
  const lista = document.getElementById('listaProjecoes');
  const resumo = document.getElementById('metaResumo');
  lista.innerHTML = '';

  if (!items.length) {
    lista.innerHTML = '<div class="notice">Nenhuma meta cadastrada.</div>';
    resumo.innerHTML = '<div class="notice">Cadastre uma meta para visualizar a projeção.</div>';
    return;
  }

  items.forEach(item => {
    const card = document.createElement('article');
    card.className = 'projection-card';
    card.innerHTML = `
      <span class="badge info">${item.progresso_percentual}%</span>
      <h4>${item.titulo}</h4>
      <div class="kpi-line"><span>Meta: ${formatMoney(item.valor_meta)}</span><span>Aporte: ${formatMoney(item.aporte_mensal)}</span></div>
      <div class="kpi-line"><span>Projetado: ${formatMoney(item.valor_projetado)}</span><span>Faltante: ${formatMoney(item.faltante)}</span></div>
      <div class="actions-row"><button class="btn ghost" data-del="${item.id}">Excluir</button></div>
    `;
    lista.appendChild(card);
  });

  const principal = items[0];
  resumo.innerHTML = `
    <div><strong>${principal.titulo}</strong></div>
    <div>Meta: ${formatMoney(principal.valor_meta)}</div>
    <div>Projetado: ${formatMoney(principal.valor_projetado)}</div>
    <div>Faltante: ${formatMoney(principal.faltante)}</div>
  `;
  renderMetaChart(principal);
}

function renderMetaChart(item) {
  const ctx = document.getElementById('chartMeta');
  if (chartMeta) chartMeta.destroy();
  chartMeta = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: ['Projetado', 'Faltante'],
      datasets: [{ data: [item.valor_projetado, item.faltante] }]
    }
  });
}

formProj.addEventListener('submit', async (e) => {
  e.preventDefault();
  await apiSend('/projecoes', 'POST', {
    titulo: document.getElementById('titulo').value,
    valor_meta: document.getElementById('valorMeta').value,
    aporte_mensal: document.getElementById('aporteMensal').value,
    rentabilidade_mensal: document.getElementById('rentabilidadeMensal').value,
    prazo_meses: document.getElementById('prazoMeses').value,
  });
  formProj.reset();
  await carregarProjecoes();
});

document.getElementById('listaProjecoes').addEventListener('click', async (e) => {
  const delId = e.target.getAttribute('data-del');
  if (!delId) return;
  await fetch(`${API}/projecoes/${delId}`, { method: 'DELETE' });
  await carregarProjecoes();
});

carregarProjecoes().catch(err => toast(err.message));
