import bpy # type: ignore
from . import operators, ui, garment_hue, animations, config

classes = [
    ui.Auto_Koda_PT_Process_Materials,
    ui.Auto_Koda_PT_Import_Item,
    ui.Auto_Koda_PT_Settings,
    ui.Auto_Koda_PT_Material_Overrides,
    ui.Auto_Koda_Preferences,
    ui.Auto_Koda_PT_Utilities,
    ui.Auto_Koda_PT_Animations,
    ui.AUTOKODA_UL_garment_hue,
    ui.AUTOKODA_UL_jba_animations,

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
    operators.Auto_Koda_OT_RefreshJBAList,
    operators.Auto_Koda_OT_ImportJBA,
    operators.Auto_Koda_OT_ImportIpp,

    garment_hue.Auto_Koda_GarmentHueItem,
    animations.Auto_Koda_JBAItem,
    animations.Auto_Koda_JBAFolderItem,
]


def _refresh_garment_hue_for_current_scene():
    try:
        garment_hue.refresh_garment_hue_collection(bpy.context.scene)
    except Exception as e:
        print(f"[Auto Koda] Garment hue refresh skipped: {e}")
    return None  # for timer: don't repeat
# Example: _refresh_garment_hue_for_current_scene() -> None  (timer runs once)


def _refresh_jba_list_for_current_scene():
    try:
        animations.refresh_jba_lists(bpy.context.scene)
    except Exception as e:
        print(f"[Auto Koda] JBA animation list refresh skipped: {e}")
    return None  # for timer: don't repeat
# Example: _refresh_jba_list_for_current_scene() -> None  (timer runs once)


def _schedule_list_refresh():
    """Refreshes the garment hue and JBA lists shortly after now, once
    the scene is safe to modify."""
    bpy.app.timers.register(_refresh_garment_hue_for_current_scene, first_interval=0.1)
    bpy.app.timers.register(_refresh_jba_list_for_current_scene, first_interval=0.1)


def _on_load_post(dummy):
    """Runs every time a .blend file finishes loading (including startup
    file, opening a saved file, or File > New), so the garment hue list
    and JBA animation list - and any stale data baked into an older save
    - get rebuilt fresh."""
    _schedule_list_refresh()


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

    bpy.types.Scene.auto_koda_jba_folders = bpy.props.CollectionProperty(
        type=animations.Auto_Koda_JBAFolderItem
    )
    bpy.types.Scene.auto_koda_jba_folder_name = bpy.props.StringProperty(
        name="Animation Set",
        description="Type to search subfolders (within the Anim Folder) containing .jba files",
        update=animations.on_jba_folder_name_changed,
    )
    bpy.types.Scene.auto_koda_jba_files = bpy.props.CollectionProperty(
        type=animations.Auto_Koda_JBAItem
    )
    bpy.types.Scene.auto_koda_jba_index = bpy.props.IntProperty(
        default=-1
    )

    bpy.types.Scene.auto_koda_ipp = bpy.props.StringProperty(
        name="Item Appearance",
        description="Item appearance node to import, e.g. ipp.class.spy.quest.tdps2.t1x1.chest",
    )
    bpy.types.Scene.auto_koda_body_type = bpy.props.EnumProperty(
        name="Body Type",
        description="Body type to import the item's models as",
        items=[(bt, bt.upper(), f"Import '{bt}' models") for bt in config.BODY_TYPES],
        default=config.DEFAULT_BODY_TYPE,
    )

    bpy.app.handlers.load_post.append(_on_load_post)

    # Cover the case where the addon is enabled live, mid-session, with a
    # file already open (load_post won't fire again for an already-open file)
    _schedule_list_refresh()


def unregister():
    if _on_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load_post)

    del bpy.types.Scene.auto_koda_body_type
    del bpy.types.Scene.auto_koda_ipp

    del bpy.types.Scene.auto_koda_jba_index
    del bpy.types.Scene.auto_koda_jba_files
    del bpy.types.Scene.auto_koda_jba_folder_name
    del bpy.types.Scene.auto_koda_jba_folders

    del bpy.types.Scene.auto_koda_garment_hue_sort_by_color
    del bpy.types.Scene.auto_koda_garment_hue_index
    del bpy.types.Scene.auto_koda_garment_hue_filter
    del bpy.types.Scene.auto_koda_garment_hue_files

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)