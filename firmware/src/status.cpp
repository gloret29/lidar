#include "status.h"

#include <WiFi.h>

#include "mpu6050.h"
#include "ota.h"
#include "settings.h"

namespace {

volatile uint32_t g_frames_ok = 0;
volatile uint32_t g_frames_bad = 0;
volatile uint16_t g_speed_dhz = 0;
volatile uint32_t g_queue = 0;
volatile uint32_t g_packets = 0;

void fillHardwareHealth(DeviceStatus& d) {
    d.wifi_ok = WiFi.status() == WL_CONNECTED;
    d.tmc_ok = scannerTmcOk();
    d.tmc_version = scannerTmcVersion();
    d.motor_enabled = scannerMotorEnabled();

    if (!d.tmc_ok) {
        d.motor_ok = false;
        d.motor_warn = false;
    } else if (!d.motor_enabled) {
        d.motor_ok = false;
        d.motor_warn = false;
    } else if (scannerHomedOk()) {
        d.motor_ok = true;
        d.motor_warn = false;
    } else {
        d.motor_ok = false;
        d.motor_warn = true;
    }

    d.imu_ok = mpu6050Ready();
    d.imu_shock = mpu6050ShockFlag();
    d.imu_has_ref = mpu6050HasLevelRef();
    if (d.imu_has_ref) {
        float g_ref[3];
        mpu6050GetLevelRef(g_ref);
        d.imu_ref_gx = g_ref[0];
        d.imu_ref_gy = g_ref[1];
        d.imu_ref_gz = g_ref[2];
    }

    const uint32_t total = d.frames_ok + d.frames_bad;
    if (total == 0) {
        d.lidar_crc_pct = -1.0f;
        d.lidar_ok = false;
        d.lidar_warn = d.uptime_s < 8;
    } else {
        d.lidar_crc_pct = 100.0f * static_cast<float>(d.frames_ok) /
                          static_cast<float>(total);
        const float hz_target = settings().lidar_hz;
        const bool hz_ok =
            d.lidar_hz_meas >= hz_target * 0.7f && d.lidar_hz_meas <= hz_target * 1.3f;
        d.lidar_ok = d.lidar_crc_pct >= 95.0f && hz_ok && d.frames_ok > 0;
        d.lidar_warn = !d.lidar_ok && d.frames_ok > 0;
    }

    float g_live[3] = {0.0f, 0.0f, -1.0f};
    if (d.imu_ok && mpu6050ReadGravity(g_live)) {
        d.imu_gx = g_live[0];
        d.imu_gy = g_live[1];
        d.imu_gz = g_live[2];
        if (mpu6050HasLevelRef()) {
            float g_ref[3];
            mpu6050GetLevelRef(g_ref);
            d.imu_tilt_deg = mpu6050TiltDeg(g_ref, g_live);
        } else {
            d.imu_tilt_deg = 0.0f;
        }
    }
}

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
    d.lidar_hz_meas = g_speed_dhz / 10.0f;
    d.frames_ok = g_frames_ok;
    d.frames_bad = g_frames_bad;
    d.queue_depth = g_queue;
    d.packets_sent = g_packets;
    d.sg_result = scannerSgResult();
    d.rssi = WiFi.RSSI();
    d.heap_free = ESP.getFreeHeap();
    d.uptime_s = millis() / 1000;
    d.ota_busy = otaInProgress();
    d.scan_busy = (d.state == ScanState::Levelling || d.state == ScanState::Homing ||
                   d.state == ScanState::Spinup || d.state == ScanState::Scanning);
    fillHardwareHealth(d);
    return d;
}
