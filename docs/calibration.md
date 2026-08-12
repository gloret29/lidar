# Calibration

Cinq mesures à effectuer une fois pour toutes. Elles conditionnent directement
la justesse du nuage : sans elles, le scanner produira un résultat
géométriquement cohérent mais faux.

## 1. Décalage optique du LD19 ($t_x$)

**La mesure la plus importante.** C'est la distance entre la face de fixation du
LD19 et son plan de balayage. Le berceau est dimensionné pour 22 mm ; la valeur
réelle doit être vérifiée.

Méthode directe :

1. Repérer visuellement la fente d'émission sur le pourtour de la tête
   rotative.
2. Mesurer au pied à coulisse la distance entre la face de fixation et le
   milieu de cette fente.
3. Comparer à `lidar_optical_offset = 22` dans `params.scad`.

Méthode par la mesure, plus fiable :

1. Monter le scanner et le mettre de niveau.
2. Placer un mur plat à distance connue $D$ (mesurée au mètre ruban depuis
   l'axe de rotation), perpendiculairement au faisceau.
3. Lancer un balayage de 180°.
4. Ajuster $t_x$ dans la configuration hôte jusqu'à ce que le mur soit **plan**
   dans le nuage.

Un $t_x$ erroné se voit immédiatement : les murs deviennent **incurvés**, avec
une courbure d'autant plus marquée que la surface est proche.

## 2. Zéro d'azimut

Le contact StallGuard définit le zéro mécanique, qui ne coïncide pas avec le
zéro souhaité pour le repère.

1. Lancer un homing.
2. Le scanner note l'orientation en butée.
3. Placer une cible verticale identifiable (piquet, arête de porte) dans une
   direction connue.
4. Relever le $\psi$ auquel elle apparaît dans le nuage.
5. Reporter l'écart dans `psi_offset`.

Répétabilité attendue : mieux que 0,5° sur dix homings. Au-delà, revoir
`SGTHRS` ou la rigidité du contrefort.

## 3. Pas par degré

En entraînement direct, la valeur théorique est :

$$\frac{200 \times 16}{360} = 8{,}889 \text{ micro-pas / degré}$$

Vérification pratique :

1. Homing.
2. Commander 3 200 micro-pas (soit un tour théorique).
3. Vérifier que le secteur de butée revient exactement au contact.

Un écart signale des pas perdus : réduire l'accélération ou augmenter le
courant.

## 4. Nivellement par l'IMU

Le MPU6050 est solidaire de la base fixe. Il ne mesure qu'une chose, mais il la
mesure bien : la direction de la gravité au repos.

Séquence, exécutée automatiquement au début de chaque scan :

1. Vérifier l'immobilité complète.
2. Acquérir 1 000 échantillons d'accéléromètre à 100 Hz (10 s).
3. Moyenner pour obtenir $\mathbf{g} = (g_x, g_y, g_z)$.
4. En déduire tangage et roulis de la base.
5. Construire $R_{\text{level}}$ et la stocker dans l'en-tête du scan.

Le moyennage sur 10 s réduit le bruit d'un facteur $\sqrt{1000} \approx 32$ :
d'environ 1° instantané à mieux que 0,05°. C'est précisément le régime où un
capteur bon marché devient exploitable.

**Étalonnage du montage.** L'IMU n'est jamais collée parfaitement d'équerre.
Une fois pour toutes :

1. Mettre le plateau de base rigoureusement de niveau (niveau à bulle de
   précision posé dessus, croisé à 90°).
2. Relever $\mathbf{g}$.
3. Stocker cette valeur comme référence `g_zero`.

Toute mesure ultérieure s'exprime relativement à `g_zero`, ce qui élimine
l'erreur de collage.

**Détection de choc.** Pendant le scan, l'IMU est relue périodiquement. Si
$\mathbf{g}$ dérive de plus de 0,3°, le trépied a bougé : le scan est marqué
comme suspect. Un scan ainsi contaminé est irrécupérable, autant le savoir tout
de suite.

## 5. Synchronisation temporelle

En balayage continu, $\psi$ est interpolé à l'horodatage de chaque point. Un
retard constant $\Delta t$ entre la mesure LiDAR et la position moteur produit
un décalage angulaire proportionnel à la vitesse.

Mise en évidence :

1. Scanner un coin de pièce en balayant dans le **sens horaire**.
2. Refaire le même scan en **sens antihoraire**.
3. Superposer les deux nuages.

Un décalage angulaire entre les deux vaut $2 \times \omega \times \Delta t$.
Corriger `timestamp_offset_us` jusqu'à superposition.

C'est un défaut typiquement invisible sur un scan isolé, mais qui dédouble
proprement les arêtes dès qu'on recale deux scans entre eux.

## 6. Validation

| Test | Critère |
|---|---|
| Mur plat à 2 m | Épaisseur du nuage < 20 mm, aucune courbure |
| Coin de pièce | Angle mesuré 90° ± 1° |
| Hauteur sous plafond | Cohérente au mètre ruban à ±30 mm |
| Distance entre deux murs | Écart < 1 % de la mesure ruban |
| Sphère de couverture | Aucune bande manquante hors cône du nadir |
| Aller-retour | Superposition à mieux que 20 mm |

Ajuster les paramètres Open3D de post-traitement :

| Traitement | Paramètres de départ |
|---|---|
| Suppression d'aberrants statistique | `nb_neighbors=20`, `std_ratio=2.0` |
| Sous-échantillonnage voxel (aperçu) | `voxel_size=0.01` |
| Estimation des normales | `radius=0.1`, `max_nn=30` |
| Reconstruction Poisson | `depth=8` |

## 7. Fichier de calibration

Les valeurs sont regroupées dans `host/calibration.json`, appliquées au
post-traitement. Elles restent ainsi modifiables **sans reflasher ni
rescanner** — c'est tout l'intérêt de transmettre les données en polaire brut.

```json
{
  "lever_arm_mm": { "tx": 0.0, "ty": 0.0, "tz": 0.0 },
  "psi_offset_deg": 0.0,
  "theta_offset_deg": 0.0,
  "steps_per_degree": 8.889,
  "timestamp_offset_us": 0,
  "g_zero": [0.0, 0.0, -1.0]
}
```
