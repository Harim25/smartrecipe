"""Diagnóstico de la conexión con Gemini, paso a paso.

Ejecutar (con el entorno virtual activado):   python probar_conexion.py

Revisa en orden: 1) que exista la API key, 2) que el SDK esté instalado,
3) que Gemini responda, 4) que una receta completa llegue bien formada.
Si algo falla, el mensaje dice qué hacer.
"""

import sys

import llm_service


def paso(numero, texto):
    print(f"\n[{numero}/4] {texto}")


def fallo(mensaje):
    print(f"   ✗ {mensaje}")
    print("\nNo se pudo completar la prueba. Corrige lo anterior y vuelve a ejecutar.")
    sys.exit(1)


print("=== Diagnóstico de la conexión con Gemini ===")
print(f"Modelo configurado: {llm_service.MODELO}")

# 1) API key
paso(1, "Buscando la API key...")
llave = llm_service._api_key()
if not llave:
    fallo(
        "No se encontró GEMINI_API_KEY. Copia el archivo .env.example como .env "
        "(en esta misma carpeta) y pega ahí tu clave."
    )
print(f"   ✓ Clave encontrada ({len(llave)} caracteres; por seguridad no se muestra).")
if not llave.startswith("AIza"):
    print("   ! Aviso: las claves de Google normalmente empiezan con 'AIza'. Revisa que la copiaste completa.")

# 2) SDK
paso(2, "Comprobando que el SDK de Google esté instalado...")
try:
    import google.genai  # noqa: F401
except ImportError:
    fallo("Falta el SDK. Ejecuta:  pip install -r requirements.txt")
print("   ✓ SDK instalado.")

# 3) Llamada mínima
paso(3, "Haciendo una consulta mínima a Gemini...")
try:
    from google import genai
    from google.genai import types

    cliente = genai.Client(
        api_key=llave,
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(attempts=1, http_status_codes=[599])
        ),
    )
    respuesta = cliente.interactions.create(
        model=llm_service.MODELO,
        input="Responde únicamente con la palabra: listo",
        timeout=llm_service.TIMEOUT_SEGUNDOS,
    )
    print(f"   ✓ Gemini respondió: {respuesta.output_text!r}")
except Exception as exc:  # se traduce a un mensaje claro
    fallo(str(llm_service._traducir_error(exc)) + f"\n     (detalle técnico: {type(exc).__name__}: {str(exc)[:300]})")

# 4) Receta completa por el mismo camino que usa la aplicación
paso(4, "Generando una receta de prueba con el flujo real de la aplicación...")
llm_service.PROVEEDOR = "gemini"
try:
    receta = llm_service.generar_receta(["pechuga de pollo", "crema", "champiñones"], 2)
except llm_service.ErrorGeneracion as exc:
    fallo(str(exc))

print(f"   ✓ Receta recibida y validada en {receta['meta']['segundos']} s")
print(f"\n   {receta['titulo']}  ({receta['comensales']} comensales, {receta['tiempo_minutos']} min)")
for ing in receta["ingredientes"]:
    print(f"     - {ing['nombre']}: {ing['cantidad']} {ing['unidad']}")
for i, texto in enumerate(receta["pasos"], 1):
    print(f"     {i}. {texto}")

print("\n=== ¡Todo funciona! Ya puedes ejecutar:  python app.py ===")
