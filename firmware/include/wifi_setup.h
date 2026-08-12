#pragma once

#include <Arduino.h>

/**
 * Démarre WiFiManager : connexion aux credentials sauvegardés,
 * ou ouverture d'un portail captif pour configurer SSID / mot de passe / IP UDP.
 *
 * @param udp_host_out  IP hôte remplie depuis le portail (paramètre persistant)
 * @return false si le portail a échoué (l'appelant doit redémarrer)
 */
bool wifiSetup(String& udp_host_out);

/** Efface les credentials WiFi si le bouton BOOT est maintenu au démarrage. */
void wifiCheckResetButton();
