#pragma once

// WiFiManager — portail captif au premier démarrage (credentials en flash)
#define WIFIMANAGER_AP_NAME "LiDAR-Scanner-Setup"
#define WIFIMANAGER_AP_PASSWORD ""  // vide = AP ouvert ; ou définir un mot de passe
#define WIFIMANAGER_PORTAL_TIMEOUT_S 180
#define WIFIMANAGER_CONNECT_TIMEOUT_S 20
#define WIFI_RESET_PIN 0  // bouton BOOT DevKitC-1 — maintenir au boot pour reset WiFi

// UDP streaming (valeur par défaut du portail WiFiManager)
#define UDP_HOST_DEFAULT "192.168.1.100"
#define UDP_PORT 9000
#define POINTS_PER_PACKET 64

// LiDAR LD19 — UART1
#define LIDAR_UART_NUM 1
#define LIDAR_RX_PIN 18
#define LIDAR_TX_PIN 17
#define LIDAR_BAUD 230400

// MPU6050 — I2C
#define I2C_SDA_PIN 8
#define I2C_SCL_PIN 9
#define MPU6050_ADDR 0x68

// TMC2209 stepper
#define STEP_PIN 4
#define DIR_PIN 5
#define EN_PIN 6
#define STEPS_PER_REV 3200  // 200 steps * 16 micro-steps
#define STEPS_PER_DEGREE (STEPS_PER_REV / 360.0f)

// Scan profile
#define ELEVATION_MIN_DEG -30.0f
#define ELEVATION_MAX_DEG 90.0f
#define ELEVATION_STEP_DEG 0.5f

// Protocol magic: "LDAR"
#define PACKET_MAGIC 0x4C444152
#define PROTOCOL_VERSION 1
