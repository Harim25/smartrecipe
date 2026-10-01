"""Pruebas automáticas del Avance 1. Ejecutar:  python -m unittest discover -s tests -v"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database  # noqa: E402
from app import app  # noqa: E402
from validacion import (  # noqa: E402
    ErrorValidacion, limpiar_ingrediente, limpiar_lista_ingredientes, validar_comensales,
)


class TestValidacion(unittest.TestCase):
    def test_limpia_simbolos_y_espacios(self):
        self.assertEqual(limpiar_ingrediente("  Pechuga   de POLLO!! "), "pechuga de pollo")

    def test_quita_html(self):
        self.assertEqual(limpiar_ingrediente("<script>alert(1)</script>"), "scriptalertscript")

    def test_duplicados_y_vacios(self):
        self.assertEqual(limpiar_lista_ingredientes(["Arroz", "arroz", "  ", "Crema"]), ["arroz", "crema"])

    def test_lista_vacia(self):
        with self.assertRaises(ErrorValidacion):
            limpiar_lista_ingredientes(["!!!", ""])

    def test_limite_de_ingredientes(self):
        with self.assertRaises(ErrorValidacion):
            limpiar_lista_ingredientes(["a" * (i + 1) for i in range(21)])

    def test_comensales(self):
        self.assertEqual(validar_comensales("4"), 4)
        for malo in (0, 21, "abc", None):
            with self.assertRaises(ErrorValidacion):
                validar_comensales(malo)


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        database.RUTA_DB = Path(self.tmp.name)
        database.iniciar_db()
        self.c = app.test_client()

    def tearDown(self):
        os.unlink(self.tmp.name)

    def _generar(self, ing=("pechuga de pollo", "crema", "champiñones"), n=2):
        return self.c.post("/api/receta", json={"ingredientes": list(ing), "comensales": n})

    def test_generar_receta_estructura(self):
        r = self._generar()
        self.assertEqual(r.status_code, 201)
        rec = r.get_json()["receta"]
        for campo in ("titulo", "comensales", "ingredientes", "pasos", "tiempo_minutos", "nota"):
            self.assertIn(campo, rec)

    def test_proporciones_escalan_con_comensales(self):
        a = {i["nombre"]: i["cantidad"] for i in self._generar(n=2).get_json()["receta"]["ingredientes"]}
        b = {i["nombre"]: i["cantidad"] for i in self._generar(n=4).get_json()["receta"]["ingredientes"]}
        self.assertEqual(b["pechuga de pollo"], 2 * a["pechuga de pollo"])

    def test_entradas_invalidas(self):
        self.assertEqual(self.c.post("/api/receta", json={"ingredientes": [], "comensales": 2}).status_code, 400)
        self.assertEqual(self.c.post("/api/receta", json={"ingredientes": ["arroz"], "comensales": 99}).status_code, 400)
        self.assertEqual(self.c.post("/api/receta", data="no es json").status_code, 400)

    def test_historial_favorita_y_borrado(self):
        id_ = self._generar().get_json()["id"]
        self.assertEqual(len(self.c.get("/api/recetas").get_json()), 1)
        self.assertEqual(len(self.c.get("/api/recetas?favoritas=1").get_json()), 0)
        self.assertTrue(self.c.post(f"/api/recetas/{id_}/favorita").get_json()["favorita"])
        self.assertEqual(len(self.c.get("/api/recetas?favoritas=1").get_json()), 1)
        self.assertEqual(self.c.delete(f"/api/recetas/{id_}").status_code, 204)
        self.assertEqual(self.c.delete(f"/api/recetas/{id_}").status_code, 404)

    def test_despensa(self):
        self.assertEqual(self.c.post("/api/despensa", json={"nombre": "Tomate"}).status_code, 201)
        self.c.post("/api/despensa", json={"nombre": "tomate"})  # duplicado: no se repite
        lista = self.c.get("/api/despensa").get_json()
        self.assertEqual([i["nombre"] for i in lista], ["tomate"])
        self.assertEqual(self.c.delete(f"/api/despensa/{lista[0]['id']}").status_code, 204)
        self.assertEqual(self.c.post("/api/despensa", json={"nombre": "!!!"}).status_code, 400)


if __name__ == "__main__":
    unittest.main()
