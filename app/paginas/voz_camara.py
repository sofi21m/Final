"""Página 2 — Voz y cámara: preguntar por voz e inspeccionar una prenda con la cámara."""

import streamlit as st
from streamlit_mic_recorder import speech_to_text

from nucleo import clima_actual, cliente_clima, responder_pregunta
from vision import ABRIGOS, describir_con_ia, evaluar_prenda, ia_disponible
from voz import hablar

st.title("Pregúntale a ClimaWear")
st.caption("Página 2 · Habla o muestra tu ropa, sin escribir")

c = clima_actual()
if c is None:
    st.warning(
        "Sin datos del sensor, no puedo recomendar. Inicia Wokwi o activa el modo demo "
        "en la barra lateral."
    )
    st.stop()

st.info(f"Clima actual: {c.temp:.1f} °C · humedad {c.hum:.0f} % · luz {c.luz:.0f} %")

tab_voz, tab_camara = st.tabs(["🎙️ Preguntar por voz", "📷 Revisar una prenda"])

# ---------------------------------------------------------------------------
# Voz
# ---------------------------------------------------------------------------
with tab_voz:
    st.markdown("Toca el botón, haz tu pregunta y vuelve a tocarlo para terminar.")
    st.caption('Prueba con: "¿Tengo que llevar chaqueta hoy?", "¿Va a llover?", "¿Qué me pongo?"')

    texto = speech_to_text(
        language="es",
        start_prompt="🎙️ Hablar",
        stop_prompt="⏹️ Terminar",
        just_once=True,
        use_container_width=True,
        key="stt",
    )

    with st.expander("¿No funciona el micrófono? Escribe la pregunta"):
        escrito = st.text_input("Pregunta", key="pregunta_escrita", label_visibility="collapsed")
        if st.button("Preguntar", key="btn_preguntar") and escrito:
            texto = escrito

    if texto:
        st.session_state["ultima_pregunta"] = texto
        st.session_state["ultima_respuesta"] = responder_pregunta(texto, c)
        cliente_clima().abrir_armario()
        st.session_state["hablar_ahora"] = True

    if st.session_state.get("ultima_pregunta"):
        with st.chat_message("user"):
            st.write(st.session_state["ultima_pregunta"])
        with st.chat_message("assistant", avatar="🌦️"):
            st.write(st.session_state["ultima_respuesta"])
            if st.session_state.pop("hablar_ahora", False):
                hablar(st.session_state["ultima_respuesta"])

# ---------------------------------------------------------------------------
# Cámara
# ---------------------------------------------------------------------------
with tab_camara:
    st.markdown("Toma una foto de la prenda que piensas ponerte.")
    foto = st.camera_input("Foto de la prenda", label_visibility="collapsed")
    if foto is None:
        foto = st.file_uploader("O sube una imagen", type=["jpg", "jpeg", "png"])

    if foto is not None:
        prenda = None

        if ia_disponible():
            with st.spinner("Analizando la prenda..."):
                try:
                    prenda = describir_con_ia(foto.getvalue(), foto.type or "image/jpeg")
                except Exception as e:
                    st.error(f"No se pudo analizar la imagen con IA ({e}). Indica la prenda a mano.")
            if prenda is not None and not prenda["es_ropa"]:
                st.warning("No veo ninguna prenda en la foto. Intenta de nuevo con la ropa a la vista.")
                prenda = None
                st.stop()

        if prenda is None:
            st.caption("Modo sin IA: indica qué tipo de prenda es.")
            abrigo = st.radio(
                "Tipo de prenda",
                list(ABRIGOS),
                format_func=lambda k: ABRIGOS[k],
                key="abrigo_manual",
            )
            imper = st.checkbox("Es impermeable", key="imper_manual")
            prenda = {"prenda": "esta prenda", "abrigo": abrigo, "impermeable": imper}

        resultado = evaluar_prenda(prenda, c)
        col_foto, col_res = st.columns([1, 1.4])
        col_foto.image(foto, use_container_width=True)
        with col_res:
            if prenda.get("prenda") and prenda["prenda"] != "esta prenda":
                st.markdown(f"Detecté: **{prenda['prenda']}** ({prenda['abrigo']})")
            if resultado["apta"]:
                st.success("**Apta para el clima de hoy**")
            else:
                st.error("**No es la mejor opción hoy**")
            st.write(resultado["motivo"])

        clave = f"{foto.file_id if hasattr(foto, 'file_id') else foto.name}-{prenda['abrigo']}-{prenda['impermeable']}"
        if st.session_state.get("ultima_foto_hablada") != clave:
            st.session_state["ultima_foto_hablada"] = clave
            hablar(("Apta para hoy. " if resultado["apta"] else "No es la mejor opción. ") + resultado["motivo"])
