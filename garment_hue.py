import os
import bpy #type: ignore
from . import config
from .prefs import get_resources_folder_path
import colorsys

def _color_sort_key(color):
    """Converts an RGBA color to an (hue, -saturation, -value) sort key so
    that similar hues cluster together, with grays/darks grouping near each
    other rather than scattering randomly (since hue is meaningless at
    low saturation/value)."""
    r, g, b = color[0], color[1], color[2]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return (h, -s, -v)


class Auto_Koda_GarmentHueItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty() #type: ignore
    color: bpy.props.FloatVectorProperty( #type: ignore
        subtype='COLOR',
        size=4,
        default=(0.5, 0.5, 0.5, 1.0),
        min=0.0,
        max=1.0,
    )


def list_garment_hue_files():
    resources_path = get_resources_folder_path()
    if not resources_path:
        return []

    garment_hue_path = os.path.join(resources_path, config.GARMENT_HUE_SUBPATH)

    if not os.path.isdir(garment_hue_path):
        print(f"[Auto Koda] Garment hue folder not found: {garment_hue_path}")
        return []

    try:
        files = sorted(
            f for f in os.listdir(garment_hue_path)
            if os.path.isfile(os.path.join(garment_hue_path, f))
        )
    except Exception as e:
        print(f"[Auto Koda] Failed to list garment hue folder: {e}")
        return []

    return files


def refresh_garment_hue_collection(scene):
    """Rebuilds scene.auto_koda_garment_hue_files, including each file's
    representative color for the UIList swatch. Always fully rebuilds -
    the previous 'skip if names unchanged' optimization caused stale
    colors to persist on outdated collection items saved into older
    .blend files (e.g. from before the color field existed)."""
    from .garment_hue_xml import parse_representative_color

    files = list_garment_hue_files()
    resources_path = get_resources_folder_path()

    scene.auto_koda_garment_hue_files.clear()
    for f in files:
        item = scene.auto_koda_garment_hue_files.add()
        item.name = f

        color = None
        if resources_path:
            filepath = os.path.join(resources_path, config.GARMENT_HUE_SUBPATH, f)
            color = parse_representative_color(filepath)

        item.color = color if color else (0.5, 0.5, 0.5, 1.0)


def get_selected_filename(scene):
    """Returns the filename of the currently active garment hue list item,
    or None if nothing is selected."""
    idx = scene.auto_koda_garment_hue_index
    items = scene.auto_koda_garment_hue_files
    if 0 <= idx < len(items):
        return items[idx].name
    return None