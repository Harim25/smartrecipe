"""Cuentas de usuario de SmartRecipe: registro, inicio de sesión y protección básica.

Decisiones de seguridad:
  - La contraseña NUNCA se guarda en texto: se guarda un hash con sal generado por
    Werkzeug (la biblioteca que usa Flask). Ni nosotros podemos leerla.
  - La sesión viaja en una cookie firmada por Flask; la clave de firma no está en
    el código (se lee de SECRET_KEY o se genera y guarda en un archivo ignorado por Git).
  - El mensaje de error del inicio de sesión no revela si el usuario existe.
  - Tras varios intentos fallidos seguidos, la cuenta se bloquea un minuto.

Limitación conocida: no hay recuperación de contraseña (no se pide correo).
"""

import os
import re
import secrets
import time
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

import database as db

MIN_USUARIO, MAX_USUARIO = 3, 20
MIN_PASSWORD, MAX_PASSWORD = 8, 128
_PATRON_USUARIO = re.compile(r"^[a-z0-9_]+$")

MAX_INTENTOS = 5          # intentos fallidos permitidos...
BLOQUEO_SEGUNDOS = 60     # ...antes de bloquear este tiempo
_intentos = {}            # usuario -> (fallos, momento del último fallo)

# Hash de relleno: se compara contra él cuando el usuario no existe, para que la
# respuesta tarde lo mismo y no delate qué nombres están registrados.
_HASH_DE_RELLENO = generate_password_hash("contraseña-de-relleno")


class ErrorCuenta(ValueError):
    """Datos de registro o de inicio de sesión no válidos."""

    codigo_http = 400


class ErrorBloqueo(ErrorCuenta):
    codigo_http = 429


def clave_de_sesion():
    """Clave con la que Flask firma la cookie de sesión.

    Se toma de la variable SECRET_KEY; si no existe, se genera una aleatoria y
    se guarda en `.clave_sesion` (ignorado por Git) para que las sesiones
    sigan siendo válidas al reiniciar la aplicación.
    """
    clave = os.environ.get("SECRET_KEY")
    if clave:
        return clave
    archivo = Path(__file__).with_name(".clave_sesion")
    if archivo.exists():
        return archivo.read_text(encoding="utf-8").strip()
    clave = secrets.token_hex(32)
    archivo.write_text(clave, encoding="utf-8")
    return clave


def normalizar_usuario(texto):
    return texto.strip().lower() if isinstance(texto, str) else ""


def validar_usuario(texto):
    usuario = normalizar_usuario(texto)
    if not MIN_USUARIO <= len(usuario) <= MAX_USUARIO:
        raise ErrorCuenta(f"El usuario debe tener entre {MIN_USUARIO} y {MAX_USUARIO} caracteres.")
    if not _PATRON_USUARIO.match(usuario):
        raise ErrorCuenta("El usuario solo puede llevar letras sin acento, números y guion bajo.")
    return usuario


def validar_password(texto, usuario=""):
    if not isinstance(texto, str) or len(texto) < MIN_PASSWORD:
        raise ErrorCuenta(f"La contraseña debe tener al menos {MIN_PASSWORD} caracteres.")
    if len(texto) > MAX_PASSWORD:
        raise ErrorCuenta(f"La contraseña no puede tener más de {MAX_PASSWORD} caracteres.")
    if usuario and texto.lower() == usuario:
        raise ErrorCuenta("La contraseña no puede ser igual al usuario.")
    return texto


def registrar(usuario, password):
    """Crea la cuenta y devuelve {"id", "usuario"}."""
    usuario = validar_usuario(usuario)
    password = validar_password(password, usuario)
    cuenta = db.crear_usuario(usuario, generate_password_hash(password))
    if cuenta is None:
        raise ErrorCuenta("Ese nombre de usuario ya está en uso. Elige otro.")
    return cuenta


def _bloqueado(usuario):
    fallos, ultimo = _intentos.get(usuario, (0, 0))
    if fallos >= MAX_INTENTOS:
        if time.time() - ultimo < BLOQUEO_SEGUNDOS:
            return True
        _intentos.pop(usuario, None)  # ya pasó el tiempo de bloqueo
    return False


def iniciar_sesion(usuario, password):
    """Comprueba usuario y contraseña. Devuelve {"id", "usuario"}."""
    usuario = normalizar_usuario(usuario)
    if _bloqueado(usuario):
        raise ErrorBloqueo("Demasiados intentos fallidos. Espera un minuto e inténtalo de nuevo.")
    cuenta = db.buscar_usuario(usuario) if usuario else None
    correcto = check_password_hash(
        cuenta["password_hash"] if cuenta else _HASH_DE_RELLENO,
        password if isinstance(password, str) else "",
    )
    if not cuenta or not correcto:
        fallos, _ = _intentos.get(usuario, (0, 0))
        _intentos[usuario] = (fallos + 1, time.time())
        raise ErrorCuenta("Usuario o contraseña incorrectos.")
    _intentos.pop(usuario, None)
    return {"id": cuenta["id"], "usuario": cuenta["usuario"]}
