import bpy # type: ignore
from . import helpers
from bpy.props import BoolProperty, FloatProperty  # type: ignore


def _selected_meshes(context):
    return [o for o in context.selected_objects if o.type == 'MESH']
# Example: _selected_meshes(context) -> [bpy.data.objects["Body"], bpy.data.objects["Head"]]


def _shaders_path_missing(operator):
    """Reports an error on `operator` and returns True if no Shaders.blend
    path is available."""
    if helpers.get_shaders_blend_path():
        return False
    operator.report({'ERROR'}, "Shaders Blend file path not set in preferences!")
    return True
# Example: _shaders_path_missing(self) -> False


class Auto_Koda_Selected(bpy.types.Operator):
    bl_idname = "autokoda.convert_selected"
    bl_label = "Auto Koda"
    bl_description = "Convert the shader of the selected object to a Koda shader"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if _shaders_path_missing(self):
            return {'CANCELLED'}

        for obj in _selected_meshes(context):
            helpers.process_object(obj)

        return {'FINISHED'}
    # Example: execute(context) -> {'FINISHED'}

class Auto_Koda_Crunch_Selected(bpy.types.Operator):
    bl_idname = "autokoda.crunch_selected"
    bl_label = "Auto Crunch"
    bl_description = "Run Auto Crunch (Selected)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if _shaders_path_missing(self):
            return {'CANCELLED'}

        objects = _selected_meshes(context)
        if not objects:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        built, errors = helpers.build_named_materials_for_objects(objects)
        for err in errors:
            print(f"[Auto Koda] {err}")

        for obj in objects:
            helpers.process_object(obj)

        if errors:
            self.report(
                {'WARNING'},
                f"Built {built} native material(s); {len(errors)} error(s) - see console"
            )
        else:
            self.report(
                {'INFO'},
                f"Built {built} native material(s), converted {len(objects)} object(s)"
            )

        return {'FINISHED'}
    # Example: execute(context) -> {'FINISHED'}  (reports "Built 5 native material(s), converted 2 object(s)")

class _OverrideSyncBase:
    """Shared execute() for the three override operators; subclasses only
    choose which steps of run_override_sync() to run."""
    bl_options = {'REGISTER', 'UNDO'}
    do_sync_values = False
    do_link_override = False

    def execute(self, context):
        helpers.run_override_sync(
            do_sync_values=self.do_sync_values,
            do_link_override=self.do_link_override,
        )
        self.report({'INFO'}, f"{self.bl_label} executed")
        return {'FINISHED'}
    # Example: execute(context) -> {'FINISHED'}  (reports "Sync Override executed")

class Auto_Koda_OT_SyncOverride(_OverrideSyncBase, bpy.types.Operator):
    bl_idname = "autokoda.sync_override"
    bl_label = "Sync Override"
    bl_description = "Sync Shader Node Group settings to Material Override Group"
    do_sync_values = True

class Auto_Koda_OT_LinkOverride(_OverrideSyncBase, bpy.types.Operator):
    bl_idname = "autokoda.link_override"
    bl_label = "Link Override"
    bl_description = "Link Shader Node Group settings to Material Override Group"
    do_link_override = True

class Auto_Koda_OT_SyncLinkOverride(_OverrideSyncBase, bpy.types.Operator):
    bl_idname = "autokoda.sync_link_override"
    bl_label = "Sync/Link Override"
    bl_description = "Sync and Link Shader Node Group settings to Material Override Group"
    do_sync_values = True
    do_link_override = True

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
    # Example: execute(context) -> {'FINISHED'}  (reports "Toggled 3 Subdivision Surface modifier(s)")

class Auto_Koda_OT_PrepareMeshes(bpy.types.Operator):
    bl_idname = "autokoda.prepare_meshes"
    bl_label = "Mesh Preparation"
    bl_description = "Merge by distance, convert tris to quads, and clear custom split normals on selected meshes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objects = _selected_meshes(context)
        if not objects:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        count = helpers.prepare_meshes(objects)
        self.report({'INFO'}, f"Prepared {count} mesh(es)")
        return {'FINISHED'}
    # Example: execute(context) -> {'FINISHED'}  (reports "Prepared 3 mesh(es)")

class _GarmentHueApplyBase:
    """Shared execute() for the Primary/Secondary garment hue operators;
    subclasses set which palette slot (1 or 2) they write to."""
    bl_options = {'REGISTER', 'UNDO'}
    palette_slot = 1

    def execute(self, context):
        from . import garment_hue, garment_hue_xml

        filename = garment_hue.get_selected_filename(context.scene)
        if not filename:
            self.report({'WARNING'}, "No garment hue file selected")
            return {'CANCELLED'}

        objects = _selected_meshes(context)
        if not objects:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        files_applied, nodes_updated = garment_hue_xml.apply_garment_hue_to_objects(
            objects, filename, slot=self.palette_slot
        )

        if not files_applied:
            self.report({'ERROR'}, f"Could not read '{filename}' - check console")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Applied '{filename}' ({self.bl_label}) to {nodes_updated} node(s)")
        return {'FINISHED'}
    # Example: execute(context) -> {'FINISHED'}  (reports "Applied 'garmenthue_red_light.xml' (Primary) to 4 node(s)")


class Auto_Koda_OT_GarmentHuePrimary(_GarmentHueApplyBase, bpy.types.Operator):
    bl_idname = "autokoda.garment_hue_primary"
    bl_label = "Primary"
    bl_description = "Apply the selected garment hue file to Palette 1 on selected objects' Koda materials"
    palette_slot = 1


class Auto_Koda_OT_GarmentHueSecondary(_GarmentHueApplyBase, bpy.types.Operator):
    bl_idname = "autokoda.garment_hue_secondary"
    bl_label = "Secondary"
    bl_description = "Apply the selected garment hue file to Palette 2 on selected objects' Koda materials"
    palette_slot = 2

class Auto_Koda_OT_RefreshGarmentHueList(bpy.types.Operator):
    bl_idname = "autokoda.refresh_garment_hue_list"
    bl_label = "Refresh Garment Hue List"
    bl_description = "Rescan the garmenthue folder for files"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        from . import garment_hue
        garment_hue.refresh_garment_hue_collection(context.scene)
        return {'FINISHED'}
    # Example: execute(context) -> {'FINISHED'}

class Auto_Koda_OT_RefreshJBAList(bpy.types.Operator):
    bl_idname = "autokoda.refresh_jba_list"
    bl_label = "Refresh Animation List"
    bl_description = "Rescan the anim folder tree for subfolders and .jba files"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        from . import animations
        animations.refresh_jba_lists(context.scene)
        return {'FINISHED'}
    # Example: execute(context) -> {'FINISHED'}

class Auto_Koda_OT_ImportJBA(bpy.types.Operator):
    bl_idname = "autokoda.import_jba"
    bl_label = "Import JBA"
    bl_description = "Import the selected .jba animation onto the active armature"
    bl_options = {'REGISTER', 'UNDO'}

    # Same properties import_jba.py's build() reads off the operator it's
    # given -- see jba_bridge.py's docstring for why these live here
    # rather than being pulled from swtor_io_tools' own preferences.
    ignore_facial_bones: BoolProperty(
        name="Ignore Facial Transl.",
        description="Ignores the data in the facial bones' translation keyframes and only uses their rotation keyframes",
        default=True,
    )  # type: ignore
    delete_180: BoolProperty(
        name="Delete 180° Rotation",
        description="Deletes Bip01's rotation keyframes and zeroes its rotation, instead of the character turning 180° to face away from camera",
        default=False,
    )  # type: ignore
    scale_animation: BoolProperty(
        name="Scale Animation",
        description="Scales the bones' translation data by Scale Factor, when the armature has no import_scale custom property to derive it from automatically",
        default=False,
    )  # type: ignore
    scale_factor: FloatProperty(
        name="Scale Factor",
        default=1.0,
        soft_min=0.1,
        soft_max=2.0,
        precision=2,
    )  # type: ignore

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'ARMATURE'
    # Example: poll(context) -> True  (active object is an armature)

    def execute(self, context):
        from . import animations, jba_bridge

        filename = animations.get_selected_jba_filename(context.scene)
        if not filename:
            self.report({'WARNING'}, "No animation selected")
            return {'CANCELLED'}

        filepath = animations.get_jba_filepath(context.scene, filename)
        if not filepath:
            self.report({'ERROR'}, "Selected .jba file no longer exists - try Refresh")
            return {'CANCELLED'}

        if jba_bridge.import_jba_onto_active_armature(self, context, filepath):
            self.report({'INFO'}, f"Imported '{filename}' onto '{context.active_object.name}'")
            return {'FINISHED'}

        return {'CANCELLED'}
    # Example: execute(context) -> {'FINISHED'}  (reports "Imported 'run_fwd.jba' onto 'Armature'")
