import bpy # type: ignore
from . import operators, ui, garment_hue

classes = [
    ui.Auto_Koda_PT_Settings,
    ui.Auto_Koda_PT_Process_Materials,
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
    operators.Auto_Koda_OT_GarmentHuePrimary,
    operators.Auto_Koda_OT_GarmentHueSecondary,
    operators.Auto_Koda_OT_RefreshGarmentHueList,
    
    garment_hue.Auto_Koda_GarmentHueItem,
]

def _initial_garment_hue_refresh():
    """Runs once, shortly after the addon loads. Deferred via a timer
    because bpy.data cannot be safely written to immediately during
    register() either - Blender may still be mid-load at that point."""
    try:
        garment_hue.refresh_garment_hue_collection(bpy.context.scene)
    except Exception as e:
        print(f"[Auto Koda] Initial garment hue refresh skipped: {e}")
    return None  # don't repeat

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.auto_koda_garment_hue_files = bpy.props.CollectionProperty(
        type=garment_hue.Auto_Koda_GarmentHueItem
    )
    bpy.types.Scene.auto_koda_garment_hue_selection = bpy.props.StringProperty(
        name="Garment Hue File",
        description="Type to filter, or select a file from resources/art/dynamic/garmenthue/",
    )

    bpy.app.timers.register(_initial_garment_hue_refresh, first_interval=0.1)

def unregister():
    del bpy.types.Scene.auto_koda_garment_hue_selection
    del bpy.types.Scene.auto_koda_garment_hue_files

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)