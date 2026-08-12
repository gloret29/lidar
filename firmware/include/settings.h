#pragma once

#include <Arduino.h>

// ============================================================
//  Paramètres de balayage persistés en NVS
//
//  Les valeurs par défaut viennent de config.h. Les bornes sont
//  appliquées à chaque écriture : un formulaire malveillant ou
//  mal rempli ne peut pas demander 3 A au moteur.
// ============================================================

struct ScanSettings {
    float lidar_hz;           // 5..13
    float scan_speed_deg_s;   // 0.5..10
    float scan_end_deg;       // 10..360
    uint16_t stallguard;      // 1..255
    uint16_t current_scan_ma; // 200..1200
    uint16_t current_homing_ma; // 100..800
};

ScanSettings settingsDefaults();
ScanSettings& settings();          // lecture / écriture en RAM
void settingsLoad();               // NVS -> RAM
bool settingsSave();               // RAM -> NVS (après clamp)
void settingsClamp(ScanSettings& s);

/// Applique les paramètres au matériel (PWM LiDAR, courants TMC, seuil).
/// Sans effet sur un balayage déjà en cours, sauf lidar_hz.
void settingsApplyHardware();
