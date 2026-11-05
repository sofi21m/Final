"""ClimaWear Smart — punto de entrada principal de la app Streamlit."""

import streamlit as st
from nucleo import cliente_clima, controles_demo

# 1. Configuración general de la página (layout="wide" da más espacio visual)
st.set_page_config(
    page_title="ClimaWear Smart",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Inyección de CSS personalizado para mejorar la interfaz (tarjetas, sombras y bordes)
st.markdown(
    """
    <style>
    /* Estilo para tarjetas y contenedores principales */
    div[data-testid="stMetric"], div.stCard {
        background-color: #1E222D;
        border: 1px solid #2E3440;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    /* Estilo del banner de la barra lateral */
    .sidebar-header {
        background: linear-gradient(135deg, #2b5876 0%, #4e4376 100%);
        padding: 16px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .sidebar-header h2 {
        color: #FFFFFF !important;
        margin: 0;
        font-size: 1.3rem;
    }
    .sidebar-header p {
        color: #E0E0E0;
        margin: 4px 0 0 0;
        font-size: 0.85rem;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# 3. Inicialización del cliente MQTT
cliente_clima()

# 4. Encabezado de marca en la barra lateral
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-header">
            <h2>🌦️ ClimaWear</h2>
            <p>Smart Outfit Recommendations</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# 5. Configuración estructurada de la navegación
paginas = st.navigation(
    {
        "Módulos Principales": [
            st.Page(
                "paginas/panel.py",
                title="Panel de Clima",
                icon="🌡️",
                default=True,
            ),
            st.Page(
                "paginas/voz_camara.py", title="Voz y Cámara", icon="🎙️"
            ),
        ]
    }
)

# 6. Renderizar controles de demo en la barra lateral con un visualizador limpio
with st.sidebar:
    st.markdown("---")
    with st.expander("🛠️ Controles de prueba (Demo)", expanded=False):
        controles_demo()

    st.caption("⚡ Powered by Multimodal AI & IoT")

# 7. Ejecución de la página seleccionada
paginas.run()
