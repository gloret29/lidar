// ============================================================
//  Vue d'assemblage complète (visualisation uniquement)
//
//  Les pièces achetées (moteur, roulements, accouplement, LiDAR)
//  sont représentées par des volumes simplifiés.
//
//  Rendu :
//    openscad -o assembly.png --imgsize=1200,1400 --camera=... assembly.scad
// ============================================================

include <lib.scad>

use <base_plate.scad>
use <bearing_tower.scad>
use <lidar_cradle.scad>

show_ghost = true;   // pièces du commerce
show_plane = true;   // plan de balayage du LiDAR

// ------------------------------------------------------------
//  Volumes simplifiés des composants achetés
// ------------------------------------------------------------
module ghost_nema17() {
    color("#404448") {
        translate([-nema_body / 2, -nema_body / 2, 0]) cube([nema_body, nema_body, nema_len]);
        translate([0, 0, nema_len]) cylinder(d = nema_boss_d, h = nema_boss_h);
        translate([0, 0, nema_len]) cylinder(d = nema_shaft_d, h = nema_shaft_l);
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

module ghost_lidar() {
    // STL-19P couché : face de fixation contre la platine (x = plate_x)
    color("#2b2f33")
        translate([plate_x, -lidar_w / 2, optical_z - lidar_h / 2])
            cube([lidar_thk, lidar_w, lidar_h]);
    // dôme rotatif, centré sur l'axe optique
    color("#1a1d20")
        translate([-1.5, 0, optical_z]) rotate([0, 90, 0]) cylinder(d = 35.3, h = 3);
}

// ------------------------------------------------------------
//  Assemblage
// ------------------------------------------------------------
module assembly() {
    // plateau (z = 0 sur sa face supérieure)
    color("#4a90d9") translate([0, 0, -plate_t]) base_plate();

    // colonne
    color("#5aa469") bearing_tower();

    if (show_ghost) {
        ghost_nema17();
        translate([0, 0, 52]) ghost_coupler();
        translate([0, 0, bearing_lo_z]) ghost_bearing();
        translate([0, 0, bearing_hi_z]) ghost_bearing();
        translate([0, 0, 65]) ghost_shaft();
        ghost_lidar();
    }

    // berceau
    color("#e8a33d") translate([0, 0, hub_z0]) lidar_cradle();

    // plan de balayage (disque vertical dans le plan x = 0)
    if (show_plane)
        color([1, 0.25, 0.25, 0.18])
            translate([0, 0, optical_z]) rotate([0, 90, 0])
                cylinder(d = 260, h = 0.6, center = true);
}

assembly();
