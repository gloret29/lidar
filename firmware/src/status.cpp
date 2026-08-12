#include "status.h"

#include <WiFi.h>

#include "ota.h"

namespace {

volatile uint32_t g_frames_ok = 0;
volatile uint32_t g_frames_bad = 0;
volatile uint16_t g_speed_dhz = 0;
volatile uint32_t g_queue = 0;
volatile uint32_t g_packets = 0;

}  // namespace

void statusSetLidarStats(uint32_t ok, uint32_t bad, uint16_t speed_dhz) {
    g_frames_ok = ok;
    g_frames_bad = bad;
    g_speed_dhz = speed_dhz;
}

void statusSetQueueDepth(uint32_t depth) { g_queue = depth; }

void statusSetPackets(uint32_t n) { g_packets = n; }

const char* scanStateName(ScanState s) {
    switch (s) {
        case ScanState::Idle:
            return "idle";
        case ScanState::Levelling:
            return "levelling";
        case ScanState::Homing:
            return "homing";
        case ScanState::Spinup:
            return "spinup";
        case ScanState::Scanning:
            return "scanning";
        case ScanState::Done:
            return "done";
        case ScanState::Fault:
            return "fault";
    }
    return "?";
}

DeviceStatus statusSnapshot() {
    DeviceStatus d{};
    d.state = scannerState();
    d.psi_deg = scannerPsiMdeg() / 1000.0f;
    d.lidar_hz_meas = g_speed_dhz / 10.0f;  // dHz -> Hz
    d.frames_ok = g_frames_ok;
    d.frames_bad = g_frames_bad;
    d.queue_depth = g_queue;
    d.packets_sent = g_packets;
    d.sg_result = scannerSgResult();
    d.rssi = WiFi.RSSI();
    d.heap_free = ESP.getFreeHeap();
    d.uptime_s = millis() / 1000;
    d.ota_busy = otaInProgress();
    d.scan_busy = (d.state == ScanState::Homing || d.state == ScanState::Spinup ||
                   d.state == ScanState::Scanning);
    return d;
}
