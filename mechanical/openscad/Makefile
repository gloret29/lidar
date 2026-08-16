# ============================================================
#  Génération des STL et des rendus PNG
#
#  Usage :
#    make            -> tous les STL dans ../stl/
#    make renders    -> aperçus PNG dans ../renders/
#    make clean
#
#  OPENSCAD peut être surchargé :
#    make OPENSCAD=/chemin/vers/openscad
# ============================================================

OPENSCAD ?= openscad
STL_DIR  := ../stl
PNG_DIR  := ../renders

PARTS := test_fits test_lidar_fit base_plate bearing_tower lidar_cradle electronics_box electronics_lid

STLS := $(addprefix $(STL_DIR)/,$(addsuffix .stl,$(PARTS)))
PNGS := $(addprefix $(PNG_DIR)/,$(addsuffix .png,$(PARTS)))

.PHONY: all renders clean

all: $(STLS)

renders: $(PNGS) $(PNG_DIR)/assembly.png

$(STL_DIR)/%.stl: %.scad params.scad lib.scad
	@mkdir -p $(STL_DIR)
	$(OPENSCAD) --export-format=binstl -o $@ $<

$(PNG_DIR)/%.png: %.scad params.scad lib.scad
	@mkdir -p $(PNG_DIR)
	$(OPENSCAD) -o $@ --imgsize=1000,800 --colorscheme=Tomorrow \
		--viewall --autocenter --projection=perspective $<

$(PNG_DIR)/assembly.png: assembly.scad params.scad lib.scad
	@mkdir -p $(PNG_DIR)
	$(OPENSCAD) -o $@ --imgsize=900,1300 --colorscheme=Tomorrow \
		--viewall --autocenter --projection=perspective assembly.scad

clean:
	rm -f $(STL_DIR)/*.stl $(PNG_DIR)/*.png
