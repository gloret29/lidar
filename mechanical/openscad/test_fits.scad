// ============================================================
//  00 — Coupon de calibration des ajustements
//
//  À IMPRIMER EN PREMIER, avant toute autre pièce.
//  Géométrie compacte : ~65 % de matière en moins que la v1.
//
//  Cinq paires d'essais, repérées par 1 à 5 encoches gravées :
//
//    index  |  1      2      3      4      5
//    ----------------------------------------------
//    delta  | -0.05   0.00  +0.05  +0.10  +0.15
//    ----------------------------------------------
//    logement 608ZZ (borgne 4 mm — suffisant pour juger la presse)
//           | 21.95  22.00  22.05  22.10  22.15
//    ----------------------------------------------
//    alésage tige Ø8 (traversant)
//           |  8.30   8.35   8.40   8.45   8.50
//
//  Impression rapide (voir docs/printing.md) :
//    couche 0,28 mm · 2 périmètres · 10 % remplissage · pas de support.
//
//  Roulement : presse à main ferme sur 4 mm de profondeur, sans jeu.
//  Reporter delta -> params.scad fit_press.
//
//  Tige : coulisse sans point dur. Reporter (delta + 0.35) -> fit_slide.
// ============================================================

include <lib.scad>

deltas = [-0.05, 0.00, 0.05, 0.10, 0.15];

// Enveloppe minimale : 5 colonnes espacées de 24 mm (parois ~2 mm).
coupon_x = 118;
coupon_y = 46;
coupon_z = 6;

bearing_test_depth = 4;   // 4 mm suffisent pour juger l'ajustement OD
bearing_row_y = 33;
shaft_row_y = 9;
index_row_y = 17;

col_pitch = 24;
col_x0 = 13;

module test_fits() {
    difference() {
        cube([coupon_x, coupon_y, coupon_z]);

        for (i = [0:4]) {
            cx = col_x0 + col_pitch * i;

            // Logement roulement : borgne, ouvert vers le HAUT (4 mm seulement).
            translate([cx, bearing_row_y, coupon_z - bearing_test_depth])
                cylinder(d = bearing_od + deltas[i], h = bearing_test_depth + 0.1,
                         $fn = 48);
            // Expulsion : Ø9 suffit à pousser le roulement (608 ID = 8).
            translate([cx, bearing_row_y, -0.1])
                cylinder(d = 9, h = coupon_z, $fn = 48);

            // Alésage tige : traversant.
            translate([cx, shaft_row_y, -0.1])
                cylinder(d = shaft_d + deltas[i] + 0.35, h = coupon_z + 0.2,
                         $fn = 48);

            // Index : i+1 encoches fines (moins de parcours buse).
            for (k = [0:i])
                translate([cx - 5 + k * 2.5, index_row_y, coupon_z - 1.0])
                    cube([1.2, 3.5, 1.1]);
        }
    }
}

test_fits();
