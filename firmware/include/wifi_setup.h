#pragma once

#include <Arduino.h>

/** Réglages réseau saisis au portail et persistés en NVS. */
struct NetworkSettings {
    String udp_host;
    String ota_password;
};

/**
 * Démarre WiFiManager : connexion aux identifiants sauvegardés, ou
 * ouverture d'un portail captif pour configurer le réseau, l'adresse de
 * la station hôte et le mot de passe OTA.
 *
 * Les paramètres du portail sont relus depuis NVS au démarrage et
 * réécrits dès qu'ils sont soumis : ils survivent donc aux redémarrages,
 * ce que WiFiManager ne fait pas de lui-même.
 *
 * @return false si le portail a échoué (l'appelant doit redémarrer)
 */
bool wifiSetup(NetworkSettings& out);

/** Efface les identifiants Wi-Fi si BOOT est maintenu au démarrage. */
void wifiCheckResetButton();
