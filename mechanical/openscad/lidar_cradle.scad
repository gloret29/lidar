// ============================================================
//  03 — Berceau LiDAR
//  Serre sur la tige Ø8 et présente le STL-19P (LDROBOT) COUCHÉ SUR LA
//  TRANCHE, plan de balayage vertical contenant l'axe de rotation.
//  Fixation : 3 oreilles M2,5 (datasheet § 5.1), câble vers le bas.
//
//  Repère local : z = 0 à la base du moyeu (= z 140 en global).
//  Centre optique du LD19 en (0, 0, 65) local.
//
//  Contrainte de non-collision : tout ce qui se trouve en
//  x > plate_x doit rester sous z = 42.7 (dessous du LD19).
//
//  Impression : COUCHÉ, platine à plat sur le plateau
//  (rotate([0, -90, 0])). Supports sous le moyeu uniquement.
// ============================================================

include <lib.scad>

hub_h = hub_z1 - hub_z0;               // 40
optical_local_z = optical_z - hub_z0;  // 65
lidar_bottom = optical_local_z - lidar_h / 2;   // 45.7
clear_z = lidar_bottom - 3;                     // 42.7 : plafond du voile

web_lo = 24;
web_hi = 40;
plate_lo = 32;
plate_hi = 92;
plate_hw = 29;      // demi-largeur platine (58 mm > envergure 54 mm)
plate_back = plate_x - cradle_plate_t;   // -27
plate_front = plate_x;                   // -22 : face de fixation LiDAR

// Perçage M2,5 : traverse platine + rebord (axe X)
module lidar_mount_hole(y, z) {
    translate([plate_back - 2, y, z])
        rotate([0, 90, 0])
            cylinder(d = lidar_screw_d, h = 20);
}

// Passage nappe ZH1.5T : fente traversante platine + rebord, ouverte vers le bas
module lidar_cable_slot() {
    z0 = plate_lo - 1;
    z1 = lidar_bottom + lidar_cable_h;
    x0 = plate_back - 1;
    xh = cradle_plate_t + 8;
    translate([x0, -lidar_cable_w / 2, z0])
        cube([xh, lidar_cable_w, z1 - z0]);
    // arrondi en haut de la fente (visible des deux faces)
    translate([x0, 0, z1])
        rotate([0, 90, 0])
            cylinder(d = lidar_cable_w, h = xh);
}

module lidar_cradle() {
    difference() {
        union() {
            // ---------- Moyeu de serrage sur la tige ----------
            cylinder(d = hub_d, h = hub_h - 10);
            translate([0, 0, hub_h - 10])
                cylinder(d1 = hub_d, d2 = hub_top_d, h = 10);

            // ---------- Oreilles de serrage ----------
            translate([5, -9, 4]) cube([14, 18, 15]);

            // ---------- Secteur de butée (chevauche le moyeu) ----------
            rotate([0, 0, 180])
                difference() {
                    cylinder(d = 48, h = 10);
                    translate([0, 0, -1]) cylinder(d = hub_d - 2, h = 12);
                    rotate([0, 0, 13]) translate([-40, 0, -1]) cube([80, 80, 12]);
                    rotate([0, 0, -13]) translate([-40, -80, -1]) cube([80, 80, 12]);
                }

            // ---------- Deux voiles (de part et d'autre de la fente nappe) ----------
            for (s = [-1, 1]) {
                hull() {
                    translate([-8, s * 6, web_lo]) cube([10, 5, web_hi - web_lo]);
                    translate([plate_back, s * 15 - 3, plate_lo])
                        cube([5, 6, 14]);
                }
            }

            // ---------- Platine de fixation du LiDAR ----------
            translate([plate_back, -plate_hw, plate_lo])
                cube([cradle_plate_t, 2 * plate_hw, plate_hi - plate_lo]);

            // ---------- Rebord de centrage (bloc plein, évidé plus bas) ----------
            translate([plate_x - 1, -(lidar_w / 2 + 2.5), lidar_bottom - 2.5])
                cube([3.5, lidar_w + 5, lidar_h + 5]);

            // ---------- Nervures dorsales (écartées des trous M2,5 à Y ±23,4) ----------
            for (s = [-1, 1])
                translate([plate_back, s * 18 - 2, plate_lo])
                    hull() {
                        cube([0.1, 4, plate_hi - plate_lo]);
                        translate([-13, 0, 0]) cube([0.1, 4, 26]);
                    }
        }

        // ---------- Alésage de la tige ----------
        translate([0, 0, -0.1]) cylinder(d = shaft_d + fit_slide, h = hub_h + 0.2);

        // ---------- Fente du collier ----------
        translate([3, -0.9, -0.1]) cube([22, 1.8, hub_h + 0.2]);

        // ---------- Vis de serrage M3 (axe Y) ----------
        translate([12, 12, 11.5]) rotate([90, 0, 0]) cylinder(d = m3_clear, h = 24);
        translate([12, -9.01, 11.5]) rotate([-90, 0, 0])
            cylinder(d = m3_nut_af / cos(30), h = 3.2, $fn = 6);

        // ---------- Logement STL-19P (évide le rebord, pas la platine) ----------
        translate([plate_x, -lidar_w / 2 - 0.25, lidar_bottom - 0.25])
            cube([5, lidar_w + 0.5, lidar_h + 0.5]);
        lidar_mount_hole(-lidar_hole_y, lidar_bottom + lidar_side_hole_z);
        lidar_mount_hole(lidar_hole_y, lidar_bottom + lidar_side_hole_z);
        lidar_mount_hole(0, lidar_bottom + lidar_top_hole_z);

        // ---------- Passage nappe (fente ouverte en bas, traverse platine + rebord) ----------
        lidar_cable_slot();

        // ---------- Colliers rilsan de sécurité ----------
        for (z = [plate_lo + 8, plate_hi - 9])
            for (y = [-1, 1])
                translate([plate_back - 0.1, y * (plate_hw - 5), z])
                    rotate([0, 90, 0])
                        cube([5, 2.8, cradle_plate_t + 3], center = true);
    }
}

lidar_cradle();
