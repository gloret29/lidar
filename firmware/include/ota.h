#pragma once

#include <Arduino.h>

// ============================================================
//  Interface web + mise à jour OTA
//
//  Une seule page authentifiée :
//    - commande de balayage (start / stop / rehome / arrêt)
//    - télémétrie live
//    - paramètres de réglage (NVS)
//    - téléversement du firmware
//
//  ArduinoOTA (port 3232) reste disponible en parallèle.
//  Voir docs/web.md et docs/ota.md.
// ============================================================

struct OtaHooks {
    bool (*is_busy)();
    void (*on_begin)();
    void (*on_abort)();
};

bool otaInit(const String& hostname, const String& password, const OtaHooks& hooks);
bool otaInProgress();
