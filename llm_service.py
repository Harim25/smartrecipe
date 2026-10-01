"""Servicio que genera la receta.

Avance 1 (esta etapa): funciona en MODO SIMULADO. No usa inteligencia
artificial; arma una receta de demostración con reglas simples para poder
probar la interfaz, la base de datos y el flujo completo de la aplicación.

Avance 2: aquí se conectará el modelo de lenguaje real (por ejemplo Gemini).
Solo hay que implementar `_generar_con_llm` y poner LLM_PROVIDER=gemini;
el resto de la aplicación no cambia, porque ya valida que la respuesta
tenga el formato JSON definido en prompts.py.
"""

import json
import os

from prompts import CAMPOS_REQUERIDOS, SYSTEM_PROMPT, construir_prompt_usuario

PROVEEDOR = os.environ.get("LLM_PROVIDER", "simulado")


class ErrorGeneracion(RuntimeError):
    """La respuesta del modelo no se pudo obtener o no tiene el formato esperado."""


# ---------------------------------------------------------------------------
# Modo simulado
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
        pasos.append(
            "Incorpora el resto de los ingredientes y cocina 5 minutos más."
        )
    pasos += [
        "Sazona con sal al gusto y prueba antes de retirar del fuego.",
        f"Sirve caliente en {comensales} porción(es).",
    ]

    return {
        "titulo": titulo,
        "comensales": comensales,
        "ingredientes": lista,
        "pasos": pasos,
        "tiempo_minutos": 20 + 2 * len(ingredientes),
        "nota": "Receta de demostración generada en modo simulado (sin IA). "
        "En el siguiente avance la generará un modelo de lenguaje.",
    }


# ---------------------------------------------------------------------------
# Modo real (pendiente para el Avance 2)
# ---------------------------------------------------------------------------
def _generar_con_llm(ingredientes, comensales):
    """Pendiente: enviar SYSTEM_PROMPT + prompt de usuario a la API del LLM.

    Pasos previstos para el Avance 2:
      1. Leer la API key desde una variable de entorno (nunca en el código).
      2. Enviar SYSTEM_PROMPT y construir_prompt_usuario(...) al modelo.
      3. Devolver el texto JSON que responda el modelo.
    """
    _ = (SYSTEM_PROMPT, construir_prompt_usuario(ingredientes, comensales))
    raise NotImplementedError("La conexión al LLM se implementa en el Avance 2.")


# ---------------------------------------------------------------------------
# Validación de la respuesta (aplica a cualquier proveedor)
# ---------------------------------------------------------------------------
def validar_respuesta(receta):
    if not isinstance(receta, dict):
        raise ErrorGeneracion("La respuesta no es un objeto JSON.")
    faltan = [c for c in CAMPOS_REQUERIDOS if c not in receta]
    if faltan:
        raise ErrorGeneracion("Faltan campos en la respuesta: " + ", ".join(faltan))
    if not isinstance(receta["ingredientes"], list) or not receta["ingredientes"]:
        raise ErrorGeneracion("La receta no trae ingredientes.")
    if not isinstance(receta["pasos"], list) or not receta["pasos"]:
        raise ErrorGeneracion("La receta no trae pasos.")
    return receta


def generar_receta(ingredientes, comensales):
    """Punto único de entrada: devuelve una receta validada (dict)."""
    if PROVEEDOR == "simulado":
        receta = _generar_simulado(ingredientes, comensales)
    else:
        try:
            texto = _generar_con_llm(ingredientes, comensales)
            receta = json.loads(texto)
        except NotImplementedError as e:
            raise ErrorGeneracion(str(e))
        except json.JSONDecodeError:
            raise ErrorGeneracion("El modelo no devolvió un JSON válido.")
    return validar_respuesta(receta)
