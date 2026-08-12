// ============================================================
//  02 — Colonne à roulements
//  Coiffe le moteur, porte les deux 608ZZ qui définissent l'axe
//  de rotation. C'est la pièce qui détermine la précision angulaire.
//
//  Impression : bride sur le plateau, telle quelle. Pas de support.
//  Réglages conseillés : 5 périmètres, 40 % remplissage.
// ============================================================

include <lib.scad>

module bearing_tower() {
    difference() {
        // ---------- Volume extérieur ----------
        union() {
            cylinder(d = tower_flange_d, h = tower_flange_t);
            translate([0, 0, tower_flange_t])
                cylinder(d1 = tower_base_d, d2 = tower_top_d,
                         h = tower_cone_top_z - tower_flange_t);
            translate([0, 0, tower_cone_top_z])
                cylinder(d = tower_top_d, h = tower_total_h - tower_cone_top_z);
        }

        // ---------- Cavité moteur ----------
        translate([0, 0, -0.1])
            cylinder(d = tower_cavity_d, h = tower_cavity_top_z + 0.1);
        // transition conique vers le col (dégagement accouplement)
        translate([0, 0, tower_cavity_top_z])
            cylinder(d1 = tower_cavity_d, d2 = tower_throat_d,
                     h = tower_throat_z - tower_cavity_top_z);
        // col
        translate([0, 0, tower_throat_z])
            cylinder(d = tower_throat_d, h = bearing_lo_z - tower_throat_z + 0.01);

        // ---------- Logements de roulements ----------
        // roulement bas (ajustement serré)
        translate([0, 0, bearing_lo_z])
            cylinder(d = bearing_od + fit_press, h = bearing_w);
        // dégagement entre roulements
        translate([0, 0, bearing_lo_z + bearing_w])
            cylinder(d = bearing_relief_d, h = bearing_hi_z - bearing_lo_z - bearing_w);
        // roulement haut (ajustement serré)
        translate([0, 0, bearing_hi_z])
            cylinder(d = bearing_od + fit_press, h = bearing_w);
        // dégagement au-dessus du roulement haut
        translate([0, 0, bearing_hi_z + bearing_w])
            cylinder(d = bearing_relief_d,
                     h = tower_total_h - bearing_hi_z - bearing_w + 0.1);

        // ---------- Fixation sur le plateau ----------
        for (i = [0:3])
            rotate([0, 0, 90 * i])
                translate([tower_bolt_circle / 2, 0, 0])
                    m3_counterbore(tower_flange_t, m3_head_h);

        // ---------- Accès aux vis de l'accouplement ----------
        // Indispensable : l'accouplement se trouve à z 52..77, à
        // l'intérieur de la colonne, une fois celle-ci en place.
        for (i = [0:2])
            rotate([0, 0, 120 * i])
                translate([0, 0, 64]) hex_window(across = 19, depth = 200);

        // ---------- Sortie du câble moteur ----------
        rotate([0, 0, 180])
            translate([0, 0, 22]) hex_window(across = 22, depth = 200);

        // ---------- Encoche de bride : passage des câbles sous la colonne ----------
        rotate([0, 0, 180])
            translate([tower_cavity_d / 2 - 2, -4.5, -0.1])
                cube([30, 9, tower_flange_t + 0.2]);

        // ---------- Aération de la cavité moteur ----------
        for (i = [0:2])
            rotate([0, 0, 60 + 120 * i])
                translate([0, 0, 24]) hex_window(across = 13, depth = 200);

        // ---------- Repère d'azimut zéro ----------
        translate([tower_flange_d / 2 - 7, -1.2, tower_flange_t - 1])
            cube([9, 2.4, 1.2]);
    }

    // ---------- Butée mécanique de référence (homing StallGuard) ----------
    // Contrefort fixe contre lequel vient buter le secteur du berceau.
    // Définit le zéro d'azimut absolu, sans capteur.
    rotate([0, 0, 180])
        difference() {
            union() {
                // contrefort triangulaire adossé au col
                hull() {
                    translate([8, -4.5, 74]) cube([10, 9, 10]);
                    translate([13, -4.5, 100]) cube([11, 9, 52]);
                }
                // raccord au cône
                hull() {
                    translate([8, -4.5, 74]) cube([10, 9, 10]);
                    translate([20, -4.5, 74]) cube([8, 9, 6]);
                }
            }
            // ne pas empiéter sur l'alésage des roulements
            cylinder(d = tower_top_d - 0.01, h = 200);
        }
}

bearing_tower();
