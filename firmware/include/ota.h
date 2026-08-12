#pragma once

#include <Arduino.h>

// ============================================================
//  Mise à jour du firmware par le réseau
//
//  Deux voies, exposées simultanément :
//    - ArduinoOTA (port 3232) pour `pio run -t upload` à distance ;
//    - une page web authentifiée pour téléverser un .bin depuis un
//      navigateur, sans chaîne de compilation.
//
//  Voir docs/ota.md.
// ============================================================

struct OtaHooks {
    /// Renvoie true si une mise à jour doit être refusée maintenant
    /// (typiquement : balayage en cours).
    bool (*is_busy)();

    /// Appelé juste avant l'écriture en flash. Doit mettre la mécanique
    /// en sécurité et libérer la bande passante.
    void (*on_begin)();

    /// Appelé si la mise à jour échoue de façon récupérable.
    void (*on_abort)();
};

/**
 * Démarre ArduinoOTA, le serveur web et mDNS, puis crée la tâche de
 * service.
 *
 * @return false si le schéma de partitions ne comporte pas de seconde
 *         partition applicative — l'OTA est alors impossible.
 */
bool otaInit(const String& hostname, const String& password, const OtaHooks& hooks);

/** true entre le début et la fin de l'écriture en flash. */
bool otaInProgress();
