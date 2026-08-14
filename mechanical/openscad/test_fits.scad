// ============================================================
//  00 — Coupon de calibration des ajustements
//
//  À IMPRIMER EN PREMIER, avant toute autre pièce.
//  Géométrie compacte (~132 × 44 × 8 mm) avec marges calculées :
//  les perçages ne débordent plus du plateau (bug v2 : coupon_x = 118).
//
//  Cinq paires d'essais, repérées par 1 à 5 encoches gravées :
//
//    index  |  1      2      3      4      5
//    ----------------------------------------------
//    delta  | -0.05   0.00  +0.05  +0.10  +0.15
//    ----------------------------------------------
//    logement 608ZZ (borgne 5 mm — suffisant pour juger la presse)
//           | 21.95  22.00  22.05  22.10  22.15
//    ----------------------------------------------
//    alésage tige Ø8 (traversant)
//           |  8.30   8.35   8.40   8.45   8.50
//
//  Impression rapide (voir docs/printing.md) :
//    couche 0,28 mm · 2 périmètres · 10 % remplissage · pas de support.
//
//  Roulement : presse à main ferme sur 5 mm de profondeur, sans jeu.
//  Reporter delta -> params.scad fit_press.
//
//  Tige : coulisse sans point dur. Reporter (delta + 0.35) -> fit_slide.
// ============================================================

include <lib.scad>

deltas = [-0.05, 0.00, 0.05, 0.10, 0.15];

edge_margin = 3;          // marge mini entre un perçage et le bord
col_pitch = 26;           // pas serré mais sans empiètement (26 - 22,15 ≈ 3,9 mm)
col_x0 = edge_margin + bearing_od / 2 + 0.15;   // pire cas : delta +0,15

coupon_x = col_x0 + col_pitch * 4 + bearing_od / 2 + 0.15 + edge_margin;
coupon_y = 44;
coupon_z = 8;

bearing_test_depth = 5;   // 5 mm : compromis vitesse / profondeur utile
bearing_row_y = coupon_y - edge_margin - bearing_od / 2 - 0.15;
shaft_row_y = edge_margin + shaft_d / 2 + 0.35 + 0.15;
index_row_y = (bearing_row_y + shaft_row_y) / 2;

module test_fits() {
    difference() {
        cube([coupon_x, coupon_y, coupon_z]);

        for (i = [0:4]) {
            cx = col_x0 + col_pitch * i;

            // Logement roulement : borgne, ouvert vers le HAUT (5 mm).
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
