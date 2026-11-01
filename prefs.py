import logging
import bpy #type: ignore
import os
from . import config

log = logging.getLogger(__name__)

# Module name of the other addon that also exposes a SWTOR resources folder
# preference, and the property name it stores the path under.
EXTERNAL_RESOURCES_ADDON_MODULE = "zg_swtor_tools"
EXTERNAL_RESOURCES_ADDON_PROPERTY = "swtor_resources_folderpath"

# Last problem logged per setting. The panels call these getters on every
# redraw, so a problem is only logged when it first appears or changes.
_last_problems = {}


def _note_problem(key, problem=None, exc_info=False):
    """Logs `problem` unless it's already the current one for `key`.
    Pass problem=None once `key` is healthy again."""
    if _last_problems.get(key) == problem:
        return
    _last_problems[key] = problem
    if problem:
        log.warning(problem, exc_info=exc_info, stacklevel=2)


def is_addon_enabled(module_name):
    """True if the addon with the given module name is installed and enabled."""
    return module_name in bpy.context.preferences.addons
# Example: is_addon_enabled("swtor_io_tools") -> True


def _get_pref_string(prop_name, label):
    """Reads a stripped string preference from this addon's preferences.
    Returns None if the preferences can't be read at all, or "" if unset."""
    try:
        prefs = bpy.context.preferences.addons[__package__].preferences
        value = getattr(prefs, prop_name, "").strip()
    except Exception as e:
        _note_problem(prop_name, f"Could not retrieve {label} from preferences: {type(e).__name__}: {e}", exc_info=True)
        return None
    _note_problem(prop_name)
    return value
# Example: _get_pref_string("animRootPath", "anim root path") -> "//../SWTOR/resources/anim"


def _existing_dir(path, label):
    """Resolves a (possibly blend-relative) folder path to an absolute
    one, or returns None if it's empty or doesn't exist on disk."""
    if not path:
        _note_problem(label, f"{label} is not set")
        return None

    path = bpy.path.abspath(path)

    if not os.path.exists(path):
        _note_problem(label, f"Configured {label} does not exist: {path}")
        return None
    if not os.path.isdir(path):
        _note_problem(label, f"Configured {label} is not a folder: {path}")
        return None
    if not os.access(path, os.R_OK | os.X_OK):
        _note_problem(label, f"Configured {label} exists but isn't readable, its contents will look empty: {path}")
        return path

    _note_problem(label)
    return path
# Example: _existing_dir("//../SWTOR/resources", "resources folder") -> "/home/koda/SWTOR/resources"


def get_shaders_blend_path():
    override_path = _get_pref_string("shadersPath", "shaders path")
    if override_path and override_path.lower().endswith(".blend"):
        _note_problem("shadersPath override")
        return override_path

    if override_path:
        _note_problem("shadersPath override", f"Ignoring Shaders.blend Path '{override_path}': not a .blend file, using the default")
    else:
        _note_problem("shadersPath override")
    return config.DEFAULT_SHADERS
# Example: get_shaders_blend_path() -> "/home/koda/.config/blender/extensions/user_default/autokoda/res/Shaders.blend"


def _get_external_resources_path():
    """Attempts to read the resources folder path from zg_swtor_tools, if
    it's installed and enabled. Returns None if unavailable for any reason."""
    try:
        external_addon = bpy.context.preferences.addons.get(EXTERNAL_RESOURCES_ADDON_MODULE)
        if not external_addon:
            return None

        if not hasattr(external_addon.preferences, EXTERNAL_RESOURCES_ADDON_PROPERTY):
            _note_problem(
                EXTERNAL_RESOURCES_ADDON_PROPERTY,
                f"'{EXTERNAL_RESOURCES_ADDON_MODULE}' is enabled but has no preference "
                f"'{EXTERNAL_RESOURCES_ADDON_PROPERTY}', falling back to Auto Koda's resources path"
            )
            return None

        path = getattr(external_addon.preferences, EXTERNAL_RESOURCES_ADDON_PROPERTY, "")
        _note_problem(EXTERNAL_RESOURCES_ADDON_PROPERTY)
        return (path or "").strip() or None
    except Exception as e:
        _note_problem(EXTERNAL_RESOURCES_ADDON_PROPERTY, f"Could not read external resources path: {type(e).__name__}: {e}", exc_info=True)
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
