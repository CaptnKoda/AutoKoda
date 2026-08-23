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
    "UBERHUEABLE": "CaptnKoda SWTOR - UberHueable Shader",
    #"ANIMATEDUV": "CaptnKodaAndC3PO SWTOR - AnimatedUV Shader"
}

ATROXA_NODE_NAMES = {
    "EYE"        : "Atroxa SWTOR - Eye Shader",
    "GARMENT"    : "Atroxa SWTOR - Garment Shader",
    "HAIRC"      : "Atroxa SWTOR - HairC Shader",
    "SKINB"      : "Atroxa SWTOR - SkinB Shader",
    "UBER"       : "Atroxa SWTOR - Uber Shader",
    "UBERHUEABLE": "Atroxa SWTOR - UberHueable Shader",
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