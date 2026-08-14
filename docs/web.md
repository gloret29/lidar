# Panneau web embarqué

Le scanner expose une page unique sur le port 80, protégée par le même mot de
passe que l'OTA (`admin` / valeur du portail WiFiManager).

```
http://lidar-scanner.local/
```

Ou l'adresse IP affichée au démarrage série.

## Ce que fait la page

Quatre blocs, un seul écran :

| Section | Rôle |
|---|---|
| **Commande** | Lancer, arrêter, rehomer, arrêt d'urgence |
| **Diagnostics** | État, ψ, fréquence LiDAR, CRC, file, StallGuard, RSSI |
| **Réglages** | Les 6 paramètres de mise au point, persistés en NVS |
| **OTA** | Téléversement d'un `firmware.bin` ou d'un `littlefs.bin` |

Le balayage **ne démarre plus tout seul** au boot. Après connexion Wi‑Fi, le
scanner reste au repos jusqu'à un clic sur « Lancer le scan » — ou jusqu'à
l'équivalent API. C'est volontaire : sur le terrain on repositionne, on
relance, on ne coupe pas l'alimentation entre deux prises de vue.

## API

Toutes les routes exigent l'authentification HTTP basic.

| Route | Méthode | Corps / query | Effet |
|---|---|---|---|
| `/api/status` | GET | — | Instantané JSON (télémétrie + version) |
| `/api/command?cmd=` | POST | `start` \| `stop` \| `rehome` \| `estop` | File de commandes FreeRTOS |
| `/api/settings` | GET | — | Réglages courants |
| `/api/settings` | POST | formulaire urlencoded | Enregistre + applique |
| `/api/settings?defaults=1` | POST | — | Restaure les valeurs d'usine |
| `/update` | POST | multipart `.bin` | OTA firmware |
| `/updatefs` | POST | multipart `.bin` | OTA LittleFS |
| `/info` | GET | — | Alias de `/api/status` (compat OTA) |

Exemple :

```bash
curl -u admin:lidar-ota -X POST 'http://lidar-scanner.local/api/command?cmd=start'
curl -u admin:lidar-ota http://lidar-scanner.local/api/status
```

## Réglages exposés

| Champ | Bornes | Effet |
|---|---|---|
| `lidar_hz` | 5…13 | Consigne PWM du LD19 |
| `speed` | 0,5…10 °/s | Vitesse d'azimut pendant le balayage |
| `end_deg` | 10…360 ° | Amplitude (180 ° couvre la sphère une fois) |
| `sg` | 1…255 | Seuil StallGuard du homing |
| `i_scan` | 200…1200 mA | Courant RMS en balayage |
| `i_home` | 100…800 mA | Courant RMS en homing |

Les bornes sont appliquées **dans le firmware**, pas seulement dans le
formulaire. Modifier les réglages pendant un balayage est refusé (HTTP 409).

Ce qui **n'y figure pas**, volontairement :

- identifiants Wi‑Fi → portail WiFiManager ;
- calibration géométrique (bras de levier, décalages, gravité) →
  `host/calibration.json`, pour pouvoir rejouer un scan sans rescanner.

## Diagnostic utile sur place

| Indicateur | Lecture |
|---|---|
| CRC % | < ~95 % → câblage UART, débit, ou alimentation LiDAR |
| Fréquence mesurée | Doit coller à la consigne ±0,3 Hz |
| StallGuard live | Chute nette à l'approche de la butée ; utile pour régler `sg` |
| File | Monte sans redescendre → Wi‑Fi saturé ou hôte absent |
| RSSI | < −75 dBm → risque de pertes UDP |

## Sécurité

- Même mot de passe que l'OTA ; à changer dans le portail captif.
- Arrêt d'urgence : coupe `EN` du TMC2209 immédiatement.
- Une OTA en cours refuse les commandes de balayage.
- Un balayage en cours refuse l'OTA et le changement de réglages.

Voir aussi [ota.md](ota.md) et [wifi.md](wifi.md).
