import bpy # type: ignore
from . import helpers
from bpy.props import StringProperty # type: ignore
from bpy.types import AddonPreferences # type: ignore

class Auto_Koda_Selected(bpy.types.Operator):
    bl_idname = "autokoda.convert_selected"
    bl_label = "Auto Koda"
    bl_description = "Convert the shader of the selected object to a Koda shader"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        shadersBlend = helpers.get_shaders_blend_path()
        if not shadersBlend:
            self.report({'ERROR'}, "Shaders Blend file path not set in preferences!")
            return {'CANCELLED'}

        for obj in bpy.context.selected_objects:
            if obj.type == 'MESH':
                helpers.process_object(obj)

        return {'FINISHED'}
                
class Auto_Koda_Crunch_Selected(bpy.types.Operator):
    bl_idname = "autokoda.crunch_selected"
    bl_label = "Auto Crunch"
    bl_description = "Run Auto Crunch (Selected)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        shadersBlend = helpers.get_shaders_blend_path()
        if not shadersBlend:
            self.report({'ERROR'}, "Shaders Blend file path not set in preferences!")
            return {'CANCELLED'}
        
        for obj in bpy.context.selected_objects:
            if obj.type == 'MESH':
                bpy.ops.zgswtor.process_named_mats(use_selection_only=True, use_overwrite_bool=False, use_collect_colliders_bool=True)
                bpy.ops.zgswtor.customize_swtor_shaders(use_selection_only=True)
                helpers.process_object(obj)
        
        return {'FINISHED'}

class Auto_Koda_OT_SyncOverride(bpy.types.Operator):
    bl_idname = "autokoda.sync_override"
    bl_label = "Sync Override"
    bl_description = "Sync Shader Node Group settings to Material Override Group"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        helpers.run_override_sync(do_sync_values=True, do_link_override=False)
        self.report({'INFO'}, "Sync Override executed")
        return {'FINISHED'}

class Auto_Koda_OT_LinkOverride(bpy.types.Operator):
    bl_idname = "autokoda.link_override"
    bl_label = "Link Override"
    bl_description = "Link Shader Node Group settings to Material Override Group"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        helpers.run_override_sync(do_sync_values=False, do_link_override=True)
        self.report({'INFO'}, "Link Override executed")
        return {'FINISHED'}

class Auto_Koda_OT_SyncLinkOverride(bpy.types.Operator):
    bl_idname = "autokoda.sync_link_override"
    bl_label = "Sync/Link Override"
    bl_description = "Sync and Link Shader Node Group settings to Material Override Group"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        helpers.run_override_sync(do_sync_values=True, do_link_override=True)
        self.report({'INFO'}, "Sync/Link Override executed")
        return {'FINISHED'}
    
class Auto_Koda_OT_ToggleSubsurfViewport(bpy.types.Operator):
    bl_idname = "autokoda.toggle_subsurf_viewport"
    bl_label = "Toggle Subsurf Viewport Display"
    bl_description = "Toggle viewport display of Subdivision Surface modifiers on selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objects = context.selected_objects
        if not objects:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}

        count = helpers.toggle_subsurf_viewport_display(objects)
        if count == 0:
            self.report({'WARNING'}, "No Subdivision Surface modifiers found on selection")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Toggled {count} Subdivision Surface modifier(s)")
        return {'FINISHED'}

class Auto_Koda_OT_PrepareMeshes(bpy.types.Operator):
    bl_idname = "autokoda.prepare_meshes"
    bl_label = "Mesh Preparation"
    bl_description = "Merge by distance, convert tris to quads, and clear custom split normals on selected meshes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not objects:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        count = helpers.prepare_meshes(objects)
        self.report({'INFO'}, f"Prepared {count} mesh(es)")
        return {'FINISHED'}

class Auto_Koda_OT_GarmentHuePrimary(bpy.types.Operator):
    bl_idname = "autokoda.garment_hue_primary"
    bl_label = "Primary"
    bl_description = "Apply the selected garment hue file to Palette 1 on selected objects' Koda materials"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from . import garment_hue_xml

        filename = context.scene.auto_koda_garment_hue_selection
        if not filename:
            self.report({'WARNING'}, "No garment hue file selected")
            return {'CANCELLED'}

        objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not objects:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        files_applied, nodes_updated = garment_hue_xml.apply_garment_hue_to_objects(
            objects, filename, slot=1
        )

        if not files_applied:
            self.report({'ERROR'}, f"Could not read '{filename}' - check console")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Applied '{filename}' (Primary) to {nodes_updated} node(s)")
        return {'FINISHED'}


class Auto_Koda_OT_GarmentHueSecondary(bpy.types.Operator):
    bl_idname = "autokoda.garment_hue_secondary"
    bl_label = "Secondary"
    bl_description = "Apply the selected garment hue file to Palette 2 on selected objects' Koda materials"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from . import garment_hue_xml

        filename = context.scene.auto_koda_garment_hue_selection
        if not filename:
            self.report({'WARNING'}, "No garment hue file selected")
            return {'CANCELLED'}

        objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not objects:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        files_applied, nodes_updated = garment_hue_xml.apply_garment_hue_to_objects(
            objects, filename, slot=2
        )

        if not files_applied:
            self.report({'ERROR'}, f"Could not read '{filename}' - check console")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Applied '{filename}' (Secondary) to {nodes_updated} node(s)")
        return {'FINISHED'}

class Auto_Koda_OT_RefreshGarmentHueList(bpy.types.Operator):
    bl_idname = "autokoda.refresh_garment_hue_list"
    bl_label = "Refresh Garment Hue List"
    bl_description = "Rescan the garmenthue folder for files"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        from . import garment_hue
        garment_hue.refresh_garment_hue_collection(context.scene)
        return {'FINISHED'}