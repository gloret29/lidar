// ============================================================
//  Scanner 3D LiDAR — paramètres partagés
//  Toutes les cotes sont en millimètres.
//
//  Repère d'assemblage : z = 0 sur la face SUPÉRIEURE du plateau
//  de base. L'axe de rotation (lacet psi) est l'axe Z.
// ============================================================

// Finesse de facettisation adaptative : les petits perçages restent
// légers, les grands diamètres restent lisses.
$fa = 4;
$fs = 0.6;

// ------------------------------------------------------------
//  Ajustements d'impression
//  À recalibrer sur votre imprimante avec mechanical/openscad/
//  test_fits.scad avant d'imprimer les pièces définitives.
// ------------------------------------------------------------
fit_press = 0.15;   // serré   : roulement — encoche 5 du coupon (delta +0,15 → Ø22,15)
fit_slide = 0.45;   // glissant: tige — encoche 4 (delta +0,10 → Ø8,45)
fit_free = 0.50;    // libre   : dégagements

// ------------------------------------------------------------
//  Roulement 608ZZ
// ------------------------------------------------------------
bearing_od = 22;
bearing_id = 8;
bearing_w = 7;

// ------------------------------------------------------------
//  Arbre vertical (tige acier rectifiée Ø8 h6)
// ------------------------------------------------------------
shaft_d = 8;
// Longueur utile : de l'accouplement (z 65) au sommet du moyeu (z 180).
// Ne PAS dépasser 180 : au-delà, la tige pénètre dans le corps du LD19.
shaft_len = 115;

// ------------------------------------------------------------
//  Moteur NEMA 17 (17HS4401)
// ------------------------------------------------------------
nema_body = 42.3;
nema_len = 40;       // longueur du corps (marge : 38 mm réels)
nema_pitch = 31;     // entraxe carré des 4 vis M3
nema_boss_d = 22;    // bossage de centrage
nema_boss_h = 2;
nema_shaft_d = 5;
nema_shaft_l = 24;

// ------------------------------------------------------------
//  Accouplement flexible 5 mm -> 8 mm (type mâchoires / araignée)
// ------------------------------------------------------------
coupler_d = 19;
coupler_l = 25;

// ------------------------------------------------------------
//  LiDAR — STL-19P / FHL-LD19P (LDROBOT, 3 oreilles de fixation)
//  Câble vers le bas au montage sur le berceau.
//  ATTENTION : lidar_optical_offset à VÉRIFIER au pied à coulisse.
//  Voir docs/calibration.md § « Mesure du décalage optique ».
//  Perçage : datasheet STL-19P § 5.1 (46,8 × 38,59 mm, M2,5).
// ------------------------------------------------------------
lidar_w = 54;                  // envergure Y (oreilles comprises)
lidar_h = 46.29;               // hauteur Z sur la platine
lidar_thk = 35;                // profondeur X (corps + dôme)
lidar_optical_offset = 22;     // plan de balayage / face de fixation  <-- À VÉRIFIER
lidar_screw_d = 2.7;           // M2.5 traversant (contre-sens 4,46 × 2 sur capteur)
lidar_hole_y = 23.4;           // demi-entraxe Y des oreilles latérales (46,8 / 2)
lidar_side_hole_z = 7.7;       // Z oreilles lat. depuis le bas du footprint (câble en bas)
lidar_top_hole_z = 43.29;      // Z oreille haute (46,29 − 3)
lidar_cable_z = 8;             // passage nappe depuis le bas du footprint

// ------------------------------------------------------------
//  Visserie M3
// ------------------------------------------------------------
m3_clear = 3.4;
m3_head_d = 6.2;
m3_head_h = 3.2;
m3_nut_af = 5.6;   // entreplat
m3_nut_h = 2.7;

// ------------------------------------------------------------
//  Insert laiton 1/4"-20 UNC (fixation trépied)
// ------------------------------------------------------------
insert_qtr_d = 8.4;
insert_qtr_l = 13;

// ------------------------------------------------------------
//  Plateau de base
// ------------------------------------------------------------
plate_d = 126;
plate_t = 8;
tripod_boss_d = 30;
tripod_boss_h = 16;
tower_bolt_circle = 106;   // hors du cône : têtes de vis accessibles

// ------------------------------------------------------------
//  Colonne à roulements  (z local = 0 sur la face inférieure,
//  qui repose sur la face supérieure du plateau)
// ------------------------------------------------------------
tower_flange_d = 118;
tower_flange_t = 6;
tower_base_d = 96;
tower_top_d = 34;
tower_cone_top_z = 100;   // fin du cône
tower_total_h = 133;      // hauteur totale
tower_cavity_d = 62;      // dégagement moteur (diagonale NEMA 17 = 59.8 mm)
tower_cavity_top_z = 42;
tower_throat_d = 26;      // dégagement accouplement (Ø19)
tower_throat_z = 78;

bearing_lo_z = 82;        // face inférieure du roulement bas
bearing_hi_z = 122;       // face inférieure du roulement haut
bearing_relief_d = 23.5;

// ------------------------------------------------------------
//  Berceau LiDAR  (cotes en repère d'assemblage global)
// ------------------------------------------------------------
hub_d = 18;
hub_z0 = 140;
hub_z1 = 180;
hub_top_d = 12;          // rétreint pour limiter l'occultation au nadir
web_z0 = 176;
web_z1 = 188;
web_hw = 7;              // demi-largeur en Y
plate_x = -22;           // face de fixation du LiDAR (= -lidar_optical_offset)
cradle_plate_t = 5;
optical_z = 205;         // hauteur du centre optique  => centre du nuage

// ------------------------------------------------------------
//  Boîtier électronique
// ------------------------------------------------------------
box_ix = 106;
box_iy = 76;
box_iz = 34;
box_wall = 2.5;
