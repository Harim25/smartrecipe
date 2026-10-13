"""Servicio que genera la receta.

Avance 2 (Actividad 4.1): la aplicación ya se conecta al modelo de lenguaje
Gemini mediante la API oficial de Google (paquete `google-genai`). El modo
simulado del Avance 1 se conserva como respaldo para poder usar y probar la
aplicación sin internet o sin API key.

Avance 3 (Actividad 4.2): cuando Gemini no puede responder (límite de uso,
saturación, sin conexión) el error indica que se puede ofrecer el modo
simulado, y el usuario decide si continúa sin IA. Además, las cantidades de la
receta se normalizan antes de mostrarlas.

¿Qué modo se usa?
  - Si existe la variable GEMINI_API_KEY (por ejemplo, en el archivo .env),
    se usa Gemini.
  - Si no existe, se usa el modo simulado.
  - Se puede forzar uno u otro con LLM_PROVIDER=gemini o LLM_PROVIDER=simulado.
"""

import json
import os
import re
import time
from pathlib import Path

from prompts import (
    CAMPOS_REQUERIDOS,
    ESQUEMA_RECETA,
    SYSTEM_PROMPT,
    construir_prompt_usuario,
)

# Lee el archivo .env (si existe) para obtener la API key sin escribirla en el código.
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).with_name(".env"))
except ImportError:  # python-dotenv no instalado: se usan solo variables de entorno
    pass


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
MODELO = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
TIMEOUT_SEGUNDOS = 60        # tiempo máximo de espera (en las pruebas reales el modelo tardó de 10 a 20 s, con picos mayores)
REINTENTOS_SERVIDOR = 2      # reintentos si Gemini responde "no disponible" (5xx)
UNIDADES_VALIDAS = {"g", "ml", "pieza", "al gusto"}


def _api_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""


PROVEEDOR = (os.environ.get("LLM_PROVIDER") or ("gemini" if _api_key() else "simulado")).lower()


def descripcion_modo():
    """Texto corto que la interfaz muestra en la esquina superior."""
    return f"gemini · {MODELO}" if PROVEEDOR == "gemini" else "simulado"


# ---------------------------------------------------------------------------
# Errores (cada uno trae el código HTTP con el que la API responde)
# ---------------------------------------------------------------------------
class ErrorGeneracion(RuntimeError):
    """La respuesta del modelo no se pudo obtener o no tiene el formato esperado.

    `tipo` es una etiqueta corta que la interfaz usa para decidir qué mostrar y
    `ofrecer_simulado` indica si tiene sentido proponer el modo sin IA.
    """

    codigo_http = 502
    tipo = "respuesta"
    ofrecer_simulado = False


class ErrorServicio(ErrorGeneracion):
    """Gemini no respondió: saturado, tardó demasiado o no hay conexión."""

    tipo = "servicio"
    ofrecer_simulado = True


class ErrorConfiguracion(ErrorGeneracion):
    """Falta la API key, el SDK o la configuración es incorrecta."""

    codigo_http = 503
    tipo = "configuracion"
    ofrecer_simulado = True


class ErrorLimiteUso(ErrorGeneracion):
    """Se alcanzó el límite de peticiones de la capa gratuita."""

    codigo_http = 429
    tipo = "limite"
    ofrecer_simulado = True


class RecetaNoViable(ErrorGeneracion):
    """El modelo indicó que con esos ingredientes no se puede preparar nada."""

    codigo_http = 422
    tipo = "no_viable"


# ---------------------------------------------------------------------------
# Modo simulado (respaldo, sin IA)
# ---------------------------------------------------------------------------
# Gramos (o ml) por persona según el tipo de ingrediente, por palabra clave.
_GRUPOS = [
    (("pollo", "pechuga", "carne", "res", "cerdo", "pescado", "atún", "atun",
      "huevo", "jamón", "jamon", "salchicha", "camarón", "camaron"), 150, "g"),
    (("arroz", "pasta", "espagueti", "fideo", "papa", "tortilla", "pan", "frijol",
      "lenteja", "garbanzo", "avena"), 80, "g"),
    (("crema", "leche", "queso", "yogur", "yogurt", "mantequilla"), 40, "ml"),
    (("salsa", "caldo", "jugo"), 60, "ml"),
]
_POR_DEFECTO = (100, "g")  # verduras y cualquier otro ingrediente


def _porcion_por_persona(nombre):
    for palabras, cantidad, unidad in _GRUPOS:
        if any(p in nombre for p in palabras):
            return cantidad, unidad
    return _POR_DEFECTO


def _lista_a_texto(nombres):
    if len(nombres) == 1:
        return nombres[0]
    return ", ".join(nombres[:-1]) + " y " + nombres[-1]


def _generar_simulado(ingredientes, comensales):
    principales = ingredientes[:3]
    titulo = "Salteado casero de " + _lista_a_texto(principales)
    if len(ingredientes) > 3:
        titulo += " y más"

    lista = []
    for nombre in ingredientes:
        por_persona, unidad = _porcion_por_persona(nombre)
        lista.append(
            {"nombre": nombre, "cantidad": por_persona * comensales, "unidad": unidad}
        )
    lista.append({"nombre": "sal", "cantidad": 0, "unidad": "al gusto"})
    lista.append({"nombre": "aceite", "cantidad": 10 * comensales, "unidad": "ml"})

    pasos = [
        "Lava y corta en trozos pequeños todos los ingredientes frescos.",
        "Calienta el aceite en una sartén grande a fuego medio.",
        f"Agrega primero los ingredientes que tardan más en cocerse "
        f"({_lista_a_texto(principales)}) y cocina de 8 a 10 minutos, moviendo de vez en cuando.",
    ]
    if len(ingredientes) > 3:
        pasos.append("Incorpora el resto de los ingredientes y cocina 5 minutos más.")
    pasos += [
        "Sazona con sal al gusto y prueba antes de retirar del fuego.",
        f"Sirve caliente en {comensales} porción(es).",
    ]

    return {
        "viable": True,
        "titulo": titulo,
        "comensales": comensales,
        "ingredientes": lista,
        "pasos": pasos,
        "tiempo_minutos": 20 + 2 * len(ingredientes),
        "nota": "Receta de demostración generada en modo simulado (sin IA).",
    }


# ---------------------------------------------------------------------------
# Modo Gemini
# ---------------------------------------------------------------------------
def _traducir_error(exc):
    """Convierte una excepción del SDK en un error con mensaje claro para el usuario.

    Se reconoce por código HTTP, nombre de la clase y texto del mensaje (y no
    importando clases internas del SDK) para que siga funcionando si Google
    cambia su biblioteca.
    """
    codigo = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    nombre = type(exc).__name__
    texto = str(exc)
    minusculas = texto.lower()

    if "timeout" in nombre.lower() or "timed out" in minusculas:
        return ErrorServicio(
            f"Gemini tardó más de {TIMEOUT_SEGUNDOS} segundos en responder. Intenta de nuevo."
        )
    if codigo == 429 or "resource_exhausted" in minusculas or "quota" in minusculas:
        return ErrorLimiteUso(
            "Se alcanzó el límite de uso gratuito de Gemini. Si fue el límite por minuto, "
            "se recupera esperando un minuto; si fue el límite diario, hasta el día siguiente."
        )
    if "api key" in minusculas or "api_key" in minusculas or codigo in (401, 403):
        return ErrorConfiguracion(
            "Gemini rechazó la API key. Revisa que GEMINI_API_KEY en el archivo .env sea correcta "
            "y esté activa."
        )
    if codigo == 404:
        return ErrorConfiguracion(
            f"El modelo '{MODELO}' no existe o no está disponible. "
            "Revisa el nombre en GEMINI_MODEL (ver la documentación de Gemini)."
        )
    if codigo == 400:
        return ErrorGeneracion(f"Gemini rechazó la petición: {texto[:200]}")
    if isinstance(codigo, int) and codigo >= 500:
        return ErrorServicio("Gemini no está disponible por el momento. Intenta de nuevo en unos segundos.")
    if "connect" in nombre.lower() or "connect" in minusculas or "network" in minusculas:
        return ErrorServicio("No se pudo conectar con Gemini. Revisa tu conexión a internet.")
    return ErrorGeneracion(f"Error inesperado al consultar Gemini ({nombre}): {texto[:200]}")


def _llamar_gemini(ingredientes, comensales):
    """Envía el system prompt y los datos del usuario a Gemini y devuelve el texto (JSON)."""
    llave = _api_key()
    if not llave:
        raise ErrorConfiguracion(
            "Falta la API key de Gemini. Crea el archivo .env con GEMINI_API_KEY=tu_clave (ver README)."
        )
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ErrorConfiguracion(
            "Falta instalar el SDK de Gemini. Ejecuta: pip install -r requirements.txt"
        )

    # Por defecto el SDK reintenta solo (hasta 4 peticiones por llamada), lo que
    # gastaría la cuota gratuita y haría esperar al usuario. Se desactiva con
    # un código de estado imposible (599) para controlar los reintentos aquí.
    cliente = genai.Client(
        api_key=llave,
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(attempts=1, http_status_codes=[599])
        ),
    )
    intentos = REINTENTOS_SERVIDOR + 1
    for intento in range(1, intentos + 1):
        try:
            interaccion = cliente.interactions.create(
                model=MODELO,
                system_instruction=SYSTEM_PROMPT,
                input=construir_prompt_usuario(ingredientes, comensales),
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": ESQUEMA_RECETA,
                },
                timeout=TIMEOUT_SEGUNDOS,
            )
            estado = getattr(interaccion, "status", None)
            if isinstance(estado, str) and estado != "completed":
                raise ErrorGeneracion(
                    f"Gemini no terminó de generar la respuesta (estado: {estado}). Intenta de nuevo."
                )
            texto = interaccion.output_text
            if not texto:
                raise ErrorGeneracion("Gemini devolvió una respuesta vacía.")
            return texto
        except ErrorGeneracion:
            raise
        except Exception as exc:  # errores del SDK, de red, etc.
            codigo = getattr(exc, "status_code", None) or getattr(exc, "code", None)
            if intento < intentos and isinstance(codigo, int) and codigo >= 500:
                time.sleep(2 * intento)  # Gemini saturado: espera creciente (2 s, 4 s) y reintenta
                continue
            raise _traducir_error(exc) from exc


def _extraer_json(texto):
    """Convierte el texto del modelo en un diccionario, tolerando bloques ```json."""
    limpio = texto.strip()
    limpio = re.sub(r"^```(?:json)?\s*|\s*```$", "", limpio, flags=re.IGNORECASE)
    try:
        return json.loads(limpio)
    except json.JSONDecodeError:
        inicio, fin = limpio.find("{"), limpio.rfind("}")
        if inicio != -1 and fin > inicio:
            try:
                return json.loads(limpio[inicio : fin + 1])
            except json.JSONDecodeError:
                pass
    raise ErrorGeneracion("El modelo no devolvió un JSON válido.")


# ---------------------------------------------------------------------------
# Validación de la respuesta (aplica a cualquier proveedor)
# ---------------------------------------------------------------------------
def _es_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _normalizar_cantidad(cantidad, unidad):
    """Deja las cantidades en una forma uniforme y fácil de medir en la cocina.

    - "al gusto" no lleva número: siempre 0 (el modelo a veces mandaba 1).
    - Las piezas se redondean a medios (1.3 -> 1.5); nunca quedan en 0.
    - Gramos y mililitros se redondean a enteros (a un decimal si son menos de 10).
    """
    if unidad == "al gusto" or cantidad <= 0:
        return 0
    if unidad == "pieza":
        valor = max(1, round(cantidad * 2)) / 2
    elif cantidad < 10:
        valor = round(cantidad, 1)
    else:
        valor = round(cantidad)
    return int(valor) if float(valor).is_integer() else valor


def validar_respuesta(receta, comensales=None):
    """Comprueba que la receta tenga el formato correcto antes de mostrarla."""
    if not isinstance(receta, dict):
        raise ErrorGeneracion("La respuesta no es un objeto JSON.")

    if receta.get("viable") is False:
        motivo = receta.get("nota") if isinstance(receta.get("nota"), str) else ""
        raise RecetaNoViable(
            motivo.strip() or "Con esos ingredientes no es posible preparar una receta segura."
        )

    faltan = [c for c in CAMPOS_REQUERIDOS if c not in receta]
    if faltan:
        raise ErrorGeneracion("Faltan campos en la respuesta: " + ", ".join(faltan))

    if not isinstance(receta["titulo"], str) or not receta["titulo"].strip():
        raise ErrorGeneracion("La receta no trae título.")
    if not isinstance(receta["ingredientes"], list) or not receta["ingredientes"]:
        raise ErrorGeneracion("La receta no trae ingredientes.")
    for ing in receta["ingredientes"]:
        if (
            not isinstance(ing, dict)
            or not isinstance(ing.get("nombre"), str)
            or not ing["nombre"].strip()
            or not _es_numero(ing.get("cantidad"))
            or ing["cantidad"] < 0
            or ing.get("unidad") not in UNIDADES_VALIDAS
        ):
            raise ErrorGeneracion("Un ingrediente de la receta tiene un formato inválido.")
    if (
        not isinstance(receta["pasos"], list)
        or not receta["pasos"]
        or not all(isinstance(p, str) and p.strip() for p in receta["pasos"])
    ):
        raise ErrorGeneracion("La receta no trae pasos válidos.")
    if not _es_numero(receta["tiempo_minutos"]):
        raise ErrorGeneracion("El tiempo de preparación no es un número.")
    if comensales is not None and receta["comensales"] != comensales:
        raise ErrorGeneracion(
            f"El modelo calculó las cantidades para {receta['comensales']} comensales "
            f"y se pidieron {comensales}."
        )

    for ing in receta["ingredientes"]:
        ing["nombre"] = ing["nombre"].strip()
        ing["cantidad"] = _normalizar_cantidad(ing["cantidad"], ing["unidad"])
    receta["viable"] = True
    return receta


def generar_receta(ingredientes, comensales, forzar_simulado=False):
    """Punto único de entrada: devuelve una receta validada (dict).

    Además de los campos de la receta, agrega "meta" con el proveedor, el
    modelo y los segundos que tardó (sirve como evidencia en las pruebas).

    `forzar_simulado=True` genera la receta sin IA aunque Gemini esté
    configurado: es el respaldo que el usuario acepta cuando Gemini falla.
    """
    inicio = time.perf_counter()
    proveedor = "simulado" if forzar_simulado else PROVEEDOR
    if proveedor == "simulado":
        receta = _generar_simulado(ingredientes, comensales)
        modelo = None
    elif proveedor == "gemini":
        receta = _extraer_json(_llamar_gemini(ingredientes, comensales))
        modelo = MODELO
    else:
        raise ErrorConfiguracion(
            f"LLM_PROVIDER='{PROVEEDOR}' no es válido. Usa 'gemini' o 'simulado'."
        )

    receta = validar_respuesta(receta, comensales)
    receta["meta"] = {
        "proveedor": proveedor,
        "modelo": modelo,
        # True si el modo simulado se usó como respaldo de Gemini.
        "respaldo": bool(forzar_simulado and PROVEEDOR != "simulado"),
        "segundos": round(time.perf_counter() - inicio, 2),
    }
    return receta
