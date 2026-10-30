# ClimaWear Smart

Recomendador de ropa según el clima real, con interfaces multimodales. Un ESP32 simulado en Wokwi mide temperatura, humedad y luz solar; una app en Streamlit de dos páginas recomienda qué ponerse y se usa por voz y por cámara.

Proyecto final · Interfaces Multimodales · Universidad EAFIT

## Arquitectura

```
Wokwi (ESP32 + DHT22 + LDR + servo)
        │  eafit-climawear/sensores  {"temp":19.4,"hum":82,"luz":61,"armario":"cerrado"}
        ▼
  broker.hivemq.com (MQTT, puerto 1883)
        ▲
        │  eafit-climawear/armario  "abrir" | "cerrar"
Streamlit
  ├─ Página 1 · Panel de clima: indicador, métricas, recomendación, botón del armario
  └─ Página 2 · Voz y cámara: pregunta hablada con respuesta en voz, inspección de prenda por foto
```

La comunicación es bidireccional: el ESP32 publica las lecturas cada 5 s y la app le envía la orden de abrir el armario (el servo gira 90° durante 5 s y el ESP32 reporta el nuevo estado).

## Modalidades de interacción

| Modalidad | Entrada / salida | Tecnología |
| --- | --- | --- |
| Sensores físicos | Entrada | DHT22, LDR, MQTT |
| Voz | Entrada | Web Speech API del navegador (`streamlit-mic-recorder`) |
| Imagen | Entrada | `st.camera_input` + Gemini (o modo sin IA) |
| Botones y controles | Entrada | Botón del armario, controles del modo demo |
| Voz sintetizada | Salida | gTTS |
| Panel visual | Salida | Indicador y métricas de Streamlit |
| Actuador | Salida | Servomotor (puerta del armario) |

## Estructura

```
climawear/
├─ wokwi/
│  ├─ sketch.ino        firmware del ESP32
│  ├─ diagram.json      circuito
│  └─ libraries.txt     librerías de Arduino
└─ app/
   ├─ app.py            entrada y navegación
   ├─ nucleo.py         MQTT y reglas de recomendación
   ├─ vision.py         análisis de prendas
   ├─ voz.py            síntesis de voz
   ├─ paginas/
   │  ├─ panel.py       página 1
   │  └─ voz_camara.py  página 2
   ├─ requirements.txt
   └─ .streamlit/secrets.toml.example
```

## Cómo correrlo

### 1. Circuito en Wokwi

1. Crea un proyecto nuevo de ESP32 en [wokwi.com](https://wokwi.com).
2. Reemplaza `sketch.ino` y `diagram.json` con los de la carpeta `wokwi/`.
3. Crea el archivo `libraries.txt` con el mismo contenido (o agrega las librerías desde el Library Manager).
4. Inicia la simulación. En el monitor serie debe aparecer `Publicado: {...}` cada 5 s.
5. Haz clic en el DHT22 o en el LDR para cambiar temperatura, humedad y luz.

> Si al subir la luz del LDR el porcentaje baja, cambia `INVERTIR_LDR` a `false` en el sketch.

### 2. App Streamlit (local)

```bash
cd app
pip install -r requirements.txt
streamlit run app.py
```

Ábrela en Chrome: el reconocimiento de voz usa la API del navegador y funciona mejor ahí.

### 3. Análisis de prendas con IA (opcional)

1. Saca una llave gratis en [Google AI Studio](https://aistudio.google.com/apikey).
2. Copia `app/.streamlit/secrets.toml.example` como `app/.streamlit/secrets.toml` y pega la llave.

Sin llave, la página de cámara pide indicar el tipo de prenda a mano y aplica las mismas reglas.

### 4. Despliegue en Streamlit Community Cloud

1. Sube el repositorio a GitHub (el `.gitignore` deja fuera `secrets.toml`).
2. En [share.streamlit.io](https://share.streamlit.io) crea una app con archivo principal `app/app.py`.
3. En *Settings → Secrets* pega el contenido de tu `secrets.toml`.

## Modo demo

En la barra lateral, *Modo demo (sin sensor)* reemplaza el circuito por tres controles. Sirve de respaldo si el WiFi o Wokwi fallan durante la sustentación.

## Reglas de recomendación

| Condición | Recomendación |
| --- | --- |
| Temperatura < 18 °C | Chaqueta o buzo abrigado |
| 18 a 24 °C | Chaqueta ligera o capa removible |
| Temperatura > 24 °C | Ropa fresca |
| Humedad > 80 % | Sombrilla o chaqueta impermeable |
| Luz > 70 % | Gafas de sol y bloqueador |

Los umbrales están al inicio de `app/nucleo.py`.

## Notas

- Los tópicos MQTT son públicos. Si otro grupo usa los mismos nombres, cambia el prefijo `eafit-climawear/` en `sketch.ino` y en `nucleo.py` por algo único (por ejemplo `climawear-camilo/`).
- Si la app dice "Sensor desconectado", revisa que la simulación de Wokwi esté corriendo y que los tópicos coincidan.
