"""Núcleo de ClimaWear Smart: conexión MQTT con el ESP32 y reglas de recomendación."""

import json
import threading
import time
import unicodedata
from dataclasses import dataclass

import paho.mqtt.client as mqtt
import streamlit as st

BROKER = "broker.hivemq.com"
PUERTO = 1883
TOPIC_SENSORES = "eafit-climawear/sensores"
TOPIC_ARMARIO = "eafit-climawear/armario"

# Si no llegan datos en este tiempo, el sensor se considera desconectado.
SEGUNDOS_SIN_DATOS = 30

# Umbrales iniciales (calibrar con usuarios)
FRIO_MAX = 18      # °C: por debajo, chaqueta o buzo
CALOR_MIN = 24     # °C: por encima, ropa fresca
HUMEDAD_LLUVIA = 80  # %: por encima, sombrilla
LUZ_ALTA = 70      # %: por encima, gafas y bloqueador


# ---------------------------------------------------------------------------
# MQTT
# ---------------------------------------------------------------------------

class ClienteClima:
    """Escucha el tópico de sensores en un hilo aparte y guarda la última lectura."""

    def __init__(self):
        self._lock = threading.Lock()
        self.ultima = None          # dict con temp, hum, luz, armario
        self.recibido_en = None     # time.time() de la última lectura
        self.conectado = False

        self.cliente = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"climawear-app-{int(time.time() * 1000) % 100000}",
        )
        self.cliente.on_connect = self._al_conectar
        self.cliente.on_disconnect = self._al_desconectar
        self.cliente.on_message = self._al_recibir
        self.cliente.connect_async(BROKER, PUERTO, keepalive=30)
        self.cliente.loop_start()

    def _al_conectar(self, client, userdata, flags, reason_code, properties):
        self.conectado = not reason_code.is_failure
        if self.conectado:
            client.subscribe(TOPIC_SENSORES)

    def _al_desconectar(self, client, userdata, flags, reason_code, properties):
        self.conectado = False

    def _al_recibir(self, client, userdata, msg):
        try:
            datos = json.loads(msg.payload.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return
        with self._lock:
            self.ultima = datos
            self.recibido_en = time.time()

    def lectura(self):
        """Devuelve (datos, segundos_desde_la_lectura) o (None, None)."""
        with self._lock:
            if self.ultima is None:
                return None, None
            return dict(self.ultima), time.time() - self.recibido_en

    def abrir_armario(self):
        self.cliente.publish(TOPIC_ARMARIO, "abrir")


@st.cache_resource
def cliente_clima() -> ClienteClima:
    return ClienteClima()


@dataclass
class Clima:
    temp: float
    hum: float
    luz: float
    fuente: str          # "sensor" o "demo"
    hace: float | None   # segundos desde la última lectura


def clima_actual() -> Clima | None:
    """Clima del sensor, o de los controles de demo si el modo demo está activo."""
    if st.session_state.get("modo_demo"):
        return Clima(
            temp=st.session_state.get("demo_temp", 19.0),
            hum=st.session_state.get("demo_hum", 85.0),
            luz=st.session_state.get("demo_luz", 75.0),
            fuente="demo",
            hace=None,
        )

    datos, hace = cliente_clima().lectura()
    if datos is None or hace > SEGUNDOS_SIN_DATOS:
        return None
    return Clima(
        temp=float(datos.get("temp", 0)),
        hum=float(datos.get("hum", 0)),
        luz=float(datos.get("luz", 0)),
        fuente="sensor",
        hace=hace,
    )


def controles_demo():
    """Barra lateral con el modo demo, útil si el WiFi o Wokwi fallan en la sustentación."""
    with st.sidebar:
        st.markdown("### Fuente de datos")
        st.toggle(
            "Modo demo (sin sensor)",
            key="modo_demo",
            help="Usa estos controles en lugar del circuito de Wokwi.",
        )
        if st.session_state.get("modo_demo"):
            st.slider("Temperatura (°C)", 5.0, 35.0, 19.0, 0.5, key="demo_temp")
            st.slider("Humedad (%)", 20.0, 100.0, 85.0, 1.0, key="demo_hum")
            st.slider("Luz solar (%)", 0.0, 100.0, 75.0, 1.0, key="demo_luz")
        else:
            st.caption(f"Escuchando `{TOPIC_SENSORES}` en {BROKER}")


# ---------------------------------------------------------------------------
# Reglas de recomendación
# ---------------------------------------------------------------------------

def sensacion(c: Clima) -> str:
    if c.temp < FRIO_MAX:
        base = "Frío"
    elif c.temp > CALOR_MIN:
        base = "Caluroso"
    else:
        base = "Fresco"
    if c.hum > HUMEDAD_LLUVIA:
        base += " y húmedo"
    elif c.luz > LUZ_ALTA:
        base += " y soleado"
    return base


def recomendacion(c: Clima) -> dict:
    """Devuelve la prenda principal y la lista de accesorios."""
    if c.temp < FRIO_MAX:
        prenda = "Chaqueta o buzo abrigado"
    elif c.temp > CALOR_MIN:
        prenda = "Ropa fresca y telas livianas"
    else:
        prenda = "Chaqueta ligera o una capa que te puedas quitar"

    accesorios = []
    if c.hum > HUMEDAD_LLUVIA:
        accesorios.append("Sombrilla o chaqueta impermeable: la humedad está alta")
    if c.luz > LUZ_ALTA:
        accesorios.append("Gafas de sol y bloqueador: hay mucha luz")

    return {
        "prenda": prenda,
        "accesorios": accesorios,
        "necesita_chaqueta": c.temp <= CALOR_MIN or c.hum > HUMEDAD_LLUVIA,
        "necesita_sombrilla": c.hum > HUMEDAD_LLUVIA,
        "necesita_gafas": c.luz > LUZ_ALTA,
    }


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")


def responder_pregunta(pregunta: str, c: Clima) -> str:
    """Respuesta corta en español a una pregunta hablada, según el clima actual."""
    p = _normalizar(pregunta)
    r = recomendacion(c)
    datos = f"Hace {c.temp:.0f} grados y la humedad está en {c.hum:.0f} por ciento."

    if any(k in p for k in ("chaqueta", "buzo", "saco", "abrigo", "chompa")):
        if r["necesita_chaqueta"]:
            return f"Sí. {datos} Te recomiendo {r['prenda'].lower()}."
        return f"No hace falta. {datos} Mejor {r['prenda'].lower()}."

    if any(k in p for k in ("sombrilla", "paraguas", "llover", "lluvia", "llueve")):
        if r["necesita_sombrilla"]:
            return f"Sí, lleva sombrilla. La humedad está en {c.hum:.0f} por ciento y puede llover."
        return f"Hoy no parece necesaria. La humedad está en {c.hum:.0f} por ciento."

    if any(k in p for k in ("gafas", "sol", "bloqueador", "lentes")):
        if r["necesita_gafas"]:
            return f"Sí. La luz solar está en {c.luz:.0f} por ciento. Lleva gafas y bloqueador."
        return f"No es necesario. La luz está en {c.luz:.0f} por ciento."

    if any(k in p for k in ("frio", "calor", "temperatura", "grados", "clima", "tiempo")):
        return f"{datos} Se siente {sensacion(c).lower()}."

    # "¿Qué me pongo?" y cualquier otra pregunta
    extra = " Además: " + "; ".join(a.split(":")[0].lower() for a in r["accesorios"]) + "." if r["accesorios"] else ""
    return f"{datos} Te recomiendo {r['prenda'].lower()}.{extra}"
