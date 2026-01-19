import os
addon_dir = os.path.dirname(__file__)

DEFAULT_SHADERS = os.path.join(addon_dir, "res", "Shaders.blend")

KODA_NODE_NAMES = {
    "EYE"       : "CaptnKoda SWTOR - Eye Shader",
    "GARMENT"   : "CaptnKoda SWTOR - Garment Shader",
    "HAIRC"     : "CaptnKoda SWTOR - HairC Shader",
    "SKINB"     : "CaptnKoda SWTOR - SkinB Shader",
    "UBER"      : "CaptnKoda SWTOR - Uber Shader",
    #"ANIMATEDUV": "CaptnKodaAndC3PO SWTOR - AnimatedUV Shader"
}

HERO_GRAVITAS_NODE_NAMES = {
    "EYE"       : "SWTOR - Eye Shader",
    "GARMENT"   : "SWTOR - Garment Shader",
    "HAIRC"     : "SWTOR - HairC Shader",
    "SKINB"     : "SWTOR - SkinB Shader",
    "UBER"      : "SWTOR - Uber Shader",
    #"ANIMATEDUV": "SWTOR - AnimatedUV Shader"
}

HERO_GRAVITAS_TEX_NAMES = { #Key is HeroGravitas image tex node name, value is Koda image tex node name
   "_d DiffuseMap"      : "DiffuseMap",
   "_n RotationMap"     : "RotationMap1",
   "_s GlossMap"        : "GlossMap",
   "_h PaletteMap"      : "PaletteMap",
   "_m PaletteMaskMap"  : "PaletteMaskMap",
   "AgeMap"             : "AgeMap",
   "ComplexionMap"      : "ComplexionMap",
   "FacepaintMap"       : "FacepaintMap",

}