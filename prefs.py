import bpy #type: ignore
import os
from . import config

# Module name of the other addon that also exposes a SWTOR resources folder
# preference, and the property name it stores the path under.
EXTERNAL_RESOURCES_ADDON_MODULE = "zg_swtor_tools"
EXTERNAL_RESOURCES_ADDON_PROPERTY = "swtor_resources_folderpath"


def get_shaders_blend_path():
    try:
        prefs = bpy.context.preferences.addons[__package__].preferences
        override_path = getattr(prefs, "shadersPath", "").strip()
        if override_path and override_path.lower().endswith(".blend"):
            return override_path
    except Exception as e:
        print(f"Could not retrieve shaders path from preferences: {e}")

    return config.DEFAULT_SHADERS


def _get_external_resources_path():
    """Attempts to read the resources folder path from zg_swtor_tools, if
    it's installed and enabled. Returns None if unavailable for any reason."""
    try:
        external_addon = bpy.context.preferences.addons.get(EXTERNAL_RESOURCES_ADDON_MODULE)
        if not external_addon:
            return None

        path = getattr(external_addon.preferences, EXTERNAL_RESOURCES_ADDON_PROPERTY, "")
        path = (path or "").strip()
        if not path:
            return None

        return path
    except Exception as e:
        print(f"[Auto Koda] Could not read external resources path: {e}")
        return None


def get_resources_folder_path():
    """Returns the TOR resources extraction folder to use, preferring the
    value set in zg_swtor_tools (if installed and set), and falling back
    to this addon's own resourcesPath preference."""
    path = _get_external_resources_path()
    source = "zg_swtor_tools"

    if not path:
        try:
            prefs = bpy.context.preferences.addons[__package__].preferences
            path = getattr(prefs, "resourcesPath", "").strip()
            source = "Auto Koda preferences"
        except Exception as e:
            print(f"[Auto Koda] Could not retrieve resources path from preferences: {e}")
            return None

    if not path:
        return None

    path = bpy.path.abspath(path)

    if not os.path.isdir(path):
        print(f"[Auto Koda] Configured resources folder ({source}) does not exist: {path}")
        return None

    return path