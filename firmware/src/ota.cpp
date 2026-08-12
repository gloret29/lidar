#include "ota.h"

#include <ArduinoOTA.h>
#include <ESPmDNS.h>
#include <Update.h>
#include <WebServer.h>
#include <WiFi.h>
#include <esp_ota_ops.h>

#include "config.h"
#include "control.h"
#include "settings.h"
#include "status.h"

namespace {

WebServer server(OTA_WEB_PORT);
OtaHooks hooks{};
String web_password;

volatile bool in_progress = false;
bool upload_authorized = false;
bool upload_refused = false;

// ------------------------------------------------------------
//  Page unique
// ------------------------------------------------------------
const char kIndexHtml[] PROGMEM = R"HTML(<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Scanner 3D LiDAR</title>
<style>
:root{color-scheme:dark;--bg:#14161a;--card:#1c1f24;--line:#2a2e35;--muted:#8b929c;
--text:#e6e8eb;--acc:#4a90d9;--ok:#5aa469;--warn:#d9a441;--err:#e06c6c}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
font:14px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
header{padding:18px 20px 8px;max-width:720px;margin:0 auto}
header h1{margin:0;font-size:18px;letter-spacing:-.01em}
header .sub{color:var(--muted);font-size:12.5px;margin-top:2px}
main{max-width:720px;margin:0 auto;padding:8px 16px 40px;display:grid;gap:14px}
section{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px}
section h2{margin:0 0 12px;font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);font-weight:600}
.row{display:flex;flex-wrap:wrap;gap:8px}
button,.btn{border:0;border-radius:8px;padding:10px 14px;font:inherit;font-weight:600;cursor:pointer;background:var(--acc);color:#fff}
button.secondary{background:#2a2e35;color:var(--text)}
button.danger{background:#8b3a3a}
button:disabled{opacity:.45;cursor:not-allowed}
dl.grid{display:grid;grid-template-columns:auto 1fr;gap:6px 16px;margin:0;font-size:13px;font-variant-numeric:tabular-nums}
dt{color:var(--muted)} dd{margin:0}
label.field{display:grid;grid-template-columns:1fr auto;gap:4px 12px;align-items:center;margin:0 0 10px;font-size:13px}
label.field span{color:var(--muted)}
label.field input{width:110px;padding:7px 8px;border-radius:7px;border:1px solid var(--line);background:#14161a;color:var(--text);font:inherit}
.hint{font-size:12px;color:var(--muted);margin:0 0 12px}
.msg{min-height:18px;font-size:13px;margin-top:10px}
.ok{color:var(--ok)} .err{color:var(--err)} .warn{color:var(--warn)}
.drop{border:1.5px dashed var(--line);border-radius:10px;padding:20px;text-align:center;cursor:pointer}
.drop:hover,.drop.over{border-color:var(--acc);background:#1f2530}
.drop input{display:none}
.name{margin-top:8px;font-size:12.5px;color:var(--acc);word-break:break-all}
.bar{height:6px;margin-top:12px;border-radius:4px;background:#2a2e35;overflow:hidden;display:none}
.bar i{display:block;height:100%;width:0;background:var(--ok)}
.pill{display:inline-block;padding:2px 8px;border-radius:999px;font-size:12px;background:#2a2e35}
.pill.busy{background:#3a2f1a;color:var(--warn)}
.pill.fault{background:#3a1f1f;color:var(--err)}
.pill.ok{background:#1f2a22;color:var(--ok)}
</style>
</head>
<body>
<header>
  <h1>Scanner 3D LiDAR</h1>
  <div class="sub">v<span id="ver">…</span> · <span id="ip">…</span></div>
</header>
<main>
<section>
  <h2>Commande</h2>
  <div class="row">
    <button id="start">Lancer le scan</button>
    <button class="secondary" id="stop">Arrêter</button>
    <button class="secondary" id="rehome">Rehomer</button>
    <button class="danger" id="estop">Arrêt d'urgence</button>
  </div>
  <div class="msg" id="cmdmsg"></div>
</section>
<section>
  <h2>Diagnostics</h2>
  <dl class="grid">
    <dt>État</dt><dd><span class="pill" id="state">…</span></dd>
    <dt>Azimut ψ</dt><dd id="psi">…</dd>
    <dt>LiDAR</dt><dd id="lidar">…</dd>
    <dt>CRC</dt><dd id="crc">…</dd>
    <dt>File / paquets</dt><dd id="queue">…</dd>
    <dt>StallGuard</dt><dd id="sg">…</dd>
    <dt>Wi‑Fi / heap</dt><dd id="net">…</dd>
  </dl>
</section>
<section>
  <h2>Réglages</h2>
  <p class="hint">Persistés en NVS. Bornés côté firmware. La calibration géométrique reste sur l'hôte.</p>
  <form id="setform">
    <label class="field"><span>Fréquence LiDAR (Hz)</span><input name="lidar_hz" type="number" step="0.1" min="5" max="13"></label>
    <label class="field"><span>Vitesse balayage (°/s)</span><input name="speed" type="number" step="0.1" min="0.5" max="10"></label>
    <label class="field"><span>Fin de balayage (°)</span><input name="end_deg" type="number" step="1" min="10" max="360"></label>
    <label class="field"><span>Seuil StallGuard</span><input name="sg" type="number" step="1" min="1" max="255"></label>
    <label class="field"><span>Courant scan (mA)</span><input name="i_scan" type="number" step="10" min="200" max="1200"></label>
    <label class="field"><span>Courant homing (mA)</span><input name="i_home" type="number" step="10" min="100" max="800"></label>
    <div class="row">
      <button type="submit">Enregistrer</button>
      <button type="button" class="secondary" id="defaults">Valeurs d'usine</button>
    </div>
  </form>
  <div class="msg" id="setmsg"></div>
</section>
<section>
  <h2>Mise à jour OTA</h2>
  <p class="hint">Fichier <code>firmware.bin</code> — indisponible pendant un balayage.</p>
  <label class="drop" id="drop">
    <input type="file" id="file" accept=".bin">
    Déposer le binaire ou cliquer
    <div class="name" id="fname"></div>
  </label>
  <button id="flash" disabled style="width:100%;margin-top:12px">Téléverser</button>
  <div class="bar" id="bar"><i id="fill"></i></div>
  <div class="msg" id="otamsg"></div>
</section>
</main>
<script>
const $=id=>document.getElementById(id);
const form=$('setform');
function setMsg(id,text,cls){const e=$(id);e.textContent=text||'';e.className='msg '+(cls||'')}
async function api(path,opts){
  const r=await fetch(path,opts);
  const t=await r.text();
  let j=null; try{j=JSON.parse(t)}catch(e){}
  if(!r.ok) throw new Error((j&&j.error)||t||r.status);
  return j||{ok:true,raw:t};
}
function pill(el,state){
  el.textContent=state;
  el.className='pill'+(state==='scanning'||state==='homing'||state==='spinup'?' busy'
    :state==='fault'?' fault':state==='idle'||state==='done'?' ok':'');
}
async function refresh(){
  try{
    const d=await api('/api/status');
    $('ver').textContent=d.version;
    $('ip').textContent=d.ip;
    pill($('state'),d.state);
    $('psi').textContent=d.psi_deg.toFixed(2)+' °';
    $('lidar').textContent=d.lidar_hz_meas.toFixed(2)+' Hz (consigne '+d.lidar_hz.toFixed(1)+')';
    const tot=d.frames_ok+d.frames_bad;
    const pct=tot? (100*d.frames_ok/tot).toFixed(1):'—';
    $('crc').textContent=d.frames_ok+' ok / '+d.frames_bad+' mauvais ('+pct+' %)';
    $('queue').textContent=d.queue_depth+' · '+d.packets_sent+' paquets';
    $('sg').textContent=d.sg_result<0?'n/d':d.sg_result+' (seuil '+d.stallguard+')';
    $('net').textContent=d.rssi+' dBm · '+(d.heap_free/1024).toFixed(0)+' ko';
    const busy=d.scan_busy||d.ota_busy;
    $('start').disabled=busy;
    $('rehome').disabled=busy;
    $('flash').disabled=busy||!$('file').files[0];
    if(d.ota_busy) setMsg('otamsg','Écriture en flash…','warn');
  }catch(e){}
}
async function cmd(c){
  setMsg('cmdmsg','…');
  try{
    await api('/api/command?cmd='+c,{method:'POST'});
    setMsg('cmdmsg','Commande « '+c+' » acceptée.','ok');
    refresh();
  }catch(e){setMsg('cmdmsg',e.message,'err')}
}
$('start').onclick=()=>cmd('start');
$('stop').onclick=()=>cmd('stop');
$('rehome').onclick=()=>cmd('rehome');
$('estop').onclick=()=>cmd('estop');

async function loadSettings(){
  const s=await api('/api/settings');
  form.lidar_hz.value=s.lidar_hz;
  form.speed.value=s.scan_speed_deg_s;
  form.end_deg.value=s.scan_end_deg;
  form.sg.value=s.stallguard;
  form.i_scan.value=s.current_scan_ma;
  form.i_home.value=s.current_homing_ma;
}
form.onsubmit=async ev=>{
  ev.preventDefault();
  const body=new URLSearchParams(new FormData(form));
  try{
    await api('/api/settings',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body});
    setMsg('setmsg','Réglages enregistrés.','ok');
    refresh();
  }catch(e){setMsg('setmsg',e.message,'err')}
};
$('defaults').onclick=async()=>{
  try{
    await api('/api/settings?defaults=1',{method:'POST'});
    await loadSettings();
    setMsg('setmsg','Valeurs d\'usine restaurées.','ok');
  }catch(e){setMsg('setmsg',e.message,'err')}
};

const drop=$('drop');
['dragover','dragleave','drop'].forEach(e=>drop.addEventListener(e,ev=>{
  ev.preventDefault(); drop.classList.toggle('over',e==='dragover');
  if(e==='drop'&&ev.dataTransfer.files.length){$('file').files=ev.dataTransfer.files;pick()}
}));
$('file').onchange=pick;
function pick(){
  const f=$('file').files[0]; if(!f)return;
  $('fname').textContent=f.name+' ('+(f.size/1024).toFixed(0)+' ko)';
  $('flash').disabled=false;
}
$('flash').onclick=()=>{
  const f=$('file').files[0]; if(!f)return;
  const fd=new FormData(); fd.append('firmware',f,f.name);
  const xhr=new XMLHttpRequest();
  $('flash').disabled=true; $('bar').style.display='block';
  setMsg('otamsg','Écriture en flash…','warn');
  xhr.upload.onprogress=e=>{if(e.lengthComputable)$('fill').style.width=(e.loaded/e.total*100).toFixed(1)+'%'};
  xhr.onload=()=>{
    const ok=xhr.status===200;
    setMsg('otamsg',ok?'Réussi — redémarrage.':('Échec : '+xhr.responseText),ok?'ok':'err');
    if(!ok)$('flash').disabled=false;
  };
  xhr.onerror=()=>{setMsg('otamsg','Connexion interrompue.','err');$('flash').disabled=false};
  xhr.open('POST','/update'); xhr.send(fd);
};

loadSettings().catch(()=>{});
refresh(); setInterval(refresh,1000);
</script>
</body>
</html>)HTML";

bool busy() { return hooks.is_busy && hooks.is_busy(); }

bool authenticate() {
    if (web_password.isEmpty()) return true;
    return server.authenticate("admin", web_password.c_str());
}

void sendJson(int code, const String& body) {
    server.send(code, "application/json", body);
}

void handleStatus() {
    if (!authenticate()) return server.requestAuthentication();

    const DeviceStatus d = statusSnapshot();
    const ScanSettings& s = settings();

    char body[768];
    snprintf(body, sizeof(body),
             "{\"version\":\"%s\",\"ip\":\"%s\",\"state\":\"%s\","
             "\"psi_deg\":%.3f,\"lidar_hz_meas\":%.2f,\"lidar_hz\":%.2f,"
             "\"frames_ok\":%u,\"frames_bad\":%u,\"queue_depth\":%u,"
             "\"packets_sent\":%u,\"sg_result\":%d,\"stallguard\":%u,"
             "\"rssi\":%d,\"heap_free\":%u,\"uptime_s\":%u,"
             "\"ota_busy\":%s,\"scan_busy\":%s}",
             FIRMWARE_VERSION, WiFi.localIP().toString().c_str(),
             scanStateName(d.state), d.psi_deg, d.lidar_hz_meas, s.lidar_hz,
             static_cast<unsigned>(d.frames_ok),
             static_cast<unsigned>(d.frames_bad),
             static_cast<unsigned>(d.queue_depth),
             static_cast<unsigned>(d.packets_sent), d.sg_result, s.stallguard,
             static_cast<int>(d.rssi), static_cast<unsigned>(d.heap_free),
             static_cast<unsigned>(d.uptime_s), d.ota_busy ? "true" : "false",
             d.scan_busy ? "true" : "false");
    sendJson(200, body);
}

void handleInfo() {
    // Compatibilité avec l'ancienne route OTA.
    handleStatus();
}

void handleCommand() {
    if (!authenticate()) return server.requestAuthentication();
    if (in_progress) return sendJson(503, "{\"error\":\"ota en cours\"}");

    String cmd = server.arg("cmd");
    cmd.toLowerCase();

    ScanCommand c;
    if (cmd == "start")
        c = ScanCommand::Start;
    else if (cmd == "stop")
        c = ScanCommand::Stop;
    else if (cmd == "rehome")
        c = ScanCommand::Rehome;
    else if (cmd == "estop")
        c = ScanCommand::EStop;
    else
        return sendJson(400, "{\"error\":\"commande inconnue\"}");

    if ((c == ScanCommand::Start || c == ScanCommand::Rehome) && busy())
        return sendJson(409, "{\"error\":\"balayage deja en cours\"}");

    if (!controlSend(c))
        return sendJson(503, "{\"error\":\"file de commandes pleine\"}");

    sendJson(200, "{\"ok\":true}");
}

String settingsJson() {
    const ScanSettings& s = settings();
    char body[320];
    snprintf(body, sizeof(body),
             "{\"lidar_hz\":%.2f,\"scan_speed_deg_s\":%.2f,\"scan_end_deg\":%.1f,"
             "\"stallguard\":%u,\"current_scan_ma\":%u,\"current_homing_ma\":%u}",
             s.lidar_hz, s.scan_speed_deg_s, s.scan_end_deg, s.stallguard,
             s.current_scan_ma, s.current_homing_ma);
    return String(body);
}

void handleSettingsGet() {
    if (!authenticate()) return server.requestAuthentication();
    sendJson(200, settingsJson());
}

void handleSettingsPost() {
    if (!authenticate()) return server.requestAuthentication();
    if (busy())
        return sendJson(409, "{\"error\":\"modifier les reglage pendant un "
                             "balayage est refuse\"}");

    if (server.hasArg("defaults") && server.arg("defaults") == "1") {
        settings() = settingsDefaults();
    } else {
        ScanSettings& s = settings();
        if (server.hasArg("lidar_hz")) s.lidar_hz = server.arg("lidar_hz").toFloat();
        if (server.hasArg("speed")) s.scan_speed_deg_s = server.arg("speed").toFloat();
        if (server.hasArg("end_deg")) s.scan_end_deg = server.arg("end_deg").toFloat();
        if (server.hasArg("sg")) s.stallguard = server.arg("sg").toInt();
        if (server.hasArg("i_scan")) s.current_scan_ma = server.arg("i_scan").toInt();
        if (server.hasArg("i_home")) s.current_homing_ma = server.arg("i_home").toInt();
    }

    settingsClamp(settings());
    settingsSave();
    settingsApplyHardware();
    sendJson(200, settingsJson());
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

void webTask(void*) {
    for (;;) {
        server.handleClient();
        if (OTA_ALLOW_DURING_SCAN || !busy()) ArduinoOTA.handle();
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

}  // namespace

bool otaInit(const String& hostname, const String& password, const OtaHooks& h) {
    hooks = h;
    web_password = password;

    const esp_partition_t* running = esp_ota_get_running_partition();
    const esp_partition_t* next = esp_ota_get_next_update_partition(nullptr);
    Serial.printf("[web] partition active « %s »\n", running ? running->label : "?");

    if (next == nullptr) {
        Serial.println("[web] ERREUR : aucune seconde partition applicative");
        return false;
    }
    Serial.printf("[web] cible OTA « %s » (%u ko)\n", next->label,
                  static_cast<unsigned>(next->size / 1024));

    ArduinoOTA.setHostname(hostname.c_str());
    ArduinoOTA.setPort(OTA_PORT);
    if (!web_password.isEmpty()) ArduinoOTA.setPassword(web_password.c_str());

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
        if (error == OTA_AUTH_ERROR) {
            if (hooks.on_abort) hooks.on_abort();
            return;
        }
        delay(400);
        ESP.restart();
    });
    ArduinoOTA.begin();

    MDNS.addService("http", "tcp", OTA_WEB_PORT);
    server.on("/", HTTP_GET, []() {
        if (!authenticate()) return server.requestAuthentication();
        server.send_P(200, "text/html", kIndexHtml);
    });
    server.on("/api/status", HTTP_GET, handleStatus);
    server.on("/api/command", HTTP_POST, handleCommand);
    server.on("/api/settings", HTTP_GET, handleSettingsGet);
    server.on("/api/settings", HTTP_POST, handleSettingsPost);
    server.on("/info", HTTP_GET, handleInfo);
    server.on("/update", HTTP_POST, handleUpdateResult, handleUpload);
    server.onNotFound([]() { server.send(404, "text/plain", "introuvable"); });
    server.begin();

    xTaskCreatePinnedToCore(webTask, "web", 8192, nullptr, 2, nullptr, 0);

    Serial.printf("[web] http://%s.local/ ou http://%s/\n", hostname.c_str(),
                  WiFi.localIP().toString().c_str());
    Serial.printf("[web] espota %s:%d\n", WiFi.localIP().toString().c_str(), OTA_PORT);
    return true;
}

bool otaInProgress() { return in_progress; }
