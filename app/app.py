"""ClimaWear Smart — punto de entrada principal de la app Streamlit."""

import streamlit as st
from nucleo import cliente_clima, controles_demo

# 1. Configuración general de la página
st.set_page_config(
    page_title="ClimaWear Smart",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Inyección de CSS con nueva paleta de colores (Turquesa / Menta / Violeta)
st.markdown(
    """
    <style>
    /* Estilo de tarjetas con borde turquesa y fondo adaptable */
    div[data-testid="stMetric"], div.stCard {
        background: rgba(0, 180, 216, 0.05);
        border: 1px solid rgba(0, 180, 216, 0.3);
        padding: 18px;
        border-radius: 14px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        backdrop-filter: blur(8px);
    }
    
    /* Hover suave en las tarjetas */
    div[data-testid="stMetric"]:hover {
        border-color: #00B4D8;
        transform: translateY(-2px);
        transition: all 0.3s ease;
    }

    /* Banner superior en la barra lateral con gradiente Turquesa -> Violeta */
    .sidebar-header {
        background: linear-gradient(135deg, #00B4D8 0%, #7209B7 100%);
        padding: 20px 15px;
        border-radius: 12px;
        color: #FFFFFF;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(114, 9, 183, 0.25);
    }
    .sidebar-header h2 {
        color: #FFFFFF !important;
        margin: 0;
        font-size: 1.4rem;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .sidebar-header p {
        color: #E0F7FA !important;
        margin: 4px 0 0 0;
        font-size: 0.85rem;
        font-weight: 400;
        opacity: 0.9;
    }

    /* Personalización sutil de divisores */
    hr {
        border-color: rgba(0, 180, 216, 0.2) !important;
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

# 6. Renderizar controles de demo en la barra lateral
with st.sidebar:
    st.markdown("---")
    with st.expander("🛠️ Controles de prueba (Demo)", expanded=False):
        controles_demo()

    st.caption("⚡ Powered by Multimodal AI & IoT")

# 7. Ejecución de la página seleccionada
paginas.run()
