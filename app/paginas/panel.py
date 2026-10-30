"""Página 1 — Panel de clima: lectura en vivo del sensor y control del armario."""

import streamlit as st

from nucleo import clima_actual, cliente_clima, recomendacion, sensacion

st.title("ClimaWear Smart")
st.caption("Página 1 · El clima de ahora y qué ponerte")


@st.fragment(run_every="3s")
def panel():
    c = clima_actual()

    if c is None:
        st.warning(
            "**Sensor desconectado.** No llegan datos del circuito de Wokwi. "
            "Inicia la simulación o activa el modo demo en la barra lateral."
        )
        return

    # Indicador grande, legible desde el armario
    color = "#2b7bd6" if c.temp < 18 else "#e07a1f" if c.temp > 24 else "#2a9d6f"
    st.markdown(
        f"""
        <div style="display:flex;justify-content:center;margin:8px 0 20px">
          <div style="width:200px;height:200px;border-radius:50%;
                      border:6px solid {color};display:flex;flex-direction:column;
                      align-items:center;justify-content:center;">
            <div style="font-size:52px;font-weight:700;line-height:1">{c.temp:.0f}°C</div>
            <div style="font-size:16px;opacity:.75;margin-top:6px">{sensacion(c)}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Temperatura", f"{c.temp:.1f} °C")
    col2.metric("Humedad", f"{c.hum:.0f} %")
    col3.metric("Luz solar", f"{c.luz:.0f} %")

    r = recomendacion(c)
    with st.container(border=True):
        st.subheader("Recomendación de hoy")
        st.markdown(f"**{r['prenda']}**")
        for a in r["accesorios"]:
            st.markdown(f"- {a}")

    if c.fuente == "sensor":
        st.caption(f"Sensor conectado · última lectura hace {c.hace:.0f} s")
    else:
        st.caption("Modo demo · datos de los controles de la barra lateral")


panel()

# --- Comunicación de vuelta al circuito (Streamlit -> ESP32) ---
st.divider()
st.subheader("Armario")


@st.fragment(run_every="3s")
def estado_armario():
    datos, hace = cliente_clima().lectura()
    if datos is None:
        st.caption("Sin estado del armario todavía.")
        return
    estado = datos.get("armario", "desconocido")
    st.markdown(f"Estado reportado por el ESP32: **{estado}**")


estado_armario()
if st.button("Abrir armario", icon="🚪", use_container_width=True):
    cliente_clima().abrir_armario()
    st.toast("Orden enviada al ESP32. El servo abre la puerta 5 s.")
