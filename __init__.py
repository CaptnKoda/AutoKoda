import bpy # type: ignore
from . import operators, ui, garment_hue, animations, config

classes = [
    ui.Auto_Koda_PT_Process_Materials,
    ui.Auto_Koda_PT_Import_Item,
    ui.Auto_Koda_PT_Settings,
    ui.Auto_Koda_PT_Material_Overrides,
    ui.Auto_Koda_Preferences,
    ui.Auto_Koda_PT_Utilities,
    ui.Auto_Koda_PT_Garment_Hue,
    ui.Auto_Koda_PT_Animations,
    ui.AUTOKODA_UL_garment_hue,
    ui.AUTOKODA_UL_jba_animations,

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


# (refresh function, label) pairs run after a file load / addon enable
_LIST_REFRESHERS = (
    (garment_hue.refresh_garment_hue_collection, "Garment hue"),
    (animations.refresh_jba_lists, "JBA animation list"),
)


def _refresh_lists():
    for refresh, label in _LIST_REFRESHERS:
        try:
            refresh(bpy.context.scene)
        except Exception as e:
            print(f"[Auto Koda] {label} refresh skipped: {e}")
    return None  # for timer: don't repeat
# Example: _refresh_lists() -> None  (timer runs once)


def _schedule_list_refresh():
    """Refreshes the garment hue and JBA lists shortly after now, once
    the scene is safe to modify."""
    bpy.app.timers.register(_refresh_lists, first_interval=0.1)


def _on_load_post(dummy):
    """Runs every time a .blend file finishes loading (including startup
    file, opening a saved file, or File > New), so the garment hue list
    and JBA animation list - and any stale data baked into an older save
    - get rebuilt fresh."""
    _schedule_list_refresh()


def _scene_properties():
    """Scene properties this addon adds, by attribute name. Built on
    demand since the CollectionProperty item classes must be registered
    first."""
    return {
        "auto_koda_garment_hue_files": bpy.props.CollectionProperty(
            type=garment_hue.Auto_Koda_GarmentHueItem
        ),
        "auto_koda_garment_hue_filter": bpy.props.StringProperty(
            name="Filter",
            description="Type to filter the garment hue list",
        ),
        "auto_koda_garment_hue_index": bpy.props.IntProperty(
            default=-1
        ),
        "auto_koda_garment_hue_sort_by_color": bpy.props.BoolProperty(
            name="Sort by Color",
            description="Group and order the list by similar colors instead of alphabetically",
            default=False,
        ),
        "auto_koda_jba_folders": bpy.props.CollectionProperty(
            type=animations.Auto_Koda_JBAFolderItem
        ),
        "auto_koda_jba_folder_name": bpy.props.StringProperty(
            name="Animation Set",
            description="Type to search subfolders (within the Anim Folder) containing .jba files",
            update=animations.on_jba_folder_name_changed,
        ),
        "auto_koda_jba_files": bpy.props.CollectionProperty(
            type=animations.Auto_Koda_JBAItem
        ),
        "auto_koda_jba_index": bpy.props.IntProperty(
            default=-1
        ),
        "auto_koda_ipp": bpy.props.StringProperty(
            name="Item Appearance",
            description="Item appearance node to import, e.g. ipp.class.spy.quest.tdps2.t1x1.chest",
        ),
        "auto_koda_body_type": bpy.props.EnumProperty(
            name="Body Type",
            description="Body type to import the item's models as",
            items=[(bt, bt.upper(), f"Import '{bt}' models") for bt in config.BODY_TYPES],
            default=config.DEFAULT_BODY_TYPE,
        ),
    }


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    for name, prop in _scene_properties().items():
        setattr(bpy.types.Scene, name, prop)

    bpy.app.handlers.load_post.append(_on_load_post)

    # Cover the case where the addon is enabled live, mid-session, with a
    # file already open (load_post won't fire again for an already-open file)
    _schedule_list_refresh()


def unregister():
    if _on_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load_post)

    for name in _scene_properties():
        delattr(bpy.types.Scene, name)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
