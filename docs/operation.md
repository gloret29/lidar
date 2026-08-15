# Guide d'utilisation

## 1. Préparation des lieux

La préparation compte davantage que les réglages : la plupart des défauts d'un
relevé d'intérieur viennent de la scène, pas du capteur.

### Fenêtres — fermer les volets (recommandé)

Le STL-19P (**FHL-LD19P**) **détecte le verre** : le faisceau peut mesurer la
surface vitrée elle-même plutôt que de la traverser. Sans volet, on obtient
souvent un plan sur la vitre — parfois souhaitable, parfois confus selon
l'angle d'incidence.

Volets fermés, on obtient en plus :

1. Une surface opaque exploitable derrière la vitre (tablier du volet).
2. La suppression de l'éblouissement. Le capteur tolère 30 klux, alors qu'une
   tache de soleil direct dépasse 100 klux et provoque des décrochages locaux.

**Nuance** : même avec détection du verre, le tablier fermé peut apparaître
quelques centimètres en retrait si le faisceau le voit à travers une interstice.
Les fenêtres peuvent aussi montrer une double surface là où le faisceau arrive
perpendiculairement à la vitre (~4 % en spéculaire) ; le filtrage statistique
l'absorbe en général.

### Miroirs — les couvrir

C'est le problème le plus sérieux, et les volets n'y changent rien.

Un miroir ne produit pas du bruit : il produit une **pièce virtuelle complète
et géométriquement cohérente** derrière lui. Aucun filtrage d'aberrants ne la
supprimera, puisque ce ne sont pas des aberrations.

Couvrir d'un drap ou d'un carton pendant le scan. On récupère alors le plan du
miroir, ce que l'on veut. Penser également aux parois de douche, portes
vitrées, vitrines et façades d'armoires laquées.

### Autres surfaces délicates

| Surface | Effet | Parade |
|---|---|---|
| Inox, chrome, électroménager | Spéculaire, retour faible | Accepter les trous |
| Écrans TV éteints | Très peu réfléchissants | Couvrir |
| Sols brillants (carrelage) | Réflexion en incidence rasante | Scanner de plus près |
| Textiles noirs mats | Portée réduite | Se rapprocher |
| Végétation | Retours multiples | Filtrer en post-traitement |

### Occupants et animaux

Un scan dure 45 à 180 s. Tout ce qui bouge laisse des traînées. Faire sortir
les occupants de la pièce et fermer les portes des pièces non concernées.

## 2. Positionnement du scanner

### Nombre de positions

Une position par pièce ne suffit presque jamais : tout ce qui est derrière un
meuble ou un angle reste dans l'ombre. Compter :

- Petite pièce dégagée : 1 à 2 positions
- Pièce meublée : 3 à 4 positions
- Couloir : une position tous les 4 à 5 m
- Escalier : une position par palier, plus une à mi-volée

### Règles de placement

1. **Recouvrement** : au moins 30 % de zones communes entre deux positions
   voisines, faute de quoi le recalage ICP échouera.
2. **Ligne de vue** : chaque position doit voir la suivante.
3. **Hauteur** : environ 1,50 m, et **varier** entre positions — cela aide le
   recalage et comble le cône du nadir.
4. **Écarter des murs** : au moins 1 m, pour ne pas gâcher la moitié du champ.
5. **Sol stable** : éviter les planchers souples ; le moindre déplacement
   pendant le scan ruine la position.

### Cibles de recalage

Sur des surfaces pauvres en géométrie (couloir aux murs nus), disposer trois à
quatre objets asymétriques bien visibles depuis deux positions consécutives.
Une boîte, un carton, une chaise suffisent. Les laisser strictement immobiles
entre les scans.

## 3. Déroulement d'un scan

### Mise en station

1. Déployer le trépied, hauteur environ 1,50 m.
2. Visser le scanner sur l'embase 1/4"-20.
3. Mettre de niveau grossièrement à la bulle.
4. Mettre sous tension et attendre la connexion Wi‑Fi.
5. Ouvrir `http://lidar-scanner.local/` (ou l'IP du scanner).
6. Lancer la réception sur la station hôte, puis cliquer **Lancer le scan**.

Voir [web.md](web.md) pour la commande, les diagnostics et les réglages.

### Séquence d'un balayage

```
  1. Nivellement IMU        10 s   moyennage de la gravité (à venir)
  2. Homing StallGuard       5 s   zéro d'azimut absolu
  3. Stabilisation STL-19P   3 s   montée en vitesse
  4. Balayage 0 → fin °  45-180 s  selon vitesse / amplitude
  5. Contrôle de choc        2 s   relecture de l'IMU (à venir)
  6. Vidange des tampons     2 s
```

Le scanner ne démarre **pas** tout seul : chaque prise se lance depuis le
panneau (ou `POST /api/command?cmd=start`). Arrêt propre ou d'urgence depuis
la même page.

Ne pas toucher au trépied pendant le balayage — pas même pour le stabiliser.

### Choix du pas

| Pas $\psi$ | Durée | Points | Usage |
|---|---|---|---|
| 0,8° | 45 s | 202 000 | Reconnaissance, contrôle de couverture |
| 0,4° | 90 s | 405 000 | **Réglage standard** |
| 0,2° | 180 s | 810 000 | Relevé de détail, pièce unique |

## 4. Station hôte

### Visualisation en direct

```bash
cd host && source .venv/bin/activate
# WSL2 : export DISPLAY=:0 si besoin
lidar-visualize --port 9000
```

Le nuage se construit à l'écran pendant le balayage. Surveiller :

- Les murs doivent apparaître **plans**. S'ils sont courbes, le bras de levier
  est mal calibré ([calibration.md](calibration.md) § 1).
- Les angles doivent être **droits**.
- Aucune bande manquante hors du cône du nadir.

Guide détaillé Open3D (navigation, enregistrement, recalage, maillage, WSL) :
[open3d.md](open3d.md).

Sans matériel, le même pipeline se valide avec
`lidar-simulate --host 127.0.0.1 --port 9000 --fast` dans un second terminal.

### Enregistrement

```bash
lidar-receive --port 9000 --output scans/salon_pos1.pcd
```

Convention de nommage : `<pièce>_pos<n>.pcd`. Tenir un croquis papier des
positions : indispensable au recalage, et impossible à reconstituer après coup.

### Recalage multi-positions

```bash
lidar-register scans/salon_*.pcd --output salon_complet.pcd
```

Recalage grossier par appariement de caractéristiques, puis affinage ICP. Si
l'ICP diverge, c'est presque toujours un recouvrement insuffisant.

### Maillage et export

```bash
lidar-mesh salon_complet.pcd --output salon.ply --depth 8
```

Formats de sortie :

| Format | Usage |
|---|---|
| `.pcd` | Nuage de travail, Open3D / PCL |
| `.ply` | Maillage, import CAO |
| `.e57` | Échange standard en photogrammétrie |
| `.las` | SIG et gros volumes |

## 5. Ce qu'il faut attendre du résultat

| Usage | Adapté ? |
|---|---|
| Plan d'étage, surfaces | Oui, très bien |
| Volumes pour dimensionner une VMC ou un chauffage | Oui |
| Vérifier qu'un meuble passe | Oui |
| Modèle d'ambiance pour de la 3D | Oui |
| Détection de collisions en BIM | Non, précision insuffisante |
| Relevé patrimonial de détail | Non |
| Contrôle dimensionnel au millimètre | Non |

Précision réaliste : environ **±5 cm** sur un mur, avec un espacement des
points de 3 à 7 cm à 5 m. Un scanner terrestre professionnel atteint ±2 mm et
des dizaines de millions de points — pour 15 000 à 50 000 €.

## 6. Dépannage

| Symptôme | Cause probable | Correction |
|---|---|---|
| Murs incurvés | Bras de levier non calibré | Calibration § 1 |
| Nuage tourné / penché | Nivellement IMU raté | Refaire à l'arrêt complet |
| Arêtes dédoublées | Décalage temporel | Calibration § 5 |
| Bandes manquantes | Pas perdus au moteur | Baisser l'accélération, monter le courant |
| Points dans le jardin | Fenêtre sans volet | Fermer les volets |
| Pièce fantôme | Miroir | Le couvrir |
| Trous sur surfaces sombres | Réflectivité faible | Se rapprocher |
| Nuage bruité près du sol | Réflexion rasante | Normal, filtrer |
| Perte de paquets UDP | Wi-Fi saturé | Se rapprocher du point d'accès |
| Le scan s'arrête en cours | Coupure de la power bank | Vérifier le seuil de veille |
| Balayage bruyant | StealthChop non actif | Vérifier la liaison UART du TMC2209 |

## 7. Entretien

| Fréquence | Opération |
|---|---|
| Avant chaque scan | Nettoyer la fenêtre optique du STL-19P au chiffon microfibre |
| Mensuel | Vérifier le serrage du berceau et de l'accouplement |
| Mensuel | Contrôler l'usure du câble tournant |
| Semestriel | Refaire la calibration complète |
| Au besoin | Remplacer les 608ZZ (il en reste 38 au tiroir) |

Le STL-19P est donné pour plus de 10 000 h, soit largement au-delà d'un usage
amateur.
