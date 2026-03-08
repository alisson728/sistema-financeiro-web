from __future__ import annotations

from datetime import date, datetime, timedelta
from .db import get_db, get_config_map
from .whatsapp import MetaWhatsAppClient, build_due_reminder_text


def preview_due_notifications(target_date: date | None = None) -> list[dict]:
    cfg = get_config_map()
    due_date = target_date or (date.today() + timedelta(days=2))
    conn = get_db()
    rows = conn.execute(
        '''
        SELECT * FROM lancamentos
        WHERE status='pendente' AND data_vencimento=? AND tipo='gasto'
        ORDER BY data_vencimento, descricao
        ''',
        (due_date.isoformat(),),
    ).fetchall()

    items: list[dict] = []
    for row in rows:
        msg = build_due_reminder_text(row['descricao'], row['valor'], str(row['data_vencimento']))
        items.append(
            {
                'lancamento_id': row['id'],
                'descricao': row['descricao'],
                'valor': row['valor'],
                'data_vencimento': str(row['data_vencimento']),
                'telefone_destino': cfg.get('whatsapp_recipient_phone', ''),
                'mensagem': msg,
            }
        )
    conn.close()
    return items


def send_due_notifications(target_date: date | None = None) -> dict:
    cfg = get_config_map()
    if cfg.get('whatsapp_enabled') != '1':
        return {'ok': False, 'message': 'Integração WhatsApp desativada nas configurações.', 'sent': [], 'errors': []}

    required = [
        cfg.get('whatsapp_phone_number_id', '').strip(),
        cfg.get('whatsapp_access_token', '').strip(),
        cfg.get('whatsapp_template_name', '').strip(),
        cfg.get('whatsapp_recipient_phone', '').strip(),
    ]
    if not all(required):
        return {'ok': False, 'message': 'Preencha Phone Number ID, token, template e telefone de destino.', 'sent': [], 'errors': []}

    due_date = target_date or (date.today() + timedelta(days=2))
    client = MetaWhatsAppClient(
        api_version=cfg.get('whatsapp_api_version', 'v23.0'),
        phone_number_id=cfg['whatsapp_phone_number_id'],
        access_token=cfg['whatsapp_access_token'],
    )

    conn = get_db()
    rows = conn.execute(
        '''
        SELECT * FROM lancamentos
        WHERE status='pendente' AND data_vencimento=? AND tipo='gasto'
        ORDER BY data_vencimento, descricao
        ''',
        (due_date.isoformat(),),
    ).fetchall()

    sent: list[dict] = []
    errors: list[dict] = []
    for row in rows:
        already_sent = conn.execute(
            '''
            SELECT 1 FROM notificacoes
            WHERE lancamento_id=? AND data_programada=? AND status='enviado'
            LIMIT 1
            ''',
            (row['id'], due_date.isoformat()),
        ).fetchone()
        if already_sent:
            continue

        due_str = str(row['data_vencimento'])
        message = build_due_reminder_text(row['descricao'], row['valor'], due_str)
        body_params = [row['descricao'], f"{row['valor']:.2f}", due_str]
        result = client.send_template_message(
            to_number=cfg['whatsapp_recipient_phone'],
            template_name=cfg['whatsapp_template_name'],
            language_code=cfg.get('whatsapp_template_lang', 'pt_BR'),
            body_params=body_params,
        )
        now = datetime.now().isoformat(timespec='seconds')
        conn.execute(
            '''
            INSERT INTO notificacoes
            (lancamento_id, canal, telefone_destino, mensagem, data_programada, status, resposta_api, created_at, sent_at)
            VALUES (?, 'whatsapp', ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                row['id'],
                cfg['whatsapp_recipient_phone'],
                message,
                due_date.isoformat(),
                'enviado' if result.ok else 'erro',
                result.response_body,
                now,
                now if result.ok else None,
            ),
        )

        item = {
            'lancamento_id': row['id'],
            'descricao': row['descricao'],
            'status_code': result.status_code,
            'response': result.response_body,
        }
        if result.ok:
            sent.append(item)
        else:
            errors.append(item)

    conn.commit()
    conn.close()
    return {'ok': len(errors) == 0, 'message': 'Processamento concluído.', 'sent': sent, 'errors': errors}
