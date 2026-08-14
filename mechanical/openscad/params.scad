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
fit_press = 0.10;   // serré   : roulement dans son logement
fit_slide = 0.45;   // glissant: tige, vis traversantes
fit_free = 0.50;    // libre   : dégagements
// Calibré après coupon test_fits : encoche 5 (delta 0,00) encore serrée
// sur l'ancienne plage — imprimante qui rétrécit les perçages.

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
//  LiDAR LD19
//  ATTENTION : lidar_optical_offset et le pattern de perçage
//  doivent être VÉRIFIÉS au pied à coulisse sur votre exemplaire.
//  Voir docs/calibration.md § « Mesure du décalage optique ».
// ------------------------------------------------------------
lidar_w = 38.6;                // empreinte (largeur)
lidar_h = 38.6;                // empreinte (hauteur, monté sur la tranche)
lidar_thk = 33.5;              // hauteur du boîtier = épaisseur une fois couché
lidar_optical_offset = 22;     // plan de balayage / face de fixation  <-- À VÉRIFIER
lidar_screw_d = 2.6;           // M2.5 (lumières oblongues, tolérant)
lidar_slot_len = 8;            // longueur des lumières de réglage

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
