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
 *   lidar_task    coeur 1  UART LD19 -> file de points
 *   network_task  coeur 0  agrégation -> datagrammes UDP
 *   motion_task   coeur 1  profil moteur, nivellement, homing
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <esp_timer.h>

#include "config.h"
#include "ld19.h"
#include "protocol.h"
#include "scanner.h"
#include "wifi_setup.h"

namespace {

WiFiUDP udp;
String udp_host = UDP_HOST_DEFAULT;

QueueHandle_t point_queue = nullptr;
uint32_t packet_sequence = 0;
volatile uint16_t lidar_speed_dhz = 0;
volatile uint16_t pending_flags = 0;

struct QueuedPoint {
    RawPoint pt;
    uint64_t t_us;
    int32_t psi_mdeg;
};

// ------------------------------------------------------------
//  Tâche LiDAR
// ------------------------------------------------------------
void lidarTask(void *) {
    Ld19Parser parser;
    parser.begin();
    Ld19Frame frame;

    for (;;) {
        while (Serial1.available()) {
            if (!parser.feed(static_cast<uint8_t>(Serial1.read()), frame)) continue;

            lidar_speed_dhz = static_cast<uint16_t>(frame.speed_dps / 36);
            const uint64_t now = esp_timer_get_time();
            const int32_t psi = scannerPsiMdeg();

            for (int i = 0; i < LD19_POINTS_PER_FRAME; i++) {
                if (frame.points[i].distance_mm == 0) continue;  // pas de retour

                QueuedPoint q;
                q.pt.rho_mm = frame.points[i].distance_mm;
                q.pt.theta_cdeg = frame.points[i].angle_cdeg;
                q.pt.intensity = frame.points[i].intensity;
                q.pt.reserved = 0;
                q.pt.dt_us = 0;
                q.t_us = now;
                q.psi_mdeg = psi;
                xQueueSend(point_queue, &q, 0);  // on préfère perdre un point
                                                 // que bloquer l'UART
            }
        }
        vTaskDelay(1);
    }
}

// ------------------------------------------------------------
//  Tâche réseau
// ------------------------------------------------------------
void networkTask(void *) {
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

        udp.beginPacket(udp_host.c_str(), UDP_PORT);
        udp.write(buffer, sizeof(PacketHeader) + count * sizeof(RawPoint));
        udp.endPacket();
    }
}

// ------------------------------------------------------------
//  Tâche mouvement
// ------------------------------------------------------------
void motionTask(void *) {
    delay(2000);

    pending_flags |= PKT_FLAG_SCAN_START;
    if (!scannerHome()) {
        Serial.println("[main] homing échoué, scan annulé");
        vTaskDelete(nullptr);
        return;
    }

    Serial.println("[main] montée en vitesse du LiDAR");
    scannerSetState(ScanState::Spinup);
    delay(3000);

    scannerStartSweep();
    while (scannerState() == ScanState::Scanning) {
        scannerTick();
        taskYIELD();
    }

    pending_flags |= PKT_FLAG_SCAN_END;
    Serial.println("[main] scan terminé");
    vTaskDelete(nullptr);
}

}  // namespace

void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.println("\n[lidar-scanner] démarrage");

    Serial1.begin(LIDAR_BAUD, SERIAL_8N1, LIDAR_RX_PIN, -1);
    Serial1.setRxBufferSize(4096);
    ld19SetSpeed(LIDAR_TARGET_HZ);

    scannerInit();

    wifiCheckResetButton();
    if (!wifiSetup(udp_host)) {
        Serial.println("[wifi] redémarrage dans 3 s");
        delay(3000);
        ESP.restart();
    }
    udp.begin(UDP_PORT);

    point_queue = xQueueCreate(2048, sizeof(QueuedPoint));
    if (!point_queue) {
        Serial.println("[main] création de la file impossible");
        ESP.restart();
    }

    xTaskCreatePinnedToCore(lidarTask, "lidar", 4096, nullptr, 5, nullptr, 1);
    xTaskCreatePinnedToCore(networkTask, "network", 4096, nullptr, 3, nullptr, 0);
    xTaskCreatePinnedToCore(motionTask, "motion", 4096, nullptr, 4, nullptr, 1);

    Serial.println("[lidar-scanner] prêt");
}

void loop() {
    static uint32_t last = 0;
    if (millis() - last > 2000) {
        last = millis();
        Serial.printf("[stat] psi=%.2f deg  file=%u  paquets=%u\n",
                      scannerPsiMdeg() / 1000.0f,
                      static_cast<unsigned>(uxQueueMessagesWaiting(point_queue)),
                      static_cast<unsigned>(packet_sequence));
    }
    vTaskDelay(pdMS_TO_TICKS(100));
}
