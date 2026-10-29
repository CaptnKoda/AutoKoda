from . import config
from .material_io import link_material_with_koda_group, copy_matching_node_inputs, finalize_material_swap
from .node_utils import iter_node_materials, find_group_node, find_hero_engine_group_node, is_koda_group_node
from .node_group_transfer import transfer_group_inputs


def _process_hero_engine_material(mat, slot_index, hero_engine_node, key):
    koda_shader_name = config.KODA_NODE_NAMES.get(key)
    if not koda_shader_name:
        print(f"[Auto Koda] No Koda mapping for '{key}' on '{mat.name}'")
        return

    new_mat = link_material_with_koda_group(koda_shader_name)
    if not new_mat:
        return

    koda_node = find_group_node(new_mat.node_tree, exact_name=koda_shader_name)
    if not koda_node:
        print(f"[Auto Koda] Could not find Koda group node in linked material for '{koda_shader_name}'")
        return

    values_copied, images_copied = transfer_group_inputs(hero_engine_node, koda_node)
    print(f"[Auto Koda] '{mat.name}': transferred {values_copied} value(s), {images_copied} image(s)")

    copy_matching_node_inputs(mat, new_mat)
    finalize_material_swap(mat, new_mat, slot_index, koda_shader_name)


def process_object(obj):
    """Swaps every HeroEngine SWTOR material on `obj` for its Koda equivalent."""
    for slot_index, mat in iter_node_materials(obj):
        if any(is_koda_group_node(node) for node in mat.node_tree.nodes):
            continue

        hero_engine_node, key = find_hero_engine_group_node(mat.node_tree)
        if hero_engine_node:
            _process_hero_engine_material(mat, slot_index, hero_engine_node, key)
