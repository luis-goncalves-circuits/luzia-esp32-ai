#include <WiFi.h>
#include <WebServer.h>
#include "secrets.h"

// LED RGB discreto de 4 pinos; cada canal exige uma resistência limitadora.
static const int PIN_RED = 25;
static const int PIN_GREEN = 26;
static const int PIN_BLUE = 27;
static const int PIN_BUZZER = 14; // buzzer activo opcional
static const bool COMMON_ANODE = false;

static const unsigned long WIFI_RETRY_INTERVAL_MS = 10000;

WebServer server(80);
int ledR = 0, ledG = 0, ledB = 0;
bool ledOn = false;
unsigned long lastWiFiAttempt = 0;
bool wifiWasConnected = false;\nbool beepActive = false;\nunsigned long beepStopAt = 0;

void writeChannel(int pin, int value) {
  const int output = COMMON_ANODE ? 255 - value : value;
  analogWrite(pin, output);
}

void applyLed(int r, int g, int b, int brightness, bool on) {
  ledOn = on;
  if (!on) r = g = b = 0;
  brightness = constrain(brightness, 1, 100);
  ledR = (r * brightness) / 100;
  ledG = (g * brightness) / 100;
  ledB = (b * brightness) / 100;
  writeChannel(PIN_RED, ledR);
  writeChannel(PIN_GREEN, ledG);
  writeChannel(PIN_BLUE, ledB);
}

void sendJsonError(int statusCode, const char* message) {
  String json = "{\"ok\":false,\"error\":\"" + String(message) + "\"}";
  server.send(statusCode, "application/json", json);
}

bool isIntegerText(const String& value) {
  if (value.length() == 0) return false;
  int index = (value[0] == '-' || value[0] == '+') ? 1 : 0;
  if (index == value.length()) return false;
  for (; index < value.length(); index++) {
    if (!isDigit(value[index])) return false;
  }
  return true;
}

void handleLed() {
  if (!server.hasArg("r") || !server.hasArg("g") || !server.hasArg("b")) {
    sendJsonError(400, "r, g e b obrigatorios");
    return;
  }
  if (!isIntegerText(server.arg("r")) || !isIntegerText(server.arg("g")) ||
      !isIntegerText(server.arg("b")) ||
      (server.hasArg("brightness") && !isIntegerText(server.arg("brightness")))) {
    sendJsonError(400, "r, g, b e brightness devem ser inteiros");
    return;
  }
  const int r = constrain(server.arg("r").toInt(), 0, 255);
  const int g = constrain(server.arg("g").toInt(), 0, 255);
  const int b = constrain(server.arg("b").toInt(), 0, 255);
  const int brightness = server.hasArg("brightness") ? server.arg("brightness").toInt() : 100;
  bool on = true;
  if (server.hasArg("on")) {
    const String onValue = server.arg("on");
    if (onValue == "false") on = false;
    else if (onValue != "true") {
      sendJsonError(400, "on deve ser true ou false");
      return;
    }
  }

  applyLed(r, g, b, brightness, on);

  String json = "{\"ok\":true,\"r\":" + String(ledR) +
                ",\"g\":" + String(ledG) + ",\"b\":" + String(ledB) +
                ",\"on\":" + String(ledOn ? "true" : "false") + "}";
  server.send(200, "application/json", json);
}

void handleStatus() {
  String json = "{\"ok\":true,\"r\":" + String(ledR) +
                ",\"g\":" + String(ledG) + ",\"b\":" + String(ledB) +
                ",\"on\":" + String(ledOn ? "true" : "false") + "}";
  server.send(200, "application/json", json);
}

void handleBeep() {
  if (server.hasArg("duration_ms") && !isIntegerText(server.arg("duration_ms"))) {
    sendJsonError(400, "duration_ms deve ser inteiro");
    return;
  }
  const int requestedDuration = server.hasArg("duration_ms") ? server.arg("duration_ms").toInt() : 250;
  const int duration = constrain(requestedDuration, 50, 2000);
  digitalWrite(PIN_BUZZER, HIGH);
  beepActive = true;
  beepStopAt = millis() + static_cast<unsigned long>(duration);
  server.send(200, "application/json", "{\"ok\":true,\"duration_ms\":" + String(duration) + "}");
}

void startHttpServer() {
  server.on("/led", HTTP_POST, handleLed);
  server.on("/status", HTTP_GET, handleStatus);
  server.on("/beep", HTTP_POST, handleBeep);
  server.onNotFound([]() {
    sendJsonError(404, "not found");
  });
  server.begin();
  Serial.println("Servidor HTTP LuzIA iniciado na porta 80.");
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_RED, OUTPUT);
  pinMode(PIN_GREEN, OUTPUT);
  pinMode(PIN_BLUE, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_BUZZER, LOW);
  analogWriteResolution(8);
  applyLed(0, 0, 0, 100, false);

  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  lastWiFiAttempt = millis();
  Serial.println("A iniciar ligação Wi-Fi...");

  // O servidor HTTP é inicializado mesmo sem Wi-Fi. A ligação é gerida no loop,
  // evitando bloquear indefinidamente o arranque quando a rede está indisponível.
  startHttpServer();
}

void loop() {
  server.handleClient();

  if (beepActive && static_cast<long>(millis() - beepStopAt) >= 0) {
    digitalWrite(PIN_BUZZER, LOW);
    beepActive = false;
  }

  if (WiFi.status() == WL_CONNECTED) {
    if (!wifiWasConnected) {
      Serial.print("ESP32 ligado. IP: ");
      Serial.println(WiFi.localIP());
      wifiWasConnected = true;
    }
    return;
  }

  if (wifiWasConnected) {
    Serial.println("Ligação Wi-Fi perdida.");
    wifiWasConnected = false;
  }

  const unsigned long now = millis();
  if (now - lastWiFiAttempt >= WIFI_RETRY_INTERVAL_MS) {
    lastWiFiAttempt = now;
    Serial.println("A tentar recuperar ligação Wi-Fi...");
    WiFi.reconnect();
  }
}
