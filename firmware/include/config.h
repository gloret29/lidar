#pragma once

// ============================================================
//  Scanner 3D LiDAR — configuration du firmware
//  Voir docs/wiring.md pour la justification du brochage.
// ============================================================

#define FIRMWARE_VERSION "0.4.2"

// ---- WiFiManager : portail captif, aucun identifiant en dur ----
#define WIFIMANAGER_AP_NAME "LiDAR-Scanner-Setup"
#define WIFIMANAGER_AP_PASSWORD ""
#define WIFIMANAGER_PORTAL_TIMEOUT_S 180
#define WIFIMANAGER_CONNECT_TIMEOUT_S 20
#define WIFI_RESET_PIN 0  // bouton BOOT : maintenu au démarrage = reset Wi-Fi

// ---- Mise à jour par le réseau (OTA) ----
// Le mot de passe se configure dans le portail WiFiManager et est
// persisté en NVS. La valeur ci-dessous n'est qu'un repli au premier
// démarrage : la changer est vivement conseillé.
#define OTA_HOSTNAME "lidar-scanner"
#define OTA_PASSWORD_DEFAULT "lidar-ota"
#define OTA_PORT 3232
#define OTA_WEB_PORT 80

// L'OTA est volontairement injoignable pendant un balayage : flasher en
// pleine acquisition perdrait le scan et laisserait la mécanique dans un
// état indéterminé. Mettre à 1 pour passer outre.
#define OTA_ALLOW_DURING_SCAN 0

// Délai d'attente avant le premier balayage, pendant lequel l'OTA est
// joignable. C'est le filet de sécurité : sans lui, un firmware qui
// plante en cours de scan ne serait plus récupérable que par USB.
#define OTA_BOOT_WINDOW_S 10

// ---- Diffusion UDP ----
#define UDP_HOST_DEFAULT "192.168.1.100"
#define UDP_PORT 9000
#define POINTS_PER_PACKET 120  // 120 x 8 o + 32 o d'en-tête = 992 o < MTU

// ---- LiDAR LD19 (UART1) ----
// ATTENTION : ne pas utiliser les GPIO 33-37, occupés par la PSRAM
// octale de la variante N16R8.
#define LIDAR_RX_PIN 18
#define LIDAR_PWM_PIN 17
#define LIDAR_BAUD 230400
#define LIDAR_TARGET_HZ 5.0f  // 5 Hz : double la résolution angulaire

// ---- MPU6050 (I2C) — monté sur la base FIXE ----
#define I2C_SDA_PIN 8
#define I2C_SCL_PIN 9
#define MPU6050_ADDR 0x68
#define MPU6050_SAMPLE_HZ 100
#define MPU6050_LEVEL_SAMPLES 1000  // 10 s à 100 Hz
#define MPU6050_STABLE_CHECK_SAMPLES 50
#define MPU6050_STABLE_MAX_DEV_G 0.02f  // écart-type instantané max (~0,02 g)
#define MPU6050_SHOCK_DEG 0.3f

// ---- TMC2209 ----
#define STEP_PIN 4
#define DIR_PIN 5
#define EN_PIN 6
#define TMC_TX_PIN 7   // via résistance 1 kOhm vers PDN_UART
#define TMC_RX_PIN 15
#define TMC_DIAG_PIN 16
#define TMC_ADDRESS 0

#define MICROSTEPS 16
#define STEPS_PER_REV (200 * MICROSTEPS)          // 3200
#define STEPS_PER_DEGREE (STEPS_PER_REV / 360.0f) // 8.889

#define CURRENT_SCAN_MA 700
#define CURRENT_HOMING_MA 300

// ---- Profil de balayage ----
// 180 deg suffisent : le plan a psi et celui a psi+180 sont identiques,
// donc la sphere est couverte exactement une fois. Voir docs/geometry.md.
#define SCAN_START_DEG 0.0f
#define SCAN_END_DEG 180.0f
#define SCAN_SPEED_DEG_S 2.0f
#define HOMING_SPEED_DEG_S 10.0f
#define STALLGUARD_THRESHOLD 80

// ---- Protocole ----
#define PACKET_MAGIC 0x4C444152  // "LDAR"
#define PROTOCOL_VERSION 2
