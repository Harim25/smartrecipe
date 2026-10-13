"""SmartRecipe: servidor Flask (API + interfaz) conectado a Gemini, con cuentas de usuario.

Ejecutar:  python app.py   y abrir http://127.0.0.1:5000
"""

import os
from datetime import timedelta
from functools import wraps

from flask import Flask, g, jsonify, render_template, request, session

import cuentas
import database as db
import llm_service
from validacion import (
    ErrorValidacion,
    limpiar_ingrediente,
    limpiar_lista_ingredientes,
    validar_comensales,
)

# PRODUCCION=1 (en el archivo .env del servidor) indica que la aplicación está publicada
# en internet con HTTPS. llm_service ya cargó el .env al importarse.
EN_PRODUCCION = os.environ.get("PRODUCCION", "").strip().lower() in ("1", "true", "si", "sí")

app = Flask(__name__)
app.config.update(
    SECRET_KEY=cuentas.clave_de_sesion(),
    SESSION_COOKIE_HTTPONLY=True,     # el JavaScript de la página no puede leer la cookie
    SESSION_COOKIE_SAMESITE="Lax",    # otros sitios no pueden enviar peticiones con la sesión
    SESSION_COOKIE_SECURE=EN_PRODUCCION,  # publicada: la cookie solo viaja por HTTPS
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
)


def _error(mensaje, codigo=400):
    return jsonify({"error": mensaje}), codigo


def requiere_sesion(vista):
    """Solo deja pasar a usuarios con sesión iniciada; deja su id en g.usuario_id."""

    @wraps(vista)
    def envoltura(*args, **kwargs):
        usuario = db.usuario_por_id(session["usuario_id"]) if "usuario_id" in session else None
        if usuario is None:
            session.clear()
            return _error("Inicia sesión para continuar.", 401)
        g.usuario_id = usuario["id"]
        return vista(*args, **kwargs)

    return envoltura


@app.get("/")
def inicio():
    return render_template("index.html", proveedor=llm_service.descripcion_modo())


# ---------- Cuentas ----------
def _abrir_sesion(cuenta):
    session.clear()
    session.permanent = True
    session["usuario_id"] = cuenta["id"]
    return jsonify({"usuario": cuenta["usuario"]})


@app.get("/api/sesion")
def sesion_actual():
    usuario = db.usuario_por_id(session["usuario_id"]) if "usuario_id" in session else None
    return jsonify({"usuario": usuario["usuario"] if usuario else None})


@app.post("/api/registro")
def registro():
    datos = request.get_json(silent=True) or {}
    try:
        cuenta = cuentas.registrar(datos.get("usuario"), datos.get("password"))
    except cuentas.ErrorCuenta as e:
        return _error(str(e), e.codigo_http)
    respuesta = _abrir_sesion(cuenta)
    return respuesta, 201


@app.post("/api/sesion")
def entrar():
    datos = request.get_json(silent=True) or {}
    try:
        cuenta = cuentas.iniciar_sesion(datos.get("usuario"), datos.get("password"))
    except cuentas.ErrorCuenta as e:
        return _error(str(e), 401 if e.codigo_http == 400 else e.codigo_http)
    return _abrir_sesion(cuenta)


@app.delete("/api/sesion")
def salir():
    session.clear()
    return "", 204


# ---------- Generar receta ----------
@app.post("/api/receta")
@requiere_sesion
def generar():
    datos = request.get_json(silent=True) or {}
    try:
        ingredientes = limpiar_lista_ingredientes(datos.get("ingredientes"))
        comensales = validar_comensales(datos.get("comensales"))
    except ErrorValidacion as e:
        return _error(str(e))

    # El usuario puede pedir el modo simulado cuando Gemini no está disponible.
    forzar_simulado = datos.get("modo") == "simulado"
    try:
        receta = llm_service.generar_receta(ingredientes, comensales, forzar_simulado)
    except llm_service.ErrorGeneracion as e:
        return (
            jsonify({"error": str(e), "tipo": e.tipo, "ofrecer_simulado": e.ofrecer_simulado}),
            e.codigo_http,
        )

    return jsonify(db.guardar_receta(g.usuario_id, ingredientes, receta)), 201


# ---------- Historial y favoritas ----------
@app.get("/api/recetas")
@requiere_sesion
def historial():
    solo_fav = request.args.get("favoritas") == "1"
    return jsonify(db.listar_recetas(g.usuario_id, solo_favoritas=solo_fav))


@app.post("/api/recetas/<int:id_>/favorita")
@requiere_sesion
def favorita(id_):
    receta = db.alternar_favorita(g.usuario_id, id_)
    if receta is None:
        return _error("Receta no encontrada.", 404)
    return jsonify(receta)


@app.delete("/api/recetas/<int:id_>")
@requiere_sesion
def borrar_receta(id_):
    if not db.borrar_receta(g.usuario_id, id_):
        return _error("Receta no encontrada.", 404)
    return "", 204


# ---------- Despensa ----------
@app.get("/api/despensa")
@requiere_sesion
def despensa():
    return jsonify(db.listar_despensa(g.usuario_id))


@app.post("/api/despensa")
@requiere_sesion
def despensa_agregar():
    datos = request.get_json(silent=True) or {}
    nombre = limpiar_ingrediente(datos.get("nombre"))
    if not nombre:
        return _error("Escribe un ingrediente válido.")
    return jsonify(db.agregar_a_despensa(g.usuario_id, nombre)), 201


@app.delete("/api/despensa/<int:id_>")
@requiere_sesion
def despensa_borrar(id_):
    if not db.borrar_de_despensa(g.usuario_id, id_):
        return _error("Ingrediente no encontrado.", 404)
    return "", 204


db.iniciar_db()

if __name__ == "__main__":
    # El modo de depuración solo se usa al ejecutar en la computadora propia; nunca en
    # producción, porque muestra el código y permite ejecutar instrucciones desde el navegador.
    app.run(debug=not EN_PRODUCCION)
