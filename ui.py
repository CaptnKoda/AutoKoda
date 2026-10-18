import bpy # type: ignore
from . import config, operators
from .prefs import get_shaders_blend_path, get_resources_folder_path, get_anim_root_path
from .garment_hue import color_sort_key
from bpy.props import StringProperty # type: ignore
from bpy.types import AddonPreferences # type: ignore


def _draw_status_box(layout, message, button_text, path=None, alert=False):
    """Draws one Settings status box: a status line, the configured path
    (if given), and a button that opens this addon's preferences."""
    box = layout.box()
    box.alert = alert
    box.row().label(text=message, icon='ERROR' if alert else 'CHECKMARK')
    if path:
        box.row().label(text=path, icon='FILE_BLEND' if path.lower().endswith(".blend") else 'FILE_FOLDER')
    box.row().operator(
        "preferences.addon_show",
        text=button_text,
        icon='FILE_FOLDER'
    ).module = __package__


def _draw_folder_status(layout, path, label):
    """Status box for a folder preference: an alert if unset/invalid,
    otherwise the configured path."""
    if not path:
        _draw_status_box(layout, f"{label} not set or invalid", f"Set {label}", alert=True)
    else:
        _draw_status_box(layout, f"{label} configured", f"Change {label}", path=path)


def _draw_missing_pref_warning(layout, label):
    row = layout.row()
    row.alert = True
    row.label(text=f"Set the {label} in Add-on Preferences first", icon='ERROR')


class _AutoKodaView3DPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Auto Koda"


class Auto_Koda_PT_Settings(_AutoKodaView3DPanel, bpy.types.Panel):
    bl_options = {'DEFAULT_CLOSED'}
    bl_label = "Settings"
    bl_idname = "VIEW3D_PT_auto_koda_settings"

    def draw(self, context):
        layout = self.layout

        shaders_blend_loc = get_shaders_blend_path()
        if shaders_blend_loc == config.DEFAULT_SHADERS:
            _draw_status_box(layout, "Using default Shaders.blend", "Set Custom Shaders.blend")
        else:
            _draw_status_box(layout, "Using custom Shaders.blend", "Change Custom Shaders.blend",
                             path=shaders_blend_loc)

        _draw_folder_status(layout, get_resources_folder_path(), "Resources Folder")
        _draw_folder_status(layout, get_anim_root_path(), "Anim Folder")

class Auto_Koda_PT_Process_Materials(_AutoKodaView3DPanel, bpy.types.Panel):
    bl_label = "Process Materials"
    bl_idname = "VIEW3D_PT_auto_koda_process"

    def draw(self, context):
        layout = self.layout
        layout.operator(operators.Auto_Koda_Crunch_Selected.bl_idname, text="Auto Crunch (Selected)", icon='MODIFIER')

class Auto_Koda_PT_Import_Item(_AutoKodaView3DPanel, bpy.types.Panel):
    bl_label = "Import Item"
    bl_idname = "VIEW3D_PT_auto_koda_import_item"

    def draw(self, context):
        layout = self.layout

        if not get_resources_folder_path():
            _draw_missing_pref_warning(layout, "Resources Folder")

        row = layout.row(align=True)
        row.prop(context.scene, "auto_koda_ipp", text="", icon='MOD_CLOTH')
        sub = row.row(align=True)
        sub.ui_units_x = 3
        sub.prop(context.scene, "auto_koda_body_type", text="")

        layout.operator(
            operators.Auto_Koda_OT_ImportIpp.bl_idname,
            text=f"Import ({context.scene.auto_koda_body_type.upper()})", icon='IMPORT'
        )

class Auto_Koda_PT_Material_Overrides(bpy.types.Panel):
    bl_label = "Material Overrides"
    bl_idname = "NODE_PT_auto_koda_material_overrides"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Auto Koda"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space and space.type == 'NODE_EDITOR' and space.tree_type == 'ShaderNodeTree'
    # Example: poll(context) -> True  (Shader Editor is open)

    def draw(self, context):
        layout = self.layout
        for op in (
            operators.Auto_Koda_OT_SyncOverride,
            operators.Auto_Koda_OT_LinkOverride,
            operators.Auto_Koda_OT_SyncLinkOverride,
        ):
            layout.operator(op.bl_idname, text=op.bl_label)

class Auto_Koda_Preferences(AddonPreferences):
    bl_idname = __package__

    shadersPath: StringProperty(
        name="",
        subtype='FILE_PATH'
    ) # type: ignore

    resourcesPath: StringProperty(
        name="",
        description="Folder containing TOR-extracted resource files",
        subtype='DIR_PATH'
    ) # type: ignore

    animRootPath: StringProperty(
        name="",
        description="Root 'anim' folder to scan recursively for subfolders containing .jba files",
        subtype='DIR_PATH'
    ) # type: ignore

    def draw(self, context):
        layout = self.layout
        layout.label(text="Select your Shaders.blend file below")
        layout.prop(self, "shadersPath", text="Shaders.blend Path")

        layout.separator()

        layout.label(text="Select your TOR resources extraction folder below")
        layout.prop(self, "resourcesPath", text="Resources Folder")

        layout.separator()

        layout.label(text="Select your SWTOR 'anim' folder below")
        layout.prop(self, "animRootPath", text="Anim Folder")

class Auto_Koda_PT_Utilities(_AutoKodaView3DPanel, bpy.types.Panel):
    bl_label = "Utilities"
    bl_idname = "VIEW3D_PT_auto_koda_utilities"

    def draw(self, context):
        layout = self.layout
        layout.operator(
            operators.Auto_Koda_OT_ToggleSubsurfViewport.bl_idname,
            text="Toggle Subsurf Viewport",
            icon='MOD_SUBSURF'
        )
        layout.separator()
        layout.operator(
            operators.Auto_Koda_OT_PrepareMeshes.bl_idname,
            text="Mesh Preparation",
            icon='MESH_DATA'
        )

class Auto_Koda_PT_Garment_Hue(_AutoKodaView3DPanel, bpy.types.Panel):
    bl_label = "Garment Hue"
    bl_idname = "VIEW3D_PT_auto_koda_garment_hue"

    def draw(self, context):
        layout = self.layout

        if not get_resources_folder_path():
            _draw_missing_pref_warning(layout, "Resources Folder")

        row = layout.row(align=True)
        row.prop(context.scene, "auto_koda_garment_hue_filter", text="", icon='VIEWZOOM')
        row.prop(context.scene, "auto_koda_garment_hue_sort_by_color", text="", icon='COLOR', toggle=True)
        row.operator(
            operators.Auto_Koda_OT_RefreshGarmentHueList.bl_idname,
            text="", icon='FILE_REFRESH'
        )

        layout.template_list(
            "AUTOKODA_UL_garment_hue", "",
            context.scene, "auto_koda_garment_hue_files",
            context.scene, "auto_koda_garment_hue_index",
            rows=5
        )

        row = layout.row(align=True)
        row.operator(operators.Auto_Koda_OT_GarmentHuePrimary.bl_idname, text="Primary")
        row.operator(operators.Auto_Koda_OT_GarmentHueSecondary.bl_idname, text="Secondary")

class AUTOKODA_UL_garment_hue(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "color", text="", icon_only=True)
        row.label(text=item.name)

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        filter_text = data.auto_koda_garment_hue_filter.lower()

        flt_flags = [
            self.bitflag_filter_item if filter_text in item.name.lower() else 0
            for item in items
        ]

        if data.auto_koda_garment_hue_sort_by_color:
            keyed = sorted(range(len(items)), key=lambda i: color_sort_key(items[i].color))
            flt_neworder = [0] * len(items)
            for new_pos, original_index in enumerate(keyed):
                flt_neworder[original_index] = new_pos
        else:
            flt_neworder = list(range(len(items)))

        return flt_flags, flt_neworder
    # Example: filter_items(context, scene, "auto_koda_garment_hue_files") -> ([1073741824, 0, 1073741824], [2, 0, 1])

class Auto_Koda_PT_Animations(_AutoKodaView3DPanel, bpy.types.Panel):
    bl_label = "Animations"
    bl_idname = "VIEW3D_PT_auto_koda_animations"

    def draw(self, context):
        layout = self.layout

        if not get_anim_root_path():
            _draw_missing_pref_warning(layout, "Anim Folder")

        layout.prop_search(
            context.scene, "auto_koda_jba_folder_name",
            context.scene, "auto_koda_jba_folders",
            text="Animation Set"
        )

        row = layout.row(align=True)
        row.label(text="")
        row.operator(
            operators.Auto_Koda_OT_RefreshJBAList.bl_idname,
            text="", icon='FILE_REFRESH'
        )

        layout.template_list(
            "AUTOKODA_UL_jba_animations", "",
            context.scene, "auto_koda_jba_files",
            context.scene, "auto_koda_jba_index",
            rows=8
        )

        layout.operator(
            operators.Auto_Koda_OT_ImportJBA.bl_idname,
            text="Import JBA", icon='ARMATURE_DATA'
        )

class AUTOKODA_UL_jba_animations(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.name, icon='ANIM')
