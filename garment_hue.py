import os
import bpy #type: ignore
from . import config
from .prefs import get_resources_folder_path
from .list_utils import list_files, existing_file_in, rebuild_name_collection, active_item_name
from .garment_hue_xml import parse_representative_color, parse_garment_hue_file
import colorsys

DEFAULT_SWATCH_COLOR = (0.5, 0.5, 0.5, 1.0)


def color_sort_key(color):
    """Converts an RGBA color to an (hue, -saturation, -value) sort key so
    that similar hues cluster together, with grays/darks grouping near each
    other rather than scattering randomly (since hue is meaningless at
    low saturation/value)."""
    h, s, v = colorsys.rgb_to_hsv(color[0], color[1], color[2])
    return (h, -s, -v)
# Example: color_sort_key((0.8, 0.2, 0.2, 1.0)) -> (0.0, -0.75, -0.8)


class Auto_Koda_GarmentHueItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty() #type: ignore
    color: bpy.props.FloatVectorProperty( #type: ignore
        subtype='COLOR',
        size=4,
        default=DEFAULT_SWATCH_COLOR,
        min=0.0,
        max=1.0,
    )


def get_garment_hue_folder():
    """Returns the absolute garmenthue folder inside the configured
    resources folder, or None if the resources folder isn't set."""
    resources_path = get_resources_folder_path()
    if not resources_path:
        return None
    return os.path.join(resources_path, config.GARMENT_HUE_SUBPATH)
# Example: get_garment_hue_folder() -> "/home/koda/SWTOR/resources/art/dynamic/garmenthue"


def refresh_garment_hue_collection(scene):
    """Rebuilds scene.auto_koda_garment_hue_files, including each file's
    representative color for the UIList swatch. Always fully rebuilds -
    the previous 'skip if names unchanged' optimization caused stale
    colors to persist on outdated collection items saved into older
    .blend files (e.g. from before the color field existed)."""
    folder = get_garment_hue_folder()
    files = list_files(folder, label="Garment hue folder")

    rebuild_name_collection(scene.auto_koda_garment_hue_files, files)
    for item in scene.auto_koda_garment_hue_files:
        color = parse_representative_color(os.path.join(folder, item.name))
        item.color = color or DEFAULT_SWATCH_COLOR


def get_selected_filename(scene):
    """Returns the filename of the currently active garment hue list item,
    or None if nothing is selected."""
    return active_item_name(scene.auto_koda_garment_hue_files, scene.auto_koda_garment_hue_index)
# Example: get_selected_filename(scene) -> "garmenthue_red_light.xml"


def load_garment_hue_values(filename):
    """Parses `filename` from the garmenthue folder into palette values.
    Returns None if the folder isn't configured or the file can't be read."""
    filepath = existing_file_in(get_garment_hue_folder(), filename, "Garment hue file")
    if not filepath:
        return None
    return parse_garment_hue_file(filepath)
# Example: load_garment_hue_values("garmenthue_red_light.xml") -> {"hue": 0.2802, "saturation": 0.58, ...}
