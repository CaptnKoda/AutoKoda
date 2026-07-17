import bpy # type: ignore
from . import config, operators, helpers
from bpy.props import StringProperty # type: ignore
from bpy.types import AddonPreferences # type: ignore

class Auto_Koda_PT_Process_Materials(bpy.types.Panel):
    bl_label = "Process Materials"
    bl_idname = "VIEW3D_PT_auto_koda_process"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Auto Koda"

    def draw(self, context):
        layout = self.layout
        layout.operator(operators.Auto_Koda_Selected.bl_idname,text="Auto Koda (Selected)",icon='RESTRICT_SELECT_OFF')
        layout.operator(operators.Auto_Koda_Crunch_Selected.bl_idname, text="Auto Crunch (Selected)", icon='MODIFIER')

class Auto_Koda_PT_Settings(bpy.types.Panel):
    bl_options = {'DEFAULT_CLOSED'}
    bl_label = "AutoKoda Settings II"
    bl_idname = "VIEW3D_PT_auto_koda_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Auto Koda"

    def draw(self, context):
        layout = self.layout
        status_box = layout.box()

        shaders_blend_loc = helpers.get_shaders_blend_path()

        # Invalid or missing path
        if not shaders_blend_loc or ".blend" not in shaders_blend_loc:
            status_box.alert = True
            row = status_box.row()
            row.label(
                text=f"Shaders.blend path not set or invalid: {shaders_blend_loc}",
                icon='ERROR'
            )
            row = status_box.row()
            row.operator(
                "preferences.addon_show",
                text="Set Shaders.blend",
                icon='FILE_FOLDER'
            ).module = __name__

        # Default shaders
        elif shaders_blend_loc == config.DEFAULT_SHADERS:
            row = status_box.row()
            row.label(text="Using default Shaders.blend", icon='CHECKMARK')
            row = status_box.row()
            row.operator(
                "preferences.addon_show",
                text="Set Custom Shaders.blend",
                icon='FILE_FOLDER'
            ).module = __name__

        # Custom shaders
        else:
            row = status_box.row()
            row.label(text="Using custom Shaders.blend", icon='CHECKMARK')
            row = status_box.row()
            row.label(text=shaders_blend_loc, icon='FILE_BLEND')
            row = status_box.row()
            row.operator(
                "preferences.addon_show",
                text="Change Custom Shaders.blend",
                icon='FILE_FOLDER'
            ).module = __name__

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

    def draw(self, context):
        layout = self.layout
        layout.operator("autokoda.sync_override", text="Sync Override")
        layout.operator("autokoda.link_override", text="Link Override")
        layout.operator("autokoda.sync_link_override", text="Sync/Link Override")

class Auto_Koda_Preferences(AddonPreferences):
    bl_idname = __name__

    shadersPath: StringProperty(
        name="",
        subtype='FILE_PATH'
    ) # type: ignore

    def draw(self, context):
        layout = self.layout
        layout.label(text="Select your Shaders.blend file below")
        layout.prop(self, "shadersPath", text="Shaders.blend Path")