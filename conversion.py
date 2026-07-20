from . import config
from .material_io import link_material_with_koda_group, assign_linked_material, finalize_material_swap
from .node_utils import find_koda_group_node
from .hero_gravitas import copy_node_inputs, transfer_textures
from .hero_engine import find_hero_engine_node, transfer_hero_engine_textures, transfer_hero_engine_properties


def _process_hero_gravitas_material(obj, mat, slot_index, hero_nodes):
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

        koda_node = find_koda_group_node(new_mat.node_tree, koda_shader_name)

        if hero_node and koda_node:
            copy_node_inputs(hero_node, koda_node)

        transfer_textures(mat.node_tree, new_mat.node_tree)

        assign_linked_material(obj, new_mat, target_slot_index=slot_index, preserve_inputs=True)
        finalize_material_swap(obj, mat, new_mat, slot_index, koda_shader_name, log_label="material")


def _process_hero_engine_material(obj, mat, slot_index):
    hero_engine_node = find_hero_engine_node(mat.node_tree)
    if not hero_engine_node:
        return False

    key = config.HERO_ENGINE_DERIVED_TO_KEY.get(hero_engine_node.derived)
    koda_shader_name = config.KODA_NODE_NAMES.get(key) if key else None

    if not koda_shader_name:
        print(f"[Auto Koda] No Koda mapping for derived='{hero_engine_node.derived}' on '{mat.name}'")
        return True

    new_mat = link_material_with_koda_group(koda_shader_name)
    if not new_mat:
        return True

    koda_node = find_koda_group_node(new_mat.node_tree, koda_shader_name)

    transfer_hero_engine_properties(hero_engine_node, koda_node)
    transfer_hero_engine_textures(hero_engine_node, new_mat.node_tree)

    assign_linked_material(obj, new_mat, target_slot_index=slot_index, preserve_inputs=True)
    finalize_material_swap(obj, mat, new_mat, slot_index, koda_shader_name, log_label="HeroEngine material")
    return True


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

        if hero_nodes:
            _process_hero_gravitas_material(obj, mat, slot_index, hero_nodes)
        else:
            _process_hero_engine_material(obj, mat, slot_index)