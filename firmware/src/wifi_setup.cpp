#include <WiFiManager.h>

#include "config.h"
#include "wifi_setup.h"

namespace {

WiFiManager wifiManager;
WiFiManagerParameter param_udp_host("udphost", "IP station hôte (UDP)", UDP_HOST_DEFAULT,
                                   40);

}  // namespace

void wifiCheckResetButton() {
  pinMode(WIFI_RESET_PIN, INPUT_PULLUP);
  if (digitalRead(WIFI_RESET_PIN) == LOW) {
    Serial.println("[wifi] BOOT pressed — effacement des credentials");
    delay(500);
    if (digitalRead(WIFI_RESET_PIN) == LOW) {
      wifiManager.resetSettings();
      Serial.println("[wifi] settings reset, redémarrage...");
      delay(1000);
      ESP.restart();
    }
  }
}

bool wifiSetup(String& udp_host_out) {
  wifiManager.setConfigPortalTimeout(WIFIMANAGER_PORTAL_TIMEOUT_S);
  wifiManager.setConnectTimeout(WIFIMANAGER_CONNECT_TIMEOUT_S);
  wifiManager.setConnectRetries(3);
  wifiManager.setCaptivePortalEnable(true);
  wifiManager.setTitle("LiDAR Scanner 3D");

  wifiManager.addParameter(&param_udp_host);

  Serial.printf("[wifi] connexion ou portail AP « %s »...\n", WIFIMANAGER_AP_NAME);
  Serial.println("[wifi] maintenir BOOT au démarrage pour réinitialiser le WiFi");

  const char* ap_password =
      (strlen(WIFIMANAGER_AP_PASSWORD) > 0) ? WIFIMANAGER_AP_PASSWORD : nullptr;

  if (!wifiManager.autoConnect(WIFIMANAGER_AP_NAME, ap_password)) {
    Serial.println("[wifi] échec portail / connexion");
    return false;
  }

  udp_host_out = param_udp_host.getValue();
  if (udp_host_out.length() == 0) {
    udp_host_out = UDP_HOST_DEFAULT;
  }

  Serial.printf("[wifi] connecté — IP: %s\n", WiFi.localIP().toString().c_str());
  Serial.printf("[wifi] gateway: %s\n", WiFi.gatewayIP().toString().c_str());
  Serial.printf("[wifi] UDP host: %s:%d\n", udp_host_out.c_str(), UDP_PORT);

  return true;
}
