"""Bridge into the external swtor_io_tools addon's material-by-name
pipeline (ops/process_materials.py's _build_named_material()).

Used as the first stage of Auto Crunch: rebuilds each selected object's
materials into real native HeroEngine (Atroxa Shaders) materials, in
place, purely by matching their current Blender name against a real
.mat file on disk -- before conversion.py hands off to the Koda
shaders. Replaces the old bpy.ops.zgswtor.process_named_mats /
customize_swtor_shaders calls, which came from a different external
addon (zg_swtor_tools).

_build_named_material() is a leading-underscore ("private") function
in swtor_io_tools, not a stable public API -- if a future swtor_io_tools
update renames/moves it, this bridge is the only place that needs
updating.
"""

from .config import EXTERNAL_SWTOR_IO_ADDON_MODULE
from .prefs import is_addon_enabled


def build_named_materials_for_objects(objects):
    """For each mesh object in `objects`, (re)builds every material slot's
    native HeroEngine shader in place by looking its current Blender name
    up against swtor_io_tools' .mat files. Deduplicates by material name
    across the whole batch (a material shared across two selected objects
    is only built once), mirroring swtor_io_tools' own
    SWTOR_OT_apply_materials_by_name_selected precedent.

    Each material's build is called with a representative object name
    (whichever object we first encounter it on), matching
    _build_named_material()'s `object_name` param, which it only uses
    for SkinB's head Invert Alpha auto-detect.

    Returns (built_count, error_messages). Never raises -- failures for
    individual materials are collected into error_messages instead, so
    one bad material doesn't stop the rest of the batch.
    """
    if not is_addon_enabled(EXTERNAL_SWTOR_IO_ADDON_MODULE):
        return 0, [f"'{EXTERNAL_SWTOR_IO_ADDON_MODULE}' addon is not installed/enabled"]

    try:
        from swtor_io_tools.ops.process_materials import _build_named_material #type: ignore
    except Exception as e:
        return 0, [f"Could not import swtor_io_tools' material pipeline: {e}"]

    seen = set()
    built = 0
    errors = []

    for obj in objects:
        if not obj or obj.type != 'MESH':
            continue

        for slot in obj.material_slots:
            mat = slot.material
            if mat is None or mat.name in seen:
                continue
            seen.add(mat.name)

            try:
                _, result = _build_named_material(mat.name, obj.name)
            except Exception as e:
                errors.append(f"'{mat.name}': {e}")
                continue

            if result.status == "built":
                built += 1
            elif result.status == "error":
                errors.append(f"'{mat.name}': {result.detail}")
            elif result.status == "not_found":
                print(f"[Auto Koda] No matching .mat file found for '{mat.name}'")
            elif result.status == "unbuilt_type":
                print(
                    f"[Auto Koda] '{mat.name}' is a recognized but "
                    f"not-yet-supported shader type ({result.detail})"
                )
            # "skipped" (already built / skip-listed name): nothing to log

    return built, errors
# Example: build_named_materials_for_objects([body, head]) -> (5, ["'mat_cape': missing diffuse texture"])


# swtor_io_tools' own preference name -> ImportGR2 operator property,
# mirroring what ImportGR2.invoke() seeds from its preferences.
_GR2_PREF_TO_OPERATOR_PROP = {
    "gr2_import_collision"               : "import_collision",
    "gr2_name_as_filename"               : "name_as_filename",
    "gr2_apply_axis_conversion"          : "apply_axis_conversion",
    "gr2_scale_object"                   : "scale_object",
    "gr2_scale_factor"                   : "scale_factor",
    "gr2_blender_friendly_skeleton"      : "blender_friendly_skeleton",
    "gr2_apply_materials_by_name_default": "apply_materials_by_name",
}


def import_gr2_files(context, filepaths):
    """Imports `filepaths` through swtor_io_tools' ImportGR2 operator
    (import_mesh.gr2), using that addon's own GR2 import preferences.

    Returns (imported_objects, error_message). error_message is None on
    success. Never raises.
    """
    if not is_addon_enabled(EXTERNAL_SWTOR_IO_ADDON_MODULE):
        return [], f"'{EXTERNAL_SWTOR_IO_ADDON_MODULE}' addon is not installed/enabled"

    import os
    import bpy  # type: ignore

    io_prefs = context.preferences.addons[EXTERNAL_SWTOR_IO_ADDON_MODULE].preferences
    settings = {
        op_prop: getattr(io_prefs, pref)
        for pref, op_prop in _GR2_PREF_TO_OPERATOR_PROP.items()
        if hasattr(io_prefs, pref)
    }

    # ImportGR2 takes one directory + file names per call
    by_directory = {}
    for path in filepaths:
        by_directory.setdefault(os.path.dirname(path), []).append(os.path.basename(path))

    objects_before = set(bpy.data.objects)

    for directory, names in by_directory.items():
        try:
            result = bpy.ops.import_mesh.gr2(
                'EXEC_DEFAULT',
                directory=directory,
                files=[{"name": name} for name in names],
                **settings,
            )
        except Exception as e:
            return [], f"GR2 import failed: {e}"

        if 'FINISHED' not in result:
            return [], f"GR2 import cancelled for {', '.join(names)} (see console)"

    return [o for o in bpy.data.objects if o not in objects_before], None
# Example: import_gr2_files(context, [".../chest_tight_bmn_archetype.gr2"]) -> ([bpy.data.objects["chest_tight_bmn_archetype"]], None)
