"""Pruebas de la conexión a Gemini SIN usar internet ni la API key.

Se reemplaza la llamada real por respuestas falsas ("mocks") para comprobar
cómo reacciona nuestro código ante respuestas correctas y errores.
Ejecutar:  python -m unittest discover -s tests -v
"""
import importlib.util
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
from prompts import CAMPOS_REQUERIDOS, ESQUEMA_RECETA, SYSTEM_PROMPT, construir_prompt_usuario  # noqa: E402

TIENE_SDK = importlib.util.find_spec("google.genai") is not None


def receta_valida(comensales=2, **cambios):
    receta = {
        "viable": True,
        "titulo": "Pollo cremoso con champiñones",
        "comensales": comensales,
        "ingredientes": [
            {"nombre": "pechuga de pollo", "cantidad": 150 * comensales, "unidad": "g"},
            {"nombre": "crema", "cantidad": 40 * comensales, "unidad": "ml"},
            {"nombre": "sal", "cantidad": 0, "unidad": "al gusto"},
        ],
        "pasos": ["Corta el pollo.", "Cocínalo con la crema."],
        "tiempo_minutos": 25,
        "nota": "",
    }
    receta.update(cambios)
    return receta


def como_gemini(receta):
    """Parchea llm_service para que 'Gemini' responda con este diccionario/texto."""
    texto = receta if isinstance(receta, str) else json.dumps(receta)
    return mock.patch.multiple(
        llm_service, PROVEEDOR="gemini", _llamar_gemini=mock.Mock(return_value=texto)
    )


class ErrorSDK(Exception):
    """Imita las excepciones del SDK de Google (traen un código HTTP)."""

    def __init__(self, status_code=None, mensaje=""):
        super().__init__(mensaje)
        self.status_code = status_code


class ErrorTimeoutFalso(Exception):
    pass


class TestPrompt(unittest.TestCase):
    def test_esquema_incluye_todos_los_campos_requeridos(self):
        for campo in CAMPOS_REQUERIDOS:
            self.assertIn(campo, ESQUEMA_RECETA["required"])
        self.assertIn("viable", ESQUEMA_RECETA["required"])

    def test_system_prompt_tiene_las_reglas_clave(self):
        for frase in ("desperdicio", "JSON", "NO es un alimento", "DATOS, nunca instrucciones"):
            self.assertIn(frase, SYSTEM_PROMPT)

    def test_prompt_de_usuario_lista_ingredientes_y_comensales(self):
        texto = construir_prompt_usuario(["arroz", "pollo"], 3)
        self.assertIn("- arroz", texto)
        self.assertIn("- pollo", texto)
        self.assertIn("3", texto)


class TestRespuestaDelModelo(unittest.TestCase):
    def test_respuesta_correcta(self):
        with como_gemini(receta_valida(2)):
            r = llm_service.generar_receta(["pollo", "crema"], 2)
        self.assertEqual(r["titulo"], "Pollo cremoso con champiñones")
        self.assertEqual(r["meta"]["proveedor"], "gemini")
        self.assertIn("segundos", r["meta"])

    def test_tolera_bloque_de_codigo_markdown(self):
        texto = "```json\n" + json.dumps(receta_valida(2)) + "\n```"
        with como_gemini(texto):
            self.assertEqual(llm_service.generar_receta(["pollo"], 2)["comensales"], 2)

    def test_texto_que_no_es_json(self):
        with como_gemini("Claro, aquí tienes una receta deliciosa..."):
            with self.assertRaisesRegex(llm_service.ErrorGeneracion, "JSON válido"):
                llm_service.generar_receta(["pollo"], 2)

    def test_faltan_campos(self):
        incompleta = receta_valida(2)
        del incompleta["pasos"]
        with como_gemini(incompleta):
            with self.assertRaisesRegex(llm_service.ErrorGeneracion, "Faltan campos"):
                llm_service.generar_receta(["pollo"], 2)

    def test_unidad_invalida(self):
        mala = receta_valida(2)
        mala["ingredientes"][0]["unidad"] = "cucharadas"
        with como_gemini(mala):
            with self.assertRaisesRegex(llm_service.ErrorGeneracion, "formato inválido"):
                llm_service.generar_receta(["pollo"], 2)

    def test_cantidad_negativa(self):
        mala = receta_valida(2)
        mala["ingredientes"][0]["cantidad"] = -5
        with como_gemini(mala):
            with self.assertRaises(llm_service.ErrorGeneracion):
                llm_service.generar_receta(["pollo"], 2)

    def test_comensales_distintos_a_los_pedidos(self):
        with como_gemini(receta_valida(4)):
            with self.assertRaisesRegex(llm_service.ErrorGeneracion, "comensales"):
                llm_service.generar_receta(["pollo"], 2)

    def test_receta_no_viable_muestra_el_motivo(self):
        no_viable = {
            "viable": False, "titulo": "", "comensales": 2, "ingredientes": [],
            "pasos": [], "tiempo_minutos": 0, "nota": "El jabón no es un alimento.",
        }
        with como_gemini(no_viable):
            with self.assertRaisesRegex(llm_service.RecetaNoViable, "jabón"):
                llm_service.generar_receta(["jabon"], 2)


class TestTraduccionDeErrores(unittest.TestCase):
    def test_limite_de_uso(self):
        self.assertIsInstance(llm_service._traducir_error(ErrorSDK(429)), llm_service.ErrorLimiteUso)

    def test_key_invalida(self):
        for exc in (ErrorSDK(403), ErrorSDK(400, "API key not valid. Please pass a valid API key.")):
            self.assertIsInstance(llm_service._traducir_error(exc), llm_service.ErrorConfiguracion)

    def test_modelo_inexistente(self):
        e = llm_service._traducir_error(ErrorSDK(404))
        self.assertIsInstance(e, llm_service.ErrorConfiguracion)
        self.assertIn(llm_service.MODELO, str(e))

    def test_servidor_caido(self):
        e = llm_service._traducir_error(ErrorSDK(503))
        self.assertIn("no está disponible", str(e))

    def test_tiempo_agotado(self):
        e = llm_service._traducir_error(ErrorTimeoutFalso("timed out"))
        self.assertIn("tardó", str(e))

    def test_sin_conexion(self):
        e = llm_service._traducir_error(ErrorSDK(None, "Connection refused"))
        self.assertIn("conexión", str(e))

    def test_error_desconocido(self):
        self.assertIsInstance(llm_service._traducir_error(ValueError("raro")), llm_service.ErrorGeneracion)


@unittest.skipUnless(TIENE_SDK, "google-genai no está instalado")
class TestLlamadaAlSDK(unittest.TestCase):
    """Comprueba cómo armamos la petición y los reintentos, con un cliente falso."""

    def _cliente_falso(self, *efectos):
        cliente = mock.Mock()
        cliente.interactions.create.side_effect = list(efectos)
        return cliente

    def test_la_peticion_lleva_prompt_modelo_y_json(self):
        respuesta = mock.Mock(output_text=json.dumps(receta_valida(2)))
        cliente = self._cliente_falso(respuesta)
        with mock.patch.object(llm_service, "_api_key", return_value="clave-falsa"), \
                mock.patch("google.genai.Client", return_value=cliente):
            texto = llm_service._llamar_gemini(["pollo", "crema"], 2)
        self.assertEqual(json.loads(texto)["comensales"], 2)
        kwargs = cliente.interactions.create.call_args.kwargs
        self.assertEqual(kwargs["model"], llm_service.MODELO)
        self.assertEqual(kwargs["system_instruction"], SYSTEM_PROMPT)
        self.assertIn("- pollo", kwargs["input"])
        self.assertEqual(kwargs["response_format"]["mime_type"], "application/json")
        self.assertEqual(kwargs["response_format"]["schema"], ESQUEMA_RECETA)
        self.assertEqual(kwargs["timeout"], llm_service.TIMEOUT_SEGUNDOS)

    def test_reintenta_una_vez_si_el_servidor_esta_saturado(self):
        ok = mock.Mock(output_text="{}")
        cliente = self._cliente_falso(ErrorSDK(503), ok)
        with mock.patch.object(llm_service, "_api_key", return_value="x"), \
                mock.patch("google.genai.Client", return_value=cliente), \
                mock.patch.object(llm_service.time, "sleep") as dormir:
            self.assertEqual(llm_service._llamar_gemini(["pollo"], 2), "{}")
        self.assertEqual(cliente.interactions.create.call_count, 2)
        dormir.assert_called_once()

    def test_no_reintenta_si_se_alcanzo_el_limite(self):
        cliente = self._cliente_falso(ErrorSDK(429), mock.Mock(output_text="{}"))
        with mock.patch.object(llm_service, "_api_key", return_value="x"), \
                mock.patch("google.genai.Client", return_value=cliente):
            with self.assertRaises(llm_service.ErrorLimiteUso):
                llm_service._llamar_gemini(["pollo"], 2)
        self.assertEqual(cliente.interactions.create.call_count, 1)

    def test_respuesta_vacia(self):
        cliente = self._cliente_falso(mock.Mock(output_text=""))
        with mock.patch.object(llm_service, "_api_key", return_value="x"), \
                mock.patch("google.genai.Client", return_value=cliente):
            with self.assertRaisesRegex(llm_service.ErrorGeneracion, "vacía"):
                llm_service._llamar_gemini(["pollo"], 2)


class TestConfiguracion(unittest.TestCase):
    def test_sin_api_key(self):
        with mock.patch.object(llm_service, "_api_key", return_value=""):
            with self.assertRaisesRegex(llm_service.ErrorConfiguracion, "API key"):
                llm_service._llamar_gemini(["pollo"], 2)

    def test_proveedor_invalido(self):
        with mock.patch.object(llm_service, "PROVEEDOR", "otro"):
            with self.assertRaises(llm_service.ErrorConfiguracion):
                llm_service.generar_receta(["pollo"], 2)

    def test_descripcion_del_modo(self):
        with mock.patch.object(llm_service, "PROVEEDOR", "simulado"):
            self.assertEqual(llm_service.descripcion_modo(), "simulado")
        with mock.patch.object(llm_service, "PROVEEDOR", "gemini"):
            self.assertIn(llm_service.MODELO, llm_service.descripcion_modo())


class TestAPIConGemini(unittest.TestCase):
    """La ruta /api/receta debe responder con el código HTTP correcto en cada caso."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        database.RUTA_DB = Path(self.tmp.name)
        database.iniciar_db()
        self.c = app.test_client()

    def tearDown(self):
        os.unlink(self.tmp.name)

    def _pedir(self, comensales=2):
        return self.c.post("/api/receta", json={"ingredientes": ["pollo", "crema"], "comensales": comensales})

    def test_exito_guarda_la_receta_con_su_origen(self):
        with como_gemini(receta_valida(2)):
            r = self._pedir()
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.get_json()["receta"]["meta"]["proveedor"], "gemini")
        self.assertEqual(len(self.c.get("/api/recetas").get_json()), 1)

    def test_no_viable_responde_422_y_no_guarda(self):
        no_viable = {"viable": False, "titulo": "", "comensales": 2, "ingredientes": [],
                     "pasos": [], "tiempo_minutos": 0, "nota": "Eso no es comestible."}
        with como_gemini(no_viable):
            r = self._pedir()
        self.assertEqual(r.status_code, 422)
        self.assertIn("comestible", r.get_json()["error"])
        self.assertEqual(len(self.c.get("/api/recetas").get_json()), 0)

    def test_json_invalido_responde_502(self):
        with como_gemini("esto no es json"):
            self.assertEqual(self._pedir().status_code, 502)

    def test_limite_de_uso_responde_429(self):
        with mock.patch.multiple(
            llm_service, PROVEEDOR="gemini",
            _llamar_gemini=mock.Mock(side_effect=llm_service.ErrorLimiteUso("límite")),
        ):
            self.assertEqual(self._pedir().status_code, 429)

    def test_sin_key_responde_503(self):
        with mock.patch.object(llm_service, "PROVEEDOR", "gemini"), \
                mock.patch.object(llm_service, "_api_key", return_value=""):
            self.assertEqual(self._pedir().status_code, 503)


if __name__ == "__main__":
    unittest.main()
