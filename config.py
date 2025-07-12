KODA_NODE_NAMES = {
    "EYE"       : "CaptnKoda SWTOR - Eye Shader",
    "GARMENT"   : "CaptnKoda SWTOR - Garment Shader",
    "HAIRC"     : "CaptnKoda SWTOR - HairC Shader",
    "SKINB"     : "CaptnKoda SWTOR - SkinB Shader",
    "UBER"      : "CaptnKoda SWTOR - Uber Shader",
}

HERO_GRAVITAS_NODE_NAMES = {
    "EYE"       : "SWTOR - Eye Shader",
    "GARMENT"   : "SWTOR - Garment Shader",
    "HAIRC"     : "SWTOR - HairC Shader",
    "SKINB"     : "SWTOR - SkinB Shader",
    "UBER"      : "SWTOR - Uber Shader",
}

HERO_TO_KODA_SOCKETS = {
    "_d DiffuseMap Color"     : "DiffuseMap Color",
    "_d DiffuseMap Alpha"     : "DiffuseMap Alpha",

    "_n RotationMap Color"    : "RotationMap1 Color",
    "_n RotationMap Alpha"    : "RotationMap1 Alpha",

    "_s GlossMap Color"       : "GlossMap Color",
    "_s GlossMap Alpha"       : "GlossMap Alpha",

    "_h PaletteMap Color"     : "PaletteMap Color",
    "_h PaletteMap Alpha"     : "PaletteMap Alpha",

    "_m PaletteMaskMap Color" : "PaletteMaskMap Color",
    "_m PaletteMaskMap Alpha" : "PaletteMaskMap Alpha",

    "AgeMap Color"            : "Scar RotationMap Color",
    "AgeMap Alpha"            : "Scar RotationMap Alpha"
}

COMMON_NODE_X = -680

COMMON_NODE_WIDTH = 375
COMMON_NODE_HEIGHT = 300

PRIMARY_LABELS = [
    '_d DiffuseMap',
    '_n RotationMap',
    '_s GlossMap'
]

SECONDARY_LABELS = [
   '_h PaletteMap',
   '_m PaletteMaskMap',
   'AgeMap',
]

TERTIARY_LABELS = [
    'ComplexionMap',
    'FacepaintMap',
    'AgeMapWrinkles',
    'animatedWrinkleMap',
    'animatedWrinkleMask',
    'DirectionMap'
]

PRIMARY_NODE_LOCS = {
   label: (COMMON_NODE_X, COMMON_NODE_HEIGHT * -i)
   for i, label in enumerate(PRIMARY_LABELS)
}

SECONDARY_NODE_LOCS = {
   label: (COMMON_NODE_X,  COMMON_NODE_HEIGHT * -(i + len(PRIMARY_LABELS)))
   for i, label in enumerate(SECONDARY_LABELS)
}

TERTIARY_NODE_LOCS = {
   label: (-1080.0,  COMMON_NODE_HEIGHT * -i)
   for i, label in enumerate(TERTIARY_LABELS)
}