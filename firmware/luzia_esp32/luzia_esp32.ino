#include <WiFi.h>
#include <WebServer.h>
#include "secrets.h"

// LED RGB de 4 pinos (cátodo comum), com uma resistência de 220-330 ohm
// em cada canal. Para ânodo comum, muda COMMON_ANODE para true.
static const int PIN_RED = 25;
static const int PIN_GREEN = 26;
static const int PIN_BLUE = 27;
static const int PIN_BUZZER = 14; // buzzer ativo, opcional
static const bool COMMON_ANODE = false;

WebServer server(80);
int ledR = 0, ledG = 0, ledB = 0;
bool ledOn = false;

void writeChannel(int pin, int value) {
  int output = COMMON_ANODE ? 255 - value : value;
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

void addCorsHeaders() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  server.sendHeader("Access-Control-Allow-Headers", "Content-Type");
}

void handleOptions() {
  addCorsHeaders();
  server.send(204);
}

void handleLed() {
  if (!server.hasArg("r") || !server.hasArg("g") || !server.hasArg("b")) {
    addCorsHeaders();
    server.send(400, "application/json", "{\"ok\":false,\"error\":\"r, g e b obrigatorios\"}");
    return;
  }
  int r = constrain(server.arg("r").toInt(), 0, 255);
  int g = constrain(server.arg("g").toInt(), 0, 255);
  int b = constrain(server.arg("b").toInt(), 0, 255);
  int brightness = server.hasArg("brightness") ? server.arg("brightness").toInt() : 100;
  bool on = !server.hasArg("on") || server.arg("on") != "false";
  applyLed(r, g, b, brightness, on);

  String json = "{\"ok\":true,\"r\":" + String(ledR) +
                ",\"g\":" + String(ledG) + ",\"b\":" + String(ledB) +
                ",\"on\":" + String(ledOn ? "true" : "false") + "}";
  addCorsHeaders();
  server.send(200, "application/json", json);
}

void handleStatus() {
  String json = "{\"ok\":true,\"r\":" + String(ledR) +
                ",\"g\":" + String(ledG) + ",\"b\":" + String(ledB) +
                ",\"on\":" + String(ledOn ? "true" : "false") + "}";
  addCorsHeaders();
  server.send(200, "application/json", json);
}

void handleBeep() {
  int duration = server.hasArg("duration_ms") ? server.arg("duration_ms").toInt() : 250;
  duration = constrain(duration, 50, 2000);
  digitalWrite(PIN_BUZZER, HIGH);
  delay(duration);
  digitalWrite(PIN_BUZZER, LOW);
  addCorsHeaders();
  server.send(200, "application/json", "{\"ok\":true,\"duration_ms\":" + String(duration) + "}");
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
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("A ligar ao Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("ESP32 ligado. IP: ");
  Serial.println(WiFi.localIP());

  server.on("/led", HTTP_POST, handleLed);
  server.on("/status", HTTP_GET, handleStatus);
  server.on("/beep", HTTP_POST, handleBeep);
  server.on("/led", HTTP_OPTIONS, handleOptions);
  server.on("/status", HTTP_OPTIONS, handleOptions);
  server.on("/beep", HTTP_OPTIONS, handleOptions);
  server.onNotFound([]() {
    addCorsHeaders();
    server.send(404, "application/json", "{\"ok\":false,\"error\":\"not found\"}");
  });
  server.begin();
  Serial.println("Servidor HTTP LuzIA iniciado na porta 80.");
}

void loop() {
  server.handleClient();
  if (WiFi.status() != WL_CONNECTED) {
    WiFi.reconnect();
  }
}
