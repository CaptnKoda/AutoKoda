"""Bridge into the external swtor_io_tools addon: its material-by-name
pipeline, its GR2 importer and its JBA animation importer.

Several entry points used here (_build_named_material(), load()) are not
a stable public API -- if a future swtor_io_tools update renames/moves
them, this bridge is the only place that needs updating.
"""

import logging
import os
import bpy  # type: ignore
from .config import EXTERNAL_SWTOR_IO_ADDON_MODULE
from .prefs import is_addon_enabled

log = logging.getLogger(__name__)


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
        # "built" doesn't guarantee every texture was found
        for _, texture_path in getattr(result, "missing_assets", ()):
            log.warning(f"'{mat_name}' built with a missing texture: {texture_path}")
        return True
    if result.status == "error":
        errors.append(f"'{mat_name}': {result.detail}")
    elif result.status == "not_found":
        log.warning(f"No matching .mat file found for '{mat_name}'")
    elif result.status == "unbuilt_type":
        log.warning(f"'{mat_name}' is a recognized but not-yet-supported shader type ({result.detail})")
    elif result.status == "skipped":
        log.debug(f"'{mat_name}' skipped: {result.detail}")
    else:
        errors.append(f"'{mat_name}': unknown swtor_io_tools result status '{result.status}' ({result.detail})")
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
        log.exception("swtor_io_tools' material pipeline failed to import")
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
            log.exception(f"swtor_io_tools crashed building '{mat_name}' for '{obj_name}'")
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
    for pref in _GR2_PREF_TO_OPERATOR_PROP:
        if not hasattr(io_prefs, pref):
            log.warning(f"swtor_io_tools has no preference '{pref}', the GR2 importer will use its default")
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

    try:
        settings = _gr2_import_settings(context)
    except Exception as e:
        log.exception("Could not read swtor_io_tools' GR2 import preferences")
        return [], f"Could not read swtor_io_tools' GR2 import preferences: {e}"

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
            log.exception(f"GR2 import crashed on {names} in '{directory}' (settings: {settings})")
            return [], f"GR2 import failed: {e}"

        if 'FINISHED' not in result:
            log.error(f"GR2 import of {names} in '{directory}' returned {result} (settings: {settings})")
            return [], f"GR2 import cancelled for {', '.join(names)} (see console)"

    return [o for o in bpy.data.objects if o not in objects_before], None
# Example: import_gr2_files(context, [".../chest_tight_bmn_archetype.gr2"]) -> ([bpy.data.objects["chest_tight_bmn_archetype"]], None)


# swtor_io_tools' own JBA import operator, whose property defaults stand in
# for any setting its load()/build() reads that Auto_Koda_OT_ImportJBA
# doesn't declare (e.g. one added in a newer swtor_io_tools).
EXTERNAL_JBA_OPERATOR = "import_animation.jba"

_MISSING = object()
_warned_missing_props = set()


def _swtor_io_jba_property_default(name):
    """Default value of `name` on swtor_io_tools' JBA import operator, or
    _MISSING if that operator or property can't be found."""
    try:
        module_name, op_name = EXTERNAL_JBA_OPERATOR.split(".")
        prop = getattr(getattr(bpy.ops, module_name), op_name).get_rna_type().properties.get(name)
    except Exception:
        return _MISSING
    if prop is None:
        return _MISSING
    return tuple(prop.default_array) if getattr(prop, "is_array", False) else prop.default
# Example: _swtor_io_jba_property_default("set_scene_fps") -> False


class _ReportLoggingOperator:
    """Stands in for an operator when handing it to swtor_io_tools, so the
    report() calls it makes -- its only record of why an import failed --
    also reach the log. Everything else is forwarded to the operator; a
    setting the operator doesn't declare falls back to swtor_io_tools' own
    default for it, with a one-time warning."""

    def __init__(self, operator):
        self._operator = operator

    def __getattr__(self, name):
        try:
            return getattr(self._operator, name)
        except AttributeError:
            if name.startswith("_"):
                raise
            default = _swtor_io_jba_property_default(name)
            if default is _MISSING:
                raise
            if name not in _warned_missing_props:
                _warned_missing_props.add(name)
                log.warning(
                    f"swtor_io_tools' JBA importer reads '{name}', which {type(self._operator).__name__} "
                    f"doesn't declare, using swtor_io_tools' default ({default!r})"
                )
            return default

    def report(self, type, message):
        self._operator.log_report(type, message)


def import_jba_onto_active_armature(operator, context, filepath):
    """Calls swtor_io_tools' JBA load() (ops/import_jba.py) directly
    against `filepath`, bypassing its File Browser-based ImportJBA
    operator.

    load()'s build() step reads ignore_facial_bones / delete_180 /
    scale_animation / scale_factor / set_scene_fps straight off whatever
    `operator` it's given, so Auto_Koda_OT_ImportJBA declares those same
    properties and passes itself through, alongside report(). Any setting
    swtor_io_tools adds later falls back to its own default (see
    _ReportLoggingOperator) until it's declared there too.

    Returns True on success, False on failure -- failures from within
    swtor_io_tools are reported by its own load()/build() through
    _ReportLoggingOperator, not duplicated here.
    """
    error = _addon_missing_error()
    if error:
        operator.log_report({'ERROR'}, error)
        return False

    try:
        from swtor_io_tools.ops.import_jba import load #type: ignore
    except Exception as e:
        log.exception("swtor_io_tools' JBA importer failed to import")
        operator.log_report({'ERROR'}, f"Could not import swtor_io_tools' JBA importer: {e}")
        return False

    try:
        succeeded = load(_ReportLoggingOperator(operator), context, filepath)
    except Exception as e:
        log.exception(f"swtor_io_tools crashed importing '{filepath}'")
        operator.log_report({'ERROR'}, f"JBA import crashed: {type(e).__name__}: {e}")
        return False

    if not succeeded:
        log.error(f"swtor_io_tools did not import '{filepath}' (load() returned {succeeded!r})")
    return succeeded
# Example: import_jba_onto_active_armature(op, context, ".../humanoid/bfa/run_fwd.jba") -> True
