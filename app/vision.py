"""Inspección de prendas por imagen.

Con una llave de Gemini en st.secrets, el modelo describe la prenda de la foto.
Sin llave, el usuario indica el tipo de prenda a mano (modo sin IA), para que la
demo funcione igual. En ambos casos la decisión de si es apta la toman las mismas
reglas de clima de nucleo.py, así la respuesta siempre coincide con el sensor.
"""

import json

import streamlit as st

from nucleo import CALOR_MIN, FRIO_MAX, HUMEDAD_LLUVIA, Clima

ABRIGOS = {
    "abrigada": "abrigada (chaqueta gruesa, buzo, abrigo)",
    "ligera": "ligera (manga larga delgada, chaqueta liviana)",
    "fresca": "fresca (camiseta, manga corta, short)",
}

PROMPT = """Mira la foto y describe la prenda principal que aparece.
Responde SOLO con un JSON con estas claves:
- "prenda": nombre corto en español (ej. "chaqueta de jean")
- "abrigo": una de "abrigada", "ligera" o "fresca"
- "impermeable": true si protege de la lluvia, si no false
- "es_ropa": false si en la foto no hay ninguna prenda de vestir
"""


def ia_disponible() -> bool:
    try:
        return bool(st.secrets.get("GEMINI_API_KEY"))
    except FileNotFoundError:
        return False


def describir_con_ia(imagen: bytes, mime: str = "image/jpeg") -> dict:
    """Pide a Gemini que clasifique la prenda. Lanza excepción si falla."""
    from google import genai
    from google.genai import types

    cliente = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    modelo = st.secrets.get("GEMINI_MODEL", "gemini-2.5-flash")
    respuesta = cliente.models.generate_content(
        model=modelo,
        contents=[types.Part.from_bytes(data=imagen, mime_type=mime), PROMPT],
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    datos = json.loads(respuesta.text)
    if datos.get("abrigo") not in ABRIGOS:
        datos["abrigo"] = "ligera"
    datos["impermeable"] = bool(datos.get("impermeable", False))
    datos["es_ropa"] = bool(datos.get("es_ropa", True))
    return datos


def evaluar_prenda(prenda: dict, c: Clima) -> dict:
    """Aplica las reglas de clima a una prenda. Devuelve apta (bool) y el motivo."""
    abrigo = prenda["abrigo"]
    nombre = prenda.get("prenda") or "esta prenda"

    if c.temp < FRIO_MAX:
        apta = abrigo == "abrigada"
        motivo = (
            f"Hace {c.temp:.0f} °C: {nombre} te mantiene caliente."
            if apta
            else f"Hace {c.temp:.0f} °C: con {nombre} vas a pasar frío. Busca algo más abrigado."
        )
    elif c.temp > CALOR_MIN:
        apta = abrigo != "abrigada"
        motivo = (
            f"Hace {c.temp:.0f} °C: {nombre} es buena para el calor."
            if apta
            else f"Hace {c.temp:.0f} °C: con {nombre} te vas a sofocar. Mejor algo más fresco."
        )
    else:
        apta = abrigo == "ligera"
        if apta:
            motivo = f"Hace {c.temp:.0f} °C: {nombre} es ideal para un clima fresco."
        elif abrigo == "abrigada":
            motivo = f"Hace {c.temp:.0f} °C: {nombre} puede quedarte caliente. Una capa ligera basta."
        else:
            motivo = f"Hace {c.temp:.0f} °C: con {nombre} sola puede darte frío. Lleva una capa ligera."

    if c.hum > HUMEDAD_LLUVIA and not prenda.get("impermeable"):
        motivo += f" La humedad está en {c.hum:.0f} %: lleva sombrilla."

    return {"apta": apta, "motivo": motivo}
