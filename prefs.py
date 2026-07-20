import bpy # type: ignore
from . import config


def get_shaders_blend_path():
    try:
        prefs = bpy.context.preferences.addons[__package__].preferences
        override_path = getattr(prefs, "shadersPath", "").strip()
        if override_path and override_path.lower().endswith(".blend"):
            return override_path
    except Exception as e:
        print(f"Could not retrieve shaders path from preferences: {e}")

    return config.DEFAULT_SHADERS