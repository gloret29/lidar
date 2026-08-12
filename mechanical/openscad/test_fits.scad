// ============================================================
//  00 — Coupon de calibration des ajustements
//
//  À IMPRIMER EN PREMIER, avant toute autre pièce.
//
//  Cinq paires d'essais, repérées par 1 à 5 encoches gravées entre
//  les deux rangées :
//
//    index  |  1      2      3      4      5
//    ----------------------------------------------
//    delta  | -0.20  -0.15  -0.10  -0.05   0.00
//    ----------------------------------------------
//    logement 608ZZ (rangée du haut, borgne, 7 mm)
//           | 21.80  21.85  21.90  21.95  22.00
//    ----------------------------------------------
//    alésage tige Ø8 (rangée du bas, traversant)
//           |  8.15   8.20   8.25   8.30   8.35
//
//  Roulement : doit entrer à la presse à main ferme, sans jeu et
//  sans faire blanchir la paroi. Reporter la valeur de delta dans
//  params.scad -> fit_press.
//
//  Tige : doit coulisser sans point dur ni jeu radial. Reporter
//  (delta + 0.35) dans params.scad -> fit_slide.
//
//  Un trou d'expulsion de Ø10 sous chaque logement permet de
//  ressortir le roulement sans l'abîmer.
// ============================================================

include <lib.scad>

deltas = [-0.20, -0.15, -0.10, -0.05, 0.00];

coupon_x = 150;
coupon_y = 62;
coupon_z = 10;

bearing_row_y = 42;
shaft_row_y = 14;
index_row_y = 24;

module test_fits() {
    difference() {
        cube([coupon_x, coupon_y, coupon_z]);

        for (i = [0:4]) {
            cx = 15 + 30 * i;

            // Logement de roulement : borgne, ouvert vers le HAUT.
            translate([cx, bearing_row_y, coupon_z - bearing_w])
                cylinder(d = bearing_od + deltas[i], h = bearing_w + 0.1);
            // Trou d'expulsion
            translate([cx, bearing_row_y, -0.1])
                cylinder(d = 10, h = coupon_z);

            // Alésage de tige : traversant.
            translate([cx, shaft_row_y, -0.1])
                cylinder(d = shaft_d + deltas[i] + 0.35, h = coupon_z + 0.2);

            // Index : i+1 encoches gravées.
            for (k = [0:i])
                translate([cx - 7 + k * 3.5, index_row_y, coupon_z - 1.2])
                    cube([1.8, 5, 1.3]);
        }
    }
}

test_fits();
