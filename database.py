"""Gestión de datos de SmartRecipe (SQLite).

Tablas:
  - despensa: ingredientes que el usuario guarda para reutilizarlos.
  - recetas:  historial de recetas generadas, con marca de favorita.
"""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

RUTA_DB = Path(__file__).with_name("smartrecipe.db")


def conectar(ruta=None):
    conexion = sqlite3.connect(ruta or RUTA_DB)
    conexion.row_factory = sqlite3.Row
    return conexion


@contextmanager
def sesion(ruta=None):
    """Abre la base, confirma (commit) al salir y SIEMPRE cierra la conexión.

    `with sqlite3.connect(...)` solo confirma la transacción pero no cierra el
    archivo; en Windows eso dejaba la base bloqueada (y las pruebas no podían
    borrar su base temporal).
    """
    conexion = conectar(ruta)
    try:
        with conexion:
            yield conexion
    finally:
        conexion.close()


def iniciar_db(ruta=None):
    with sesion(ruta) as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS despensa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                creado TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS recetas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                comensales INTEGER NOT NULL,
                ingredientes_usuario TEXT NOT NULL,  -- JSON: lista que escribió el usuario
                receta TEXT NOT NULL,                -- JSON: respuesta completa
                favorita INTEGER NOT NULL DEFAULT 0,
                creada TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


# ---------- Despensa ----------
def listar_despensa(ruta=None):
    with sesion(ruta) as c:
        filas = c.execute("SELECT id, nombre FROM despensa ORDER BY nombre").fetchall()
    return [dict(f) for f in filas]


def agregar_a_despensa(nombre, ruta=None):
    with sesion(ruta) as c:
        c.execute("INSERT OR IGNORE INTO despensa (nombre) VALUES (?)", (nombre,))
        fila = c.execute(
            "SELECT id, nombre FROM despensa WHERE nombre = ?", (nombre,)
        ).fetchone()
    return dict(fila)


def borrar_de_despensa(id_, ruta=None):
    with sesion(ruta) as c:
        cur = c.execute("DELETE FROM despensa WHERE id = ?", (id_,))
    return cur.rowcount > 0


# ---------- Recetas / historial ----------
def _fila_a_dict(fila):
    return {
        "id": fila["id"],
        "titulo": fila["titulo"],
        "comensales": fila["comensales"],
        "ingredientes_usuario": json.loads(fila["ingredientes_usuario"]),
        "receta": json.loads(fila["receta"]),
        "favorita": bool(fila["favorita"]),
        "creada": fila["creada"],
    }


def guardar_receta(ingredientes_usuario, receta, ruta=None):
    with sesion(ruta) as c:
        cur = c.execute(
            "INSERT INTO recetas (titulo, comensales, ingredientes_usuario, receta) "
            "VALUES (?, ?, ?, ?)",
            (
                receta["titulo"],
                receta["comensales"],
                json.dumps(ingredientes_usuario, ensure_ascii=False),
                json.dumps(receta, ensure_ascii=False),
            ),
        )
        fila = c.execute("SELECT * FROM recetas WHERE id = ?", (cur.lastrowid,)).fetchone()
    return _fila_a_dict(fila)


def listar_recetas(solo_favoritas=False, ruta=None):
    consulta = "SELECT * FROM recetas"
    if solo_favoritas:
        consulta += " WHERE favorita = 1"
    consulta += " ORDER BY id DESC"
    with sesion(ruta) as c:
        filas = c.execute(consulta).fetchall()
    return [_fila_a_dict(f) for f in filas]


def alternar_favorita(id_, ruta=None):
    """Invierte la marca de favorita. Devuelve la receta o None si no existe."""
    with sesion(ruta) as c:
        c.execute("UPDATE recetas SET favorita = 1 - favorita WHERE id = ?", (id_,))
        fila = c.execute("SELECT * FROM recetas WHERE id = ?", (id_,)).fetchone()
    return _fila_a_dict(fila) if fila else None


def borrar_receta(id_, ruta=None):
    with sesion(ruta) as c:
        cur = c.execute("DELETE FROM recetas WHERE id = ?", (id_,))
    return cur.rowcount > 0
