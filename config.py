import os
import bpy # type: ignore

addon_dir = os.path.dirname(__file__)

DEFAULT_SHADERS = os.path.join(addon_dir, "res", "Shaders.blend")
GARMENT_HUE_SUBPATH = os.path.join("art", "dynamic", "garmenthue")

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

HERO_ENGINE_NODE_TYPE = "ShaderNodeHeroEngine"

# Maps the HeroEngine node's `derived` enum value -> the same keys used in
# KODA_NODE_NAMES / HERO_GRAVITAS_NODE_NAMES
HERO_ENGINE_DERIVED_TO_KEY = {
    "UBER"    : "UBER",
    "SKINB"    : "SKINB",
    "HAIRC"    : "HAIRC",
    "EYE"     : "EYE",
    "GARMENT" : "GARMENT",
}

# Maps HeroEngine's custom image-pointer properties -> Koda Image Texture node name
# (values reused from your existing HERO_GRAVITAS_TEX_NAMES targets)
HERO_ENGINE_TEX_FIELDS = {
    "diffuseMap"     : "DiffuseMap",
    "rotationMap"    : "RotationMap1",
    "glossMap"       : "GlossMap",
    "paletteMap"     : "PaletteMap",
    "paletteMaskMap" : "PaletteMaskMap",
    "ageMap"         : "AgeMap",
    "complexionMap"  : "ComplexionMap",
    "facepaintMap"   : "FacepaintMap",
}

# Maps HeroEngine's custom scalar/color properties -> input socket name on
# the corresponding Koda group node. Only properties present in this dict
# get transferred; anything else on the HeroEngine node is ignored.
HERO_ENGINE_PROP_TO_KODA_INPUT = {
    "palette1_hue"               : "Palette1 Hue",
    "palette1_saturation"        : "Palette1 Saturation",
    "palette1_brightness"        : "Palette1 Brightness",
    "palette1_contrast"          : "Palette1 Contrast",
    "palette1_specular"          : "Palette1 Specular",
    "palette1_metallic_specular" : "Palette1 Metallic Specular",
    "palette2_hue"                : "Palette2 Hue",
    "palette2_saturation"         : "Palette2 Saturation",
    "palette2_brightness"         : "Palette2 Brightness",
    "palette2_contrast"           : "Palette2 Contrast",
    "palette2_specular"           : "Palette2 Specular",
    "palette2_metallic_specular"  : "Palette2 Metallic Specular",
    "flush_tone"                  : "Flush Tone",
}


Shader_Pairs = [
    {
        "master_name": "CaptnKoda SWTOR - SkinB Shader",
        "override_suffix": "Skin Override"
    },
    {
        "master_name": "CaptnKoda SWTOR - Garment Shader",
        "override_suffix": "Garment Override"
    },
    # Add more master/override pairs here
]

Allowed_Socket_Types = (
    bpy.types.NodeSocketFloat,
    bpy.types.NodeSocketFloatFactor,
    bpy.types.NodeSocketInt,
    bpy.types.NodeSocketBool,
    bpy.types.NodeSocketVector,
    bpy.types.NodeSocketColor,
)