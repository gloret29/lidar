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
};

void statusSetLidarStats(uint32_t ok, uint32_t bad, uint16_t speed_dhz);
void statusSetQueueDepth(uint32_t depth);
void statusSetPackets(uint32_t n);
DeviceStatus statusSnapshot();

const char* scanStateName(ScanState s);
