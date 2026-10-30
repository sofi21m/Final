// ClimaWear Smart — circuito ESP32 para Wokwi
// Lee temperatura y humedad (DHT22) y luz (LDR), publica por MQTT
// y mueve el servomotor (puerta del armario) cuando la app lo pide.

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHTesp.h>
#include <ESP32Servo.h>

// ---------- Configuración ----------
const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASS = "";

const char* MQTT_BROKER = "broker.hivemq.com";
const int   MQTT_PORT   = 1883;
const char* TOPIC_SENSORES = "eafit-climawear/sensores";  // ESP32 -> app
const char* TOPIC_ARMARIO  = "eafit-climawear/armario";   // app -> ESP32

const int PIN_DHT   = 15;
const int PIN_LDR   = 34;
const int PIN_SERVO = 13;

// En el módulo LDR de Wokwi, más luz da una lectura analógica MÁS BAJA.
// Si al mover el slider de luz el porcentaje va al revés, cambia esto a false.
const bool INVERTIR_LDR = true;

const unsigned long INTERVALO_PUBLICACION = 5000;  // ms
const unsigned long TIEMPO_ARMARIO_ABIERTO = 5000; // ms

// ---------- Objetos ----------
WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);
DHTesp dht;
Servo puerta;

unsigned long ultimaPublicacion = 0;
unsigned long armarioAbiertoDesde = 0;
bool armarioAbierto = false;

void abrirArmario() {
  puerta.write(90);
  armarioAbierto = true;
  armarioAbiertoDesde = millis();
  Serial.println("Armario: abierto");
}

void cerrarArmario() {
  puerta.write(0);
  armarioAbierto = false;
  Serial.println("Armario: cerrado");
}

void alRecibirMensaje(char* topic, byte* payload, unsigned int length) {
  String mensaje;
  for (unsigned int i = 0; i < length; i++) mensaje += (char)payload[i];
  mensaje.trim();
  Serial.printf("MQTT [%s]: %s\n", topic, mensaje.c_str());

  if (mensaje == "abrir") abrirArmario();
  else if (mensaje == "cerrar") cerrarArmario();
}

void conectarWiFi() {
  Serial.print("Conectando a WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.println(" conectado");
}

void conectarMQTT() {
  while (!mqtt.connected()) {
    String clientId = "climawear-esp32-" + String((uint32_t)esp_random(), HEX);
    Serial.print("Conectando a MQTT... ");
    if (mqtt.connect(clientId.c_str())) {
      Serial.println("listo");
      mqtt.subscribe(TOPIC_ARMARIO);
    } else {
      Serial.printf("falló (rc=%d), reintento en 2 s\n", mqtt.state());
      delay(2000);
    }
  }
}

int leerLuzPorcentaje() {
  int crudo = analogRead(PIN_LDR);          // 0 a 4095 en el ESP32
  int pct = map(crudo, 0, 4095, 0, 100);
  if (INVERTIR_LDR) pct = 100 - pct;
  return constrain(pct, 0, 100);
}

void publicarLecturas() {
  TempAndHumidity th = dht.getTempAndHumidity();
  if (isnan(th.temperature) || isnan(th.humidity)) {
    Serial.println("Error leyendo el DHT22");
    return;
  }

  JsonDocument doc;
  doc["temp"] = round(th.temperature * 10) / 10.0;
  doc["hum"]  = round(th.humidity * 10) / 10.0;
  doc["luz"]  = leerLuzPorcentaje();
  doc["armario"] = armarioAbierto ? "abierto" : "cerrado";

  char buffer[128];
  serializeJson(doc, buffer);
  mqtt.publish(TOPIC_SENSORES, buffer);
  Serial.printf("Publicado: %s\n", buffer);
}

void setup() {
  Serial.begin(115200);
  dht.setup(PIN_DHT, DHTesp::DHT22);
  puerta.attach(PIN_SERVO);
  cerrarArmario();

  conectarWiFi();
  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt.setCallback(alRecibirMensaje);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) conectarWiFi();
  if (!mqtt.connected()) conectarMQTT();
  mqtt.loop();

  unsigned long ahora = millis();
  if (ahora - ultimaPublicacion >= INTERVALO_PUBLICACION) {
    ultimaPublicacion = ahora;
    publicarLecturas();
  }

  if (armarioAbierto && ahora - armarioAbiertoDesde >= TIEMPO_ARMARIO_ABIERTO) {
    cerrarArmario();
  }
}
