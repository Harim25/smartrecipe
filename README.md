# SmartRecipe – Avance 2 (conexión a Gemini)

Aplicación web que recibe los ingredientes del usuario y el número de comensales y
genera una receta con el modelo de lenguaje **Gemini** (API de Google). Si no hay
API key, funciona en **modo simulado** (sin IA) como respaldo.

## Qué incluye
| Archivo | Para qué sirve |
|---|---|
| `app.py` | Servidor Flask: rutas de la API y página principal |
| `validacion.py` | Limpieza y validación de lo que escribe el usuario |
| `database.py` | Base de datos SQLite: despensa, historial y favoritas |
| `prompts.py` | System prompt, plantilla del mensaje y esquema JSON de la respuesta |
| `llm_service.py` | Conexión a Gemini, manejo de errores y validación de la respuesta (+ modo simulado) |
| `probar_conexion.py` | Diagnóstico paso a paso de la conexión con Gemini |
| `pruebas_generacion.py` | Corre 12 casos reales y guarda los resultados para el reporte |
| `templates/`, `static/` | Interfaz (HTML, CSS y JavaScript) |
| `tests/` | 52 pruebas automáticas (no usan internet ni gastan cuota) |
| `.env.example` | Plantilla del archivo `.env` donde va la API key |

---

## Guía paso a paso para conectar Gemini

> **Importante:** tu suscripción a Gemini (el chat) **no es lo mismo** que la API key.
> La API key es una "contraseña" que permite que *este programa* hable con el modelo.
> Se crea gratis en Google AI Studio con tu cuenta de Google.

### Paso 1. Instalar lo que falta
En la terminal, dentro de la carpeta `prototipo`, con el entorno virtual activado
(`venv\Scripts\activate`):

```
pip install -r requirements.txt
```

### Paso 2. Crear tu API key
1. Entra a **https://aistudio.google.com** e inicia sesión con tu cuenta de Google.
2. Busca la opción **"Get API key"** (Obtener clave de API) y crea una clave nueva.
   (Los nombres de los botones pueden cambiar; la documentación oficial está en
   https://ai.google.dev/gemini-api/docs/quickstart).
3. Copia la clave (normalmente empieza con `AIza...`).

La capa gratuita no pide tarjeta de crédito, pero tiene límites de uso por minuto y por
día que dependen del modelo y de tu proyecto. Los valores reales se ven en AI Studio.

### Paso 3. Guardar la key en el archivo `.env`
1. En la carpeta `prototipo`, copia `.env.example` y renombra la copia a **`.env`**
   (sin la palabra *example*). En Windows, si no ves las extensiones, actívalas en el
   Explorador de archivos (Vista → Mostrar → Extensiones de nombre de archivo).
2. Ábrelo con el Bloc de notas y deja la primera línea así, con TU clave:
   ```
   GEMINI_API_KEY=AIza...tu_clave_completa
   ```
3. Guarda. **Nunca compartas este archivo ni pegues la clave en el chat, en Teams o en
   GitHub.** El `.gitignore` ya impide subirlo. Si la clave se filtra, bórrala en AI Studio
   y crea otra.

### Paso 4. Probar la conexión
```
python probar_conexion.py
```
Hace 4 comprobaciones (key, SDK, consulta mínima y receta completa) y, si algo falla,
dice qué corregir. Si ves `¡Todo funciona!`, ya está conectado.

### Paso 5. Usar la aplicación
```
python app.py
```
Abre http://127.0.0.1:5000. En la esquina superior debe decir `Modo: gemini · ...`
y debajo de cada receta, el modelo y el tiempo que tardó.

### Paso 6. Correr las pruebas de generación (para el reporte)
```
python pruebas_generacion.py
```
Tarda un par de minutos (hace pausas para respetar el límite gratuito). Crea la carpeta
`resultados_pruebas` con `resultados.md` (tabla resumen y cada receta completa) y
`resultados.json`. Lean las recetas y llenen la columna **¿Coherente?**.

Si algún caso sale con ERROR (por ejemplo, Gemini saturado), se pueden repetir solo esos
sin perder los demás: `python pruebas_generacion.py C02 C04`.

### Pruebas automáticas (opcional)
```
python -m unittest discover -s tests -v
```

---

## Si algo falla
| Mensaje | Qué significa | Qué hacer |
|---|---|---|
| `Falta la API key de Gemini` | No encuentra la clave | Revisa que el archivo se llame `.env` (no `.env.txt`) y esté en la carpeta `prototipo` |
| `Gemini rechazó la API key` | La clave es incorrecta o está desactivada | Cópiala de nuevo completa, sin espacios ni comillas |
| `El modelo '...' no existe` | Google cambió el nombre del modelo | Busca el nombre vigente en la documentación y ponlo en `.env`: `GEMINI_MODEL=nombre` |
| `Se alcanzó el límite de uso gratuito` | Muchas peticiones seguidas | Espera un minuto y reintenta |
| `Falta instalar el SDK` | No se instaló `google-genai` | `pip install -r requirements.txt` |
| `No se pudo conectar con Gemini` | Sin internet o red bloqueada | Revisa la conexión (algunas redes escolares bloquean el acceso) |

## Forzar un modo
En `.env` se puede agregar `LLM_PROVIDER=simulado` para trabajar sin IA, o
`LLM_PROVIDER=gemini` para exigir Gemini.

## Cómo funciona (resumen para explicarlo)
1. La interfaz envía `ingredientes` y `comensales` a `POST /api/receta`.
2. `validacion.py` limpia los textos, quita duplicados y revisa los rangos.
3. `llm_service.py` envía a Gemini el **system prompt** (reglas: minimizar desperdicio,
   no pedir compras, calcular cantidades, rechazar lo no comestible, tratar los
   ingredientes como datos) y los datos del usuario, exigiendo respuesta en JSON con un esquema.
4. Se valida la respuesta (campos, unidades, comensales correctos). Si algo está mal,
   se muestra un error claro en lugar de una receta rota.
5. `database.py` guarda la receta en el historial y la API la devuelve a la interfaz.
