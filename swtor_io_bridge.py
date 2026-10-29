"""Bridge into the external swtor_io_tools addon: its material-by-name
pipeline, its GR2 importer and its JBA animation importer.

Several entry points used here (_build_named_material(), load()) are not
a stable public API -- if a future swtor_io_tools update renames/moves
them, this bridge is the only place that needs updating.
"""

import os
import bpy  # type: ignore
from .config import EXTERNAL_SWTOR_IO_ADDON_MODULE
from .prefs import is_addon_enabled


def _addon_missing_error():
    """Returns an error message if swtor_io_tools isn't enabled, else None."""
    if is_addon_enabled(EXTERNAL_SWTOR_IO_ADDON_MODULE):
        return None
    return f"'{EXTERNAL_SWTOR_IO_ADDON_MODULE}' addon is not installed/enabled"
# Example: _addon_missing_error() -> None


def _unique_materials(objects):
    """Yields (material, object) once per distinct material name across
    `objects`, paired with the first object it was found on."""
    seen = set()
    for obj in objects:
        for slot in obj.material_slots:
            mat = slot.material
            if mat is None or mat.name in seen:
                continue
            seen.add(mat.name)
            yield mat, obj
# Example: list(_unique_materials([body, head])) -> [(<Material "skin">, body), (<Material "eye">, head)]


def _log_build_result(mat_name, result, errors):
    """Records one _build_named_material() result. Returns True if the
    material was built; appends to `errors` on failure."""
    if result.status == "built":
        return True
    if result.status == "error":
        errors.append(f"'{mat_name}': {result.detail}")
    elif result.status == "not_found":
        print(f"[Auto Koda] No matching .mat file found for '{mat_name}'")
    elif result.status == "unbuilt_type":
        print(f"[Auto Koda] '{mat_name}' is a recognized but not-yet-supported shader type ({result.detail})")
    # "skipped" (already built / skip-listed name): nothing to log
    return False


def build_named_materials_for_objects(objects):
    """Used as the first stage of Auto Crunch: (re)builds every material
    slot's native HeroEngine shader in place by looking its
    current Blender name up against swtor_io_tools' .mat files, before
    conversion.py hands off to the Koda shaders. A material shared across
    several objects is only built once, called with the first object's
    name (which _build_named_material() only uses for SkinB's head Invert
    Alpha auto-detect).

    Returns (built_count, error_messages). Never raises -- failures for
    individual materials are collected into error_messages instead, so
    one bad material doesn't stop the rest of the batch.
    """
    error = _addon_missing_error()
    if error:
        return 0, [error]

    try:
        from swtor_io_tools.ops.process_materials import _build_named_material #type: ignore
    except Exception as e:
        return 0, [f"Could not import swtor_io_tools' material pipeline: {e}"]

    built = 0
    errors = []

    # Names are taken up front: a successful build user_remap()s the old
    # material onto a new one and removes it, leaving `mat` invalid.
    targets = [(mat.name, obj.name) for mat, obj in _unique_materials(objects)]

    for mat_name, obj_name in targets:
        try:
            _, result = _build_named_material(mat_name, obj_name)
        except Exception as e:
            errors.append(f"'{mat_name}': {e}")
            continue
        built += _log_build_result(mat_name, result, errors)

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


def _gr2_import_settings(context):
    """ImportGR2 operator kwargs taken from swtor_io_tools' preferences."""
    io_prefs = context.preferences.addons[EXTERNAL_SWTOR_IO_ADDON_MODULE].preferences
    return {
        op_prop: getattr(io_prefs, pref)
        for pref, op_prop in _GR2_PREF_TO_OPERATOR_PROP.items()
        if hasattr(io_prefs, pref)
    }
# Example: _gr2_import_settings(context) -> {"import_collision": False, "scale_factor": 1.0, ...}


def _group_by_directory(filepaths):
    by_directory = {}
    for path in filepaths:
        by_directory.setdefault(os.path.dirname(path), []).append(os.path.basename(path))
    return by_directory
# Example: _group_by_directory(["/a/x.gr2", "/a/y.gr2"]) -> {"/a": ["x.gr2", "y.gr2"]}


def import_gr2_files(context, filepaths):
    """Imports `filepaths` through swtor_io_tools' ImportGR2 operator
    (import_mesh.gr2), using that addon's own GR2 import preferences.

    Returns (imported_objects, error_message). error_message is None on
    success. Never raises.
    """
    error = _addon_missing_error()
    if error:
        return [], error

    settings = _gr2_import_settings(context)
    objects_before = set(bpy.data.objects)

    # ImportGR2 takes one directory + file names per call
    for directory, names in _group_by_directory(filepaths).items():
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


def import_jba_onto_active_armature(operator, context, filepath):
    """Calls swtor_io_tools' JBA load() (ops/import_jba.py) directly
    against `filepath`, bypassing its File Browser-based ImportJBA
    operator.

    load()'s build() step reads ignore_facial_bones / delete_180 /
    scale_animation / scale_factor straight off whatever `operator` it's
    given, so Auto_Koda_OT_ImportJBA declares those same four properties
    and passes itself through, alongside report().

    Returns True on success, False on failure -- failures from within
    swtor_io_tools are reported via operator.report() by its own
    load()/build(), not duplicated here.
    """
    error = _addon_missing_error()
    if error:
        operator.report({'ERROR'}, error)
        return False

    try:
        from swtor_io_tools.ops.import_jba import load #type: ignore
    except Exception as e:
        operator.report({'ERROR'}, f"Could not import swtor_io_tools' JBA importer: {e}")
        return False

    return load(operator, context, filepath)
# Example: import_jba_onto_active_armature(op, context, ".../humanoid/bfa/run_fwd.jba") -> True
