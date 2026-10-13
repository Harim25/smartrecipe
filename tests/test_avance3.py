"""Pruebas de los refinamientos del Avance 3 (Actividad 4.2).

Cubren: normalización de cantidades, modo simulado como respaldo cuando Gemini
falla, datos del error que usa la interfaz y reglas nuevas del prompt.
No usan internet ni gastan cuota. Ejecutar:  python -m unittest discover -s tests -v
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database  # noqa: E402
import llm_service  # noqa: E402
from app import app  # noqa: E402
from prompts import SYSTEM_PROMPT  # noqa: E402


def receta(comensales=2, ingredientes=None):
    return {
        "viable": True,
        "titulo": "Pollo con arroz",
        "comensales": comensales,
        "ingredientes": ingredientes
        or [{"nombre": "pollo", "cantidad": 300, "unidad": "g"}],
        "pasos": ["Cocina el pollo."],
        "tiempo_minutos": 20,
        "nota": "",
    }


class ErrorSDK(Exception):
    def __init__(self, status_code=None, mensaje=""):
        super().__init__(mensaje)
        self.status_code = status_code


class TestNormalizacion(unittest.TestCase):
    def test_al_gusto_siempre_es_cero(self):
        self.assertEqual(llm_service._normalizar_cantidad(1, "al gusto"), 0)
        self.assertEqual(llm_service._normalizar_cantidad(0, "al gusto"), 0)

    def test_piezas_se_redondean_a_medios(self):
        self.assertEqual(llm_service._normalizar_cantidad(1.3, "pieza"), 1.5)
        self.assertEqual(llm_service._normalizar_cantidad(0.99, "pieza"), 1)
        self.assertEqual(llm_service._normalizar_cantidad(2, "pieza"), 2)

    def test_una_pieza_nunca_queda_en_cero(self):
        self.assertEqual(llm_service._normalizar_cantidad(0.1, "pieza"), 0.5)

    def test_gramos_y_mililitros_a_enteros(self):
        self.assertEqual(llm_service._normalizar_cantidad(152.6, "g"), 153)
        self.assertEqual(llm_service._normalizar_cantidad(22.5, "ml"), 22)
        self.assertEqual(llm_service._normalizar_cantidad(7.26, "g"), 7.3)

    def test_los_enteros_no_llevan_decimales(self):
        valor = llm_service._normalizar_cantidad(300.0, "g")
        self.assertIsInstance(valor, int)

    def test_validar_respuesta_normaliza_toda_la_receta(self):
        r = llm_service.validar_respuesta(
            receta(ingredientes=[
                {"nombre": " cebolla ", "cantidad": 0.66, "unidad": "pieza"},
                {"nombre": "sal", "cantidad": 1, "unidad": "al gusto"},
                {"nombre": "aceite", "cantidad": 14.9, "unidad": "ml"},
            ]),
            2,
        )
        self.assertEqual(
            [(i["nombre"], i["cantidad"]) for i in r["ingredientes"]],
            [("cebolla", 0.5), ("sal", 0), ("aceite", 15)],
        )


class TestRespaldoSimulado(unittest.TestCase):
    def test_forzar_simulado_no_llama_a_gemini(self):
        llamada = mock.Mock()
        with mock.patch.multiple(llm_service, PROVEEDOR="gemini", _llamar_gemini=llamada):
            r = llm_service.generar_receta(["arroz", "pollo"], 3, forzar_simulado=True)
        llamada.assert_not_called()
        self.assertEqual(r["meta"]["proveedor"], "simulado")
        self.assertTrue(r["meta"]["respaldo"])
        self.assertEqual(r["comensales"], 3)

    def test_en_modo_simulado_normal_no_es_respaldo(self):
        with mock.patch.object(llm_service, "PROVEEDOR", "simulado"):
            r = llm_service.generar_receta(["arroz"], 2)
        self.assertFalse(r["meta"]["respaldo"])

    def test_con_gemini_funcionando_no_es_respaldo(self):
        with mock.patch.multiple(
            llm_service, PROVEEDOR="gemini", _llamar_gemini=mock.Mock(return_value=json.dumps(receta()))
        ):
            r = llm_service.generar_receta(["pollo"], 2)
        self.assertEqual(r["meta"]["proveedor"], "gemini")
        self.assertFalse(r["meta"]["respaldo"])


class TestTipoDeError(unittest.TestCase):
    """La interfaz decide si ofrece el modo simulado según estos datos."""

    def test_limite_ofrece_simulado(self):
        e = llm_service._traducir_error(ErrorSDK(429, "RESOURCE_EXHAUSTED"))
        self.assertEqual((e.tipo, e.ofrecer_simulado), ("limite", True))

    def test_servidor_saturado_ofrece_simulado(self):
        e = llm_service._traducir_error(ErrorSDK(503, "UNAVAILABLE"))
        self.assertIsInstance(e, llm_service.ErrorServicio)
        self.assertTrue(e.ofrecer_simulado)

    def test_sin_conexion_ofrece_simulado(self):
        e = llm_service._traducir_error(ErrorSDK(None, "Connection refused"))
        self.assertTrue(e.ofrecer_simulado)

    def test_key_invalida_ofrece_simulado(self):
        e = llm_service._traducir_error(ErrorSDK(403, "API key not valid"))
        self.assertEqual((e.tipo, e.ofrecer_simulado), ("configuracion", True))

    def test_receta_no_viable_no_ofrece_simulado(self):
        # Si los ingredientes no son comestibles, el modo simulado no debe "cocinarlos".
        self.assertFalse(llm_service.RecetaNoViable.ofrecer_simulado)

    def test_respuesta_mal_formada_no_ofrece_simulado(self):
        self.assertFalse(llm_service.ErrorGeneracion.ofrecer_simulado)


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        database.RUTA_DB = Path(self.tmp.name)
        database.iniciar_db()
        self.c = app.test_client()

    def tearDown(self):
        os.unlink(self.tmp.name)

    def _pedir(self, **extra):
        return self.c.post(
            "/api/receta", json={"ingredientes": ["pollo", "arroz"], "comensales": 2, **extra}
        )

    def _gemini_falla_con(self, error):
        return mock.patch.multiple(
            llm_service, PROVEEDOR="gemini", _llamar_gemini=mock.Mock(side_effect=error)
        )

    def test_limite_responde_con_los_datos_para_el_aviso(self):
        with self._gemini_falla_con(llm_service.ErrorLimiteUso("límite")):
            r = self._pedir()
        self.assertEqual(r.status_code, 429)
        datos = r.get_json()
        self.assertEqual(datos["tipo"], "limite")
        self.assertTrue(datos["ofrecer_simulado"])
        self.assertEqual(self.c.get("/api/recetas").get_json(), [])  # no se guardó nada

    def test_aceptar_el_modo_simulado_genera_y_guarda_la_receta(self):
        llamada = mock.Mock(side_effect=llm_service.ErrorLimiteUso("límite"))
        with mock.patch.multiple(llm_service, PROVEEDOR="gemini", _llamar_gemini=llamada):
            r = self._pedir(modo="simulado")
        self.assertEqual(r.status_code, 201)
        meta = r.get_json()["receta"]["meta"]
        self.assertEqual((meta["proveedor"], meta["respaldo"]), ("simulado", True))
        llamada.assert_not_called()
        self.assertEqual(len(self.c.get("/api/recetas").get_json()), 1)

    def test_no_viable_no_ofrece_simulado(self):
        no_viable = json.dumps({"viable": False, "nota": "El jabón no es comestible."})
        with mock.patch.multiple(
            llm_service, PROVEEDOR="gemini", _llamar_gemini=mock.Mock(return_value=no_viable)
        ):
            r = self._pedir()
        self.assertEqual(r.status_code, 422)
        self.assertFalse(r.get_json()["ofrecer_simulado"])

    def test_un_modo_desconocido_se_ignora(self):
        with mock.patch.multiple(
            llm_service, PROVEEDOR="gemini", _llamar_gemini=mock.Mock(return_value=json.dumps(receta()))
        ):
            r = self._pedir(modo="otro")
        self.assertEqual(r.get_json()["receta"]["meta"]["proveedor"], "gemini")


class TestPromptRefinado(unittest.TestCase):
    def test_incluye_las_reglas_del_avance_3(self):
        for fragmento in ("proporcionales al número de comensales", "enteros o medios", "criterio culinario", '"cantidad": 0'):
            self.assertIn(fragmento, SYSTEM_PROMPT)


if __name__ == "__main__":
    unittest.main()
