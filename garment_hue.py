"""Garment Hue file listing, and the collection-backed searchable field used
by the Utilities panel. Uses prop_search rather than a plain EnumProperty so
the user can type to filter file names."""

import os
import bpy # type: ignore
from . import config
from .prefs import get_resources_folder_path


class Auto_Koda_GarmentHueItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()  #type: ignore


def list_garment_hue_files():
    """Returns a sorted list of filenames found directly inside
    resources/art/dynamic/garmenthue/. Returns an empty list if the
    resources folder isn't configured or the subfolder doesn't exist."""
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
    """Rebuilds scene.auto_koda_garment_hue_files from the current contents
    of the garmenthue folder. Cheap enough to call on every panel draw -
    just a directory listing, no file reads."""
    files = list_garment_hue_files()
    current_names = {item.name for item in scene.auto_koda_garment_hue_files}

    if current_names == set(files):
        return  # already in sync, avoid needless collection churn

    scene.auto_koda_garment_hue_files.clear()
    for f in files:
        item = scene.auto_koda_garment_hue_files.add()
        item.name = f