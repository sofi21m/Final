"""ClimaWear Smart — punto de entrada de la app Streamlit.

Ejecutar con:  streamlit run app.py
"""

import streamlit as st

from nucleo import cliente_clima, controles_demo

st.set_page_config(page_title="ClimaWear Smart", page_icon="🌦️", layout="centered")

# Arranca la conexión MQTT una sola vez para toda la app.
cliente_clima()

paginas = st.navigation(
    [
        st.Page("paginas/panel.py", title="Panel de clima", icon="🌡️", default=True),
        st.Page("paginas/voz_camara.py", title="Voz y cámara", icon="🎙️"),
    ]
)

controles_demo()
paginas.run()
