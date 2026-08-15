#pragma once

#include <Arduino.h>

#include "scanner.h"

// ============================================================
//  Instantané d'état pour la page web et la console
// ============================================================

struct DeviceStatus {
    ScanState state;
    float psi_deg;
    float lidar_hz_meas;   // mesurée (vitesse trame / 360)
    uint32_t frames_ok;
    uint32_t frames_bad;
    uint32_t queue_depth;
    uint32_t packets_sent;
    int16_t sg_result;     // StallGuard live (-1 si indisponible)
    int8_t rssi;
    uint32_t heap_free;
    uint32_t uptime_s;
    bool ota_busy;
    bool scan_busy;
    bool imu_ok;
    bool imu_shock;
    bool imu_has_ref;
    float imu_gx;
    float imu_gy;
    float imu_gz;
    float imu_ref_gx;
    float imu_ref_gy;
    float imu_ref_gz;
    float imu_tilt_deg;
    // Santé matérielle (panneau web)
    bool wifi_ok;
    bool lidar_ok;
    bool lidar_warn;
    bool tmc_ok;
    bool motor_enabled;
    bool motor_ok;
    bool motor_warn;
    uint8_t tmc_version;
    float lidar_crc_pct;  // 0..100, -1 si aucune trame
};

void statusSetLidarStats(uint32_t ok, uint32_t bad, uint16_t speed_dhz);
void statusSetQueueDepth(uint32_t depth);
void statusSetPackets(uint32_t n);
DeviceStatus statusSnapshot();

const char* scanStateName(ScanState s);
