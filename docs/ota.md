# Mise à jour par le réseau (OTA)

Le scanner se met à jour par Wi-Fi, sans câble USB. C'est particulièrement
utile une fois l'appareil sanglé sur son trépied, port USB tourné vers
l'intérieur du boîtier.

Deux voies coexistent :

| Voie | Port | Usage |
|---|---|---|
| **espota** | 3232 | Développement : `pio run -e ota -t upload` |
| **Page web** | 80 | Terrain : téléverser un `.bin` depuis un navigateur |

## 1. Prérequis : schéma de partitions

L'OTA écrit le nouveau firmware dans une **seconde partition applicative**,
puis bascule le pointeur de démarrage. Il faut donc un schéma de partitions qui
en comporte deux.

`default_16MB.csv`, déjà configuré, fournit `app0` et `app1` de 6,5 Mo chacune.

Le firmware le vérifie au démarrage et le signale sur le port série :

```
[ota] partition active « app0 »
[ota] cible de mise à jour « app1 » (6400 ko)
```

Si l'on lit `[ota] ERREUR : aucune seconde partition applicative`, c'est que
`board_build.partitions` a été modifié. L'OTA est alors désactivé, mais le
scanner fonctionne normalement.

## 2. Mot de passe

Il se configure dans le **portail WiFiManager**, à côté de l'adresse de la
station hôte, et il est persisté en NVS.

Valeur de repli au premier démarrage : `lidar-ota`. Le firmware le rappelle
au démarrage :

```
[wifi] ATTENTION : mot de passe OTA laissé par défaut
```

Le même mot de passe protège les deux voies. Pour la page web, il s'agit d'une
authentification HTTP basic avec l'identifiant **`admin`**.

> Sans mot de passe, n'importe qui sur le réseau local peut reflasher
> l'appareil. Le changer prend dix secondes dans le portail.

## 3. Mise à jour depuis PlatformIO

```bash
cd firmware
pio run -e ota -t upload
```

L'environnement `ota` de `platformio.ini` vise `lidar-scanner.local`. Si mDNS
ne résout pas sur votre réseau — c'est fréquent sous Windows et sur certains
réseaux invités — passer l'adresse IP directement :

```bash
pio run -e ota -t upload --upload-port 192.168.1.42
```

Le mot de passe est dans `upload_flags` (`--auth=`). Le corriger s'il a été
changé dans le portail.

Le port série n'est évidemment pas disponible par cette voie. Pour suivre les
journaux à distance, garder l'USB branché pour le moniteur et n'utiliser l'OTA
que pour le téléversement.

## 4. Mise à jour depuis un navigateur

Ouvrir `http://lidar-scanner.local/` — ou l'adresse IP — et s'authentifier avec
`admin` et le mot de passe OTA.

La page affiche la version, la partition active, la mémoire libre et l'état du
scanner, puis propose de déposer un fichier `firmware.bin`. Une barre de
progression suit l'écriture, et le scanner redémarre tout seul.

Le binaire à téléverser est produit par la compilation :

```
firmware/.pio/build/usb/firmware.bin
```

C'est bien `firmware.bin` qu'il faut, **pas** `firmware.elf` ni
`firmware.factory.bin`.

### Points d'accès

| Route | Méthode | Rôle |
|---|---|---|
| `/` | GET | Page de mise à jour |
| `/info` | GET | État en JSON : version, partitions, mémoire, occupation |
| `/update` | POST | Téléversement multipart du `.bin` |

## 5. Sécurité mécanique

Une mise à jour arrête le moteur **avant** d'écrire quoi que ce soit en flash.
Sans cette précaution, l'ESP32 redémarrerait avec le TMC2209 encore alimenté,
laissant l'axe en couple pendant plusieurs secondes.

Séquence exécutée au démarrage d'une mise à jour :

1. `ota_lock` posé : plus aucun balayage ne peut démarrer.
2. `scannerEmergencyStop()` : broche `EN` du TMC2209 relâchée, moteur libre.
3. Suspension des tâches LiDAR et réseau, qui libèrent CPU et bande passante.
4. Écriture en flash, puis redémarrage.

### L'OTA est refusé pendant un balayage

Flasher en pleine acquisition perdrait le scan en cours et laisserait la
mécanique dans un état indéterminé. Tant que l'état est `Homing`, `Spinup` ou
`Scanning` :

- ArduinoOTA n'est pas servi — le port 3232 ne répond simplement pas ;
- la page web reste accessible et affiche « balayage en cours », et
  `/update` renvoie **503**.

Un balayage dure au plus 180 s. Pour passer outre, mettre
`OTA_ALLOW_DURING_SCAN` à 1 dans `config.h` — en connaissance de cause.

### La fenêtre OTA au démarrage

C'est le filet de sécurité contre le scénario classique : téléverser un
firmware qui plante pendant le scan, et se retrouver avec un appareil qui
redémarre en boucle sans jamais laisser d'occasion de le corriger.

À chaque démarrage, `motion_task` attend **10 secondes** avant de lancer le
homing. Pendant ce délai le scanner est au repos, donc joignable en OTA.

```
[main] fenêtre OTA de 10 s avant le balayage
```

Si une mise à jour démarre pendant la fenêtre, le balayage est annulé au profit
de la mise à jour.

Durée réglable par `OTA_BOOT_WINDOW_S` dans `config.h`. La réduire raccourcit
d'autant le filet de sécurité.

## 6. Comportement en cas d'échec

| Cas | Réaction |
|---|---|
| Mot de passe erroné | Refus avant toute écriture ; rien n'est touché |
| Balayage en cours | Refus, code 503 |
| Coupure en cours d'écriture | Redémarrage automatique sur l'**ancienne** partition |
| Binaire corrompu | `Update.end()` échoue, la bascule n'a pas lieu |

La partition en cours d'exécution n'est jamais écrasée : l'écriture se fait
toujours dans l'autre. Une mise à jour interrompue laisse donc l'ancien
firmware intact et bootable. C'est la propriété fondamentale du mécanisme, et
la raison pour laquelle un `.bin` mal formé ne brique pas l'appareil.

Après un échec autre qu'une erreur d'authentification, le firmware redémarre
de lui-même : la flash pouvant être partiellement écrite, un état propre vaut
mieux qu'un état indéterminé.

## 7. Récupération

Si l'OTA devient inaccessible — mauvaise configuration Wi-Fi, plantage
précoce — il reste toujours l'USB :

```bash
cd firmware
pio run -e usb -t upload
```

Et pour repartir d'une configuration réseau vierge : maintenir **BOOT** au
démarrage. Cela efface les identifiants Wi-Fi, l'adresse de la station hôte et
le mot de passe OTA, et rouvre le portail captif.

## 8. Dépannage

| Symptôme | Cause probable | Correction |
|---|---|---|
| `lidar-scanner.local` introuvable | mDNS non résolu | Utiliser l'adresse IP |
| espota expire | Balayage en cours | Attendre la fin, ou utiliser la fenêtre de démarrage |
| `Authentication Failed` | Mot de passe divergent | Aligner `--auth=` sur la valeur du portail |
| La page demande sans cesse le mot de passe | Identifiant oublié | L'identifiant est `admin` |
| `Not Enough Space` | Schéma sans OTA | Rétablir `default_16MB.csv` |
| Redémarre sur l'ancienne version | Écriture incomplète | Vérifier le Wi-Fi, réessayer |
| Coupure à mi-parcours, systématique | Alimentation limite | Brancher sur secteur plutôt que power bank |
