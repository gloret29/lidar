#include "ota.h"

#include <ArduinoOTA.h>
#include <ESPmDNS.h>
#include <Update.h>
#include <WebServer.h>
#include <WiFi.h>
#include <esp_ota_ops.h>

#include "config.h"

namespace {

WebServer server(OTA_WEB_PORT);
OtaHooks hooks{};
String ota_password;

volatile bool in_progress = false;
bool upload_authorized = false;
bool upload_refused = false;

const char kIndexHtml[] PROGMEM = R"HTML(<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Scanner 3D LiDAR — mise à jour</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin:0; min-height:100vh; display:flex; align-items:center;
         justify-content:center; background:#14161a; color:#e6e8eb;
         font:15px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif; }
  .card { width:min(560px,92vw); background:#1c1f24; border:1px solid #2a2e35;
          border-radius:14px; padding:28px 30px; }
  h1 { margin:0 0 4px; font-size:19px; letter-spacing:-.01em; }
  .sub { color:#8b929c; font-size:13px; margin-bottom:22px; }
  dl { display:grid; grid-template-columns:auto 1fr; gap:7px 18px;
       margin:0 0 22px; font-size:13px; }
  dt { color:#8b929c; } dd { margin:0; font-variant-numeric:tabular-nums; }
  .drop { border:1.5px dashed #363b44; border-radius:10px; padding:26px;
          text-align:center; cursor:pointer; transition:.15s; }
  .drop:hover, .drop.over { border-color:#4a90d9; background:#1f2530; }
  .drop input { display:none; }
  .name { margin-top:12px; font-size:13px; color:#4a90d9; word-break:break-all; }
  button { width:100%; margin-top:18px; padding:12px; border:0; border-radius:9px;
           background:#4a90d9; color:#fff; font-size:15px; font-weight:600;
           cursor:pointer; }
  button:disabled { background:#2a2e35; color:#6b7280; cursor:not-allowed; }
  .bar { height:7px; margin-top:18px; border-radius:4px; background:#2a2e35;
         overflow:hidden; display:none; }
  .bar i { display:block; height:100%; width:0; background:#5aa469; transition:.2s; }
  .msg { margin-top:14px; font-size:13px; min-height:19px; }
  .warn { margin-top:20px; padding:11px 13px; border-radius:8px;
          background:#2a2119; border:1px solid #4a3a24; color:#d9a441;
          font-size:12.5px; }
  .err { color:#e06c6c; } .ok { color:#5aa469; }
</style>
</head>
<body>
<div class="card">
  <h1>Scanner 3D LiDAR</h1>
  <div class="sub">Mise à jour du firmware par le réseau</div>

  <dl>
    <dt>Version</dt><dd id="ver">…</dd>
    <dt>Partition</dt><dd id="part">…</dd>
    <dt>Mémoire libre</dt><dd id="heap">…</dd>
    <dt>Fonctionnement</dt><dd id="up">…</dd>
    <dt>État</dt><dd id="state">…</dd>
  </dl>

  <label class="drop" id="drop">
    <input type="file" id="file" accept=".bin">
    Déposer <code>firmware.bin</code> ou cliquer pour choisir
    <div class="name" id="name"></div>
  </label>

  <button id="go" disabled>Téléverser</button>
  <div class="bar" id="bar"><i id="fill"></i></div>
  <div class="msg" id="msg"></div>

  <div class="warn">Ne pas couper l'alimentation pendant l'écriture.
    Le scanner redémarre automatiquement à la fin.</div>
</div>
<script>
const $ = id => document.getElementById(id);
fetch('info').then(r => r.json()).then(d => {
  $('ver').textContent   = d.version;
  $('part').textContent  = d.partition + ' → ' + d.next;
  $('heap').textContent  = (d.heap / 1024).toFixed(0) + ' ko';
  $('up').textContent    = Math.floor(d.uptime / 60) + ' min ' + (d.uptime % 60) + ' s';
  $('state').textContent = d.busy ? 'balayage en cours' : 'au repos';
  if (d.busy) { $('msg').textContent =
    'Mise à jour indisponible pendant un balayage.'; $('msg').className = 'msg err'; }
}).catch(() => {});

const drop = $('drop');
['dragover','dragleave','drop'].forEach(e => drop.addEventListener(e, ev => {
  ev.preventDefault();
  drop.classList.toggle('over', e === 'dragover');
  if (e === 'drop' && ev.dataTransfer.files.length) {
    $('file').files = ev.dataTransfer.files; pick();
  }
}));
$('file').onchange = pick;
function pick() {
  const f = $('file').files[0];
  if (!f) return;
  $('name').textContent = f.name + '  (' + (f.size / 1024).toFixed(0) + ' ko)';
  $('go').disabled = false;
}

$('go').onclick = () => {
  const f = $('file').files[0];
  if (!f) return;
  const fd = new FormData(); fd.append('firmware', f, f.name);
  const xhr = new XMLHttpRequest();
  $('go').disabled = true; $('bar').style.display = 'block';
  $('msg').className = 'msg'; $('msg').textContent = 'Écriture en flash…';

  xhr.upload.onprogress = e => {
    if (e.lengthComputable)
      $('fill').style.width = (e.loaded / e.total * 100).toFixed(1) + '%';
  };
  xhr.onload = () => {
    const ok = xhr.status === 200;
    $('msg').className = 'msg ' + (ok ? 'ok' : 'err');
    $('msg').textContent = ok
      ? 'Mise à jour réussie — redémarrage en cours.'
      : 'Échec (' + xhr.status + ') : ' + xhr.responseText;
    if (!ok) $('go').disabled = false;
  };
  xhr.onerror = () => {
    $('msg').className = 'msg err';
    $('msg').textContent = 'Connexion interrompue.';
    $('go').disabled = false;
  };
  xhr.open('POST', 'update');
  xhr.send(fd);
};
</script>
</body>
</html>)HTML";

bool busy() { return hooks.is_busy && hooks.is_busy(); }

bool authenticate() {
    if (ota_password.isEmpty()) return true;
    return server.authenticate("admin", ota_password.c_str());
}

void handleInfo() {
    if (!authenticate()) return server.requestAuthentication();

    const esp_partition_t* running = esp_ota_get_running_partition();
    const esp_partition_t* next = esp_ota_get_next_update_partition(nullptr);

    char body[256];
    snprintf(body, sizeof(body),
             "{\"version\":\"%s\",\"partition\":\"%s\",\"next\":\"%s\","
             "\"heap\":%u,\"uptime\":%lu,\"busy\":%s}",
             FIRMWARE_VERSION, running ? running->label : "?",
             next ? next->label : "aucune",
             static_cast<unsigned>(ESP.getFreeHeap()),
             static_cast<unsigned long>(millis() / 1000),
             busy() ? "true" : "false");
    server.send(200, "application/json", body);
}

void handleUpload() {
    HTTPUpload& up = server.upload();

    switch (up.status) {
        case UPLOAD_FILE_START: {
            upload_authorized = authenticate();
            upload_refused = false;
            if (!upload_authorized) return;

            if (busy() && !OTA_ALLOW_DURING_SCAN) {
                upload_refused = true;
                Serial.println("[ota] refusé : balayage en cours");
                return;
            }

            Serial.printf("[ota] téléversement web de « %s »\n", up.filename.c_str());
            if (hooks.on_begin) hooks.on_begin();
            in_progress = true;

            if (!Update.begin(UPDATE_SIZE_UNKNOWN)) {
                Update.printError(Serial);
                in_progress = false;
            }
            break;
        }

        case UPLOAD_FILE_WRITE:
            if (!in_progress) break;
            if (Update.write(up.buf, up.currentSize) != up.currentSize)
                Update.printError(Serial);
            break;

        case UPLOAD_FILE_END:
            if (!in_progress) break;
            if (Update.end(true))
                Serial.printf("[ota] %u octets écrits\n",
                              static_cast<unsigned>(up.totalSize));
            else
                Update.printError(Serial);
            in_progress = false;
            break;

        default:
            if (in_progress) {
                Update.abort();
                in_progress = false;
                if (hooks.on_abort) hooks.on_abort();
            }
            break;
    }
}

void handleUpdateResult() {
    if (!upload_authorized) return server.requestAuthentication();

    if (upload_refused) {
        server.send(503, "text/plain", "balayage en cours");
        return;
    }

    server.sendHeader("Connection", "close");
    if (Update.hasError()) {
        server.send(500, "text/plain", "echec de l'ecriture");
        if (hooks.on_abort) hooks.on_abort();
        return;
    }

    server.send(200, "text/plain", "ok");
    Serial.println("[ota] redémarrage");
    delay(400);
    ESP.restart();
}

void otaTask(void*) {
    for (;;) {
        server.handleClient();
        // ArduinoOTA n'est pas servi pendant un balayage : le port devient
        // simplement injoignable, plutôt que d'interrompre l'acquisition.
        if (OTA_ALLOW_DURING_SCAN || !busy()) ArduinoOTA.handle();
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

}  // namespace

bool otaInit(const String& hostname, const String& password, const OtaHooks& h) {
    hooks = h;
    ota_password = password;

    const esp_partition_t* running = esp_ota_get_running_partition();
    const esp_partition_t* next = esp_ota_get_next_update_partition(nullptr);
    Serial.printf("[ota] partition active « %s »\n", running ? running->label : "?");

    if (next == nullptr) {
        Serial.println("[ota] ERREUR : aucune seconde partition applicative.");
        Serial.println("[ota] utiliser un schéma de partitions OTA "
                       "(board_build.partitions = default_16MB.csv)");
        return false;
    }
    Serial.printf("[ota] cible de mise à jour « %s » (%u ko)\n", next->label,
                  static_cast<unsigned>(next->size / 1024));

    ArduinoOTA.setHostname(hostname.c_str());
    ArduinoOTA.setPort(OTA_PORT);
    if (!ota_password.isEmpty()) ArduinoOTA.setPassword(ota_password.c_str());

    ArduinoOTA.onStart([]() {
        Serial.println("[ota] début (espota)");
        if (hooks.on_begin) hooks.on_begin();
        in_progress = true;
    });
    ArduinoOTA.onProgress([](unsigned int done, unsigned int total) {
        static int last = -1;
        const int pct = total ? static_cast<int>(done * 100 / total) : 0;
        if (pct / 10 != last / 10) {
            Serial.printf("[ota] %d %%\n", pct);
            last = pct;
        }
    });
    ArduinoOTA.onEnd([]() {
        in_progress = false;
        Serial.println("[ota] terminé, redémarrage");
    });
    ArduinoOTA.onError([](ota_error_t error) {
        in_progress = false;
        Serial.printf("[ota] erreur %u\n", error);

        // Un mot de passe erroné n'a rien écrit : on reprend simplement.
        // Toute autre erreur peut laisser la flash à moitié écrite, auquel
        // cas un redémarrage propre vaut mieux qu'un état indéterminé.
        if (error == OTA_AUTH_ERROR) {
            Serial.println("[ota] authentification refusée");
            if (hooks.on_abort) hooks.on_abort();
            return;
        }
        Serial.println("[ota] écriture interrompue, redémarrage");
        delay(400);
        ESP.restart();
    });

    ArduinoOTA.begin();

    MDNS.addService("http", "tcp", OTA_WEB_PORT);
    server.on("/", HTTP_GET, []() {
        if (!authenticate()) return server.requestAuthentication();
        server.send_P(200, "text/html", kIndexHtml);
    });
    server.on("/info", HTTP_GET, handleInfo);
    server.on("/update", HTTP_POST, handleUpdateResult, handleUpload);
    server.onNotFound([]() { server.send(404, "text/plain", "introuvable"); });
    server.begin();

    xTaskCreatePinnedToCore(otaTask, "ota", 6144, nullptr, 2, nullptr, 0);

    Serial.printf("[ota] prêt — http://%s.local/ ou http://%s/\n", hostname.c_str(),
                  WiFi.localIP().toString().c_str());
    Serial.printf("[ota] espota sur %s:%d\n", WiFi.localIP().toString().c_str(),
                  OTA_PORT);
    return true;
}

bool otaInProgress() { return in_progress; }
