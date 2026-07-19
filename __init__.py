import bpy # type: ignore
from . import operators, ui

classes = [
    ui.Auto_Koda_PT_Process_Materials,
    ui.Auto_Koda_PT_Settings,
    ui.Auto_Koda_PT_Material_Overrides,
    ui.Auto_Koda_Preferences,
    ui.Auto_Koda_PT_Utilities,

    operators.Auto_Koda_Selected,
    operators.Auto_Koda_Crunch_Selected,
    operators.Auto_Koda_OT_SyncOverride,
    operators.Auto_Koda_OT_LinkOverride,
    operators.Auto_Koda_OT_SyncLinkOverride,
    operators.Auto_Koda_OT_ToggleSubsurfViewport,
    operators.Auto_Koda_OT_PrepareMeshes,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
