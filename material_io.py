import bpy # type: ignore
from .prefs import get_shaders_blend_path
from .socket_utils import copy_socket_to_socket


def link_material_with_koda_group(koda_group_name):
    shaders_blend_path = get_shaders_blend_path()
    if not shaders_blend_path:
        print("[Auto Koda] Shaders.blend path invalid or not set.")
        return None

    with bpy.data.libraries.load(shaders_blend_path, link=True) as (data_from, data_to):
        data_to.materials = data_from.materials

    for mat in bpy.data.materials:
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
                try:
                    return mat.copy()
                except Exception as e:
                    print(f"[Auto Koda] Failed to copy material for '{koda_group_name}': {e}")
                    return None

    print(f"[Auto Koda] No linked template material found for '{koda_group_name}'")
    return None


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


def finalize_material_swap(obj, mat, new_mat, slot_index, koda_shader_name, log_label="material"):
    """Shared rename/remap/log step used after both the Hero Gravitas and
    HeroEngine conversion paths successfully build a replacement material."""
    old_name = mat.name
    mat.name = f"{old_name}_OLD"
    new_mat.name = old_name

    old_mat = bpy.data.materials.get(f"{old_name}_OLD")
    remap_old_material_references(old_mat, new_mat)

    print(
        f"[Auto Koda] Replaced {log_label} '{old_name}' "
        f"with Koda shader '{koda_shader_name}' in slot {slot_index}"
    )