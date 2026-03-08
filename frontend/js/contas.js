const filtroAno = document.getElementById('filtroAno');
const filtroMes = document.getElementById('filtroMes');
const filtroTipo = document.getElementById('filtroTipo');
const filtroStatus = document.getElementById('filtroStatus');
const busca = document.getElementById('busca');
const fixa = document.getElementById('fixa');
const recorrenciaArea = document.getElementById('recorrenciaArea');
const form = document.getElementById('formLancamento');
const previewBox = document.getElementById('previewNotificacoes');
const tbody = document.querySelector('#tabelaLancamentos tbody');
const heroMesConta = document.getElementById('heroMesConta');

populateYearSelect(filtroAno);
populateMonthSelect(filtroMes);
['mesInicio', 'mesFim'].forEach(id => populateMonthSelect(document.getElementById(id)));
['anoInicio', 'anoFim'].forEach(id => populateYearSelect(document.getElementById(id)));
document.getElementById('dataVencimento').value = new Date().toISOString().slice(0, 10);
heroMesConta.textContent = `${MONTHS[new Date().getMonth()]} ${new Date().getFullYear()}`;

fixa.addEventListener('change', () => recorrenciaArea.classList.toggle('hidden', !fixa.checked));

function atualizarHeroMes() {
  const mesIdx = Number(filtroMes.value || new Date().getMonth() + 1) - 1;
  heroMesConta.textContent = `${MONTHS[mesIdx]} ${filtroAno.value}`;
}

async function carregarLancamentos() {
  atualizarHeroMes();
  const qs = new URLSearchParams({
    ano: filtroAno.value,
    mes: filtroMes.value,
    tipo: filtroTipo.value,
    status: filtroStatus.value,
    q: busca.value || '',
  });
  const items = await apiGet(`/lancamentos?${qs.toString()}`);
  tbody.innerHTML = '';
  items.forEach(item => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${item.descricao}${item.fixa ? ' <span class="badge info">Recorrente</span>' : ''}</td>
      <td><span class="tag ${item.tipo}">${item.tipo}</span></td>
      <td>${item.data_vencimento}</td>
      <td>${formatMoney(item.valor)}</td>
      <td><span class="tag status-${item.status}">${item.status}</span></td>
      <td class="actions-row">
        ${item.status === 'pendente' ? `<button class="btn ghost" data-pay="${item.id}">Marcar pago</button>` : ''}
        <button class="btn ghost" data-del="${item.id}">Excluir</button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  if (!items.length) {
    tbody.innerHTML = '<tr><td colspan="6"><div class="notice">Nenhum lançamento encontrado para o filtro selecionado.</div></td></tr>';
  }
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const payload = {
    descricao: document.getElementById('descricao').value,
    tipo: document.getElementById('tipo').value,
    valor: document.getElementById('valor').value,
    data_vencimento: document.getElementById('dataVencimento').value,
    status: document.getElementById('status').value,
    fixa: fixa.checked,
    observacao: document.getElementById('observacao').value,
    mes_inicio: document.getElementById('mesInicio').value,
    ano_inicio: document.getElementById('anoInicio').value,
    mes_fim: document.getElementById('mesFim').value,
    ano_fim: document.getElementById('anoFim').value,
  };
  await apiSend('/lancamentos', 'POST', payload);
  toast('Lançamento salvo com sucesso.');
  form.reset();
  document.getElementById('dataVencimento').value = new Date().toISOString().slice(0, 10);
  recorrenciaArea.classList.add('hidden');
  await carregarLancamentos();
});

document.getElementById('btnPreviewNotif').addEventListener('click', async () => {
  const items = await apiGet('/notificacoes/preview');
  previewBox.innerHTML = items.length
    ? items.map(item => `<div class="preview-item"><strong>${item.descricao}</strong><div>${item.data_vencimento} • ${formatMoney(item.valor)}</div><div>${item.telefone_destino}</div><div>${item.mensagem}</div></div>`).join('')
    : '<div class="notice">Nenhuma conta vence em 2 dias.</div>';
});

tbody.addEventListener('click', async (e) => {
  const payId = e.target.getAttribute('data-pay');
  const delId = e.target.getAttribute('data-del');
  if (payId) {
    await apiSend(`/lancamentos/${payId}/pagar`, 'PUT');
    await carregarLancamentos();
  }
  if (delId) {
    await fetch(`${API}/lancamentos/${delId}`, { method: 'DELETE' });
    await carregarLancamentos();
  }
});

[filtroAno, filtroMes, filtroTipo, filtroStatus].forEach(el => el.addEventListener('change', carregarLancamentos));
busca.addEventListener('input', carregarLancamentos);
carregarLancamentos().catch(err => toast(err.message));
