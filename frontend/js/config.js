const formConfig = document.getElementById('formConfig');

async function carregarConfig() {
  const cfg = await apiGet('/config');
  document.getElementById('whatsappEnabled').checked = cfg.whatsapp_enabled === '1';
  document.getElementById('phoneNumberId').value = cfg.whatsapp_phone_number_id || '';
  document.getElementById('apiVersion').value = cfg.whatsapp_api_version || 'v23.0';
  document.getElementById('accessToken').value = cfg.whatsapp_access_token || '';
  document.getElementById('templateName').value = cfg.whatsapp_template_name || 'financeiro_vencimento';
  document.getElementById('templateLang').value = cfg.whatsapp_template_lang || 'pt_BR';
  document.getElementById('recipientPhone').value = cfg.whatsapp_recipient_phone || '+5547997573257';
}

formConfig.addEventListener('submit', async (e) => {
  e.preventDefault();
  await apiSend('/config', 'POST', {
    whatsapp_enabled: document.getElementById('whatsappEnabled').checked ? '1' : '0',
    whatsapp_phone_number_id: document.getElementById('phoneNumberId').value,
    whatsapp_api_version: document.getElementById('apiVersion').value,
    whatsapp_access_token: document.getElementById('accessToken').value,
    whatsapp_template_name: document.getElementById('templateName').value,
    whatsapp_template_lang: document.getElementById('templateLang').value,
    whatsapp_recipient_phone: document.getElementById('recipientPhone').value,
  });
  toast('Configuração salva.');
});

async function carregarPreview() {
  const items = await apiGet('/notificacoes/preview');
  const host = document.getElementById('previewArea');
  host.innerHTML = items.length
    ? items.map(item => `<div class="preview-item"><strong>${item.descricao}</strong><div>${item.data_vencimento}</div><div>${formatMoney(item.valor)}</div><div>${item.telefone_destino}</div><div>${item.mensagem}</div></div>`).join('')
    : '<div class="notice">Nenhuma conta vence em 2 dias.</div>';
}

async function carregarLogs() {
  const items = await apiGet('/notificacoes/logs');
  const host = document.getElementById('logsArea');
  host.innerHTML = items.length
    ? items.map(item => `<div class="preview-item"><strong>${item.telefone_destino}</strong><div>${item.data_programada} • ${item.status}</div><div>${item.mensagem}</div><small>${item.resposta_api || ''}</small></div>`).join('')
    : '<div class="notice">Nenhum log ainda.</div>';
}

document.getElementById('btnPreview').addEventListener('click', carregarPreview);
document.getElementById('btnLogs').addEventListener('click', carregarLogs);
document.getElementById('btnDispararAgora').addEventListener('click', async () => {
  const result = await apiSend('/notificacoes/disparar', 'POST');
  toast(`Enviadas: ${result.sent.length} | Erros: ${result.errors.length}`);
  await carregarLogs();
});

carregarConfig().then(carregarPreview).then(carregarLogs).catch(err => toast(err.message));
