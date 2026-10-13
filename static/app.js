// SmartRecipe: lógica de la interfaz.
// Todo el texto dinámico se inserta con textContent (nunca innerHTML)
// para evitar que lo escrito por el usuario se ejecute como código.

const estado = {
  ingredientes: [],      // lo que el usuario va a usar en esta receta
  comensales: 2,
  recetaActual: null,    // última receta mostrada
  pestana: "cocinar",    // "cocinar" | "historial" | "favoritas"
  generando: false,      // evita enviar dos peticiones a la vez
};

const $ = (id) => document.getElementById(id);

// ---------- API ----------
async function api(url, opciones = {}) {
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...opciones,
  });
  if (resp.status === 204) return null;
  const datos = await resp.json();
  if (!resp.ok) {
    // Se conservan los datos del error (tipo, ofrecer_simulado) para decidir qué mostrar.
    const error = new Error(datos.error || "Ocurrió un error.");
    error.tipo = datos.tipo;
    error.ofrecerSimulado = !!datos.ofrecer_simulado;
    throw error;
  }
  return datos;
}

// ---------- Mensajes ----------
function mostrarMensaje(texto, ok = false) {
  const el = $("mensaje");
  el.textContent = texto;
  el.classList.toggle("ok", ok);
  el.hidden = !texto;
}

// ---------- Ingredientes de esta receta ----------
function limpiar(texto) {
  return texto.toLowerCase().replace(/\s+/g, " ").trim();
}

function agregarIngrediente(nombre) {
  nombre = limpiar(nombre);
  if (!nombre) return;
  if (estado.ingredientes.includes(nombre)) {
    mostrarMensaje(`"${nombre}" ya está en la lista.`);
    return;
  }
  if (estado.ingredientes.length >= 20) {
    mostrarMensaje("El máximo es de 20 ingredientes.");
    return;
  }
  mostrarMensaje("");
  estado.ingredientes.push(nombre);
  pintarIngredientes();
}

function quitarIngrediente(nombre) {
  estado.ingredientes = estado.ingredientes.filter((i) => i !== nombre);
  pintarIngredientes();
}

function crearChip(texto, textoBoton, etiquetaBoton, alClic, claseBoton) {
  const li = document.createElement("li");
  li.className = "chip";
  const span = document.createElement("span");
  span.textContent = texto;
  const btn = document.createElement("button");
  btn.type = "button";
  btn.textContent = textoBoton;
  btn.setAttribute("aria-label", etiquetaBoton);
  if (claseBoton) btn.className = claseBoton;
  btn.addEventListener("click", alClic);
  li.append(span, btn);
  return li;
}

function pintarIngredientes() {
  const ul = $("lista-ingredientes");
  ul.replaceChildren(
    ...estado.ingredientes.map((n) =>
      crearChip(n, "×", `Quitar ${n}`, () => quitarIngrediente(n))
    )
  );
  $("vacio-ingredientes").hidden = estado.ingredientes.length > 0;
}

// ---------- Despensa ----------
async function cargarDespensa() {
  const items = await api("/api/despensa");
  $("lista-despensa").replaceChildren(
    ...items.map((it) => {
      const li = crearChip(`+ ${it.nombre}`, "×", `Borrar ${it.nombre} de la despensa`, async () => {
        await api(`/api/despensa/${it.id}`, { method: "DELETE" });
        cargarDespensa();
      });
      // Clic en el texto = usar el ingrediente en la receta actual.
      const texto = li.querySelector("span");
      texto.style.cursor = "pointer";
      texto.addEventListener("click", () => agregarIngrediente(it.nombre));
      return li;
    })
  );
  $("vacio-despensa").hidden = items.length > 0;
}

async function guardarEnDespensa() {
  if (!estado.ingredientes.length) {
    mostrarMensaje("Primero agrega ingredientes arriba.");
    return;
  }
  try {
    for (const n of estado.ingredientes) {
      await api("/api/despensa", { method: "POST", body: JSON.stringify({ nombre: n }) });
    }
    await cargarDespensa();
    mostrarMensaje("Ingredientes guardados en tu despensa.", true);
  } catch (e) {
    mostrarMensaje(e.message);
  }
}

// ---------- Comensales ----------
function cambiarComensales(delta) {
  estado.comensales = Math.min(20, Math.max(1, estado.comensales + delta));
  $("comensales").textContent = estado.comensales;
}

// ---------- Receta ----------
function formatoCantidad(ing) {
  if (ing.unidad === "al gusto") return "al gusto";
  return `${ing.cantidad} ${ing.unidad}`;
}

// El panel derecho muestra una sola cosa a la vez.
function mostrarPanel(nombre) {
  for (const id of ["receta-vacia", "cargando", "aviso", "receta"]) {
    $(id).hidden = id !== nombre;
  }
}

// Vuelve a lo que había antes de generar: la receta anterior o el panel vacío.
function restaurarPanel() {
  mostrarPanel(estado.recetaActual ? "receta" : "receta-vacia");
}

function mostrarReceta(fila) {
  estado.recetaActual = fila;
  const r = fila.receta;
  mostrarPanel("receta");
  $("r-titulo").textContent = r.titulo;
  $("r-comensales").textContent = `${r.comensales} ${r.comensales === 1 ? "comensal" : "comensales"}`;
  $("r-tiempo").textContent = `${r.tiempo_minutos} min`;

  $("r-ingredientes").replaceChildren(
    ...r.ingredientes.map((ing) => {
      const li = document.createElement("li");
      const nombre = document.createElement("span");
      nombre.textContent = ing.nombre;
      const cant = document.createElement("span");
      cant.className = "cant";
      cant.textContent = formatoCantidad(ing);
      li.append(nombre, cant);
      return li;
    })
  );
  $("r-pasos").replaceChildren(
    ...r.pasos.map((p) => {
      const li = document.createElement("li");
      li.textContent = p;
      return li;
    })
  );
  $("r-nota").textContent = r.nota || "";
  $("r-nota").hidden = !r.nota;

  // Origen de la receta: modelo y tiempo de respuesta (evidencia de que viene del LLM).
  const meta = r.meta;
  const origen = $("r-origen");
  if (meta) {
    if (meta.proveedor === "gemini") {
      origen.textContent = `Generada con ${meta.modelo} en ${meta.segundos} s`;
    } else if (meta.respaldo) {
      origen.textContent = "Generada en modo simulado (sin IA) porque Gemini no estaba disponible";
    } else {
      origen.textContent = "Generada en modo simulado (sin IA)";
    }
  } else {
    origen.textContent = "";
  }
  origen.hidden = !meta;
  pintarFavoritaActual();
}

function pintarFavoritaActual() {
  const fav = !!(estado.recetaActual && estado.recetaActual.favorita);
  const btn = $("r-favorita");
  btn.textContent = fav ? "★" : "☆";
  btn.setAttribute("aria-pressed", String(fav));
  btn.setAttribute("aria-label", fav ? "Quitar de favoritas" : "Marcar como favorita");
}

// ---------- Estado de carga ----------
const MENSAJES_CARGA = [
  "Preparando tu receta…",
  "Revisando tus ingredientes…",
  "Calculando las cantidades…",
  "Ordenando los pasos…",
  "Ya casi está lista…",
];
let relojCarga = null;

function iniciarCarga(conIA) {
  mostrarPanel("cargando");
  const inicio = Date.now();
  const pintar = () => {
    const seg = Math.floor((Date.now() - inicio) / 1000);
    $("cargando-segundos").textContent = seg;
    // Cambia el mensaje cada 5 segundos para que se note que sigue trabajando.
    $("cargando-texto").textContent = conIA
      ? MENSAJES_CARGA[Math.min(Math.floor(seg / 5), MENSAJES_CARGA.length - 1)]
      : "Preparando tu receta…";
  };
  pintar();
  relojCarga = setInterval(pintar, 1000);
}

function detenerCarga() {
  clearInterval(relojCarga);
  relojCarga = null;
}

// ---------- Aviso cuando Gemini no puede responder ----------
const TITULOS_AVISO = {
  limite: "Se acabó el uso gratuito de la IA por ahora",
  servicio: "La IA no está disponible en este momento",
  configuracion: "La IA no está configurada",
};

function mostrarAviso(error) {
  $("aviso-titulo").textContent = TITULOS_AVISO[error.tipo] || "No se pudo generar la receta";
  $("aviso-texto").textContent = error.message;
  $("aviso-pregunta").textContent =
    "¿Quieres continuar en modo simulado (sin IA)? La receta será una versión básica hecha con reglas simples.";
  // Si falta configurar la IA, reintentar no sirve de nada.
  $("aviso-reintentar").hidden = error.tipo === "configuracion";
  mostrarPanel("aviso");
  $("aviso-simulado").focus();
}

function cancelarAviso() {
  // Los ingredientes y los comensales se conservan tal como estaban.
  restaurarPanel();
  mostrarMensaje("");
}

// ---------- Generar ----------
async function generarReceta(modo = "auto") {
  if (estado.generando) return; // ya hay una petición en curso
  if (!estado.ingredientes.length) {
    mostrarMensaje("Agrega al menos un ingrediente.");
    return;
  }
  const boton = $("btn-generar");
  estado.generando = true;
  boton.disabled = true;
  boton.textContent = "Generando…";
  mostrarMensaje("");
  iniciarCarga(modo !== "simulado");
  try {
    const cuerpo = { ingredientes: estado.ingredientes, comensales: estado.comensales };
    if (modo === "simulado") cuerpo.modo = "simulado";
    const fila = await api("/api/receta", { method: "POST", body: JSON.stringify(cuerpo) });
    mostrarReceta(fila);
  } catch (e) {
    if (e.ofrecerSimulado) {
      mostrarAviso(e);
    } else {
      restaurarPanel();
      // TypeError = el navegador no pudo comunicarse con el servidor de la aplicación.
      mostrarMensaje(
        e instanceof TypeError
          ? "No se pudo contactar al servidor de SmartRecipe. Revisa que la aplicación siga abierta."
          : e.message
      );
    }
  } finally {
    detenerCarga();
    estado.generando = false;
    boton.disabled = false;
    boton.textContent = "Generar receta";
  }
}

async function alternarFavoritaActual() {
  if (!estado.recetaActual) return;
  estado.recetaActual = await api(`/api/recetas/${estado.recetaActual.id}/favorita`, { method: "POST" });
  pintarFavoritaActual();
}

// ---------- Historial / favoritas ----------
function boton(texto, clase, alClic) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = clase;
  b.textContent = texto;
  b.addEventListener("click", alClic);
  return b;
}

async function cargarHistorial() {
  const url = estado.pestana === "favoritas" ? "/api/recetas?favoritas=1" : "/api/recetas";
  const filas = await api(url);
  $("lista-historial").replaceChildren(
    ...filas.map((fila) => {
      const li = document.createElement("li");
      li.className = "item-historial";

      const info = document.createElement("div");
      info.className = "info";
      const t = document.createElement("p");
      t.className = "titulo";
      t.textContent = (fila.favorita ? "★ " : "") + fila.titulo;
      const d = document.createElement("p");
      d.className = "detalle";
      d.textContent = `${fila.comensales} comensal(es) · ${fila.ingredientes_usuario.join(", ")}`;
      info.append(t, d);

      const acciones = document.createElement("div");
      acciones.className = "acciones";
      acciones.append(
        boton("Ver", "mini", () => { mostrarReceta(fila); cambiarPestana("cocinar"); }),
        boton(fila.favorita ? "Quitar ★" : "★ Favorita", "mini", async () => {
          const act = await api(`/api/recetas/${fila.id}/favorita`, { method: "POST" });
          if (estado.recetaActual && estado.recetaActual.id === act.id) {
            estado.recetaActual = act;
            pintarFavoritaActual();
          }
          cargarHistorial();
        }),
        boton("Borrar", "mini", async () => {
          await api(`/api/recetas/${fila.id}`, { method: "DELETE" });
          if (estado.recetaActual && estado.recetaActual.id === fila.id) {
            estado.recetaActual = null;
            mostrarPanel("receta-vacia");
          }
          cargarHistorial();
        })
      );
      li.append(info, acciones);
      return li;
    })
  );
  const vacio = $("vacio-historial");
  vacio.hidden = filas.length > 0;
  vacio.textContent =
    estado.pestana === "favoritas"
      ? "Aún no tienes recetas favoritas."
      : "Todavía no hay recetas guardadas.";
}

function cambiarPestana(nombre) {
  estado.pestana = nombre;
  for (const n of ["cocinar", "historial", "favoritas"]) {
    const activa = n === nombre;
    $("nav-" + n).classList.toggle("activa", activa);
    if (activa) $("nav-" + n).setAttribute("aria-current", "page");
    else $("nav-" + n).removeAttribute("aria-current");
  }
  $("vista-cocinar").hidden = nombre !== "cocinar";
  $("vista-lista").hidden = nombre === "cocinar";
  if (nombre !== "cocinar") {
    $("t-historial").textContent = nombre === "favoritas" ? "Favoritas" : "Historial";
    cargarHistorial();
  }
  window.scrollTo({ top: 0 });
}

// ---------- Eventos ----------
$("form-ingrediente").addEventListener("submit", (e) => {
  e.preventDefault();
  const campo = $("entrada-ingrediente");
  agregarIngrediente(campo.value);
  campo.value = "";
  campo.focus();
});
$("menos").addEventListener("click", () => cambiarComensales(-1));
$("mas").addEventListener("click", () => cambiarComensales(1));
$("btn-generar").addEventListener("click", () => generarReceta());
$("aviso-simulado").addEventListener("click", () => generarReceta("simulado"));
$("aviso-reintentar").addEventListener("click", () => generarReceta());
$("aviso-cancelar").addEventListener("click", cancelarAviso);
$("btn-guardar-despensa").addEventListener("click", guardarEnDespensa);
$("r-favorita").addEventListener("click", alternarFavoritaActual);
$("nav-cocinar").addEventListener("click", () => cambiarPestana("cocinar"));
$("nav-historial").addEventListener("click", () => cambiarPestana("historial"));
$("nav-favoritas").addEventListener("click", () => cambiarPestana("favoritas"));

// ---------- Inicio ----------
pintarIngredientes();
cargarDespensa();
