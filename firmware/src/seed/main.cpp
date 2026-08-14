/**
 * Amorce OTA — premier firmware à flasher en USB.
 *
 * Ne pilote ni le LiDAR ni le moteur. Sert uniquement à :
 *   - configurer le Wi-Fi (même portail / NVS que le firmware scanner)
 *   - accepter une mise à jour OTA du firmware (app0/app1)
 *   - accepter une mise à jour OTA du filesystem (LittleFS)
 *
 * Ensuite : pio run -e ota -t upload  et  pio run -e ota -t uploadfs
 * plus besoin de câble USB.
 */

#include <Arduino.h>
#include <ArduinoOTA.h>
#include <ESPmDNS.h>
#include <LittleFS.h>
#include <Update.h>
#include <WebServer.h>
#include <WiFi.h>
#include <esp_ota_ops.h>

#include "config.h"
#include "wifi_setup.h"

#define SEED_VERSION "0.1.0-seed"

namespace {

WebServer server(OTA_WEB_PORT);
NetworkSettings net_settings;

volatile bool in_progress = false;
bool upload_authorized = false;
bool upload_refused = false;
int upload_command = U_FLASH;

const char kIndexHtml[] PROGMEM = R"HTML(<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Amorce OTA — LiDAR</title>
<style>
:root{color-scheme:dark;--bg:#14161a;--card:#1c1f24;--line:#2a2e35;--muted:#8b929c;
--text:#e6e8eb;--acc:#4a90d9;--ok:#5aa469;--warn:#d9a441;--err:#e06c6c}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
font:14px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
header{padding:18px 20px 8px;max-width:640px;margin:0 auto}
header h1{margin:0;font-size:18px;letter-spacing:-.01em}
header .sub{color:var(--muted);font-size:12.5px;margin-top:2px}
main{max-width:640px;margin:0 auto;padding:8px 16px 40px;display:grid;gap:14px}
section{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px}
section h2{margin:0 0 12px;font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);font-weight:600}
dl.grid{display:grid;grid-template-columns:auto 1fr;gap:6px 16px;margin:0;font-size:13px;font-variant-numeric:tabular-nums}
dt{color:var(--muted)} dd{margin:0}
.hint{font-size:12px;color:var(--muted);margin:0 0 12px}
.msg{min-height:18px;font-size:13px;margin-top:10px}
.ok{color:var(--ok)} .err{color:var(--err)} .warn{color:var(--warn)}
.drop{border:1.5px dashed var(--line);border-radius:10px;padding:20px;text-align:center;cursor:pointer;display:block}
.drop:hover,.drop.over{border-color:var(--acc);background:#1f2530}
.drop input{display:none}
.name{margin-top:8px;font-size:12.5px;color:var(--acc);word-break:break-all}
.bar{height:6px;margin-top:12px;border-radius:4px;background:#2a2e35;overflow:hidden;display:none}
.bar i{display:block;height:100%;width:0;background:var(--ok)}
button{border:0;border-radius:8px;padding:10px 14px;font:inherit;font-weight:600;cursor:pointer;background:var(--acc);color:#fff;width:100%;margin-top:12px}
button:disabled{opacity:.45;cursor:not-allowed}
ul.files{margin:0;padding:0;list-style:none;font-size:13px}
ul.files li{display:flex;justify-content:space-between;gap:12px;padding:4px 0;border-bottom:1px solid var(--line)}
ul.files span{color:var(--muted);font-variant-numeric:tabular-nums}
</style>
</head>
<body>
<header>
  <h1>Amorce OTA</h1>
  <div class="sub">v<span id="ver">…</span> · <span id="ip">…</span> · plus besoin d'USB</div>
</header>
<main>
<section>
  <h2>État</h2>
  <p class="hint">Ce firmware ne scanne pas. Il sert à pousser le firmware scanner et le filesystem par le réseau.</p>
  <dl class="grid">
    <dt>Rôle</dt><dd>amorce</dd>
    <dt>Partition app</dt><dd id="app">…</dd>
    <dt>Cible OTA</dt><dd id="next">…</dd>
    <dt>LittleFS</dt><dd id="fs">…</dd>
    <dt>Wi‑Fi / heap</dt><dd id="net">…</dd>
  </dl>
</section>
<section>
  <h2>Fichiers LittleFS</h2>
  <ul class="files" id="files"><li>…</li></ul>
</section>
<section>
  <h2>Firmware applicatif</h2>
  <p class="hint">Fichier <code>firmware.bin</code> — <code>pio run -e usb</code> ou <code>-e ota</code>.</p>
  <label class="drop" id="dropfw">
    <input type="file" id="filefw" accept=".bin">
    Déposer le firmware ou cliquer
    <div class="name" id="namefw"></div>
  </label>
  <button id="flashfw" disabled>Téléverser le firmware</button>
  <div class="bar" id="barfw"><i id="fillfw"></i></div>
  <div class="msg" id="msgfw"></div>
</section>
<section>
  <h2>Filesystem LittleFS</h2>
  <p class="hint">Fichier <code>littlefs.bin</code> — <code>pio run -e ota -t uploadfs</code>.</p>
  <label class="drop" id="dropfs">
    <input type="file" id="filefs" accept=".bin">
    Déposer l'image filesystem ou cliquer
    <div class="name" id="namefs"></div>
  </label>
  <button id="flashfs" disabled>Téléverser le filesystem</button>
  <div class="bar" id="barfs"><i id="fillfs"></i></div>
  <div class="msg" id="msgfs"></div>
</section>
</main>
<script>
const $=id=>document.getElementById(id);
function setMsg(id,text,cls){const e=$(id);e.textContent=text||'';e.className='msg '+(cls||'')}
function bindDrop(dropId,fileId,nameId,btnId){
  const drop=$(dropId);
  ['dragover','dragleave','drop'].forEach(e=>drop.addEventListener(e,ev=>{
    ev.preventDefault(); drop.classList.toggle('over',e==='dragover');
    if(e==='drop'&&ev.dataTransfer.files.length){$(fileId).files=ev.dataTransfer.files;pick()}
  }));
  $(fileId).onchange=pick;
  function pick(){
    const f=$(fileId).files[0]; if(!f)return;
    $(nameId).textContent=f.name+' ('+(f.size/1024).toFixed(0)+' ko)';
    $(btnId).disabled=false;
  }
}
function bindFlash(fileId,btnId,barId,fillId,msgId,url){
  $(btnId).onclick=()=>{
    const f=$(fileId).files[0]; if(!f)return;
    const fd=new FormData(); fd.append('image',f,f.name);
    const xhr=new XMLHttpRequest();
    $(btnId).disabled=true; $(barId).style.display='block';
    setMsg(msgId,'Écriture en flash…','warn');
    xhr.upload.onprogress=e=>{if(e.lengthComputable)$(fillId).style.width=(e.loaded/e.total*100).toFixed(1)+'%'};
    xhr.onload=()=>{
      const ok=xhr.status===200;
      setMsg(msgId,ok?'Réussi — redémarrage.':('Échec : '+xhr.responseText),ok?'ok':'err');
      if(!ok)$(btnId).disabled=false;
    };
    xhr.onerror=()=>{setMsg(msgId,'Connexion interrompue.','err');$(btnId).disabled=false};
    xhr.open('POST',url); xhr.send(fd);
  };
}
async function refresh(){
  try{
    const r=await fetch('/api/status');
    if(!r.ok) return;
    const d=await r.json();
    $('ver').textContent=d.version;
    $('ip').textContent=d.ip;
    $('app').textContent=d.app_partition+' ('+d.app_size_kb+' ko)';
    $('next').textContent=d.next_partition+' ('+d.next_size_kb+' ko)';
    $('fs').textContent=d.fs_mounted
      ? (d.fs_used/1024).toFixed(0)+' / '+(d.fs_total/1024).toFixed(0)+' ko'
      : 'non monté';
    $('net').textContent=d.rssi+' dBm · '+(d.heap_free/1024).toFixed(0)+' ko';
    const ul=$('files'); ul.innerHTML='';
    if(!d.files||!d.files.length){ul.innerHTML='<li>vide</li>';return}
    d.files.forEach(f=>{
      const li=document.createElement('li');
      li.innerHTML='<code></code><span></span>';
      li.querySelector('code').textContent=f.name;
      li.querySelector('span').textContent=f.size+' o';
      ul.appendChild(li);
    });
  }catch(e){}
}
bindDrop('dropfw','filefw','namefw','flashfw');
bindDrop('dropfs','filefs','namefs','flashfs');
bindFlash('filefw','flashfw','barfw','fillfw','msgfw','/update');
bindFlash('filefs','flashfs','barfs','fillfs','msgfs','/updatefs');
refresh(); setInterval(refresh,2000);
</script>
</body>
</html>)HTML";

bool authenticate() {
    if (net_settings.ota_password.isEmpty()) return true;
    return server.authenticate("admin", net_settings.ota_password.c_str());
}

void appendJsonEscaped(String& out, const char* s) {
    for (const char* p = s; *p; ++p) {
        const char c = *p;
        if (c == '"' || c == '\\') {
            out += '\\';
            out += c;
        } else if (static_cast<unsigned char>(c) < 0x20) {
            out += ' ';
        } else {
            out += c;
        }
    }
}

void handleStatus() {
    if (!authenticate()) return server.requestAuthentication();

    const esp_partition_t* running = esp_ota_get_running_partition();
    const esp_partition_t* next = esp_ota_get_next_update_partition(nullptr);

    String body = "{";
    body += "\"version\":\"" SEED_VERSION "\",";
    body += "\"role\":\"seed\",";
    body += "\"ip\":\"";
    body += WiFi.localIP().toString();
    body += "\",\"rssi\":";
    body += String(WiFi.RSSI());
    body += ",\"heap_free\":";
    body += String(ESP.getFreeHeap());
    body += ",\"app_partition\":\"";
    body += running ? running->label : "?";
    body += "\",\"app_size_kb\":";
    body += String(running ? running->size / 1024 : 0);
    body += ",\"next_partition\":\"";
    body += next ? next->label : "?";
    body += "\",\"next_size_kb\":";
    body += String(next ? next->size / 1024 : 0);
    const bool fs_ok = LittleFS.totalBytes() > 0;
    body += ",\"fs_mounted\":";
    body += fs_ok ? "true" : "false";

    const size_t used = fs_ok ? LittleFS.usedBytes() : 0;
    const size_t total = fs_ok ? LittleFS.totalBytes() : 0;
    body += ",\"fs_used\":";
    body += String(static_cast<unsigned>(used));
    body += ",\"fs_total\":";
    body += String(static_cast<unsigned>(total));
    body += ",\"files\":[";

    bool first = true;
    if (fs_ok) {
        File root = LittleFS.open("/");
        if (root && root.isDirectory()) {
            File f = root.openNextFile();
            int n = 0;
            while (f && n < 24) {
                if (!f.isDirectory()) {
                    if (!first) body += ',';
                    first = false;
                    body += "{\"name\":\"";
                    appendJsonEscaped(body, f.name());
                    body += "\",\"size\":";
                    body += String(static_cast<unsigned>(f.size()));
                    body += '}';
                    n++;
                }
                f = root.openNextFile();
            }
        }
    }
    body += "]}";
    server.send(200, "application/json", body);
}

void handleUpload() {
    HTTPUpload& up = server.upload();

    switch (up.status) {
        case UPLOAD_FILE_START: {
            upload_authorized = authenticate();
            upload_refused = false;
            if (!upload_authorized) return;

            Serial.printf("[seed] téléversement %s « %s »\n",
                          upload_command == U_SPIFFS ? "filesystem" : "firmware",
                          up.filename.c_str());

            if (upload_command == U_SPIFFS) LittleFS.end();

            in_progress = true;
            if (!Update.begin(UPDATE_SIZE_UNKNOWN, upload_command)) {
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
                Serial.printf("[seed] %u octets écrits\n",
                              static_cast<unsigned>(up.totalSize));
            else
                Update.printError(Serial);
            in_progress = false;
            break;
        default:
            if (in_progress) {
                Update.abort();
                in_progress = false;
            }
            break;
    }
}

void handleUpdateResult() {
    if (!upload_authorized) return server.requestAuthentication();
    if (upload_refused) {
        server.send(503, "text/plain", "refuse");
        return;
    }
    server.sendHeader("Connection", "close");
    if (Update.hasError()) {
        server.send(500, "text/plain", "echec de l'ecriture");
        return;
    }
    server.send(200, "text/plain", "ok");
    Serial.println("[seed] redémarrage");
    delay(400);
    ESP.restart();
}

void webTask(void*) {
    for (;;) {
        server.handleClient();
        ArduinoOTA.handle();
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

}  // namespace

void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.printf("\n[lidar-scanner] amorce OTA %s\n", SEED_VERSION);
    Serial.println("[seed] pas de LiDAR, pas de moteur — USB plus nécessaire après le Wi-Fi");

    wifiCheckResetButton();
    if (!wifiSetup(net_settings)) {
        Serial.println("[wifi] redémarrage dans 3 s");
        delay(3000);
        ESP.restart();
    }

    if (!LittleFS.begin(true))
        Serial.println("[seed] LittleFS : montage impossible");
    else
        Serial.printf("[seed] LittleFS %u / %u octets\n",
                      static_cast<unsigned>(LittleFS.usedBytes()),
                      static_cast<unsigned>(LittleFS.totalBytes()));

    const esp_partition_t* running = esp_ota_get_running_partition();
    const esp_partition_t* next = esp_ota_get_next_update_partition(nullptr);
    Serial.printf("[seed] partition active « %s »\n", running ? running->label : "?");
    if (next == nullptr) {
        Serial.println("[seed] ERREUR : aucune seconde partition applicative");
    } else {
        Serial.printf("[seed] cible OTA « %s » (%u ko)\n", next->label,
                      static_cast<unsigned>(next->size / 1024));
    }

    ArduinoOTA.setHostname(OTA_HOSTNAME);
    ArduinoOTA.setPort(OTA_PORT);
    if (!net_settings.ota_password.isEmpty())
        ArduinoOTA.setPassword(net_settings.ota_password.c_str());

    ArduinoOTA.onStart([]() {
        const bool fs = ArduinoOTA.getCommand() == U_SPIFFS;
        Serial.printf("[seed] début espota (%s)\n", fs ? "filesystem" : "firmware");
        if (fs) LittleFS.end();
        in_progress = true;
    });
    ArduinoOTA.onProgress([](unsigned int done, unsigned int total) {
        static int last = -1;
        const int pct = total ? static_cast<int>(done * 100 / total) : 0;
        if (pct / 10 != last / 10) {
            Serial.printf("[seed] %d %%\n", pct);
            last = pct;
        }
    });
    ArduinoOTA.onEnd([]() {
        in_progress = false;
        Serial.println("[seed] terminé, redémarrage");
    });
    ArduinoOTA.onError([](ota_error_t error) {
        in_progress = false;
        Serial.printf("[seed] erreur %u\n", error);
        if (error != OTA_AUTH_ERROR) {
            delay(400);
            ESP.restart();
        }
    });
    ArduinoOTA.begin();

    MDNS.addService("http", "tcp", OTA_WEB_PORT);
    server.on("/", HTTP_GET, []() {
        if (!authenticate()) return server.requestAuthentication();
        server.send_P(200, "text/html", kIndexHtml);
    });
    server.on("/api/status", HTTP_GET, handleStatus);
    server.on("/info", HTTP_GET, handleStatus);
    server.on(
        "/update", HTTP_POST, handleUpdateResult, []() {
            upload_command = U_FLASH;
            handleUpload();
        });
    server.on(
        "/updatefs", HTTP_POST, handleUpdateResult, []() {
            upload_command = U_SPIFFS;
            handleUpload();
        });
    server.onNotFound([]() { server.send(404, "text/plain", "introuvable"); });
    server.begin();

    xTaskCreatePinnedToCore(webTask, "web", 8192, nullptr, 2, nullptr, 0);

    Serial.printf("[seed] http://%s.local/ ou http://%s/\n", OTA_HOSTNAME,
                  WiFi.localIP().toString().c_str());
    Serial.printf("[seed] espota %s:%d  (firmware + filesystem)\n",
                  WiFi.localIP().toString().c_str(), OTA_PORT);
}

void loop() {
    static uint32_t last = 0;
    if (millis() - last > 2000) {
        last = millis();
        Serial.printf("[seed] %s  rssi=%d  heap=%u  fs=%u/%u%s\n",
                      WiFi.localIP().toString().c_str(), WiFi.RSSI(),
                      static_cast<unsigned>(ESP.getFreeHeap()),
                      static_cast<unsigned>(LittleFS.usedBytes()),
                      static_cast<unsigned>(LittleFS.totalBytes()),
                      in_progress ? "  [OTA]" : "");
    }
    vTaskDelay(pdMS_TO_TICKS(100));
}
