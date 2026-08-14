# Configuration WiFi (WiFiManager)

Le firmware utilise [WiFiManager](https://github.com/tzapu/WiFiManager) : pas de SSID/mot de passe codés en dur. Les credentials sont stockés en flash NVS.

## Premier démarrage

1. Flasher l'**amorce** en USB (`pio run -e seed -t upload`) et alimenter
   l'ESP32-S3.
2. L'ESP32 tente de se connecter au WiFi sauvegardé ; s'il n'y en a pas (ou échec), il ouvre un **point d'accès** :
   - SSID AP : `LiDAR-Scanner-Setup`
   - Mot de passe : aucun (AP ouvert par défaut)
3. Depuis un téléphone ou un PC, se connecter à cet AP.
4. Le portail captif s'ouvre (ou naviguer vers `192.168.4.1`).
5. Renseigner :
   - **SSID** et **mot de passe** du réseau local
   - **IP station hôte (UDP)** : adresse IP du PC qui reçoit le nuage de points (ex. `192.168.1.100`)
6. Valider — l'ESP32 redémarre et se connecte au WiFi.

## Démarrages suivants

Connexion automatique avec les paramètres sauvegardés. L'IP UDP hôte est également persistée.

## Réinitialiser le WiFi

Maintenir le bouton **BOOT** (GPIO 0) enfoncé **pendant la mise sous tension** :

- Les credentials WiFi et l'IP UDP sont effacés.
- Au prochain boot, le portail de configuration réapparaît.

## Paramètres (`config.h`)

| Constante | Défaut | Description |
|-----------|--------|-------------|
| `WIFIMANAGER_AP_NAME` | `LiDAR-Scanner-Setup` | Nom du point d'accès |
| `WIFIMANAGER_AP_PASSWORD` | *(vide)* | Mot de passe AP ; vide = ouvert |
| `WIFIMANAGER_PORTAL_TIMEOUT_S` | 180 | Timeout portail (s) |
| `UDP_HOST_DEFAULT` | `192.168.1.100` | IP hôte par défaut dans le portail |

## Dépannage

| Symptôme | Action |
|----------|--------|
| Portail ne s'ouvre pas | Reset WiFi (BOOT au boot), vérifier serial monitor |
| Connexion OK mais pas de points | Vérifier `IP station hôte` = IP du PC sur le même réseau |
| PC derrière firewall | Autoriser UDP entrant port 9000 |
| Changement de box / SSID | Reset WiFi et reconfigurer |

## Serial monitor

```
[lidar-scanner] amorce OTA 0.1.0-seed
[wifi] connexion, sinon portail AP « LiDAR-Scanner-Setup »
[wifi] connecté — IP 192.168.1.42
[seed] http://lidar-scanner.local/ ou http://192.168.1.42/
```
