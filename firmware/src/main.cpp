/**
 * Scanner 3D LiDAR DIY — firmware ESP32-S3
 *
 * Tasks FreeRTOS (à implémenter progressivement) :
 *   1. lidar_task   — parsing UART LD19
 *   2. stepper_task — balayage vertical phi
 *   3. imu_task     — lecture MPU6050
 *   4. fusion_task  — conversion (X, Y, Z)
 *   5. network_task — streaming UDP
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <esp_timer.h>

#include "config.h"
#include "wifi_setup.h"

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

struct LidarPoint {
  float rho;
  float theta;
  uint64_t timestamp_us;
};

struct CartesianPoint {
  float x;
  float y;
  float z;
  uint32_t quality;
};

// ---------------------------------------------------------------------------
// Globals
// ---------------------------------------------------------------------------

WiFiUDP udp;
static String udp_host = UDP_HOST_DEFAULT;

static float pitch_offset_deg = 0.0f;
static float elevation_deg = 0.0f;

// ---------------------------------------------------------------------------
// Coordinate transform
// ---------------------------------------------------------------------------

CartesianPoint toCartesian(float rho, float theta_deg, float phi_deg) {
  const float theta = theta_deg * DEG_TO_RAD;
  const float phi = phi_deg * DEG_TO_RAD;

  CartesianPoint p{};
  p.x = rho * cosf(phi) * cosf(theta);
  p.y = rho * cosf(phi) * sinf(theta);
  p.z = rho * sinf(phi);
  p.quality = 0;
  return p;
}

// ---------------------------------------------------------------------------
// Network (stub)
// ---------------------------------------------------------------------------

void sendPointBatch(const CartesianPoint* points, uint16_t count) {
  if (WiFi.status() != WL_CONNECTED || count == 0) {
    return;
  }

  // Header: magic(4) + version(2) + count(2) + timestamp(8) = 16 bytes
  // Point: x(4) + y(4) + z(4) + quality(4) = 16 bytes
  const size_t header_size = 16;
  const size_t point_size = 16;
  const size_t buf_size = header_size + count * point_size;

  uint8_t* buf = static_cast<uint8_t*>(malloc(buf_size));
  if (!buf) {
    return;
  }

  uint32_t magic = PACKET_MAGIC;
  uint16_t version = PROTOCOL_VERSION;
  uint64_t ts = esp_timer_get_time();

  memcpy(buf + 0, &magic, 4);
  memcpy(buf + 4, &version, 2);
  memcpy(buf + 6, &count, 2);
  memcpy(buf + 8, &ts, 8);

  for (uint16_t i = 0; i < count; i++) {
    size_t off = header_size + i * point_size;
    memcpy(buf + off + 0, &points[i].x, 4);
    memcpy(buf + off + 4, &points[i].y, 4);
    memcpy(buf + off + 8, &points[i].z, 4);
    memcpy(buf + off + 12, &points[i].quality, 4);
  }

  udp.beginPacket(udp_host.c_str(), UDP_PORT);
  udp.write(buf, buf_size);
  udp.endPacket();

  free(buf);
}

// ---------------------------------------------------------------------------
// Stepper (stub — STEP/DIR bit-bang)
// ---------------------------------------------------------------------------

void stepperInit() {
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  pinMode(EN_PIN, OUTPUT);
  digitalWrite(EN_PIN, LOW);  // enable driver
}

void stepperStep(int32_t steps, bool direction_cw) {
  digitalWrite(DIR_PIN, direction_cw ? HIGH : LOW);
  for (int32_t i = 0; i < steps; i++) {
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(2);
    digitalWrite(STEP_PIN, LOW);
    delayMicroseconds(2);
  }
}

// ---------------------------------------------------------------------------
// Setup / loop (skeleton)
// ---------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("[lidar-scanner] boot");

  stepperInit();

  // LiDAR UART
  Serial1.begin(LIDAR_BAUD, SERIAL_8N1, LIDAR_RX_PIN, LIDAR_TX_PIN);

  wifiCheckResetButton();
  if (!wifiSetup(udp_host)) {
    Serial.println("[wifi] redémarrage dans 3 s...");
    delay(3000);
    ESP.restart();
  }

  udp.begin(UDP_PORT);
  Serial.println("[lidar-scanner] ready");
}

void loop() {
  // TODO: replace with FreeRTOS tasks
  // Demo: send a single test point every second
  static uint32_t last = 0;
  if (millis() - last > 1000) {
    last = millis();
    elevation_deg += ELEVATION_STEP_DEG;
    if (elevation_deg > ELEVATION_MAX_DEG) {
      elevation_deg = ELEVATION_MIN_DEG;
    }

    const float phi = elevation_deg + pitch_offset_deg;
    CartesianPoint demo = toCartesian(1.0f, 0.0f, phi);
    sendPointBatch(&demo, 1);

    Serial.printf("[demo] phi=%.1f -> (%.3f, %.3f, %.3f)\n", phi, demo.x, demo.y,
                  demo.z);
  }
}
