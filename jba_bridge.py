"""Bridge into the external swtor_io_tools addon's JBA animation importer
(ops/import_jba.py's load()), used by Auto_Koda_OT_ImportJBA to apply a
selected .jba animation onto the active armature without going through
swtor_io_tools' own File Browser-based ImportJBA operator.

load()'s build() step reads ignore_facial_bones / delete_180 /
scale_animation / scale_factor straight off whatever `operator` object
gets passed in (see swtor_io_tools' ImportJBA.invoke(), which normally
sets these from its own addon preferences before calling execute()).
Since we're calling load() directly rather than going through that
operator, our own Auto_Koda_OT_ImportJBA declares the same four
properties and passes itself through as `operator` -- load()/build()
neither know nor care which operator class they came from, only that
report() and those four attributes exist.
"""

import bpy  # type: ignore

EXTERNAL_SWTOR_IO_ADDON_MODULE = "swtor_io_tools"


def import_jba_onto_active_armature(operator, context, filepath):
    """Calls swtor_io_tools' own load() directly against `filepath`.
    `operator` must expose report() plus ignore_facial_bones,
    delete_180, scale_animation and scale_factor (Auto_Koda_OT_ImportJBA
    does). Returns True on success, False on failure -- failures from
    within swtor_io_tools are reported via operator.report() by its own
    load()/build(), not duplicated here.
    """
    if EXTERNAL_SWTOR_IO_ADDON_MODULE not in bpy.context.preferences.addons:
        operator.report({'ERROR'}, f"'{EXTERNAL_SWTOR_IO_ADDON_MODULE}' addon is not installed/enabled")
        return False

    try:
        from swtor_io_tools.ops.import_jba import load
    except Exception as e:
        operator.report({'ERROR'}, f"Could not import swtor_io_tools' JBA importer: {e}")
        return False

    return load(operator, context, filepath)