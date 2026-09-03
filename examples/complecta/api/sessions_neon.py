# Хранилище сессий в Neon (Postgres): serverless-хостинг не держит память между вызовами,
# а эталонный SessionStore живёт в словарях процесса. Шесть методов хранилища переводим на
# таблицы; остальное поведение (версии, конфликт записи, транскрипт по частям) — от базового.
from __future__ import annotations

import json
import os
from typing import Any

import psycopg
from demo_common.sessions import SessionConflictError, SessionStore


class NeonSessionStore(SessionStore):
    """``SessionStore`` over two таблицы: alxndra_sessions (состояние с версией) и
    alxndra_messages (транскрипт по индексу). Одно соединение на процесс, автокоммит."""

    def __init__(self, state_type, dsn: str | None = None) -> None:
        super().__init__(state_type)
        self._dsn = dsn or os.environ["DATABASE_URL"]
        self._conn: psycopg.Connection | None = None
        self._ensure()

    def _c(self) -> psycopg.Connection:
        if self._conn is None or self._conn.closed:
            self._conn = psycopg.connect(self._dsn, autocommit=True, connect_timeout=10)
        return self._conn

    def _ensure(self) -> None:
        with self._c().cursor() as cur:
            cur.execute("""create table if not exists alxndra_sessions (
                session_id text primary key, user_id text not null, version int not null,
                document jsonb not null, updated_at timestamptz not null default now())""")
            cur.execute("""create table if not exists alxndra_messages (
                session_id text not null, idx int not null, message jsonb not null,
                primary key (session_id, idx))""")
            cur.execute("create index if not exists alxndra_sessions_user_idx on alxndra_sessions (user_id, updated_at desc)")

    # -- шесть методов хранилища
    def read_state(self, session_id: str) -> tuple[int, dict[str, Any]] | None:
        with self._c().cursor() as cur:
            cur.execute("select version, document from alxndra_sessions where session_id = %s", (session_id,))
            row = cur.fetchone()
        return (row[0], row[1]) if row else None

    def write_state(self, session_id: str, document: dict[str, Any], version: int) -> None:
        with self._c().cursor() as cur:
            cur.execute("select version, user_id from alxndra_sessions where session_id = %s", (session_id,))
            row = cur.fetchone()
            if row is None:
                if version != 0:
                    raise SessionConflictError(session_id)
                cur.execute("insert into alxndra_sessions (session_id, user_id, version, document) values (%s, %s, %s, %s)",
                            (session_id, document.get("user_id", ""), 1, json.dumps(document)))
                return
            if row[0] != version:
                raise SessionConflictError(session_id)
            cur.execute("update alxndra_sessions set version = %s, document = %s, updated_at = now() where session_id = %s and version = %s",
                        (version + 1, json.dumps(document), session_id, version))
            if cur.rowcount != 1:
                raise SessionConflictError(session_id)

    def read_messages(self, session_id: str) -> list[dict[str, Any]]:
        with self._c().cursor() as cur:
            cur.execute("select message from alxndra_messages where session_id = %s order by idx", (session_id,))
            return [r[0] for r in cur.fetchall()]

    def write_messages(self, session_id: str, messages: list[dict[str, Any]], start: int) -> None:
        with self._c().cursor() as cur:
            cur.execute("delete from alxndra_messages where session_id = %s and idx >= %s", (session_id, start))
            for i, m in enumerate(messages):
                cur.execute("insert into alxndra_messages (session_id, idx, message) values (%s, %s, %s)",
                            (session_id, start + i, json.dumps(m)))

    def delete(self, session_id: str) -> None:
        with self._c().cursor() as cur:
            cur.execute("delete from alxndra_messages where session_id = %s", (session_id,))
            cur.execute("delete from alxndra_sessions where session_id = %s", (session_id,))

    def session_ids_for_user(self, user_id: str) -> list[str]:
        with self._c().cursor() as cur:
            cur.execute("select session_id from alxndra_sessions where user_id = %s order by updated_at desc limit 20", (user_id,))
            return [r[0] for r in cur.fetchall()]
