/**
 * Scanner 3D LiDAR DIY — firmware ESP32-S3
 *
 * Le LD19 est monté sur la tranche : son plan de balayage est vertical
 * et contient l'axe de rotation. L'angle interne du LiDAR est donc
 * l'ÉLÉVATION, et l'angle moteur l'AZIMUT. Voir docs/geometry.md.
 *
 * Les points partent en POLAIRE BRUT ; la conversion cartésienne est
 * faite côté hôte, où la calibration reste modifiable après coup.
 *
 * Tâches :
 *   lidar_task    cœur 1  UART LD19 -> file de points
 *   network_task  cœur 0  agrégation -> datagrammes UDP
 *   motion_task   cœur 1  commandes start/stop/rehome/estop
 *   web_task      cœur 0  panneau web + OTA (voir ota.cpp)
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <esp_timer.h>

#include "config.h"
#include "control.h"
#include "ld19.h"
#include "mpu6050.h"
#include "ota.h"
#include "protocol.h"
#include "scanner.h"
#include "settings.h"
#include "status.h"
#include "wifi_setup.h"

namespace {

WiFiUDP udp;
NetworkSettings net_settings;

QueueHandle_t point_queue = nullptr;
TaskHandle_t lidar_task_handle = nullptr;
TaskHandle_t network_task_handle = nullptr;

uint32_t packet_sequence = 0;
volatile uint16_t lidar_speed_dhz = 0;
volatile uint16_t pending_flags = 0;

volatile bool ota_lock = false;

struct QueuedPoint {
    RawPoint pt;
    uint64_t t_us;
    int32_t psi_mdeg;
};

Ld19Parser g_parser;

bool imuAbortRequested() {
    ScanCommand pending;
    if (!controlTryRecv(pending)) return false;
    if (pending == ScanCommand::EStop) {
        scannerEmergencyStop();
        return true;
    }
    return pending == ScanCommand::Stop;
}

bool pollScanShock(const float g_ref[3]) {
    if (!mpu6050Ready()) return false;
    if (!mpu6050DetectShock(g_ref)) return false;
    pending_flags |= PKT_FLAG_SHOCK_DETECTED;
    mpu6050SetShockFlag(true);
    Serial.println("[main] choc détecté — scan suspect");
    return true;
}

void pollScanCommands(bool &estop, bool &stop) {
    ScanCommand pending;
    while (controlTryRecv(pending)) {
        if (pending == ScanCommand::EStop) estop = true;
        if (pending == ScanCommand::Stop) stop = true;
    }
}

void lidarTask(void*) {
    g_parser.begin();
    Ld19Frame frame;

    for (;;) {
        while (Serial1.available()) {
            if (!g_parser.feed(static_cast<uint8_t>(Serial1.read()), frame)) continue;

            lidar_speed_dhz = static_cast<uint16_t>(frame.speed_dps / 36);
            statusSetLidarStats(g_parser.framesOk(), g_parser.framesBad(),
                                lidar_speed_dhz);
            const uint64_t now = esp_timer_get_time();
            const int32_t psi = scannerPsiMdeg();

            for (int i = 0; i < LD19_POINTS_PER_FRAME; i++) {
                if (frame.points[i].distance_mm == 0) continue;

                QueuedPoint q;
                q.pt.rho_mm = frame.points[i].distance_mm;
                q.pt.theta_cdeg = frame.points[i].angle_cdeg;
                q.pt.intensity = frame.points[i].intensity;
                q.pt.reserved = 0;
                q.pt.dt_us = 0;
                q.t_us = now;
                q.psi_mdeg = psi;
                xQueueSend(point_queue, &q, 0);
            }
        }
        statusSetQueueDepth(uxQueueMessagesWaiting(point_queue));
        vTaskDelay(1);
    }
}

void networkTask(void*) {
    static uint8_t buffer[sizeof(PacketHeader) + POINTS_PER_PACKET * sizeof(RawPoint)];
    QueuedPoint q;

    for (;;) {
        uint16_t count = 0;
        uint64_t t_start = 0;
        int32_t psi_start = 0, psi_end = 0;

        while (count < POINTS_PER_PACKET) {
            const TickType_t wait = (count == 0) ? pdMS_TO_TICKS(200) : 0;
            if (xQueueReceive(point_queue, &q, wait) != pdTRUE) break;

            if (count == 0) {
                t_start = q.t_us;
                psi_start = q.psi_mdeg;
            }
            psi_end = q.psi_mdeg;

            const uint64_t delta = q.t_us - t_start;
            q.pt.dt_us = static_cast<uint16_t>(delta > 65535 ? 65535 : delta);

            memcpy(buffer + sizeof(PacketHeader) + count * sizeof(RawPoint), &q.pt,
                   sizeof(RawPoint));
            count++;
        }

        if (count == 0 || WiFi.status() != WL_CONNECTED) continue;

        PacketHeader h{};
        h.magic = PACKET_MAGIC;
        h.version = PROTOCOL_VERSION;
        h.flags = pending_flags;
        h.sequence = packet_sequence++;
        h.point_count = count;
        h.lidar_speed_dhz = lidar_speed_dhz;
        h.t_start_us = t_start;
        h.psi_start_mdeg = psi_start;
        h.psi_end_mdeg = psi_end;
        pending_flags = 0;
        memcpy(buffer, &h, sizeof(h));

        udp.beginPacket(net_settings.udp_host.c_str(), UDP_PORT);
        udp.write(buffer, sizeof(PacketHeader) + count * sizeof(RawPoint));
        udp.endPacket();
        statusSetPackets(packet_sequence);
    }
}

bool runScanSequence() {
    if (ota_lock) {
        Serial.println("[main] balayage refusé : OTA en cours");
        return false;
    }

    scannerEnable();
    pending_flags |= PKT_FLAG_SCAN_START;
    mpu6050SetShockFlag(false);

    float g_ref[3] = {0.0f, 0.0f, -1.0f};
    if (mpu6050Ready()) {
        scannerSetState(ScanState::Levelling);
        if (!mpu6050MeasureLevel(g_ref, imuAbortRequested)) {
            Serial.println("[main] nivellement IMU échoué");
            pending_flags |= PKT_FLAG_SCAN_END;
            scannerSetState(ScanState::Fault);
            return false;
        }
        pending_flags |= PKT_FLAG_LEVEL_VALID;
        mpu6050StoreLevelRef(g_ref);
    } else {
        Serial.println("[main] IMU absent — nivellement ignoré");
    }

    if (!scannerHome()) {
        Serial.println("[main] homing échoué");
        pending_flags |= PKT_FLAG_SCAN_END;
        return false;
    }

    // Une commande Stop/EStop pendant le homing a pu arriver.
    ScanCommand pending;
    while (controlTryRecv(pending)) {
        if (pending == ScanCommand::EStop) {
            scannerEmergencyStop();
            pending_flags |= PKT_FLAG_SCAN_END;
            return false;
        }
        if (pending == ScanCommand::Stop) {
            pending_flags |= PKT_FLAG_SCAN_END;
            scannerSetState(ScanState::Idle);
            return false;
        }
    }

    Serial.println("[main] montée en vitesse du LiDAR");
    scannerSetState(ScanState::Spinup);
    for (int i = 0; i < 30; i++) {
        bool estop = false, stop = false;
        pollScanCommands(estop, stop);
        if (estop) {
            pending_flags |= PKT_FLAG_SCAN_END;
            return false;
        }
        if (stop) {
            scannerSetState(ScanState::Idle);
            pending_flags |= PKT_FLAG_SCAN_END;
            return false;
        }
        if (mpu6050HasLevelRef()) pollScanShock(g_ref);
        vTaskDelay(pdMS_TO_TICKS(100));
    }

    scannerStartSweep();
    uint32_t last_shock_ms = millis();
    while (scannerState() == ScanState::Scanning) {
        bool estop = false, stop = false;
        pollScanCommands(estop, stop);
        if (estop) {
            scannerEmergencyStop();
            pending_flags |= PKT_FLAG_SCAN_END;
            return false;
        }
        if (stop) scannerRequestStop();
        if (mpu6050HasLevelRef() && millis() - last_shock_ms >= 100) {
            last_shock_ms = millis();
            pollScanShock(g_ref);
        }
        scannerTick();
        taskYIELD();
    }

    if (mpu6050HasLevelRef()) {
        Serial.println("[main] contrôle IMU post-balayage");
        const uint32_t t0 = millis();
        while (millis() - t0 < 2000) {
            pollScanShock(g_ref);
            bool estop = false, stop = false;
            pollScanCommands(estop, stop);
            if (estop) {
                scannerEmergencyStop();
                pending_flags |= PKT_FLAG_SCAN_END;
                return false;
            }
            vTaskDelay(pdMS_TO_TICKS(50));
        }
    }

    pending_flags |= PKT_FLAG_SCAN_END;
    if (scannerState() == ScanState::Done) scannerSetState(ScanState::Idle);
    Serial.println("[main] scan terminé");
    return true;
}

void motionTask(void*) {
    // Au démarrage on reste au repos : l'OTA et le panneau web sont
    // immédiatement joignables. Plus de balayage automatique — un scan
    // se lance depuis http://lidar-scanner.local/
    Serial.println("[main] en attente de commande (web / API)");
    scannerSetState(ScanState::Idle);

    for (;;) {
        const ScanCommand cmd = controlWait();
        if (ota_lock && cmd != ScanCommand::EStop) {
            Serial.println("[main] commande ignorée : OTA en cours");
            continue;
        }

        switch (cmd) {
            case ScanCommand::Start:
                runScanSequence();
                break;
            case ScanCommand::Rehome:
                scannerEnable();
                if (scannerHome()) scannerSetState(ScanState::Idle);
                break;
            case ScanCommand::Stop:
                scannerRequestStop();
                break;
            case ScanCommand::EStop:
                scannerEmergencyStop();
                break;
        }
    }
}

bool otaIsBusy() {
    switch (scannerState()) {
        case ScanState::Homing:
        case ScanState::Spinup:
        case ScanState::Scanning:
            return true;
        default:
            return false;
    }
}

void otaOnBegin() {
    ota_lock = true;
    controlSend(ScanCommand::EStop);
    scannerEmergencyStop();
    if (lidar_task_handle) vTaskSuspend(lidar_task_handle);
    if (network_task_handle) vTaskSuspend(network_task_handle);
}

void otaOnAbort() {
    if (lidar_task_handle) vTaskResume(lidar_task_handle);
    if (network_task_handle) vTaskResume(network_task_handle);
    ota_lock = false;
    Serial.println("[main] mise à jour abandonnée");
}

}  // namespace

void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.printf("\n[lidar-scanner] démarrage — firmware %s\n", FIRMWARE_VERSION);

    settingsLoad();

    Serial1.begin(LIDAR_BAUD, SERIAL_8N1, LIDAR_RX_PIN, -1);
    Serial1.setRxBufferSize(4096);

    scannerInit();
    settingsApplyHardware();
    mpu6050Init();

    wifiCheckResetButton();
    if (!wifiSetup(net_settings)) {
        Serial.println("[wifi] redémarrage dans 3 s");
        delay(3000);
        ESP.restart();
    }
    udp.begin(UDP_PORT);

    controlInit();
    otaInit(OTA_HOSTNAME, net_settings.ota_password,
            OtaHooks{otaIsBusy, otaOnBegin, otaOnAbort});

    point_queue = xQueueCreate(2048, sizeof(QueuedPoint));
    if (!point_queue) {
        Serial.println("[main] création de la file impossible");
        ESP.restart();
    }

    xTaskCreatePinnedToCore(lidarTask, "lidar", 4096, nullptr, 5, &lidar_task_handle,
                            1);
    xTaskCreatePinnedToCore(networkTask, "network", 4096, nullptr, 3,
                            &network_task_handle, 0);
    xTaskCreatePinnedToCore(motionTask, "motion", 4096, nullptr, 4, nullptr, 1);

    Serial.println("[lidar-scanner] prêt — ouvrir http://lidar-scanner.local/");
}

void loop() {
    static uint32_t last = 0;
    if (millis() - last > 2000) {
        last = millis();
        const DeviceStatus d = statusSnapshot();
        Serial.printf("[stat] %s  psi=%.2f  LiDAR=%.1fHz  file=%u  crc=%u/%u%s\n",
                      scanStateName(d.state), d.psi_deg, d.lidar_hz_meas,
                      static_cast<unsigned>(d.queue_depth),
                      static_cast<unsigned>(d.frames_ok),
                      static_cast<unsigned>(d.frames_bad),
                      otaInProgress() ? "  [OTA]" : "");
    }
    vTaskDelay(pdMS_TO_TICKS(100));
}
