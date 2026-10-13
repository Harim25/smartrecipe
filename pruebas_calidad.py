"""Pruebas de calidad del Avance 3 (Actividad 4.2): casos límite y consistencia.

Ejecutar (con el entorno virtual activado):
    python pruebas_calidad.py              -> corre todo (13 consultas a Gemini)
    python pruebas_calidad.py limite       -> solo los casos límite (7 consultas)
    python pruebas_calidad.py consistencia -> solo la consistencia (6 consultas)
    python pruebas_calidad.py L03 K1-2     -> repite solo esos casos
    python pruebas_calidad.py --simulado   -> prueba el script sin gastar cuota

Complementa a pruebas_generacion.py (los 12 casos base). Guarda en
resultados_pruebas/ los archivos calidad.md y calidad.json, y conserva los
resultados anteriores de los casos que no se repiten.

La capa gratuita de Gemini permite pocas consultas por día: conviene revisar
cuántas quedan antes de correrlo completo.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import llm_service
from pruebas_generacion import PAUSA_ENTRE_CASOS, cantidad_texto, ejecutar_caso, revisar

# ---------------------------------------------------------------------------
# Casos límite: entradas en los extremos de lo que la aplicación permite
# ---------------------------------------------------------------------------
VEINTE = ["pollo", "arroz", "frijol", "jitomate", "cebolla", "ajo", "zanahoria", "papa",
          "calabacita", "elote", "queso", "crema", "huevo", "tortilla", "chile", "limón",
          "cilantro", "aguacate", "lechuga", "pasta"]

LIMITE = [
    ("L01", "Máximo de ingredientes (20)", VEINTE, 4,
     "receta coherente; no tiene que usar los 20, pero sí explicar lo que deja fuera"),
    ("L02", "Máximo de comensales (20)", ["pollo", "arroz", "zanahoria"], 20,
     "cantidades para 20 personas (kilos de pollo y arroz)"),
    ("L03", "Faltas de ortografía", ["poyo", "aros", "sevolla", "jitomate"], 2,
     "entiende pollo, arroz y cebolla"),
    ("L04", "Ingredientes en inglés", ["chicken", "rice", "onion"], 2,
     "receta en español con esos ingredientes"),
    ("L05", "Solo condimentos", ["sal", "azúcar"], 2,
     "rechaza o explica que no alcanza para un platillo"),
    ("L06", "Carne que requiere cocción completa", ["carne molida", "lechuga", "jitomate"], 2,
     "cuece bien la carne; no la sirve cruda"),
    ("L07", "Ingredientes dulces", ["plátano", "avena", "leche", "miel"], 3,
     "propone un postre o desayuno, no un guisado salado"),
]

# ---------------------------------------------------------------------------
# Consistencia: la misma petición varias veces (el entorno es estocástico)
# ---------------------------------------------------------------------------
REPETICIONES = 3
GRUPOS = [
    ("K1", "Desayuno", ["huevo", "tortilla", "frijol", "queso"], 2),
    ("K2", "Pasta", ["pasta", "jitomate", "ajo"], 4),
]
CONSISTENCIA = [
    (f"{gid}-{n}", f"{desc} (repetición {n})", ing, com, "debe parecerse a las otras repeticiones")
    for gid, desc, ing, com in GRUPOS
    for n in range(1, REPETICIONES + 1)
]

TODOS = LIMITE + CONSISTENCIA


def analizar_consistencia(por_id):
    """Compara las repeticiones de cada grupo: títulos, ingredientes y cantidades."""
    lineas = []
    for gid, desc, ingredientes, comensales in GRUPOS:
        corridas = [por_id.get(f"{gid}-{n}") for n in range(1, REPETICIONES + 1)]
        buenas = [c for c in corridas if c and c["resultado"] == "OK"]
        lineas += [f"### {gid} · {desc}: {', '.join(ingredientes)} para {comensales}", ""]
        if len(buenas) < 2:
            lineas += ["No hay suficientes repeticiones correctas para comparar.", ""]
            continue
        lineas.append(f"- Repeticiones correctas: {len(buenas)} de {REPETICIONES}")
        lineas.append("- Títulos: " + " / ".join(c["receta"]["titulo"] for c in buenas))
        tiempos_prep = [c["receta"]["tiempo_minutos"] for c in buenas]
        lineas.append(f"- Tiempo de preparación indicado: de {min(tiempos_prep)} a {max(tiempos_prep)} min")
        segundos = [c["segundos"] for c in buenas]
        lineas.append(f"- Tiempo de respuesta: de {min(segundos)} a {max(segundos)} s")
        lineas.append(f"- Número de pasos: {', '.join(str(len(c['receta']['pasos'])) for c in buenas)}")
        lineas += ["", "| Ingrediente del usuario | " + " | ".join(f"Rep. {n}" for n in range(1, len(buenas) + 1)) + " | Variación |",
                   "|---|" + "---|" * (len(buenas) + 1)]
        for enviado in ingredientes:
            celdas, valores = [], []
            for c in buenas:
                hallado = next((i for i in c["receta"]["ingredientes"] if enviado in i["nombre"].lower()), None)
                if hallado:
                    celdas.append(cantidad_texto(hallado))
                    valores.append((hallado["cantidad"], hallado["unidad"]))
                else:
                    celdas.append("no lo usó")
            unidades = {u for _, u in valores}
            if len(valores) == len(buenas) and len(unidades) == 1 and min(v for v, _ in valores) > 0:
                minimo, maximo = min(v for v, _ in valores), max(v for v, _ in valores)
                variacion = "igual" if minimo == maximo else f"x{maximo / minimo:.1f} entre la menor y la mayor"
            elif not valores:
                variacion = "nunca lo usó"
            else:
                variacion = "cambia de unidad o no siempre lo usa"
            lineas.append(f"| {enviado} | " + " | ".join(celdas) + f" | {variacion} |")
        lineas.append("")
    return lineas


def escribir(registros):
    carpeta = Path(__file__).with_name("resultados_pruebas")
    carpeta.mkdir(exist_ok=True)
    (carpeta / "calidad.json").write_text(json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8")
    por_id = {r["id"]: r for r in registros}

    lineas = ["# Pruebas de calidad: casos límite y consistencia", "",
              f"- Fecha: {datetime.now():%d/%m/%Y %H:%M}",
              f"- Modo: {llm_service.descripcion_modo()}", "",
              "## Casos límite", "",
              "| Caso | Descripción | Comensales | Resultado | Tiempo (s) | % ingredientes usados | Observación automática |",
              "|---|---|---|---|---|---|---|"]
    for caso in LIMITE:
        r = por_id.get(caso[0])
        if not r:
            continue
        porcentaje, obs = revisar(r)
        lineas.append(f"| {r['id']} | {r['descripcion']} | {r['comensales']} | {r['resultado']} | {r['segundos']} | "
                      f"{'' if porcentaje is None else str(porcentaje) + ' %'} | {obs} |")
    lineas += ["", "## Consistencia", ""] + analizar_consistencia(por_id)

    lineas += ["## Detalle de cada caso", ""]
    for r in registros:
        lineas += [f"### {r['id']} · {r['descripcion']}", "",
                   f"- Ingredientes: {', '.join(r['ingredientes_enviados'])} · Comensales: {r['comensales']}",
                   f"- Se esperaba: {r['esperado']}",
                   f"- Resultado: **{r['resultado']}**" + (f" en {r['segundos']} s" if r["segundos"] is not None else "")]
        if r["mensaje"]:
            lineas.append(f"- Mensaje: {r['mensaje']}")
        rec = r["receta"]
        if rec:
            lineas += ["", f"**{rec['titulo']}** ({rec['tiempo_minutos']} min)", "", "Ingredientes:"]
            lineas += [f"- {i['nombre']}: {cantidad_texto(i)}" for i in rec["ingredientes"]]
            lineas += ["", "Pasos:"] + [f"{n}. {p}" for n, p in enumerate(rec["pasos"], 1)]
            if rec.get("nota"):
                lineas += ["", f"Nota del modelo: {rec['nota']}"]
        lineas.append("")
    (carpeta / "calidad.md").write_text("\n".join(lineas), encoding="utf-8")
    return carpeta


def main():
    print(f"=== Pruebas de calidad ({llm_service.descripcion_modo()}) ===")
    if llm_service.PROVEEDOR == "gemini" and not llm_service._api_key():
        print("Falta GEMINI_API_KEY. Revisa el archivo .env (ver README).")
        sys.exit(1)

    pedidos = [a.upper() for a in sys.argv[1:] if not a.startswith("--")]
    if "LIMITE" in pedidos:
        pedidos += [c[0] for c in LIMITE]
    if "CONSISTENCIA" in pedidos:
        pedidos += [c[0] for c in CONSISTENCIA]
    archivo = Path(__file__).with_name("resultados_pruebas") / "calidad.json"
    previos = {r["id"]: r for r in json.loads(archivo.read_text(encoding="utf-8"))} if archivo.exists() else {}
    casos = [c for c in TODOS if not pedidos or c[0].upper() in pedidos]

    nuevos = {}
    for n, caso in enumerate(casos, 1):
        print(f"[{n}/{len(casos)}] {caso[0]} · {caso[1]} ...", flush=True)
        registro = ejecutar_caso(*caso)
        nuevos[caso[0]] = registro
        print(f"     -> {registro['resultado']}" + (f" ({registro['segundos']} s)" if registro["segundos"] is not None else "")
              + (f" · {registro['mensaje']}" if registro["mensaje"] else ""), flush=True)
        if n < len(casos) and llm_service.PROVEEDOR == "gemini":
            time.sleep(PAUSA_ENTRE_CASOS)

    registros = [nuevos.get(c[0]) or previos.get(c[0]) for c in TODOS]
    carpeta = escribir([r for r in registros if r])
    print(f"\nListo. Resultados guardados en: {carpeta} (calidad.md y calidad.json)")


if __name__ == "__main__":
    main()
