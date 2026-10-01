"""SmartRecipe - Avance 1: servidor Flask (API + interfaz).

Ejecutar:  python app.py   y abrir http://127.0.0.1:5000
"""

from flask import Flask, jsonify, render_template, request

import database as db
import llm_service
from validacion import (
    ErrorValidacion,
    limpiar_ingrediente,
    limpiar_lista_ingredientes,
    validar_comensales,
)

app = Flask(__name__)


def _error(mensaje, codigo=400):
    return jsonify({"error": mensaje}), codigo


@app.get("/")
def inicio():
    return render_template("index.html", proveedor=llm_service.PROVEEDOR)


# ---------- Generar receta ----------
@app.post("/api/receta")
def generar():
    datos = request.get_json(silent=True) or {}
    try:
        ingredientes = limpiar_lista_ingredientes(datos.get("ingredientes"))
        comensales = validar_comensales(datos.get("comensales"))
    except ErrorValidacion as e:
        return _error(str(e))

    try:
        receta = llm_service.generar_receta(ingredientes, comensales)
    except llm_service.ErrorGeneracion as e:
        return _error(str(e), 502)

    return jsonify(db.guardar_receta(ingredientes, receta)), 201


# ---------- Historial y favoritas ----------
@app.get("/api/recetas")
def historial():
    solo_fav = request.args.get("favoritas") == "1"
    return jsonify(db.listar_recetas(solo_favoritas=solo_fav))


@app.post("/api/recetas/<int:id_>/favorita")
def favorita(id_):
    receta = db.alternar_favorita(id_)
    if receta is None:
        return _error("Receta no encontrada.", 404)
    return jsonify(receta)


@app.delete("/api/recetas/<int:id_>")
def borrar_receta(id_):
    if not db.borrar_receta(id_):
        return _error("Receta no encontrada.", 404)
    return "", 204


# ---------- Despensa ----------
@app.get("/api/despensa")
def despensa():
    return jsonify(db.listar_despensa())


@app.post("/api/despensa")
def despensa_agregar():
    datos = request.get_json(silent=True) or {}
    nombre = limpiar_ingrediente(datos.get("nombre"))
    if not nombre:
        return _error("Escribe un ingrediente válido.")
    return jsonify(db.agregar_a_despensa(nombre)), 201


@app.delete("/api/despensa/<int:id_>")
def despensa_borrar(id_):
    if not db.borrar_de_despensa(id_):
        return _error("Ingrediente no encontrado.", 404)
    return "", 204


db.iniciar_db()

if __name__ == "__main__":
    app.run(debug=True)
