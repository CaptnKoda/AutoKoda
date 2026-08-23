import bpy # type: ignore
from . import operators, ui, garment_hue

classes = [
    ui.Auto_Koda_PT_Process_Materials,
    ui.Auto_Koda_PT_Settings,
    ui.Auto_Koda_PT_Material_Overrides,
    ui.Auto_Koda_Preferences,
    ui.Auto_Koda_PT_Utilities,
    ui.AUTOKODA_UL_garment_hue,

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


def _refresh_garment_hue_for_current_scene():
    try:
        garment_hue.refresh_garment_hue_collection(bpy.context.scene)
    except Exception as e:
        print(f"[Auto Koda] Garment hue refresh skipped: {e}")
    return None  # for timer: don't repeat


def _on_load_post(dummy):
    """Runs every time a .blend file finishes loading (including startup
    file, opening a saved file, or File > New), so the garment hue list -
    and any stale colors baked into an older save - gets rebuilt fresh."""
    bpy.app.timers.register(_refresh_garment_hue_for_current_scene, first_interval=0.1)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.auto_koda_garment_hue_files = bpy.props.CollectionProperty(
        type=garment_hue.Auto_Koda_GarmentHueItem
    )
    bpy.types.Scene.auto_koda_garment_hue_filter = bpy.props.StringProperty(
        name="Filter",
        description="Type to filter the garment hue list",
    )
    bpy.types.Scene.auto_koda_garment_hue_index = bpy.props.IntProperty(
        default=-1
    )
    bpy.types.Scene.auto_koda_garment_hue_sort_by_color = bpy.props.BoolProperty(
        name="Sort by Color",
        description="Group and order the list by similar colors instead of alphabetically",
        default=False,
    )

    bpy.app.handlers.load_post.append(_on_load_post)

    # Cover the case where the addon is enabled live, mid-session, with a
    # file already open (load_post won't fire again for an already-open file)
    bpy.app.timers.register(_refresh_garment_hue_for_current_scene, first_interval=0.1)


def unregister():
    if _on_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load_post)

    del bpy.types.Scene.auto_koda_garment_hue_sort_by_color
    del bpy.types.Scene.auto_koda_garment_hue_index
    del bpy.types.Scene.auto_koda_garment_hue_filter
    del bpy.types.Scene.auto_koda_garment_hue_files

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)