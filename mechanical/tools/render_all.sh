#!/usr/bin/env bash
# Génère les STL puis les aperçus PNG de toutes les pièces.
#
#   OPENSCAD=/chemin/vers/openscad ./tools/render_all.sh
#
# Les PNG sont produits par tools/stl_preview.py (Python pur), ce qui
# évite d'avoir besoin d'un serveur graphique.

set -euo pipefail

OPENSCAD="${OPENSCAD:-openscad}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCAD="$HERE/openscad"
STL="$HERE/stl"
PNG="$HERE/renders"

mkdir -p "$STL" "$PNG"

# nom:couleur:azimut:élévation
PARTS=(
    "test_fits:8a8f94:35:28"
    "base_plate:4a90d9:35:26"
    "bearing_tower:5aa469:35:16"
    "lidar_cradle:e8a33d:40:18"
    "electronics_box:9b6bc4:35:30"
    "electronics_lid:9b6bc4:35:30"
)

for entry in "${PARTS[@]}"; do
    IFS=: read -r name color azim elev <<< "$entry"
    echo "==> $name"
    "$OPENSCAD" --export-format=binstl -o "$STL/$name.stl" "$SCAD/$name.scad" 2>&1 \
        | grep -Ei 'error|warning' || true
    python3 "$HERE/tools/stl_preview.py" "$STL/$name.stl" "$PNG/$name.png" \
        --color "$color" --azim "$azim" --elev "$elev"
done

# L'assemblage n'est qu'une visualisation : son STL part dans un fichier
# temporaire pour que stl/ ne contienne que des pièces imprimables.
echo "==> assembly"
tmp_asm="$(mktemp -t assembly-XXXXXX.stl)"
trap 'rm -f "$tmp_asm"' EXIT
"$OPENSCAD" --export-format=binstl -D 'show_plane=false' \
    -o "$tmp_asm" "$SCAD/assembly.scad" 2>&1 \
    | grep -Ei 'error|warning' || true
python3 "$HERE/tools/stl_preview.py" "$tmp_asm" "$PNG/assembly.png" \
    --color 6f7c8a --azim 38 --elev 12 --width 700 --height 900

echo "Terminé : $PNG"
