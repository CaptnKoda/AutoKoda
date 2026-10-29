import os
import bpy # type: ignore

addon_dir = os.path.dirname(__file__)

DEFAULT_SHADERS = os.path.join(addon_dir, "res", "Shaders.blend")
GARMENT_HUE_SUBPATH = os.path.join("art", "dynamic", "garmenthue")

# Module name of the external swtor_io_tools addon that the JBA and
# material-by-name bridges call into.
EXTERNAL_SWTOR_IO_ADDON_MODULE = "swtor_io_tools"

# Body types substituted for '[bt]' in model paths by the ipp importer.
BODY_TYPES = ("bma", "bmn", "bmf", "bms", "bfa", "bfn", "bfb", "bfs")
DEFAULT_BODY_TYPE = "bmn"

KODA_NODE_NAMES = {
    "EYE"       : "CaptnKoda SWTOR - Eye Shader",
    "GARMENT"   : "CaptnKoda SWTOR - Garment Shader",
    "HAIRC"     : "CaptnKoda SWTOR - HairC Shader",
    "SKINB"     : "CaptnKoda SWTOR - SkinB Shader",
    "UBER"      : "CaptnKoda SWTOR - Uber Shader",
    "UBERHUEABLE": "CaptnKoda SWTOR - UberHueable Shader",
    "ANIMATEDUV": "CaptnKodaAndC3PO SWTOR - AnimatedUV Shader"
}

# swtor_io_tools' native shader groups.
HERO_ENGINE_NODE_NAMES = {
    "EYE"        : "HeroEngine SWTOR - Eye Shader",
    "GARMENT"    : "HeroEngine SWTOR - Garment Shader",
    "HAIRC"      : "HeroEngine SWTOR - HairC Shader",
    "SKINB"      : "HeroEngine SWTOR - SkinB Shader",
    "UBER"       : "HeroEngine SWTOR - Uber Shader",
    "UBERHUEABLE": "HeroEngine SWTOR - UberHueable Shader",
    "ANIMATEDUV": "HeroEngine SWTOR - AnimatedUV Shader"
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
        "master_name": KODA_NODE_NAMES["SKINB"],
        "override_suffix": "Skin Override"
    },
    {
        "master_name": KODA_NODE_NAMES["GARMENT"],
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

# Folder names to prune entirely from the Animations panel's recursive
# .jba folder scan (case-insensitive), wherever they appear in the tree.
IGNORED_JBA_FOLDER_NAMES = {"placeable"}