"""Gestión de datos de SmartRecipe (SQLite).

Tablas:
  - usuarios: cuentas de la aplicación (la contraseña se guarda cifrada).
  - despensa: ingredientes que cada usuario guarda para reutilizarlos.
  - recetas:  historial de recetas de cada usuario, con marca de favorita.

Cada fila de despensa y de recetas pertenece a un usuario (`usuario_id`), y
todas las consultas filtran por él: nadie puede ver ni borrar datos de otro.
"""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

RUTA_DB = Path(__file__).with_name("smartrecipe.db")

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    creado TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS despensa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER REFERENCES usuarios(id),
    nombre TEXT NOT NULL,
    creado TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (usuario_id, nombre)
);
CREATE TABLE IF NOT EXISTS recetas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER REFERENCES usuarios(id),
    titulo TEXT NOT NULL,
    comensales INTEGER NOT NULL,
    ingredientes_usuario TEXT NOT NULL,  -- JSON: lista que escribió el usuario
    receta TEXT NOT NULL,                -- JSON: respuesta completa
    favorita INTEGER NOT NULL DEFAULT 0,
    creada TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


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


def _columnas(c, tabla):
    return [fila["name"] for fila in c.execute(f"PRAGMA table_info({tabla})")]


def _migrar(c):
    """Adapta una base creada antes de que existieran las cuentas de usuario.

    Las filas antiguas quedan con usuario_id vacío y se asignan a la primera
    cuenta que se registre (ver crear_usuario), para no perder el historial.
    """
    if "usuario_id" not in _columnas(c, "recetas"):
        c.execute("ALTER TABLE recetas ADD COLUMN usuario_id INTEGER REFERENCES usuarios(id)")
    if "usuario_id" not in _columnas(c, "despensa"):
        # La regla "nombre único" pasa a ser "único por usuario": hay que rehacer la tabla.
        c.executescript(
            """
            ALTER TABLE despensa RENAME TO despensa_anterior;
            CREATE TABLE despensa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER REFERENCES usuarios(id),
                nombre TEXT NOT NULL,
                creado TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (usuario_id, nombre)
            );
            INSERT INTO despensa (id, nombre, creado) SELECT id, nombre, creado FROM despensa_anterior;
            DROP TABLE despensa_anterior;
            """
        )


def iniciar_db(ruta=None):
    with sesion(ruta) as c:
        c.executescript(_ESQUEMA)
        _migrar(c)


# ---------- Usuarios ----------
def crear_usuario(usuario, password_hash, ruta=None):
    """Crea la cuenta y devuelve {"id", "usuario"}; None si el nombre ya existe."""
    with sesion(ruta) as c:
        try:
            cur = c.execute(
                "INSERT INTO usuarios (usuario, password_hash) VALUES (?, ?)",
                (usuario, password_hash),
            )
        except sqlite3.IntegrityError:
            return None
        nuevo_id = cur.lastrowid
        # La primera cuenta hereda los datos guardados antes de que hubiera cuentas.
        if c.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 1:
            c.execute("UPDATE recetas SET usuario_id = ? WHERE usuario_id IS NULL", (nuevo_id,))
            c.execute("UPDATE despensa SET usuario_id = ? WHERE usuario_id IS NULL", (nuevo_id,))
    return {"id": nuevo_id, "usuario": usuario}


def buscar_usuario(usuario, ruta=None):
    """Devuelve {"id", "usuario", "password_hash"} o None."""
    with sesion(ruta) as c:
        fila = c.execute(
            "SELECT id, usuario, password_hash FROM usuarios WHERE usuario = ?", (usuario,)
        ).fetchone()
    return dict(fila) if fila else None


def usuario_por_id(id_, ruta=None):
    with sesion(ruta) as c:
        fila = c.execute("SELECT id, usuario FROM usuarios WHERE id = ?", (id_,)).fetchone()
    return dict(fila) if fila else None


# ---------- Despensa ----------
def listar_despensa(usuario_id, ruta=None):
    with sesion(ruta) as c:
        filas = c.execute(
            "SELECT id, nombre FROM despensa WHERE usuario_id = ? ORDER BY nombre", (usuario_id,)
        ).fetchall()
    return [dict(f) for f in filas]


def agregar_a_despensa(usuario_id, nombre, ruta=None):
    with sesion(ruta) as c:
        c.execute(
            "INSERT OR IGNORE INTO despensa (usuario_id, nombre) VALUES (?, ?)", (usuario_id, nombre)
        )
        fila = c.execute(
            "SELECT id, nombre FROM despensa WHERE usuario_id = ? AND nombre = ?",
            (usuario_id, nombre),
        ).fetchone()
    return dict(fila)


def borrar_de_despensa(usuario_id, id_, ruta=None):
    with sesion(ruta) as c:
        cur = c.execute("DELETE FROM despensa WHERE id = ? AND usuario_id = ?", (id_, usuario_id))
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


def guardar_receta(usuario_id, ingredientes_usuario, receta, ruta=None):
    with sesion(ruta) as c:
        cur = c.execute(
            "INSERT INTO recetas (usuario_id, titulo, comensales, ingredientes_usuario, receta) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                usuario_id,
                receta["titulo"],
                receta["comensales"],
                json.dumps(ingredientes_usuario, ensure_ascii=False),
                json.dumps(receta, ensure_ascii=False),
            ),
        )
        fila = c.execute("SELECT * FROM recetas WHERE id = ?", (cur.lastrowid,)).fetchone()
    return _fila_a_dict(fila)


def listar_recetas(usuario_id, solo_favoritas=False, ruta=None):
    consulta = "SELECT * FROM recetas WHERE usuario_id = ?"
    if solo_favoritas:
        consulta += " AND favorita = 1"
    consulta += " ORDER BY id DESC"
    with sesion(ruta) as c:
        filas = c.execute(consulta, (usuario_id,)).fetchall()
    return [_fila_a_dict(f) for f in filas]


def alternar_favorita(usuario_id, id_, ruta=None):
    """Invierte la marca de favorita. Devuelve la receta o None si no existe o no es suya."""
    with sesion(ruta) as c:
        c.execute(
            "UPDATE recetas SET favorita = 1 - favorita WHERE id = ? AND usuario_id = ?",
            (id_, usuario_id),
        )
        fila = c.execute(
            "SELECT * FROM recetas WHERE id = ? AND usuario_id = ?", (id_, usuario_id)
        ).fetchone()
    return _fila_a_dict(fila) if fila else None


def borrar_receta(usuario_id, id_, ruta=None):
    with sesion(ruta) as c:
        cur = c.execute("DELETE FROM recetas WHERE id = ? AND usuario_id = ?", (id_, usuario_id))
    return cur.rowcount > 0
