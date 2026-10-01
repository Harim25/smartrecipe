"""Limpieza y validación de los datos que llegan desde la interfaz.

Es el "algoritmo de limpieza de cadenas" descrito en la Actividad 3.1:
antes de armar el prompt, el servidor sanitiza lo que escribió el usuario.
"""

import re

MAX_INGREDIENTES = 20
MAX_LARGO_INGREDIENTE = 40
MIN_COMENSALES = 1
MAX_COMENSALES = 20

# Solo letras (con acentos y ñ), espacios y guiones.
_PATRON_PERMITIDO = re.compile(r"[^a-záéíóúüñ\s-]")


class ErrorValidacion(ValueError):
    """Se lanza cuando los datos del usuario no son válidos."""


def limpiar_ingrediente(texto):
    """Devuelve el ingrediente limpio o '' si no queda nada válido."""
    if not isinstance(texto, str):
        return ""
    texto = texto.lower().strip()
    texto = _PATRON_PERMITIDO.sub("", texto)
    texto = re.sub(r"\s+", " ", texto).strip(" -")
    return texto[:MAX_LARGO_INGREDIENTE]


def limpiar_lista_ingredientes(lista):
    """Limpia, quita vacíos y duplicados (conservando el orden)."""
    if not isinstance(lista, list):
        raise ErrorValidacion("Los ingredientes deben enviarse como una lista.")
    limpios = []
    for item in lista:
        nombre = limpiar_ingrediente(item)
        if nombre and nombre not in limpios:
            limpios.append(nombre)
    if not limpios:
        raise ErrorValidacion("Agrega al menos un ingrediente válido.")
    if len(limpios) > MAX_INGREDIENTES:
        raise ErrorValidacion(f"El máximo es de {MAX_INGREDIENTES} ingredientes.")
    return limpios


def validar_comensales(valor):
    """Convierte a entero y verifica el rango permitido."""
    try:
        comensales = int(valor)
    except (TypeError, ValueError):
        raise ErrorValidacion("El número de comensales debe ser un entero.")
    if not MIN_COMENSALES <= comensales <= MAX_COMENSALES:
        raise ErrorValidacion(
            f"Los comensales deben estar entre {MIN_COMENSALES} y {MAX_COMENSALES}."
        )
    return comensales
