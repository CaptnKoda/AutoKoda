import bpy #type: ignore
import os
from . import config

# Module name of the other addon that also exposes a SWTOR resources folder
# preference, and the property name it stores the path under.
EXTERNAL_RESOURCES_ADDON_MODULE = "zg_swtor_tools"
EXTERNAL_RESOURCES_ADDON_PROPERTY = "swtor_resources_folderpath"


def is_addon_enabled(module_name):
    """True if the addon with the given module name is installed and enabled."""
    return module_name in bpy.context.preferences.addons
# Example: is_addon_enabled("swtor_io_tools") -> True


def _get_pref_string(prop_name, label):
    """Reads a stripped string preference from this addon's preferences.
    Returns None if the preferences can't be read at all, or "" if unset."""
    try:
        prefs = bpy.context.preferences.addons[__package__].preferences
        return getattr(prefs, prop_name, "").strip()
    except Exception as e:
        print(f"[Auto Koda] Could not retrieve {label} from preferences: {e}")
        return None
# Example: _get_pref_string("animRootPath", "anim root path") -> "//../SWTOR/resources/anim"


def _existing_dir(path, label):
    """Resolves a (possibly blend-relative) folder path to an absolute
    one, or returns None if it's empty or doesn't exist on disk."""
    if not path:
        return None

    path = bpy.path.abspath(path)

    if not os.path.isdir(path):
        print(f"[Auto Koda] Configured {label} does not exist: {path}")
        return None

    return path
# Example: _existing_dir("//../SWTOR/resources", "resources folder") -> "/home/koda/SWTOR/resources"


def get_shaders_blend_path():
    override_path = _get_pref_string("shadersPath", "shaders path")
    if override_path and override_path.lower().endswith(".blend"):
        return override_path

    return config.DEFAULT_SHADERS
# Example: get_shaders_blend_path() -> "/home/koda/.config/blender/extensions/user_default/autokoda/res/Shaders.blend"


def _get_external_resources_path():
    """Attempts to read the resources folder path from zg_swtor_tools, if
    it's installed and enabled. Returns None if unavailable for any reason."""
    try:
        external_addon = bpy.context.preferences.addons.get(EXTERNAL_RESOURCES_ADDON_MODULE)
        if not external_addon:
            return None

        path = getattr(external_addon.preferences, EXTERNAL_RESOURCES_ADDON_PROPERTY, "")
        return (path or "").strip() or None
    except Exception as e:
        print(f"[Auto Koda] Could not read external resources path: {e}")
        return None
# Example: _get_external_resources_path() -> "/home/koda/SWTOR/resources"


def get_resources_folder_path():
    """Returns the TOR resources extraction folder to use, preferring the
    value set in zg_swtor_tools (if installed and set), and falling back
    to this addon's own resourcesPath preference."""
    path = _get_external_resources_path()
    source = "zg_swtor_tools"

    if not path:
        path = _get_pref_string("resourcesPath", "resources path")
        source = "Auto Koda preferences"

    return _existing_dir(path, f"resources folder ({source})")
# Example: get_resources_folder_path() -> "/home/koda/SWTOR/resources"


def get_anim_root_path():
    """Returns the configured 'anim' root folder for the Animations
    panel, or None if unset/invalid."""
    return _existing_dir(_get_pref_string("animRootPath", "anim root path"), "anim root folder")
# Example: get_anim_root_path() -> "/home/koda/SWTOR/resources/anim"
