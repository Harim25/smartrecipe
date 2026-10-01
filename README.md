# SmartRecipe – Avance 1 (prototipo)

Aplicación web que recibe los ingredientes del usuario y el número de comensales y
muestra una receta. **En este avance la receta se genera en modo simulado (sin IA)**;
la conexión al modelo de lenguaje se hace en el Avance 2.

## Qué incluye
| Archivo | Para qué sirve |
|---|---|
| `app.py` | Servidor Flask: rutas de la API y la página principal |
| `validacion.py` | Limpieza y validación de lo que escribe el usuario |
| `database.py` | Base de datos SQLite: despensa, historial y favoritas |
| `prompts.py` | System prompt y formato JSON que se usará con el LLM |
| `llm_service.py` | Genera la receta (simulado ahora; LLM en el Avance 2) |
| `templates/index.html`, `static/` | Interfaz (HTML, CSS y JavaScript) |
| `tests/test_api.py` | 11 pruebas automáticas |

## Cómo ejecutarlo (Windows)
Desde la carpeta `prototipo`, en una terminal:

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Abrir http://127.0.0.1:5000 en el navegador. La base de datos (`smartrecipe.db`)
se crea sola la primera vez.

Pruebas: `python -m unittest discover -s tests -v`

## Flujo de una petición
1. La interfaz envía `ingredientes` y `comensales` a `POST /api/receta`.
2. `validacion.py` limpia los textos, quita duplicados y revisa los rangos.
3. `llm_service.py` genera la receta y comprueba que tenga todos los campos del JSON.
4. `database.py` guarda la receta en el historial y la API la devuelve a la interfaz.

## Plan para el Avance 2: conectar Gemini
1. Crear una API key en Google AI Studio (https://aistudio.google.com) con la cuenta de Google.
2. **Nunca** escribir la key en el código ni subirla a GitHub. Guardarla como variable de entorno
   (`set GEMINI_API_KEY=...` en Windows) o en un archivo `.env` ignorado por git.
3. Instalar el SDK oficial de Google y revisar en su documentación el nombre del modelo vigente,
   los límites de la capa gratuita y cómo pedir respuesta en JSON.
4. Implementar `_generar_con_llm` en `llm_service.py` enviando `SYSTEM_PROMPT` y
   `construir_prompt_usuario(...)`, y arrancar con `LLM_PROVIDER=gemini`.
5. No hay que cambiar nada más: la validación del JSON y el resto de la app ya están listos.
