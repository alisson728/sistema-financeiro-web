from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import os
import threading
import time

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from .db import get_db, get_config_map, init_db, insert_and_return_id, set_config_values
from .reminders import preview_due_notifications, send_due_notifications
from .utils import MONTH_NAMES, adjust_due_date, month_iter, now_iso, parse_date, recurrence_group

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / 'frontend'

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path='')
CORS(app)
init_db()
_background_started = False


def as_dicts(rows):
    return [dict(r) for r in rows]


def currency(num: float) -> float:
    return round(float(num or 0), 2)


def month_summary_row(year: int, month: int) -> dict:
    conn = get_db()
    row = conn.execute(
        '''
        SELECT
            SUM(CASE WHEN tipo='ganho' THEN valor ELSE 0 END) AS ganhos,
            SUM(CASE WHEN tipo='gasto' THEN valor ELSE 0 END) AS gastos,
            SUM(CASE WHEN tipo='investimento' THEN valor ELSE 0 END) AS investimentos,
            SUM(CASE WHEN tipo='gasto' AND status='pago' THEN valor ELSE 0 END) AS gastos_pagos,
            SUM(CASE WHEN tipo='gasto' AND status='pendente' THEN valor ELSE 0 END) AS gastos_pendentes
        FROM lancamentos
        WHERE competencia_ano=? AND competencia_mes=?
        ''',
        (year, month),
    ).fetchone()
    conn.close()
    return {
        'ganhos': currency(row['ganhos']),
        'gastos': currency(row['gastos']),
        'investimentos': currency(row['investimentos']),
        'gastos_pagos': currency(row['gastos_pagos']),
        'gastos_pendentes': currency(row['gastos_pendentes']),
    }


def build_month_status(year: int) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        '''
        SELECT
            competencia_mes,
            SUM(CASE WHEN tipo='ganho' THEN valor ELSE 0 END) AS ganhos,
            SUM(CASE WHEN tipo='gasto' THEN valor ELSE 0 END) AS gastos,
            SUM(CASE WHEN tipo='investimento' THEN valor ELSE 0 END) AS investimentos,
            SUM(CASE WHEN tipo='gasto' AND status='pago' THEN valor ELSE 0 END) AS pagos,
            SUM(CASE WHEN tipo='gasto' AND status='pendente' THEN valor ELSE 0 END) AS pendente
        FROM lancamentos
        WHERE competencia_ano=?
        GROUP BY competencia_mes
        ORDER BY competencia_mes
        ''',
        (year,),
    ).fetchall()
    conn.close()

    by_month = {row['competencia_mes']: row for row in rows}
    items = []
    for month in range(1, 13):
        row = by_month.get(month)
        pendente = currency(row['pendente']) if row else 0.0
        pagos = currency(row['pagos']) if row else 0.0
        ganhos = currency(row['ganhos']) if row else 0.0
        investimentos = currency(row['investimentos']) if row else 0.0
        gastos = currency(row['gastos']) if row else 0.0

        if gastos == 0 and ganhos == 0 and investimentos == 0:
            situacao = 'Sem lançamentos'
        elif pendente <= 0:
            situacao = 'Tudo pago'
        else:
            situacao = 'Conta pendente'

        items.append(
            {
                'mes': month,
                'mes_nome': MONTH_NAMES[month - 1],
                'situacao': situacao,
                'valor_pendente': pendente,
                'valor_pago': pagos,
                'ganhos': ganhos,
                'gastos': gastos,
                'investimentos': investimentos,
            }
        )
    return items


def compute_investment_projection(proj: dict) -> dict:
    saldo = 0.0
    for _ in range(int(proj['prazo_meses'])):
        saldo = (saldo + float(proj['aporte_mensal'])) * (1 + (float(proj['rentabilidade_mensal']) / 100.0))
    meta = float(proj['valor_meta'])
    progresso = 0 if meta <= 0 else min(100.0, (saldo / meta) * 100.0)
    return {
        **proj,
        'valor_projetado': round(saldo, 2),
        'faltante': round(max(meta - saldo, 0), 2),
        'progresso_percentual': round(progresso, 2),
    }


@app.get('/')
def root():
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.get('/<path:path>')
def static_proxy(path: str):
    file_path = FRONTEND_DIR / path
    if file_path.exists() and file_path.is_file():
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.get('/api/dashboard')
def api_dashboard():
    today = date.today()
    year = int(request.args.get('ano', today.year))
    month = int(request.args.get('mes', today.month))

    resumo = month_summary_row(year, month)
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM projecoes_investimento ORDER BY updated_at DESC, id DESC'
    ).fetchall()
    conn.close()
    projections = [compute_investment_projection(dict(r)) for r in rows]
    principal = projections[0] if projections else None

    return jsonify(
        {
            'ano': year,
            'mes': month,
            'totais': {
                'contas_a_pagar': resumo['gastos_pendentes'],
                'contas_pagas': resumo['gastos_pagos'],
                'investimento': resumo['investimentos'],
                'ganhos': resumo['ganhos'],
                'saldo_mes': round(resumo['ganhos'] - resumo['gastos'] - resumo['investimentos'], 2),
            },
            'meses': build_month_status(year),
            'projecao_principal': principal,
        }
    )


@app.get('/api/lancamentos')
def api_lancamentos_list():
    today = date.today()
    year = int(request.args.get('ano', today.year))
    month = int(request.args.get('mes', today.month))
    tipo = request.args.get('tipo', '').strip()
    status = request.args.get('status', '').strip()
    q = request.args.get('q', '').strip().lower()

    query = 'SELECT * FROM lancamentos WHERE competencia_ano=? AND competencia_mes=?'
    params: list = [year, month]
    if tipo:
        query += ' AND tipo=?'
        params.append(tipo)
    if status:
        query += ' AND status=?'
        params.append(status)
    if q:
        query += ' AND LOWER(descricao) LIKE ?'
        params.append(f'%{q}%')
    query += ' ORDER BY data_vencimento ASC, id DESC'

    conn = get_db()
    rows = conn.execute(query, tuple(params)).fetchall()
    conn.close()
    return jsonify(as_dicts(rows))


@app.post('/api/lancamentos')
def api_lancamentos_create():
    data = request.get_json(force=True)
    descricao = data['descricao'].strip()
    tipo = data['tipo']
    valor = float(data['valor'])
    vencimento_base = parse_date(data['data_vencimento'])
    fixa = bool(data.get('fixa', False))
    observacao = data.get('observacao', '').strip()
    status = data.get('status', 'pendente')

    conn = get_db()
    now = now_iso()

    if fixa:
        start_month = int(data['mes_inicio'])
        start_year = int(data['ano_inicio'])
        end_month = int(data['mes_fim'])
        end_year = int(data['ano_fim'])
        group = recurrence_group()
        created_ids = []
        for year, month in month_iter(start_year, start_month, end_year, end_month):
            due = adjust_due_date(vencimento_base, year, month)
            new_id = insert_and_return_id(
                conn,
                '''
                INSERT INTO lancamentos
                (descricao, tipo, valor, data_vencimento, status, fixa, competencia_mes, competencia_ano, recorrencia_grupo, observacao, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (descricao, tipo, valor, due, status, True, month, year, group, observacao, now, now),
            )
            created_ids.append(new_id)
        conn.commit()
        conn.close()
        return jsonify({'ok': True, 'created_ids': created_ids, 'recorrencia_grupo': group})

    new_id = insert_and_return_id(
        conn,
        '''
        INSERT INTO lancamentos
        (descricao, tipo, valor, data_vencimento, status, fixa, competencia_mes, competencia_ano, recorrencia_grupo, observacao, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?)
        ''',
        (descricao, tipo, valor, vencimento_base.isoformat(), status, False, vencimento_base.month, vencimento_base.year, observacao, now, now),
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'id': new_id})


@app.put('/api/lancamentos/<int:item_id>')
def api_lancamento_update(item_id: int):
    data = request.get_json(force=True)
    allowed = {'descricao', 'tipo', 'valor', 'data_vencimento', 'status', 'observacao'}
    updates = []
    params: list = []
    for key, value in data.items():
        if key in allowed:
            updates.append(f'{key}=?')
            params.append(value)
    if not updates:
        return jsonify({'ok': False, 'message': 'Nada para atualizar.'}), 400
    updates.append('updated_at=?')
    params.append(now_iso())
    params.append(item_id)

    conn = get_db()
    conn.execute(f'UPDATE lancamentos SET {", ".join(updates)} WHERE id=?', tuple(params))
    if 'data_vencimento' in data:
        dt = parse_date(data['data_vencimento'])
        conn.execute(
            'UPDATE lancamentos SET competencia_mes=?, competencia_ano=? WHERE id=?',
            (dt.month, dt.year, item_id),
        )
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


@app.put('/api/lancamentos/<int:item_id>/pagar')
def api_lancamento_pay(item_id: int):
    conn = get_db()
    conn.execute('UPDATE lancamentos SET status=? , updated_at=? WHERE id=?', ('pago', now_iso(), item_id))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


@app.delete('/api/lancamentos/<int:item_id>')
def api_lancamento_delete(item_id: int):
    conn = get_db()
    conn.execute('DELETE FROM lancamentos WHERE id=?', (item_id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


@app.get('/api/projecoes')
def api_projecoes_list():
    conn = get_db()
    rows = conn.execute('SELECT * FROM projecoes_investimento ORDER BY updated_at DESC, id DESC').fetchall()
    conn.close()
    payload = [compute_investment_projection(dict(r)) for r in rows]
    return jsonify(payload)


@app.post('/api/projecoes')
def api_projecoes_create():
    data = request.get_json(force=True)
    now = now_iso()
    conn = get_db()
    new_id = insert_and_return_id(
        conn,
        '''
        INSERT INTO projecoes_investimento
        (titulo, valor_meta, aporte_mensal, rentabilidade_mensal, prazo_meses, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            data['titulo'].strip(),
            float(data['valor_meta']),
            float(data['aporte_mensal']),
            float(data['rentabilidade_mensal']),
            int(data['prazo_meses']),
            now,
            now,
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'id': new_id})


@app.delete('/api/projecoes/<int:item_id>')
def api_projecao_delete(item_id: int):
    conn = get_db()
    conn.execute('DELETE FROM projecoes_investimento WHERE id=?', (item_id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


@app.get('/api/meses')
def api_meses():
    year = int(request.args.get('ano', date.today().year))
    return jsonify(build_month_status(year))


@app.get('/api/config')
def api_config_get():
    return jsonify(get_config_map())


@app.post('/api/config')
def api_config_save():
    data = request.get_json(force=True)
    set_config_values({k: v for k, v in data.items() if v is not None})
    return jsonify({'ok': True})


@app.get('/api/notificacoes/preview')
def api_notif_preview():
    return jsonify(preview_due_notifications())


@app.post('/api/notificacoes/disparar')
def api_notif_send():
    return jsonify(send_due_notifications())


@app.get('/api/notificacoes/logs')
def api_notif_logs():
    conn = get_db()
    rows = conn.execute('SELECT * FROM notificacoes ORDER BY id DESC LIMIT 50').fetchall()
    conn.close()
    return jsonify(as_dicts(rows))


@app.get('/api/health')
def api_health():
    return jsonify({'ok': True, 'timestamp': now_iso()})


def background_worker() -> None:
    while True:
        try:
            cfg = get_config_map()
            if cfg.get('whatsapp_enabled') == '1':
                now = datetime.now()
                if now.hour in (8, 9):
                    send_due_notifications()
        except Exception:
            pass
        time.sleep(3600)


def start_background_worker() -> None:
    global _background_started
    if _background_started:
        return
    if os.getenv('RUN_REMINDER_THREAD', '1') != '1':
        return
    t = threading.Thread(target=background_worker, daemon=True)
    t.start()
    _background_started = True


start_background_worker()


if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_DEBUG', '0') == '1')
