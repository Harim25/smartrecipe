"""Pruebas de las cuentas de usuario: registro, sesión y separación de datos.

No usan internet ni gastan cuota. Ejecutar:  python -m unittest discover -s tests -v
"""
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cuentas  # noqa: E402
import database  # noqa: E402
import llm_service  # noqa: E402
from app import app  # noqa: E402

CLAVE = "clave-segura-1"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        database.RUTA_DB = Path(self.tmp.name)
        database.iniciar_db()
        cuentas._intentos.clear()
        self.parche = mock.patch.object(llm_service, "PROVEEDOR", "simulado")
        self.parche.start()

    def tearDown(self):
        self.parche.stop()
        os.unlink(self.tmp.name)

    def cliente(self, usuario=None):
        """Un navegador nuevo; si se da un usuario, ya registrado y con sesión."""
        c = app.test_client()
        if usuario:
            r = c.post("/api/registro", json={"usuario": usuario, "password": CLAVE})
            self.assertEqual(r.status_code, 201)
        return c


class TestRegistro(Base):
    def test_registro_correcto_abre_la_sesion(self):
        c = self.cliente()
        r = c.post("/api/registro", json={"usuario": "Ana_01", "password": CLAVE})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.get_json(), {"usuario": "ana_01"})  # se guarda en minúsculas
        self.assertEqual(c.get("/api/sesion").get_json(), {"usuario": "ana_01"})

    def test_la_contrasena_no_se_guarda_en_texto(self):
        self.cliente("ana")
        with sqlite3.connect(self.tmp.name) as con:
            guardado = con.execute("SELECT password_hash FROM usuarios").fetchone()[0]
        con.close()
        self.assertNotIn(CLAVE, guardado)
        self.assertGreater(len(guardado), 50)

    def test_dos_cuentas_con_la_misma_clave_tienen_hash_distinto(self):
        self.cliente("ana")
        self.cliente("beto")
        con = sqlite3.connect(self.tmp.name)
        hashes = [f[0] for f in con.execute("SELECT password_hash FROM usuarios")]
        con.close()
        self.assertNotEqual(hashes[0], hashes[1])  # cada hash lleva su propia sal

    def test_usuario_repetido(self):
        self.cliente("ana")
        r = self.cliente().post("/api/registro", json={"usuario": "ANA", "password": CLAVE})
        self.assertEqual(r.status_code, 400)
        self.assertIn("ya está en uso", r.get_json()["error"])

    def test_datos_invalidos(self):
        c = self.cliente()
        malos = [
            {"usuario": "ab", "password": CLAVE},              # usuario muy corto
            {"usuario": "a" * 21, "password": CLAVE},          # usuario muy largo
            {"usuario": "ana maría", "password": CLAVE},       # espacios y acentos
            {"usuario": "<script>", "password": CLAVE},        # símbolos
            {"usuario": "ana", "password": "corta"},           # contraseña corta
            {"usuario": "anabanana", "password": "anabanana"}, # igual al usuario
            {"usuario": "ana"},                                # sin contraseña
            {},
        ]
        for datos in malos:
            with self.subTest(datos=datos):
                self.assertEqual(c.post("/api/registro", json=datos).status_code, 400)
        self.assertEqual(c.get("/api/sesion").get_json(), {"usuario": None})


class TestSesion(Base):
    def test_entrar_y_salir(self):
        self.cliente("ana")
        c = self.cliente()
        self.assertEqual(c.get("/api/sesion").get_json(), {"usuario": None})
        r = c.post("/api/sesion", json={"usuario": "ana", "password": CLAVE})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(c.get("/api/despensa").status_code, 200)
        self.assertEqual(c.delete("/api/sesion").status_code, 204)
        self.assertEqual(c.get("/api/despensa").status_code, 401)

    def test_el_error_no_revela_si_el_usuario_existe(self):
        self.cliente("ana")
        c = self.cliente()
        mala = c.post("/api/sesion", json={"usuario": "ana", "password": "otra-clave-9"})
        nadie = c.post("/api/sesion", json={"usuario": "noexiste", "password": CLAVE})
        self.assertEqual((mala.status_code, nadie.status_code), (401, 401))
        self.assertEqual(mala.get_json(), nadie.get_json())

    def test_bloqueo_tras_varios_intentos_fallidos(self):
        self.cliente("ana")
        c = self.cliente()
        for _ in range(cuentas.MAX_INTENTOS):
            self.assertEqual(c.post("/api/sesion", json={"usuario": "ana", "password": "mala-clave-0"}).status_code, 401)
        # Ya bloqueada: ni con la contraseña correcta entra
        self.assertEqual(c.post("/api/sesion", json={"usuario": "ana", "password": CLAVE}).status_code, 429)
        # Pasado el tiempo de bloqueo vuelve a funcionar
        with mock.patch.object(cuentas.time, "time", return_value=cuentas.time.time() + cuentas.BLOQUEO_SEGUNDOS + 1):
            self.assertEqual(c.post("/api/sesion", json={"usuario": "ana", "password": CLAVE}).status_code, 200)

    def test_el_bloqueo_de_una_cuenta_no_afecta_a_otra(self):
        self.cliente("ana")
        self.cliente("beto")
        c = self.cliente()
        for _ in range(cuentas.MAX_INTENTOS):
            c.post("/api/sesion", json={"usuario": "ana", "password": "mala-clave-0"})
        self.assertEqual(c.post("/api/sesion", json={"usuario": "beto", "password": CLAVE}).status_code, 200)

    def test_sin_sesion_todas_las_rutas_de_datos_responden_401(self):
        c = self.cliente()
        peticiones = [
            c.post("/api/receta", json={"ingredientes": ["arroz"], "comensales": 2}),
            c.get("/api/recetas"),
            c.post("/api/recetas/1/favorita"),
            c.delete("/api/recetas/1"),
            c.get("/api/despensa"),
            c.post("/api/despensa", json={"nombre": "arroz"}),
            c.delete("/api/despensa/1"),
        ]
        self.assertEqual([r.status_code for r in peticiones], [401] * 7)

    def test_una_cookie_falsificada_no_sirve(self):
        c = self.cliente()
        c.set_cookie("session", "eyJ1c3VhcmlvX2lkIjoxfQ.falsa.firma")
        self.assertEqual(c.get("/api/despensa").status_code, 401)

    def test_la_sesion_de_una_cuenta_borrada_deja_de_valer(self):
        c = self.cliente("ana")
        con = sqlite3.connect(self.tmp.name)
        con.execute("DELETE FROM usuarios")
        con.commit()
        con.close()
        self.assertEqual(c.get("/api/despensa").status_code, 401)


class TestDatosSeparados(Base):
    def setUp(self):
        super().setUp()
        self.ana = self.cliente("ana")
        self.beto = self.cliente("beto")

    def _receta(self, c):
        r = c.post("/api/receta", json={"ingredientes": ["pollo", "arroz"], "comensales": 2})
        self.assertEqual(r.status_code, 201)
        return r.get_json()["id"]

    def test_cada_quien_ve_solo_su_historial(self):
        self._receta(self.ana)
        self.assertEqual(len(self.ana.get("/api/recetas").get_json()), 1)
        self.assertEqual(self.beto.get("/api/recetas").get_json(), [])

    def test_no_se_puede_tocar_la_receta_de_otro(self):
        id_ = self._receta(self.ana)
        self.assertEqual(self.beto.post(f"/api/recetas/{id_}/favorita").status_code, 404)
        self.assertEqual(self.beto.delete(f"/api/recetas/{id_}").status_code, 404)
        receta = self.ana.get("/api/recetas").get_json()[0]
        self.assertFalse(receta["favorita"])  # sigue ahí y sin cambios

    def test_las_favoritas_son_de_cada_usuario(self):
        self.ana.post(f"/api/recetas/{self._receta(self.ana)}/favorita")
        self._receta(self.beto)
        self.assertEqual(len(self.ana.get("/api/recetas?favoritas=1").get_json()), 1)
        self.assertEqual(self.beto.get("/api/recetas?favoritas=1").get_json(), [])

    def test_la_despensa_es_de_cada_usuario(self):
        id_ = self.ana.post("/api/despensa", json={"nombre": "tomate"}).get_json()["id"]
        # Beto puede tener el mismo ingrediente sin chocar con el de Ana
        self.assertEqual(self.beto.post("/api/despensa", json={"nombre": "tomate"}).status_code, 201)
        self.beto.post("/api/despensa", json={"nombre": "cebolla"})
        self.assertEqual([i["nombre"] for i in self.ana.get("/api/despensa").get_json()], ["tomate"])
        self.assertEqual(self.beto.delete(f"/api/despensa/{id_}").status_code, 404)
        self.assertEqual(len(self.ana.get("/api/despensa").get_json()), 1)


class TestMigracion(unittest.TestCase):
    """Una base creada antes de las cuentas no pierde sus datos."""

    def test_los_datos_anteriores_pasan_a_la_primera_cuenta(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        con = sqlite3.connect(tmp.name)
        con.executescript(
            """
            CREATE TABLE despensa (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE,
                                   creado TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE recetas (id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT NOT NULL,
                                  comensales INTEGER NOT NULL, ingredientes_usuario TEXT NOT NULL,
                                  receta TEXT NOT NULL, favorita INTEGER NOT NULL DEFAULT 0,
                                  creada TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            INSERT INTO despensa (nombre) VALUES ('arroz'), ('pollo');
            INSERT INTO recetas (titulo, comensales, ingredientes_usuario, receta, favorita)
                VALUES ('Arroz con pollo', 2, '["arroz","pollo"]', '{"titulo":"Arroz con pollo"}', 1);
            """
        )
        con.commit()
        con.close()
        try:
            database.RUTA_DB = Path(tmp.name)
            database.iniciar_db()
            database.iniciar_db()  # ejecutarla dos veces no debe romper nada
            primera = database.crear_usuario("primera", "hash")
            segunda = database.crear_usuario("segunda", "hash")
            self.assertEqual([i["nombre"] for i in database.listar_despensa(primera["id"])], ["arroz", "pollo"])
            recetas = database.listar_recetas(primera["id"])
            self.assertEqual([(r["titulo"], r["favorita"]) for r in recetas], [("Arroz con pollo", True)])
            self.assertEqual(database.listar_despensa(segunda["id"]), [])
            self.assertEqual(database.listar_recetas(segunda["id"]), [])
        finally:
            os.unlink(tmp.name)


if __name__ == "__main__":
    unittest.main()
