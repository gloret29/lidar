# Géométrie et transformation des coordonnées

Ce document justifie l'architecture retenue et donne la transformation exacte
utilisée pour convertir les mesures brutes en nuage de points cartésien.
C'est le cœur mathématique du projet : une erreur ici ne produit pas du bruit,
elle produit un nuage **cohérent mais faux**, ce qui est bien plus difficile à
détecter après coup.

## 1. Principe du balayage

Le LD19 désigne ici la **famille de capteurs** (protocole UART commun). Le
prototype utilise la variante **STL-19P** (FHL-LD19P, 5 000 Hz, détection
verre, 3 oreilles M2,5).

Le LD19 est un LiDAR **2D** : il mesure une distance $\rho$ dans un plan, en
tournant sur 360° autour de son propre axe. Pour obtenir un volume 3D, il faut
déplacer ce plan.

L'architecture retenue est la suivante :

- Le LD19 est monté **couché sur la tranche** : son plan de balayage est
  **vertical**.
- L'ensemble tourne autour d'un **axe vertical** (lacet $\psi$), entraîné par
  le NEMA 17.
- Le centre optique du LD19 est placé **sur l'axe de rotation**.

```
            plan de balayage (vertical, tourne avec la tête)
                        │
              ╔═════════╪═════════╗
              ║         │         ║
              ║      ┌──┴──┐      ║   LD19 couché : son axe de rotation
              ║      │LD19 │      ║   propre est HORIZONTAL
              ║      └──┬──┘      ║
              ╚═════════╪═════════╝
                        │  axe de lacet psi (vertical)
                     ───┼───
                     colonne
                        │
                     trépied
```

### Pourquoi pas l'inclinaison d'un plan horizontal ?

L'approche intuitive — poser le LD19 à plat et basculer le plan autour d'un axe
horizontal — est nettement inférieure :

| Critère | Basculement d'un plan horizontal | Lacet d'un plan vertical |
|---|---|---|
| Pôles d'échantillonnage | Deux points horizontaux arbitraires, sur des murs | Zénith et nadir |
| Densité sur les murs | Très inégale | Uniforme |
| Couple moteur | Varie avec l'angle (gravité) | Constant, frottement seul |
| Fléchissement mécanique | Variable pendant le scan | Statique |
| Alignement avec la gravité | Indirect | L'axe EST la verticale |

Tous les plans de balayage contiennent l'axe de rotation. Ce sont donc des
grands cercles passant par les deux pôles. Avec un axe vertical, ces pôles sont
le zénith et le nadir : le nadir est de toute façon masqué par le trépied, et
la sur-densité au zénith est sans conséquence. Avec un axe horizontal, les
pôles tombent sur deux murs au hasard, où l'on récolte deux taches
hyper-denses entourées de zones clairsemées.

**Conséquence pratique** : puisque le plan à $\psi$ et le plan à $\psi + 180°$
sont le même plan, un balayage de **180° suffit** à couvrir la sphère complète
exactement une fois.

## 2. Rôle des angles

| Symbole | Origine | Rôle | Plage |
|---|---|---|---|
| $\rho$ | LD19 | Distance mesurée | 0,02 – 12 m |
| $\theta$ | LD19 (angle interne) | **Élévation** | 0 – 360° |
| $\psi$ | Moteur pas-à-pas | **Azimut** | 0 – 180° |

C'est le point contre-intuitif : l'angle rapide du LiDAR est l'élévation, et
l'angle lent du moteur est l'azimut. L'inverse produirait un nuage faux.

## 3. Transformation exacte

Dans son propre repère, le LD19 émet dans son plan de balayage. Une fois couché
de sorte que ce plan soit le plan $XZ$, la direction du faisceau est :

$$
\mathbf{u}(\theta) = (\cos\theta,\; 0,\; \sin\theta)
$$

La tête tourne ensuite de $\psi$ autour de l'axe $Z$ :

$$
R_z(\psi) =
\begin{pmatrix}
\cos\psi & -\sin\psi & 0 \\
\sin\psi & \cos\psi & 0 \\
0 & 0 & 1
\end{pmatrix}
$$

D'où, pour un centre optique parfaitement sur l'axe :

$$
\boxed{\;
X = \rho \cos\psi \cos\theta, \quad
Y = \rho \sin\psi \cos\theta, \quad
Z = \rho \sin\theta
\;}
$$

Ce sont exactement les coordonnées sphériques usuelles, à condition de bien
poser **azimut $= \psi$** et **élévation $= \theta$**.

### L'erreur à ne pas commettre

Une spécification naïve écrit souvent :

$$
X = \rho \cos\phi \cos\theta, \quad
Y = \rho \cos\phi \sin\theta, \quad
Z = \rho \sin\phi
$$

en prenant $\theta$ (LiDAR) pour l'azimut et $\phi$ (moteur) pour l'élévation.
Cette formule décrit une **rotule pan-tilt à faisceau unique**, pas un plan de
balayage que l'on fait pivoter.

Contre-exemple immédiat : à $\phi = 90°$, elle donne $(0, 0, \rho)$ pour *tous*
les points — le scan entier s'effondre au zénith. En réalité, un LiDAR 2D
incliné à 90° balaie toujours un cercle complet. L'erreur croît continûment
avec $\phi$ et déforme l'intégralité du nuage.

## 4. Correction du bras de levier

En pratique le centre optique n'est jamais exactement sur l'axe. Soit
$\mathbf{t} = (t_x, t_y, t_z)$ le vecteur allant de l'axe de rotation au centre
optique, exprimé dans le repère de la tête. La transformation devient :

$$
\mathbf{p} = R_z(\psi) \cdot \big( \rho\,\mathbf{u}(\theta) + \mathbf{t} \big)
$$

soit, en développant :

$$
\begin{aligned}
X &= \cos\psi\,(\rho\cos\theta + t_x) - \sin\psi\,t_y \\
Y &= \sin\psi\,(\rho\cos\theta + t_x) + \cos\psi\,t_y \\
Z &= \rho\sin\theta + t_z
\end{aligned}
$$

**Pourquoi c'est important** : le boîtier du STL-19P fait **54 × 46 mm**
(oreilles comprises). Un décalage résiduel de 20 à 30 mm est du même ordre que
la précision du capteur (±45 mm). Mais contrairement au bruit, cette erreur est
**systématique** : elle ne se moyenne pas, elle courbe légèrement les murs et
fausse les angles.

Le berceau est conçu pour amener $\mathbf{t}$ aussi près de zéro que possible.
Le résidu se mesure et se compense en post-traitement : voir
[calibration.md](calibration.md).

## 5. Redressement selon la gravité

L'axe de lacet n'est vertical que si le trépied est de niveau. Le MPU6050,
solidaire de la **base fixe**, mesure le vecteur gravité au repos :

$$
\mathbf{g} = (g_x, g_y, g_z)
$$

On construit la rotation $R_{\text{level}}$ qui amène $\mathbf{g}$ sur
$(0, 0, -1)$, et on l'applique au nuage entier :

$$
\mathbf{p}_{\text{monde}} = R_{\text{level}} \cdot \mathbf{p}
$$

Une seule mesure statique, moyennée sur quelques secondes, suffit — et c'est
justement le régime où un MPU6050 est précis.

### Ce qu'il ne faut PAS faire

Injecter la mesure d'inclinaison de l'IMU **point par point** dans $\psi$ ou
$\theta$. Le bruit d'un MPU6050 est de 0,5 à 1° :

| Distance | Erreur induite par 1° |
|---|---|
| 2 m | 35 mm |
| 5 m | 87 mm |
| 10 m | 175 mm |

À comparer aux 0,1125° par micro-pas du moteur en 1/16, et aux ±45 mm du LD19.
L'IMU dégraderait la mesure d'un facteur 2 à 4. Le moteur est la référence
angulaire ; l'IMU sert au **nivellement** et à la **détection de choc**.

## 6. Résolution et durée de scan

Le STL-19P échantillonne à **5 000 Hz** quelle que soit sa vitesse de rotation,
elle-même réglable de 5 à 13 Hz par PWM. Sur trépied le temps n'est pas
critique : **descendre à 5 Hz double la densité angulaire gratuitement**.

| Vitesse STL-19P | Points / tour | Résolution en $\theta$ | Tour |
|---|---|---|---|
| 10 Hz (défaut) | 500 | 0,72° | 100 ms |
| 5 Hz | 1 000 | 0,36° | 200 ms |

Pour un balayage de 180° en azimut :

| Pas en $\psi$ | Tranches | Points (à 5 Hz) | Durée |
|---|---|---|---|
| 0,8° | 225 | 225 000 | 45 s |
| 0,4° | 450 | 450 000 | 90 s |
| 0,2° | 900 | 900 000 | 180 s |

Espacement des points à 5 m avec un pas de 0,4° : environ **35 mm** dans les
deux directions.

## 7. Budget d'erreur

| Source | Contribution | Nature |
|---|---|---|
| Précision LD19 | ±45 mm (0,3–12 m) | Aléatoire |
| Bras de levier non compensé | jusqu'à 30 mm | **Systématique** |
| Micro-pas moteur (1/16) | 0,11° → 10 mm à 5 m | Systématique, répétable |
| Jeu des roulements | < 0,05° | Aléatoire |
| Défaut de nivellement | 0,2° après réglage IMU | Systématique, corrigeable |
| Décalage temporel $\rho$ / $\psi$ | voir ci-dessous | Systématique |

**Réalisme** : environ ±5 cm sur un mur, pour un espacement de points de 3 à
7 cm. Excellent pour un plan d'étage ou un relevé volumétrique ; insuffisant
pour du BIM de détail, où un scanner professionnel donne ±2 mm.

### Décalage temporel

Le LD19 émet des trames de 12 points horodatées côté capteur. Si le moteur
avance en continu pendant l'émission d'une trame, tous les points d'une trame
ne partagent pas le même $\psi$. Deux stratégies :

1. **Pas à pas discret** — le moteur s'arrête à chaque tranche, on capture un
   tour complet, puis on avance. Aucune ambiguïté, mais plus lent et les
   accélérations sollicitent la mécanique.
2. **Balayage continu** — le moteur tourne lentement et régulièrement, et on
   interpole $\psi$ à l'horodatage de chaque point. Plus rapide, plus doux, et
   l'échantillonnage devient hélicoïdal.

Le firmware retient la seconde approche : $\psi$ est interpolé linéairement
entre deux jalons de position moteur, à partir de l'horodatage du point.
