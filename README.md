# SmartRecipe – Avance 3 (pruebas de calidad y refinamiento)

Aplicación web que recibe los ingredientes del usuario y el número de comensales y
genera una receta con el modelo de lenguaje **Gemini** (API de Google). Si no hay
API key, funciona en **modo simulado** (sin IA) como respaldo.

## Cuentas de usuario
Para usar la aplicación hay que crear una cuenta (usuario y contraseña). Cada cuenta tiene
su propia despensa, historial y favoritas; nadie puede ver ni borrar los datos de otra.

- La contraseña se guarda **cifrada con hash y sal**; no se puede leer ni desde la base de datos.
- La sesión dura 7 días en el navegador y se cierra con **Cerrar sesión**.
- Tras 5 intentos fallidos seguidos, la cuenta se bloquea un minuto.
- **No hay recuperación de contraseña** (no se pide correo): si se olvida, hay que crear otra cuenta.
- Si ya tenías recetas guardadas de una versión anterior, pasan a la **primera cuenta** que se registre.
- La clave que firma las sesiones se genera sola en el archivo `.clave_sesion` (ignorado por
  Git). Para un servidor público conviene definirla con la variable `SECRET_KEY` y usar HTTPS.

## Novedades del Avance 3
- **Respaldo cuando la IA no responde:** si se acaba el límite gratuito, Gemini está
  saturado o no hay conexión, la página muestra un aviso y el usuario elige entre usar el
  modo simulado, reintentar con IA o cancelar. Los ingredientes capturados se conservan.
- **Estado de carga:** mientras se genera la receta se muestra un indicador con los
  segundos transcurridos, y no se puede enviar una segunda petición por error.
- **Diseño adaptable:** el contenido usa el ancho de la pantalla; en pantallas grandes los
  ingredientes y la preparación se muestran lado a lado, y en celular en una sola columna.
- **Cantidades uniformes:** el prompt pide cantidades proporcionales a los comensales y el
  servidor normaliza la respuesta ("al gusto" sin número, piezas en enteros o medios,
  gramos y mililitros en enteros).
- **Logo** del proyecto en el encabezado y en la pestaña del navegador.

## Qué incluye
| Archivo | Para qué sirve |
|---|---|
| `app.py` | Servidor Flask: rutas de la API y página principal |
| `validacion.py` | Limpieza y validación de lo que escribe el usuario |
| `cuentas.py` | Cuentas de usuario: registro, inicio de sesión y bloqueo por intentos fallidos |
| `database.py` | Base de datos SQLite: usuarios, y la despensa, el historial y las favoritas de cada uno |
| `prompts.py` | System prompt, plantilla del mensaje y esquema JSON de la respuesta |
| `llm_service.py` | Conexión a Gemini, manejo de errores y validación de la respuesta (+ modo simulado) |
| `probar_conexion.py` | Diagnóstico paso a paso de la conexión con Gemini |
| `pruebas_generacion.py` | Corre 12 casos reales y guarda los resultados para el reporte |
| `templates/`, `static/` | Interfaz (HTML, CSS y JavaScript) |
| `tests/` | 89 pruebas automáticas (no usan internet ni gastan cuota) |
| `.env.example` | Plantilla del archivo `.env` donde va la API key |
| `DESPLIEGUE.md` | Guía paso a paso para publicar la aplicación en internet |

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
| `Se alcanzó el límite de uso gratuito` | Se agotó el límite por minuto o el diario | Espera un minuto y reintenta; si era el diario, usa el modo simulado desde el aviso de la página |
| `Falta instalar el SDK` | No se instaló `google-genai` | `pip install -r requirements.txt` |
| `No se pudo conectar con Gemini` | Sin internet o red bloqueada | Revisa la conexión (algunas redes escolares bloquean el acceso) |

## Forzar un modo
En `.env` se puede agregar `LLM_PROVIDER=simulado` para trabajar sin IA, o
`LLM_PROVIDER=gemini` para exigir Gemini.

## Cómo funciona (resumen para explicarlo)
1. El usuario inicia sesión. La interfaz envía `ingredientes` y `comensales` a `POST /api/receta`.
2. `validacion.py` limpia los textos, quita duplicados y revisa los rangos.
3. `llm_service.py` envía a Gemini el **system prompt** (reglas: minimizar desperdicio,
   no pedir compras, calcular cantidades, rechazar lo no comestible, tratar los
   ingredientes como datos) y los datos del usuario, exigiendo respuesta en JSON con un esquema.
4. Se valida la respuesta (campos, unidades, comensales correctos) y se normalizan las
   cantidades. Si algo está mal, se muestra un error claro en lugar de una receta rota; si
   el problema es que Gemini no respondió, se ofrece continuar en modo simulado.
5. `database.py` guarda la receta en el historial de ese usuario y la API la devuelve a la interfaz.
