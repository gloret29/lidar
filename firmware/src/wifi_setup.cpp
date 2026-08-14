#include <Preferences.h>
#include <WiFiManager.h>

#include "config.h"
#include "wifi_setup.h"

namespace {

constexpr char kNvsNamespace[] = "lidarnet";
constexpr char kKeyUdpHost[] = "udp_host";
constexpr char kKeyOtaPass[] = "ota_pass";

WiFiManager wifiManager;
Preferences prefs;

// Les valeurs par défaut sont injectées après lecture de la NVS : les
// objets sont donc créés vides.
WiFiManagerParameter param_udp_host("udphost", "IP station hôte (UDP)", "", 40);
WiFiManagerParameter param_ota_pass("otapass", "Mot de passe OTA", "", 32);

bool params_submitted = false;

void onParamsSaved() { params_submitted = true; }

String loadOr(const char* key, const char* fallback) {
    if (!prefs.isKey(key)) return String(fallback);
    const String value = prefs.getString(key, "");
    return value.length() ? value : String(fallback);
}

}  // namespace

void wifiCheckResetButton() {
    pinMode(WIFI_RESET_PIN, INPUT_PULLUP);
    if (digitalRead(WIFI_RESET_PIN) != LOW) return;

    Serial.println("[wifi] BOOT maintenu — effacement des identifiants");
    delay(500);
    if (digitalRead(WIFI_RESET_PIN) != LOW) return;

    wifiManager.resetSettings();
    prefs.begin(kNvsNamespace, false);
    prefs.clear();
    prefs.end();
    Serial.println("[wifi] réglages effacés, redémarrage");
    delay(1000);
    ESP.restart();
}

bool wifiSetup(NetworkSettings& out) {
    prefs.begin(kNvsNamespace, false);
    out.udp_host = loadOr(kKeyUdpHost, UDP_HOST_DEFAULT);
    out.ota_password = loadOr(kKeyOtaPass, OTA_PASSWORD_DEFAULT);

    param_udp_host.setValue(out.udp_host.c_str(), 40);
    param_ota_pass.setValue(out.ota_password.c_str(), 32);

    wifiManager.setConfigPortalTimeout(WIFIMANAGER_PORTAL_TIMEOUT_S);
    wifiManager.setConnectTimeout(WIFIMANAGER_CONNECT_TIMEOUT_S);
    wifiManager.setConnectRetries(3);
    wifiManager.setCaptivePortalEnable(true);
    wifiManager.setTitle("LiDAR Scanner 3D");
    wifiManager.setSaveParamsCallback(onParamsSaved);
    wifiManager.addParameter(&param_udp_host);
    wifiManager.addParameter(&param_ota_pass);

    Serial.printf("[wifi] connexion, sinon portail AP « %s »\n", WIFIMANAGER_AP_NAME);
    Serial.println("[wifi] maintenir BOOT au démarrage pour réinitialiser");

    const char* ap_password =
        (strlen(WIFIMANAGER_AP_PASSWORD) > 0) ? WIFIMANAGER_AP_PASSWORD : nullptr;

    if (!wifiManager.autoConnect(WIFIMANAGER_AP_NAME, ap_password)) {
        Serial.println("[wifi] échec du portail / de la connexion");
        prefs.end();
        return false;
    }

    if (params_submitted) {
        out.udp_host = param_udp_host.getValue();
        out.ota_password = param_ota_pass.getValue();
        if (out.udp_host.length() == 0) out.udp_host = UDP_HOST_DEFAULT;
        if (out.ota_password.length() == 0) out.ota_password = OTA_PASSWORD_DEFAULT;

        prefs.putString(kKeyUdpHost, out.udp_host);
        prefs.putString(kKeyOtaPass, out.ota_password);
        Serial.println("[wifi] paramètres du portail enregistrés en NVS");
    }
    prefs.end();

    Serial.printf("[wifi] connecté — IP %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("[wifi] passerelle %s\n", WiFi.gatewayIP().toString().c_str());
    Serial.printf("[wifi] station hôte %s:%d\n", out.udp_host.c_str(), UDP_PORT);

    if (out.ota_password == OTA_PASSWORD_DEFAULT)
        Serial.println("[wifi] ATTENTION : mot de passe OTA laissé par défaut");

    return true;
}
