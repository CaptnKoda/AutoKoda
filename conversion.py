from . import config
from .material_io import link_material_with_koda_group, assign_linked_material, finalize_material_swap
from .node_utils import find_koda_group_node
from .hero_engine import find_atroxa_group_node
from .node_group_transfer import transfer_group_inputs


def _process_atroxa_material(obj, mat, slot_index, atroxa_node, key):
    koda_shader_name = config.KODA_NODE_NAMES.get(key)
    if not koda_shader_name:
        print(f"[Auto Koda] No Koda mapping for '{key}' on '{mat.name}'")
        return

    new_mat = link_material_with_koda_group(koda_shader_name)
    if not new_mat:
        return

    koda_node = find_koda_group_node(new_mat.node_tree, koda_shader_name)
    if not koda_node:
        print(f"[Auto Koda] Could not find Koda group node in linked material for '{koda_shader_name}'")
        return

    values_copied, images_copied = transfer_group_inputs(atroxa_node, koda_node)
    print(f"[Auto Koda] '{mat.name}': transferred {values_copied} value(s), {images_copied} image(s)")

    assign_linked_material(obj, new_mat, target_slot_index=slot_index, preserve_inputs=True)
    finalize_material_swap(obj, mat, new_mat, slot_index, koda_shader_name, log_label="Atroxa material")


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

        atroxa_node, key = find_atroxa_group_node(mat.node_tree)
        if atroxa_node:
            _process_atroxa_material(obj, mat, slot_index, atroxa_node, key)