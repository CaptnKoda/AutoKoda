import logging
from . import config
from .material_io import link_material_with_koda_group, copy_matching_node_inputs, finalize_material_swap
from .node_utils import iter_node_materials, find_group_node, find_hero_engine_group_node, is_koda_group_node
from .node_group_transfer import transfer_group_inputs

log = logging.getLogger(__name__)


def _process_hero_engine_material(mat, slot_index, hero_engine_node, key):
    """Returns True if `mat` was replaced by its Koda equivalent."""
    koda_shader_name = config.KODA_NODE_NAMES.get(key)
    if not koda_shader_name:
        log.error(f"No Koda mapping for '{key}' on '{mat.name}'")
        return False

    new_mat = link_material_with_koda_group(koda_shader_name)
    if not new_mat:
        log.error(f"'{mat.name}' not converted: no template material for '{koda_shader_name}'")
        return False

    koda_node = find_group_node(new_mat.node_tree, exact_name=koda_shader_name)
    if not koda_node:
        log.error(f"Could not find Koda group node in linked material for '{koda_shader_name}'")
        return False

    values_copied, images_copied = transfer_group_inputs(hero_engine_node, koda_node)
    log.info(f"'{mat.name}': transferred {values_copied} value(s), {images_copied} image(s)")

    copy_matching_node_inputs(mat, new_mat)
    finalize_material_swap(mat, new_mat, slot_index, koda_shader_name)
    return True


def process_object(obj):
    """Swaps every HeroEngine SWTOR material on `obj` for its Koda
    equivalent. Returns (converted_count, failed_count). A material that
    fails doesn't stop the rest of the object's materials."""
    converted = 0
    failed = 0

    for slot_index, mat in iter_node_materials(obj):
        mat_name = mat.name
        try:
            if any(is_koda_group_node(node) for node in mat.node_tree.nodes):
                log.debug(f"'{mat_name}' on '{obj.name}' already uses a Koda shader, skipping")
                continue

            hero_engine_node, key = find_hero_engine_group_node(mat.node_tree)
            if not hero_engine_node:
                groups = [n.node_tree.name for n in mat.node_tree.nodes if n.type == 'GROUP' and n.node_tree]
                log.warning(f"'{mat_name}' on '{obj.name}' has no HeroEngine shader, not converted (group nodes: {groups})")
                continue

            if _process_hero_engine_material(mat, slot_index, hero_engine_node, key):
                converted += 1
            else:
                failed += 1
        except Exception:
            log.exception(f"Failed to convert material '{mat_name}' on '{obj.name}' (slot {slot_index})")
            failed += 1

    return converted, failed
# Example: process_object(body) -> (3, 0)
