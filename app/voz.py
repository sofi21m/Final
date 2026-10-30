"""Salida de voz con gTTS."""

from io import BytesIO

import streamlit as st
from gtts import gTTS


@st.cache_data(show_spinner=False, max_entries=50)
def sintetizar(texto: str) -> bytes:
    buffer = BytesIO()
    gTTS(texto, lang="es", tld="com.mx").write_to_fp(buffer)
    return buffer.getvalue()


def hablar(texto: str):
    """Muestra la respuesta en texto y la reproduce en voz alta."""
    try:
        st.audio(sintetizar(texto), format="audio/mp3", autoplay=True)
    except Exception:
        st.caption("No se pudo generar el audio; la respuesta queda en texto.")
