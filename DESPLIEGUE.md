# Publicar SmartRecipe en internet (PythonAnywhere, plan gratuito)

Guía para dejar la aplicación en `https://TU-USUARIO.pythonanywhere.com`.
En todos los pasos, cambia `TU-USUARIO` por tu nombre de usuario de PythonAnywhere.

> Los nombres de los botones pueden cambiar con el tiempo. La documentación oficial está en
> https://help.pythonanywhere.com/pages/Flask/

## Antes de empezar
- El plan gratuito **apaga la aplicación si no se renueva cada mes**: hay que entrar a la
  pestaña **Web** y pulsar el botón de extender.
- Cualquier persona con el enlace puede crear una cuenta y gastar la cuota diaria de la API
  key de Gemini. Cuando se acaba, la página ofrece el modo simulado.
- La API key y la clave de sesión **no se suben con el código**: se escriben a mano en el
  servidor (paso 4).

## Paso 1. Crear la cuenta
Entra a https://www.pythonanywhere.com y crea una cuenta gratuita ("Beginner").

## Paso 2. Bajar el código
En la pestaña **Consoles**, abre una consola **Bash** y ejecuta:

```
git clone https://github.com/Harim25/smartrecipe.git
```

Queda en la carpeta `/home/TU-USUARIO/smartrecipe`.

## Paso 3. Crear el entorno e instalar las bibliotecas
En la misma consola (usa la versión de Python más reciente que ofrezca PythonAnywhere;
la aplicación necesita 3.10 o superior):

```
mkvirtualenv --python=/usr/bin/python3.13 smartrecipe-env
pip install -r ~/smartrecipe/requirements.txt
```

Recuerda qué versión de Python elegiste: se vuelve a pedir en el paso 5.

## Paso 4. Escribir las claves en el servidor
Genera la clave de las sesiones y cópiala:

```
python -c "import secrets; print(secrets.token_hex(32))"
```

Crea el archivo de configuración:

```
nano ~/smartrecipe/.env
```

Escribe estas tres líneas con tus valores (sin comillas ni espacios):

```
GEMINI_API_KEY=tu_api_key_de_gemini
SECRET_KEY=la_clave_que_generaste
PRODUCCION=1
```

Guarda con `Ctrl+O`, `Enter`, y sal con `Ctrl+X`. Después protege el archivo para que solo
tu usuario pueda leerlo:

```
chmod 600 ~/smartrecipe/.env
```

## Paso 5. Crear la aplicación web
1. Ve a la pestaña **Web** y pulsa **Add a new web app**.
2. Elige **Manual configuration** (no "Flask") y la **misma versión de Python** del paso 3.
3. En la sección **Virtualenv**, escribe `smartrecipe-env` y confirma. Debe quedar como
   `/home/TU-USUARIO/.virtualenvs/smartrecipe-env`.
4. En **Source code** y **Working directory**, escribe `/home/TU-USUARIO/smartrecipe`.

## Paso 6. Conectar la aplicación (archivo WSGI)
En la pestaña **Web**, abre el enlace **WSGI configuration file**, borra todo su contenido y
deja solo esto:

```python
import sys

path = '/home/TU-USUARIO/smartrecipe'
if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application
```

Guarda el archivo.

## Paso 7. Encender y probar
1. En la pestaña **Web**, pulsa el botón verde **Reload**.
2. Abre `https://TU-USUARIO.pythonanywhere.com`. Debe aparecer la pantalla de acceso.
3. Crea una cuenta y genera una receta.
   - Si arriba dice `Modo: gemini · ...` y la receta trae "Generada con gemini-...", todo funciona.
   - Si aparece el aviso "La IA no está disponible", revisa el paso 8.

## Paso 8. Si algo falla
- **La página muestra un error ("Something went wrong")**: en la pestaña **Web** abre el
  **Error log**; las últimas líneas dicen qué pasó. Lo más común es una ruta mal escrita en
  el archivo WSGI o una biblioteca sin instalar.
- **Dice `Modo: simulado`**: no encontró la API key. Revisa que el archivo se llame `.env`,
  esté en `~/smartrecipe` y que la línea empiece con `GEMINI_API_KEY=`. Luego pulsa **Reload**.
- **Gemini no responde desde el servidor**: comprueba la conexión desde la consola:

  ```
  workon smartrecipe-env
  cd ~/smartrecipe
  python probar_conexion.py
  ```

  El plan gratuito solo permite conectarse a una lista de sitios; `googleapis.com` está en
  ella, pero si la prueba indica que no hay conexión, ese es el motivo.
- **No se puede iniciar sesión (entra y vuelve a salir)**: abre la página con `https://`,
  no con `http://`. Con `PRODUCCION=1` la sesión solo viaja por conexión segura.

## Actualizar la aplicación después de un cambio
```
cd ~/smartrecipe
git pull
```
y pulsa **Reload** en la pestaña **Web**. Si cambió `requirements.txt`, ejecuta antes
`workon smartrecipe-env` y `pip install -r requirements.txt`.

## Dónde quedan los datos
Las cuentas y las recetas están en `/home/TU-USUARIO/smartrecipe/smartrecipe.db`. Para
empezar desde cero, borra ese archivo y pulsa **Reload**.
