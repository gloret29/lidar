#pragma once

#include <Arduino.h>

// ============================================================
//  MPU6050 (GY-521) — base fixe, I2C
//
//  Nivellement statique au début de chaque scan et détection
//  de choc pendant le balayage. Voir docs/calibration.md § 4.
// ============================================================

/// Initialise le bus I2C et le capteur. Renvoie false si absent.
bool mpu6050Init();

bool mpu6050Ready();

/// Moyenne MPU6050_LEVEL_SAMPLES à MPU6050_SAMPLE_HZ (≈10 s).
/// Remplit g avec le vecteur gravité normalisé (repère capteur).
/// Échoue si le capteur bouge ou si |g| s'écarte trop de 1 g.
/// abort_fn() true => abandon (Stop / EStop).
bool mpu6050MeasureLevel(float g[3], bool (*abort_fn)() = nullptr);

/// Angle en degrés entre deux vecteurs gravité (normalisés en interne).
float mpu6050TiltDeg(const float ref[3], const float cur[3]);

/// true si le trépied a bougé de plus de MPU6050_SHOCK_DEG vs ref.
bool mpu6050DetectShock(const float ref[3]);

/// Moyenne courte (10 échantillons) pour la télémétrie live.
bool mpu6050ReadGravity(float g[3]);

void mpu6050StoreLevelRef(const float g[3]);
bool mpu6050HasLevelRef();
void mpu6050GetLevelRef(float g[3]);

void mpu6050SetShockFlag(bool v);
bool mpu6050ShockFlag();
