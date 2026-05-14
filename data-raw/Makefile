PYTHON := python3
FONTFORGE := fontforge
CONVERTER := convert_to_otf.py
SFD_FILE := ArcadeFont.sfd
OTF_FILE := ArcadeFont.otf

# Default target
.PHONY: all
all: otf

# Generate both SFD and OTF files
.PHONY: otf
otf: $(OTF_FILE)

# Generate only SFD file
.PHONY: sfd
sfd: $(SFD_FILE)

$(OTF_FILE): $(CONVERTER)
	$(PYTHON) $(CONVERTER)

$(SFD_FILE): $(CONVERTER)
	$(PYTHON) -c "from convert_to_otf import generate_sfd_only; generate_sfd_only()"

.PHONY: sfd-to-otf
sfd-to-otf: $(SFD_FILE)
	$(FONTFORGE) -lang=ff -c 'Open("$(SFD_FILE)"); Generate("$(OTF_FILE)")'
