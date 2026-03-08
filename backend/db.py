from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SQLITE_PATH = BASE_DIR / 'financeiro.db'
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}')

_IS_POSTGRES = DATABASE_URL.startswith(('postgres://', 'postgresql://'))

if _IS_POSTGRES:
    import psycopg
    from psycopg.rows import dict_row
else:
    psycopg = None
    dict_row = None


class DBConnection:
    def __init__(self, conn: Any, backend: str):
        self.conn = conn
        self.backend = backend

    def execute(self, sql: str, params: tuple | list | None = None):
        if params is None:
            params = ()
        sql = adapt_sql(sql, self.backend)
        return self.conn.execute(sql, params)

    def commit(self) -> None:
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


def is_postgres() -> bool:
    return _IS_POSTGRES


def get_db() -> DBConnection:
    if _IS_POSTGRES:
        conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
        return DBConnection(conn, 'postgres')

    sqlite_path = DATABASE_URL.removeprefix('sqlite:///') if DATABASE_URL.startswith('sqlite:///') else str(DEFAULT_SQLITE_PATH)
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    return DBConnection(conn, 'sqlite')


def adapt_sql(sql: str, backend: str) -> str:
    sql = sql.strip()
    if backend == 'postgres':
        sql = sql.replace('datetime("now")', 'CURRENT_TIMESTAMP')
        sql = sql.replace("datetime('now')", 'CURRENT_TIMESTAMP')
        sql = sql.replace('INSERT OR IGNORE', 'INSERT INTO')
        sql = re.sub(r'\?', '%s', sql)
    return sql


def insert_and_return_id(conn: DBConnection, sql: str, params: tuple | list | None = None, id_column: str = 'id') -> int:
    params = params or ()
    if conn.backend == 'postgres':
        if 'RETURNING' not in sql.upper():
            sql = f"{sql.rstrip()} RETURNING {id_column}"
        row = conn.execute(sql, params).fetchone()
        if not row:
            raise RuntimeError('Falha ao obter ID inserido no PostgreSQL.')
        return int(row[id_column])

    cur = conn.execute(sql, params)
    return int(cur.lastrowid)


def init_db() -> None:
    conn = get_db()
    if conn.backend == 'postgres':
        _init_postgres(conn)
    else:
        _init_sqlite(conn)
    _ensure_defaults(conn)
    conn.commit()
    conn.close()


def _init_sqlite(conn: DBConnection) -> None:
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('ganho', 'gasto', 'investimento')),
            valor REAL NOT NULL,
            data_vencimento TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pendente' CHECK(status IN ('pendente', 'pago')),
            fixa INTEGER NOT NULL DEFAULT 0,
            competencia_mes INTEGER NOT NULL,
            competencia_ano INTEGER NOT NULL,
            recorrencia_grupo TEXT,
            observacao TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        '''
    )

    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS projecoes_investimento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            valor_meta REAL NOT NULL,
            aporte_mensal REAL NOT NULL,
            rentabilidade_mensal REAL NOT NULL,
            prazo_meses INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        '''
    )

    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        '''
    )

    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS notificacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lancamento_id INTEGER NOT NULL,
            canal TEXT NOT NULL DEFAULT 'whatsapp',
            telefone_destino TEXT NOT NULL,
            mensagem TEXT NOT NULL,
            data_programada TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pendente' CHECK(status IN ('pendente', 'enviado', 'erro')),
            resposta_api TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            sent_at TEXT DEFAULT '',
            FOREIGN KEY(lancamento_id) REFERENCES lancamentos(id)
        )
        '''
    )


def _init_postgres(conn: DBConnection) -> None:
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS lancamentos (
            id BIGSERIAL PRIMARY KEY,
            descricao TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('ganho', 'gasto', 'investimento')),
            valor DOUBLE PRECISION NOT NULL,
            data_vencimento DATE NOT NULL,
            status TEXT NOT NULL DEFAULT 'pendente' CHECK(status IN ('pendente', 'pago')),
            fixa BOOLEAN NOT NULL DEFAULT FALSE,
            competencia_mes INTEGER NOT NULL,
            competencia_ano INTEGER NOT NULL,
            recorrencia_grupo TEXT,
            observacao TEXT DEFAULT '',
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
        '''
    )

    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS projecoes_investimento (
            id BIGSERIAL PRIMARY KEY,
            titulo TEXT NOT NULL,
            valor_meta DOUBLE PRECISION NOT NULL,
            aporte_mensal DOUBLE PRECISION NOT NULL,
            rentabilidade_mensal DOUBLE PRECISION NOT NULL,
            prazo_meses INTEGER NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
        '''
    )

    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
        '''
    )

    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS notificacoes (
            id BIGSERIAL PRIMARY KEY,
            lancamento_id BIGINT NOT NULL REFERENCES lancamentos(id) ON DELETE CASCADE,
            canal TEXT NOT NULL DEFAULT 'whatsapp',
            telefone_destino TEXT NOT NULL,
            mensagem TEXT NOT NULL,
            data_programada DATE NOT NULL,
            status TEXT NOT NULL DEFAULT 'pendente' CHECK(status IN ('pendente', 'enviado', 'erro')),
            resposta_api TEXT DEFAULT '',
            created_at TIMESTAMP NOT NULL,
            sent_at TIMESTAMP NULL
        )
        '''
    )


def _ensure_defaults(conn: DBConnection) -> None:
    defaults = {
        'whatsapp_provider': 'meta_cloud_api',
        'whatsapp_enabled': '0',
        'whatsapp_phone_number_id': '',
        'whatsapp_access_token': '',
        'whatsapp_api_version': 'v23.0',
        'whatsapp_template_name': 'financeiro_vencimento',
        'whatsapp_template_lang': 'pt_BR',
        'whatsapp_recipient_phone': '+5547997573257',
        'ui_currency': 'BRL',
    }
    for key, value in defaults.items():
        conn.execute(
            '''
            INSERT INTO configuracoes (chave, valor, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(chave) DO NOTHING
            ''',
            (key, value, now_db()),
        )


def now_db() -> str:
    from datetime import datetime
    return datetime.now().isoformat(timespec='seconds')


def get_config_map() -> dict[str, str]:
    conn = get_db()
    rows = conn.execute('SELECT chave, valor FROM configuracoes').fetchall()
    conn.close()
    return {row['chave']: row['valor'] for row in rows}


def set_config_values(payload: dict[str, str]) -> None:
    conn = get_db()
    now = now_db()
    for key, value in payload.items():
        conn.execute(
            '''
            INSERT INTO configuracoes (chave, valor, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(chave) DO UPDATE SET valor=EXCLUDED.valor, updated_at=EXCLUDED.updated_at
            ''',
            (key, str(value), now),
        )
    conn.commit()
    conn.close()
