import bpy # type: ignore
from . import config, operators, helpers
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


class Auto_Koda_PT_Settings(bpy.types.Panel):
    bl_options = {'DEFAULT_CLOSED'}
    bl_label = "Settings"
    bl_idname = "VIEW3D_PT_auto_koda_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Auto Koda"

    def draw(self, context):
        layout = self.layout

        shaders_blend_loc = helpers.get_shaders_blend_path()
        if not shaders_blend_loc or ".blend" not in shaders_blend_loc:
            _draw_status_box(layout, f"Shaders.blend path not set or invalid: {shaders_blend_loc}",
                             "Set Shaders.blend", alert=True)
        elif shaders_blend_loc == config.DEFAULT_SHADERS:
            _draw_status_box(layout, "Using default Shaders.blend", "Set Custom Shaders.blend")
        else:
            _draw_status_box(layout, "Using custom Shaders.blend", "Change Custom Shaders.blend",
                             path=shaders_blend_loc)

        resources_path = helpers.get_resources_folder_path()
        if not resources_path:
            _draw_status_box(layout, "TOR resources folder not set or invalid", "Set Resources Folder", alert=True)
        else:
            _draw_status_box(layout, "Resources folder configured", "Change Resources Folder", path=resources_path)

        anim_root_path = helpers.get_anim_root_path()
        if not anim_root_path:
            _draw_status_box(layout, "Anim folder not set or invalid", "Set Anim Folder", alert=True)
        else:
            _draw_status_box(layout, "Anim folder configured", "Change Anim Folder", path=anim_root_path)

class Auto_Koda_PT_Process_Materials(bpy.types.Panel):
    bl_label = "Process Materials"
    bl_idname = "VIEW3D_PT_auto_koda_process"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Auto Koda"

    def draw(self, context):
        layout = self.layout
        layout.operator(operators.Auto_Koda_Crunch_Selected.bl_idname, text="Auto Crunch (Selected)", icon='MODIFIER')

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
        layout.operator("autokoda.sync_override", text="Sync Override")
        layout.operator("autokoda.link_override", text="Link Override")
        layout.operator("autokoda.sync_link_override", text="Sync/Link Override")

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

class Auto_Koda_PT_Utilities(bpy.types.Panel):
    bl_label = "Utilities"
    bl_idname = "VIEW3D_PT_auto_koda_utilities"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Auto Koda"

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
        layout.separator()

        layout.label(text="Garment Hue")

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
        from .garment_hue import _color_sort_key

        items = getattr(data, propname)
        filter_text = getattr(data, "auto_koda_garment_hue_filter", "").lower()

        if filter_text:
            flt_flags = [
                self.bitflag_filter_item if filter_text in item.name.lower() else 0
                for item in items
            ]
        else:
            flt_flags = [self.bitflag_filter_item] * len(items)

        sort_by_color = getattr(data, "auto_koda_garment_hue_sort_by_color", False)

        if sort_by_color:
            keyed = sorted(
                range(len(items)),
                key=lambda i: _color_sort_key(items[i].color)
            )
            flt_neworder = [0] * len(items)
            for new_pos, original_index in enumerate(keyed):
                flt_neworder[original_index] = new_pos
        else:
            flt_neworder = list(range(len(items)))

        return flt_flags, flt_neworder
    # Example: filter_items(context, scene, "auto_koda_garment_hue_files") -> ([1073741824, 0, 1073741824], [2, 0, 1])

class Auto_Koda_PT_Animations(bpy.types.Panel):
    bl_label = "Animations"
    bl_idname = "VIEW3D_PT_auto_koda_animations"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Auto Koda"

    def draw(self, context):
        layout = self.layout

        if not helpers.get_anim_root_path():
            row = layout.row()
            row.alert = True
            row.label(text="Set the Anim Folder in Add-on Preferences first", icon='ERROR')

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