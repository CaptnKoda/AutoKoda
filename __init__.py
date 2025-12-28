import bpy
from . import config
from bpy.props import StringProperty
from bpy.types import AddonPreferences


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

    with bpy.data.libraries.load(shaders_blend_path, link=True) as (data_from, data_to):
        data_to.materials = list(data_from.materials)

    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue

        for node in mat.node_tree.nodes:
            if (
                node.type == 'GROUP'
                and node.node_tree
                and node.node_tree.name == koda_group_name
            ):
                try:
                    return mat.copy()
                except Exception as e:
                    print(f"[Auto Koda] Failed to copy material for '{koda_group_name}': {e}")
                    return None

    print(f"[Auto Koda] No material found containing node group '{koda_group_name}'")
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


class Auto_Koda_Selected(bpy.types.Operator):
    bl_idname = "autokoda.convert_selected"
    bl_label = "Auto Koda"
    bl_description = "Convert the shader of the selected object to a Koda shader"

    def execute(self, context):
        shadersBlend = get_shaders_blend_path()
        if not shadersBlend:
            self.report({'ERROR'}, "Shaders Blend file path not set in preferences!")
            return {'CANCELLED'}

        for obj in bpy.context.selected_objects:
            if obj.type == 'MESH':
                process_object(obj)

        return {'FINISHED'}


class Auto_Koda_Button(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_auto_koda"
    bl_category = "Auto Koda"
    bl_label = "Auto Koda"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        status_box = layout.box()

        shaders_blend_loc = get_shaders_blend_path()

        if not shaders_blend_loc or ".blend" not in shaders_blend_loc:
            status_box.alert = True
            row = status_box.row()
            row.label(text=f"Shaders.blend path not set or invalid: {shaders_blend_loc}", icon='ERROR')
            row = status_box.row()
            row.operator(
                "preferences.addon_show",
                text="Set Shaders.blend",
                icon='FILE_FOLDER'
            ).module = __name__

        elif shaders_blend_loc == config.DEFAULT_SHADERS:
            row = status_box.row()
            row.label(text="Using default Shaders.blend", icon='CHECKMARK')
            row = status_box.row()
            row.operator(
                "preferences.addon_show",
                text="Set Custom Shaders.blend",
                icon='FILE_FOLDER'
            ).module = __name__

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

        layout.row().operator(
            Auto_Koda_Selected.bl_idname,
            text="Auto Koda (Selected)",
            icon='RESTRICT_SELECT_OFF'
        )


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


classes = [
    Auto_Koda_Selected,
    Auto_Koda_Button,
    Auto_Koda_Preferences
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
