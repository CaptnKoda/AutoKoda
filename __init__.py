import bpy
from . import config
from bpy.props import StringProperty
from bpy.types import AddonPreferences

# ======================================================
# ======================= Helpers ======================
# ======================================================
def get_shaders_blend_path():
    try:
        prefs = bpy.context.preferences.addons[__name__].preferences
        override_path = getattr(prefs, "shadersPath", "").strip()
        if override_path and override_path.lower().endswith(".blend"):
            return override_path
    except Exception as e:
        print(f"Could not retrieve shaders path from preferences: {e}")

    return config.DEFAULT_SHADERS


def assign_linked_material(obj, new_material, target_slot_index=None, preserve_inputs=False):
    if not obj or obj.type != 'MESH' or not new_material:
        return

    def copy_socket_value_safe(new_input, old_input):
        try:
            if not hasattr(new_input, 'default_value') or not hasattr(old_input, 'default_value'):
                return

            old_val = old_input.default_value

            if isinstance(old_val, (list, tuple)):
                old_val = list(old_val)
                if len(old_val) != len(new_input.default_value):
                    while len(old_val) < len(new_input.default_value):
                        old_val.append(1.0)
                    old_val = old_val[:len(new_input.default_value)]

            elif isinstance(new_input.default_value, float) and isinstance(old_val, (list, tuple)):
                old_val = float(old_val[0])

            new_input.default_value = old_val

        except Exception as e:
            print(f"[Auto Koda] Skipping socket '{new_input.name}': {e}")

    if target_slot_index is None:
        target_slot_index = next(
            (i for i, mat in enumerate(obj.data.materials)
             if mat and mat.name == new_material.name),
            None
        )

        if target_slot_index is None:
            target_slot_index = next(
                (i for i, mat in enumerate(obj.data.materials) if mat is None),
                0
            )

    if target_slot_index >= len(obj.data.materials):
        return

    old_mat = obj.data.materials[target_slot_index]

    if preserve_inputs and old_mat and old_mat.use_nodes and new_material.use_nodes:
        old_nodes_by_name = {node.name: node for node in old_mat.node_tree.nodes}

        for new_node in new_material.node_tree.nodes:
            old_node = old_nodes_by_name.get(new_node.name)
            if not old_node:
                continue

            old_inputs_by_name = {inp.name: inp for inp in old_node.inputs}
            for new_input in new_node.inputs:
                old_input = old_inputs_by_name.get(new_input.name)
                if old_input:
                    copy_socket_value_safe(new_input, old_input)

    obj.data.materials[target_slot_index] = new_material


def link_material_with_koda_group(koda_group_name):
    shaders_blend_path = get_shaders_blend_path()
    if not shaders_blend_path:
        print("[Auto Koda] Shaders.blend path invalid or not set.")
        return None

    # Ensure materials from the library are linked
    with bpy.data.libraries.load(shaders_blend_path, link=True) as (data_from, data_to):
        data_to.materials = data_from.materials

    for mat in bpy.data.materials:
        # CRITICAL FILTERS
        if mat.library is None:
            continue

        if mat.library.filepath != shaders_blend_path:
            continue

        if not mat.use_nodes:
            continue

        for node in mat.node_tree.nodes:
            if (
                node.type == 'GROUP'
                and node.node_tree
                and node.node_tree.name == koda_group_name
            ):
                # Always copy from a clean, linked template
                try:
                    return mat.copy()
                except Exception as e:
                    print(f"[Auto Koda] Failed to copy material for '{koda_group_name}': {e}")
                    return None

    print(f"[Auto Koda] No linked template material found for '{koda_group_name}'")
    return None


def transfer_textures(source_tree, target_tree):
    if not source_tree or not target_tree:
        return

    source_images = {
        node.name: node
        for node in source_tree.nodes
        if node.type == 'TEX_IMAGE'
    }

    for target_node in target_tree.nodes:
        if target_node.type != 'TEX_IMAGE':
            continue

        for hero_name, koda_name in config.HERO_GRAVITAS_TEX_NAMES.items():
            if target_node.name == koda_name and hero_name in source_images:
                source_node = source_images[hero_name]
                if source_node.image:
                    try:
                        target_node.image = source_node.image
                    except Exception as e:
                        print(
                            f"[Auto Koda] Failed to transfer image '{hero_name}' "
                            f"to '{koda_name}': {e}"
                        )


def copy_node_inputs(source_node, target_node):
    if not source_node or not target_node:
        return

    source_inputs = {inp.name: inp for inp in source_node.inputs}
    target_inputs = {inp.name: inp for inp in target_node.inputs}

    for name, target_input in target_inputs.items():
        source_input = source_inputs.get(name)
        if not source_input:
            continue

        try:
            old_val = source_input.default_value

            if isinstance(old_val, (list, tuple)):
                old_val = list(old_val)
                while len(old_val) < len(target_input.default_value):
                    old_val.append(1.0)
                old_val = old_val[:len(target_input.default_value)]
            elif isinstance(target_input.default_value, float) and isinstance(old_val, (list, tuple)):
                old_val = float(old_val[0])

            target_input.default_value = old_val
        except Exception as e:
            print(f"[Auto Koda] Failed to copy socket '{name}': {e}")


def remap_old_material_references(old_mat, new_mat):
    if not old_mat or not new_mat:
        return

    old_name = old_mat.name
    old_mat_ptr = old_mat

    for obj in bpy.data.objects:
        if not obj or not hasattr(obj.data, "materials"):
            continue

        for i, slot_mat in enumerate(obj.data.materials):
            if slot_mat == old_mat_ptr:
                obj.data.materials[i] = new_mat
                print(f"[Auto Koda] Remapped material on '{obj.name}' slot {i}")

    if old_mat_ptr.users <= 1:
        try:
            bpy.data.materials.remove(old_mat_ptr)
            print(f"[Auto Koda] Removed unused material '{old_name}'")
        except Exception as e:
            print(f"[Auto Koda] Failed to remove '{old_name}': {e}")


def process_object(obj):
    if not obj or obj.type != 'MESH':
        return

    for slot_index, slot in enumerate(obj.material_slots):
        mat = slot.material
        if not mat or not mat.use_nodes:
            continue

        if any(
            node.type == 'GROUP'
            and node.node_tree
            and node.node_tree.name in config.KODA_NODE_NAMES.values()
            for node in mat.node_tree.nodes
        ):
            continue

        hero_nodes = [
            node for node in mat.node_tree.nodes
            if node.type == 'GROUP'
            and node.node_tree
            and node.node_tree.name in config.HERO_GRAVITAS_NODE_NAMES.values()
        ]

        if not hero_nodes:
            continue

        for hero_node in hero_nodes:
            hero_key = next(
                (key for key, name in config.HERO_GRAVITAS_NODE_NAMES.items()
                 if name == hero_node.node_tree.name),
                None
            )

            if not hero_key:
                continue

            koda_shader_name = config.KODA_NODE_NAMES.get(hero_key)
            if not koda_shader_name:
                continue

            new_mat = link_material_with_koda_group(koda_shader_name)
            if not new_mat:
                continue

            koda_node = next(
                (node for node in new_mat.node_tree.nodes
                 if node.type == 'GROUP'
                 and node.node_tree
                 and node.node_tree.name == koda_shader_name),
                None
            )

            if hero_node and koda_node:
                copy_node_inputs(hero_node, koda_node)

            transfer_textures(mat.node_tree, new_mat.node_tree)

            assign_linked_material(
                obj,
                new_mat,
                target_slot_index=slot_index,
                preserve_inputs=True
            )

            old_name = mat.name
            mat.name = f"{old_name}_OLD"
            new_mat.name = old_name

            old_mat = bpy.data.materials.get(f"{old_name}_OLD")
            remap_old_material_references(old_mat, new_mat)

            print(
                f"[Auto Koda] Replaced '{old_name}' "
                f"with Koda shader '{koda_shader_name}' "
                f"in slot {slot_index}"
            )

def find_group_node(node_tree, exact_name=None, suffix=None):
    for node in node_tree.nodes:
        if node.type == 'GROUP' and node.node_tree:
            name = node.node_tree.name
            if exact_name and name == exact_name:
                return node
            if suffix and name.endswith(suffix):
                return node
    return None

def get_group_output_node(group_tree):
    for node in group_tree.nodes:
        if node.type == 'GROUP_OUTPUT':
            return node
    return None
    
def sync_master_inputs_to_override(master_node, override_tree):
    override_output = get_group_output_node(override_tree)
    if not override_output:
        return 0

    copied = 0
    for master_input in master_node.inputs:
        if not isinstance(master_input, Allowed_Socket_Types):
            continue
        override_input = override_output.inputs.get(master_input.name)
        if not override_input:
            continue
        if type(master_input) is not type(override_input):
            continue
        try:
            override_input.default_value = master_input.default_value
            copied += 1
            print(f"[COPY] {master_input.name} = {master_input.default_value}")
        except Exception:
            print(f"[SKIP] {master_input.name} (non-writable)")

    return copied
    
def link_override_to_master(material, master_node, override_node):
    if not material.use_nodes:
        print(f"[ERROR] Material '{material.name}' has no node tree.")
        return 0
    
    nt = material.node_tree
    linked_count = 0

    for master_input in master_node.inputs:
        override_output = override_node.outputs.get(master_input.name)
        if override_output:
            try:
                nt.links.new(override_output, master_input)
                print(f"[LINK] {master_input.name}")
                linked_count += 1
            except RuntimeError:
                print(f"[FAIL LINK] {master_input.name} - incompatible socket type")

    return linked_count

def run_override_sync(do_sync_values=True, do_link_override=False):
    obj = bpy.context.object
    if not obj:
        print("❌ No active object selected")
        return

    print(f"▶ Processing object: {obj.name}")

    total_copied = 0
    total_links = 0

    for slot in obj.material_slots:
        mat = slot.material
        if not mat or not mat.use_nodes:
            continue
        nt = mat.node_tree

        for shader in Shader_Pairs:
            master_node = find_group_node(nt, exact_name=shader["master_name"])
            override_node = find_group_node(nt, suffix=shader["override_suffix"])

            if not master_node or not override_node:
                continue

            print(f"\n● Material: {mat.name}")
            print(f"  Master:   {master_node.node_tree.name}")
            print(f"  Override: {override_node.node_tree.name}")

            if do_sync_values:
                copied = sync_master_inputs_to_override(master_node, override_node.node_tree)
                total_copied += copied
                print(f"  → {copied} value(s) copied")

            if do_link_override:
                links = link_override_to_master(mat, master_node, override_node)
                total_links += links
                print(f"  → {links} link(s) created")

    print("\n✔ Done")
    if do_sync_values:
        print(f"✔ Total values copied: {total_copied}")
    if do_link_override:
        print(f"✔ Total links created: {total_links}")


# ======================================================
# ===================== Operators ======================
# ======================================================
class Auto_Koda_Selected(bpy.types.Operator):
    bl_idname = "autokoda.convert_selected"
    bl_label = "Auto Koda"
    bl_description = "Convert the shader of the selected object to a Koda shader"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        shadersBlend = get_shaders_blend_path()
        if not shadersBlend:
            self.report({'ERROR'}, "Shaders Blend file path not set in preferences!")
            return {'CANCELLED'}

        for obj in bpy.context.selected_objects:
            if obj.type == 'MESH':
                process_object(obj)

        return {'FINISHED'}
        
        
class Auto_Koda_Crunch_Selected(bpy.types.Operator):
    bl_idname = "autokoda.crunch_selected"
    bl_label = "Auto Crunch"
    bl_description = "Run Auto Crunch (Selected)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        shadersBlend = get_shaders_blend_path()
        if not shadersBlend:
            self.report({'ERROR'}, "Shaders Blend file path not set in preferences!")
            return {'CANCELLED'}
        
        for obj in bpy.context.selected_objects:
            if obj.type == 'MESH':
                bpy.ops.zgswtor.process_named_mats(use_selection_only=True, use_overwrite_bool=False, use_collect_colliders_bool=True)
                bpy.ops.zgswtor.customize_swtor_shaders(use_selection_only=True)
                process_object(obj)
        
        return {'FINISHED'}

class Auto_Koda_OT_SyncOverride(bpy.types.Operator):
    bl_idname = "autokoda.sync_override"
    bl_label = "Sync Override"
    bl_description = "Sync Shader Node Group settings to Material Override Group"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        run_override_sync(do_sync_values=True, do_link_override=False)
        self.report({'INFO'}, "Sync Override executed")
        return {'FINISHED'}

class Auto_Koda_OT_LinkOverride(bpy.types.Operator):
    bl_idname = "autokoda.link_override"
    bl_label = "Link Override"
    bl_description = "Link Shader Node Group settings to Material Override Group"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        run_override_sync(do_sync_values=False, do_link_override=True)
        self.report({'INFO'}, "Link Override executed")
        return {'FINISHED'}

class Auto_Koda_OT_SyncLinkOverride(bpy.types.Operator):
    bl_idname = "autokoda.sync_link_override"
    bl_label = "Sync/Link Override"
    bl_description = "Sync and Link Shader Node Group settings to Material Override Group"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        run_override_sync(do_sync_values=True, do_link_override=True)
        self.report({'INFO'}, "Sync/Link Override executed")
        return {'FINISHED'}

# ======================================================
# ======================= Panels =======================
# ======================================================
class Auto_Koda_PT_Process_Materials(bpy.types.Panel):
    bl_label = "Process Materials"
    bl_idname = "VIEW3D_PT_auto_koda_process"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Auto Koda"

    def draw(self, context):
        layout = self.layout
        layout.operator(Auto_Koda_Selected.bl_idname,text="Auto Koda (Selected)",icon='RESTRICT_SELECT_OFF')
        layout.operator(Auto_Koda_Crunch_Selected.bl_idname, text="Auto Crunch (Selected)", icon='MODIFIER')



class Auto_Koda_PT_Settings(bpy.types.Panel):
    bl_options = {'DEFAULT_CLOSED'}
    bl_label = "AutoKoda Settings"
    bl_idname = "VIEW3D_PT_auto_koda_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Auto Koda"

    def draw(self, context):
        layout = self.layout
        status_box = layout.box()

        shaders_blend_loc = get_shaders_blend_path()

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

# ======================================================
# ===================== Preferences ====================
# ======================================================
class Auto_Koda_Preferences(AddonPreferences):
    bl_idname = __name__

    shadersPath: StringProperty(
        name="",
        subtype='FILE_PATH'
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Select your Shaders.blend file below")
        layout.prop(self, "shadersPath", text="Shaders.blend Path")

# ======================================================
# ==================== Registration ====================
# ======================================================
classes = [
    Auto_Koda_PT_Material_Overrides,
    Auto_Koda_Selected,
    Auto_Koda_Crunch_Selected,
    Auto_Koda_PT_Process_Materials,
    Auto_Koda_PT_Settings,
    Auto_Koda_Preferences,
    Auto_Koda_OT_SyncOverride,
    Auto_Koda_OT_LinkOverride,
    Auto_Koda_OT_SyncLinkOverride
]

Shader_Pairs = [
    {
        "master_name": "CaptnKoda SWTOR - SkinB Shader",
        "override_suffix": "Skin Override"
    },
    {
        "master_name": "CaptnKoda SWTOR - Garment Shader",
        "override_suffix": "Garment Override"
    },
    # Add more master/override pairs here
]

Allowed_Socket_Types = (
    bpy.types.NodeSocketFloat,
    bpy.types.NodeSocketFloatFactor,
    bpy.types.NodeSocketInt,
    bpy.types.NodeSocketBool,
    bpy.types.NodeSocketVector,
    bpy.types.NodeSocketColor,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
