// ============================================================
//  Vues d'assemblage par étape (docs/assembly.md)
//
//  Usage :
//    openscad -D step=3 -o /tmp/step.stl assembly_steps.scad
//
//  step = 1 … 11  →  montage mécanique / câblage
// ============================================================

include <lib.scad>

use <base_plate.scad>
use <bearing_tower.scad>
use <lidar_cradle.scad>
use <electronics_box.scad>

step = 1;   // surchargé en ligne de commande : -D step=N

module ghost_nema17() {
    color("#404448") {
        translate([-nema_body / 2, -nema_body / 2, 0]) cube([nema_body, nema_body, nema_len]);
        translate([0, 0, nema_len]) cylinder(d = nema_boss_d, h = nema_boss_h);
        translate([0, 0, nema_len + nema_boss_h]) cylinder(d = nema_shaft_d, h = nema_shaft_l);
    }
}

module ghost_bearing() {
    color("#9aa0a6")
        difference() {
            cylinder(d = bearing_od, h = bearing_w);
            translate([0, 0, -0.5]) cylinder(d = bearing_id, h = bearing_w + 1);
        }
}

module ghost_coupler() {
    color("#c0392b") cylinder(d = coupler_d, h = coupler_l);
}

module ghost_shaft() {
    color("#d8dce0") cylinder(d = shaft_d, h = shaft_len);
}

// Ghost des trous de fixation (validation cotes datasheet § 5.1)
module ghost_lidar_holes() {
    color("#e74c3c", 0.35)
        for (y = [-1, 1])
            translate([plate_x, y * lidar_hole_y, optical_z - lidar_h / 2 + lidar_side_hole_z])
                rotate([0, 90, 0]) cylinder(d = lidar_screw_d, h = 8, center = true);
    color("#e74c3c", 0.35)
        translate([plate_x, 0, optical_z - lidar_h / 2 + lidar_top_hole_z])
            rotate([0, 90, 0]) cylinder(d = lidar_screw_d, h = 8, center = true);
    color("#f39c12", 0.25)
        translate([plate_front - 1, -lidar_cable_w / 2, optical_z - lidar_h / 2 + lidar_cable_z - lidar_cable_h / 2])
            cube([lidar_thk + 5, lidar_cable_w, lidar_cable_h]);
}

module ghost_lidar() {
    color("#2b2f33")
        translate([plate_x, -lidar_w / 2, optical_z - lidar_h / 2])
            cube([lidar_thk, lidar_w, lidar_h]);
    color("#1a1d20")
        translate([-1.5, 0, optical_z]) rotate([0, 90, 0]) cylinder(d = 30, h = 3);
}

// Câble LiDAR simplifié (hélice le long de la colonne)
module ghost_lidar_cable() {
    color("#f39c12")
        for (i = [0:24])
            translate([14 * cos(i * 30), 14 * sin(i * 30), 40 + i * 5.5])
                rotate([0, 90, i * 30]) cylinder(d = 4, h = 6, center = true);
}

// Étape 1 — tige recoupée 115 mm
module step01() {
    rotate([0, 90, 0]) translate([0, 0, -shaft_len / 2]) ghost_shaft();
}

// Étape 2 — insert trépied (plateau à l'envers, bossage visible)
module step02() {
    rotate([180, 0, 0])
        translate([0, 0, -plate_t])
            color("#4a90d9") base_plate();
}

// Étape 3 — moteur vissé sous le plateau
module step03() {
    rotate([180, 0, 0]) {
        translate([0, 0, -plate_t]) color("#4a90d9") base_plate();
        translate([0, 0, -plate_t - nema_len]) ghost_nema17();
    }
}

// Étape 4 — roulements dans la colonne (seule)
module step04() {
    color("#5aa469") bearing_tower();
    translate([0, 0, bearing_lo_z]) ghost_bearing();
    translate([0, 0, bearing_hi_z]) ghost_bearing();
}

// Étape 5 — accouplement sur l'arbre moteur (plateau + moteur + coupleur)
module step05() {
    translate([0, 0, -plate_t]) color("#4a90d9") base_plate();
    ghost_nema17();
    translate([0, 0, 52]) ghost_coupler();
}

// Étape 6 — colonne fixée sur le plateau
module step06() {
    translate([0, 0, -plate_t]) color("#4a90d9") base_plate();
    color("#5aa469") bearing_tower();
    ghost_nema17();
}

// Étape 7 — tige + serrage accouplement
module step07() {
    translate([0, 0, -plate_t]) color("#4a90d9") base_plate();
    color("#5aa469") bearing_tower();
    ghost_nema17();
    translate([0, 0, 52]) ghost_coupler();
    translate([0, 0, 65]) ghost_shaft();
    translate([0, 0, bearing_lo_z]) ghost_bearing();
    translate([0, 0, bearing_hi_z]) ghost_bearing();
}

// Étape 8 — LD19 sur le berceau
module step08() {
    translate([0, 0, hub_z0]) {
        color("#e8a33d") lidar_cradle();
        ghost_lidar();
        ghost_lidar_holes();
    }
}

// Étape 9 — berceau sur la tige (tête tournante)
module step09() {
    translate([0, 0, -plate_t]) color("#4a90d9") base_plate();
    color("#5aa469") bearing_tower();
    translate([0, 0, 65]) ghost_shaft();
    translate([0, 0, bearing_lo_z]) ghost_bearing();
    translate([0, 0, bearing_hi_z]) ghost_bearing();
    translate([0, 0, hub_z0]) {
        color("#e8a33d") lidar_cradle();
        ghost_lidar();
    }
}

// Étape 10 — boîtier électronique
module step10() {
    color("#9b6bc4") electronics_box();
}

// Étape 11 — câble LiDAR + assemblage complet
module step11() {
    translate([0, 0, -plate_t]) color("#4a90d9") base_plate();
    color("#5aa469") bearing_tower();
    translate([0, 0, 65]) ghost_shaft();
    translate([0, 0, bearing_lo_z]) ghost_bearing();
    translate([0, 0, bearing_hi_z]) ghost_bearing();
    translate([0, 0, hub_z0]) {
        color("#e8a33d") lidar_cradle();
        ghost_lidar();
    }
    ghost_lidar_cable();
    translate([0, 0, -plate_t - box_iz / 2 - 8])
        rotate([0, 0, 45])
            color("#9b6bc4") electronics_box();
}

module dispatch() {
    if (step == 1) step01();
    else if (step == 2) step02();
    else if (step == 3) step03();
    else if (step == 4) step04();
    else if (step == 5) step05();
    else if (step == 6) step06();
    else if (step == 7) step07();
    else if (step == 8) step08();
    else if (step == 9) step09();
    else if (step == 10) step10();
    else if (step == 11) step11();
    else union();  // step inconnu → STL vide (erreur visible)
}

dispatch();
