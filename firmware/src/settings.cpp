#include "settings.h"

#include <Preferences.h>

#include "config.h"
#include "ld19.h"
#include "scanner.h"

namespace {

Preferences prefs;
ScanSettings current = settingsDefaults();

constexpr char kNs[] = "scanset";

}  // namespace

ScanSettings settingsDefaults() {
    ScanSettings s{};
    s.lidar_hz = LIDAR_TARGET_HZ;
    s.scan_speed_deg_s = SCAN_SPEED_DEG_S;
    s.scan_end_deg = SCAN_END_DEG;
    s.stallguard = STALLGUARD_THRESHOLD;
    s.current_scan_ma = CURRENT_SCAN_MA;
    s.current_homing_ma = CURRENT_HOMING_MA;
    return s;
}

ScanSettings& settings() { return current; }

void settingsClamp(ScanSettings& s) {
    s.lidar_hz = constrain(s.lidar_hz, 5.0f, 13.0f);
    s.scan_speed_deg_s = constrain(s.scan_speed_deg_s, 0.5f, 10.0f);
    s.scan_end_deg = constrain(s.scan_end_deg, 10.0f, 360.0f);
    s.stallguard = constrain(s.stallguard, static_cast<uint16_t>(1),
                             static_cast<uint16_t>(255));
    s.current_scan_ma = constrain(s.current_scan_ma, static_cast<uint16_t>(200),
                                  static_cast<uint16_t>(1200));
    s.current_homing_ma =
        constrain(s.current_homing_ma, static_cast<uint16_t>(100),
                  static_cast<uint16_t>(800));
}

void settingsLoad() {
    prefs.begin(kNs, true);
    ScanSettings s = settingsDefaults();
    s.lidar_hz = prefs.getFloat("lidar_hz", s.lidar_hz);
    s.scan_speed_deg_s = prefs.getFloat("speed", s.scan_speed_deg_s);
    s.scan_end_deg = prefs.getFloat("end_deg", s.scan_end_deg);
    s.stallguard = prefs.getUShort("sg", s.stallguard);
    s.current_scan_ma = prefs.getUShort("i_scan", s.current_scan_ma);
    s.current_homing_ma = prefs.getUShort("i_home", s.current_homing_ma);
    prefs.end();
    settingsClamp(s);
    current = s;
    Serial.printf("[settings] LiDAR %.1f Hz, %.1f deg/s jusqu'à %.0f deg, "
                  "SG=%u, I=%u/%u mA\n",
                  current.lidar_hz, current.scan_speed_deg_s, current.scan_end_deg,
                  current.stallguard, current.current_scan_ma,
                  current.current_homing_ma);
}

bool settingsSave() {
    settingsClamp(current);
    prefs.begin(kNs, false);
    prefs.putFloat("lidar_hz", current.lidar_hz);
    prefs.putFloat("speed", current.scan_speed_deg_s);
    prefs.putFloat("end_deg", current.scan_end_deg);
    prefs.putUShort("sg", current.stallguard);
    prefs.putUShort("i_scan", current.current_scan_ma);
    prefs.putUShort("i_home", current.current_homing_ma);
    prefs.end();
    Serial.println("[settings] enregistrés en NVS");
    return true;
}

void settingsApplyHardware() {
    settingsClamp(current);
    ld19SetSpeed(current.lidar_hz);
    scannerApplySettings(current);
}
