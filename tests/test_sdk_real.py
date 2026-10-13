"""Pruebas con las clases REALES del SDK de Google, pero sin internet.

Se reemplaza solo la red: un "servidor falso" (httpx.MockTransport) responde
como lo haría Gemini (éxito, límite de uso, key inválida, etc.). Así se
comprueba que nuestro código entiende las excepciones y respuestas reales del
SDK. Si el SDK no está instalado, estas pruebas se omiten.
"""
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import llm_service  # noqa: E402

TIENE_SDK = importlib.util.find_spec("google.genai") is not None
if TIENE_SDK:
    import httpx
    from google import genai
    from google.genai import types

    ClienteReal = genai.Client  # se guarda antes de parchearlo en las pruebas


def respuesta_exitosa(receta):
    """Cuerpo JSON con la forma de una Interaction completada."""
    return {
        "id": "interaccion-de-prueba",
        "status": "completed",
        "model": llm_service.MODELO,
        "steps": [
            {"type": "user_input", "content": [{"type": "text", "text": "pedido"}]},
            {"type": "model_output", "content": [{"type": "text", "text": json.dumps(receta)}]},
        ],
    }


def error_google(codigo, estado, mensaje):
    return httpx.Response(codigo, json={"error": {"code": codigo, "status": estado, "message": mensaje}})


@unittest.skipUnless(TIENE_SDK, "google-genai no está instalado")
class TestConClasesRealesDelSDK(unittest.TestCase):
    def _llamar(self, *respuestas):
        """Ejecuta _llamar_gemini con un servidor falso que responde en orden."""
        pendientes = list(respuestas)
        peticiones = []

        def servidor(request):
            peticiones.append(json.loads(request.content.decode() or "{}"))
            siguiente = pendientes.pop(0) if len(pendientes) > 1 else pendientes[0]
            if isinstance(siguiente, Exception):
                raise siguiente
            return siguiente

        def cliente_falso(**kwargs):
            # Se conservan las opciones que pone llm_service (p. ej. reintentos)
            # y solo se cambia la red por el servidor falso.
            opciones = kwargs["http_options"].model_copy(
                update={"httpx_client": httpx.Client(transport=httpx.MockTransport(servidor))}
            )
            return ClienteReal(api_key=kwargs["api_key"], http_options=opciones)

        with mock.patch.object(llm_service, "_api_key", return_value="clave-falsa"), \
                mock.patch("google.genai.Client", side_effect=cliente_falso), \
                mock.patch.object(llm_service.time, "sleep"):
            try:
                return llm_service._llamar_gemini(["pollo", "crema"], 2), peticiones
            except llm_service.ErrorGeneracion as e:
                e.peticiones = peticiones
                raise

    def test_exito_y_cuerpo_de_la_peticion(self):
        receta = {"viable": True, "titulo": "X", "comensales": 2}
        texto, peticiones = self._llamar(httpx.Response(200, json=respuesta_exitosa(receta)))
        self.assertEqual(json.loads(texto)["titulo"], "X")
        cuerpo = peticiones[0]
        self.assertEqual(cuerpo["model"], llm_service.MODELO)
        self.assertEqual(cuerpo["response_format"]["mime_type"], "application/json")
        self.assertIn("required", cuerpo["response_format"]["schema"])
        self.assertIn("SmartRecipe", cuerpo["system_instruction"])

    def test_flujo_completo_hasta_la_receta_validada(self):
        receta = {
            "viable": True, "titulo": "Pollo con crema", "comensales": 2,
            "ingredientes": [{"nombre": "pollo", "cantidad": 300, "unidad": "g"}],
            "pasos": ["Cocina el pollo."], "tiempo_minutos": 20, "nota": "",
        }
        texto, _ = self._llamar(httpx.Response(200, json=respuesta_exitosa(receta)))
        validada = llm_service.validar_respuesta(llm_service._extraer_json(texto), 2)
        self.assertEqual(validada["titulo"], "Pollo con crema")

    def test_limite_de_uso_429(self):
        with self.assertRaises(llm_service.ErrorLimiteUso) as ctx:
            self._llamar(error_google(429, "RESOURCE_EXHAUSTED", "Quota exceeded"))
        self.assertEqual(len(ctx.exception.peticiones), 1)  # no se reintenta

    def test_key_invalida_400(self):
        with self.assertRaisesRegex(llm_service.ErrorConfiguracion, "API key"):
            self._llamar(error_google(400, "INVALID_ARGUMENT", "API key not valid. Please pass a valid API key."))

    def test_key_sin_permiso_403(self):
        with self.assertRaisesRegex(llm_service.ErrorConfiguracion, "API key"):
            self._llamar(error_google(403, "PERMISSION_DENIED", "denied"))

    def test_modelo_inexistente_404(self):
        with self.assertRaisesRegex(llm_service.ErrorConfiguracion, "GEMINI_MODEL"):
            self._llamar(error_google(404, "NOT_FOUND", "model not found"))

    def test_servidor_saturado_se_reintenta_y_se_recupera(self):
        receta = {"viable": True, "titulo": "X", "comensales": 2}
        texto, peticiones = self._llamar(
            error_google(503, "UNAVAILABLE", "overloaded"),
            httpx.Response(200, json=respuesta_exitosa(receta)),
        )
        self.assertEqual(len(peticiones), 2)
        self.assertEqual(json.loads(texto)["titulo"], "X")

    def test_servidor_caido_agota_los_reintentos(self):
        with self.assertRaisesRegex(llm_service.ErrorGeneracion, "no está disponible") as ctx:
            self._llamar(error_google(500, "INTERNAL", "boom"))
        self.assertEqual(len(ctx.exception.peticiones), llm_service.REINTENTOS_SERVIDOR + 1)

    def test_tiempo_agotado(self):
        with self.assertRaisesRegex(llm_service.ErrorGeneracion, "tardó"):
            self._llamar(httpx.ReadTimeout("timed out"))

    def test_sin_conexion(self):
        with self.assertRaises(llm_service.ErrorGeneracion) as ctx:
            self._llamar(httpx.ConnectError("Connection refused"))
        self.assertTrue(
            "conexión" in str(ctx.exception) or "tardó" in str(ctx.exception) or "Error inesperado" in str(ctx.exception)
        )

    def test_interaccion_incompleta(self):
        cuerpo = respuesta_exitosa({"x": 1})
        cuerpo["status"] = "incomplete"
        with self.assertRaisesRegex(llm_service.ErrorGeneracion, "incomplete"):
            self._llamar(httpx.Response(200, json=cuerpo))


if __name__ == "__main__":
    unittest.main()
