import bpy # type: ignore
from .prefs import get_shaders_blend_path
from .socket_utils import copy_socket_to_socket
from .node_utils import find_group_node


def link_material_with_koda_group(koda_group_name):
    shaders_blend_path = get_shaders_blend_path()
    if not shaders_blend_path:
        print("[Auto Koda] Shaders.blend path invalid or not set.")
        return None

    # Template materials are named after the Koda group they hold, so link
    # just that one rather than every material (and all their node groups)
    # in Shaders.blend. A custom Shaders.blend with different material
    # names falls back to linking everything and searching below.
    with bpy.data.libraries.load(shaders_blend_path, link=True) as (data_from, data_to):
        if koda_group_name in data_from.materials:
            data_to.materials = [koda_group_name]
        else:
            data_to.materials = data_from.materials

    for mat in bpy.data.materials:
        if mat.library is None:
            continue
        if mat.library.filepath != shaders_blend_path:
            continue
        if not mat.use_nodes:
            continue

        if find_group_node(mat.node_tree, exact_name=koda_group_name):
            try:
                return mat.copy()
            except Exception as e:
                print(f"[Auto Koda] Failed to copy material for '{koda_group_name}': {e}")
                return None

    print(f"[Auto Koda] No linked template material found for '{koda_group_name}'")
    return None
# Example: link_material_with_koda_group("CaptnKoda SWTOR - Garment Shader") -> <Material "Garment Template.001">


def assign_linked_material(obj, new_material, target_slot_index=None, preserve_inputs=False):
    if not obj or obj.type != 'MESH' or not new_material:
        return

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
                    if not copy_socket_to_socket(old_input, new_input):
                        print(f"[Auto Koda] Skipping socket '{new_input.name}'")

    obj.data.materials[target_slot_index] = new_material


def remap_old_material_references(old_mat, new_mat):
    if not old_mat or not new_mat:
        return

    old_name = old_mat.name

    for obj in bpy.data.objects:
        if not obj or not hasattr(obj.data, "materials"):
            continue

        for i, slot_mat in enumerate(obj.data.materials):
            if slot_mat == old_mat:
                obj.data.materials[i] = new_mat
                print(f"[Auto Koda] Remapped material on '{obj.name}' slot {i}")

    if old_mat.users <= 1:
        try:
            bpy.data.materials.remove(old_mat)
            print(f"[Auto Koda] Removed unused material '{old_name}'")
        except Exception as e:
            print(f"[Auto Koda] Failed to remove '{old_name}': {e}")


def finalize_material_swap(mat, new_mat, slot_index, koda_shader_name, log_label="material"):
    """Rename/remap/log step run after a replacement Koda material has been
    built: the new material takes over the old one's name, every user of
    the old material is pointed at the new one, and the old one is removed."""
    old_name = mat.name
    mat.name = f"{old_name}_OLD"
    new_mat.name = old_name

    remap_old_material_references(mat, new_mat)

    print(
        f"[Auto Koda] Replaced {log_label} '{old_name}' "
        f"with Koda shader '{koda_shader_name}' in slot {slot_index}"
    )