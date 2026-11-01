import logging
import bpy # type: ignore
from . import config
from .node_utils import iter_node_materials, find_group_node, get_group_output_node

log = logging.getLogger(__name__)


def sync_master_inputs_to_override(master_node, override_tree):
    override_output = get_group_output_node(override_tree)
    if not override_output:
        log.error(f"Override group '{override_tree.name}' has no Group Output node, nothing to sync to")
        return 0

    copied = 0
    for master_input in master_node.inputs:
        if not isinstance(master_input, config.Allowed_Socket_Types):
            log.debug(f"'{master_input.name}': socket type {type(master_input).__name__} isn't synced")
            continue
        override_input = override_output.inputs.get(master_input.name)
        if not override_input:
            log.debug(f"'{master_input.name}': no such socket on override group '{override_tree.name}'")
            continue
        if type(master_input) is not type(override_input):
            log.warning(
                f"'{master_input.name}': socket type differs between master "
                f"({type(master_input).__name__}) and override ({type(override_input).__name__}), skipping"
            )
            continue
        try:
            override_input.default_value = master_input.default_value
            copied += 1
            log.debug(f"Copied '{master_input.name}'")
        except Exception as e:
            log.warning(f"Could not copy '{master_input.name}': {type(e).__name__}: {e}")

    return copied
# Example: sync_master_inputs_to_override(master_node, override_node.node_tree) -> 22


def link_override_to_master(node_tree, master_node, override_node):
    linked_count = 0

    for master_input in master_node.inputs:
        override_output = override_node.outputs.get(master_input.name)
        if override_output:
            try:
                node_tree.links.new(override_output, master_input)
                log.debug(f"Linked '{master_input.name}'")
                linked_count += 1
            except RuntimeError as e:
                log.warning(f"Could not link '{master_input.name}': {e}")
        else:
            log.debug(f"'{master_input.name}': no such output on override node '{override_node.name}'")

    return linked_count
# Example: link_override_to_master(mat.node_tree, master_node, override_node) -> 22


def _iter_override_pairs(node_tree):
    """Yields (master_node, override_node) for every Shader_Pairs entry
    with both nodes present in `node_tree`."""
    for shader in config.Shader_Pairs:
        master_node = find_group_node(node_tree, exact_name=shader["master_name"])
        override_node = find_group_node(node_tree, suffix=shader["override_suffix"])
        if master_node and override_node:
            yield master_node, override_node
        elif master_node:
            log.debug(f"'{shader['master_name']}' present, but no group ending in '{shader['override_suffix']}'")
        elif override_node:
            log.warning(f"'{override_node.node_tree.name}' present, but its master '{shader['master_name']}' isn't")
# Example: list(_iter_override_pairs(mat.node_tree)) -> [(<ShaderNodeGroup "Group">, <ShaderNodeGroup "Group.001">)]


def run_override_sync(do_sync_values=True, do_link_override=False):
    """Returns (pairs_processed, values_copied, links_created) across the
    active object's materials."""
    obj = bpy.context.object
    if not obj:
        log.warning("No active object selected")
        return 0, 0, 0

    log.info(f"Processing object: {obj.name}")

    total_pairs = 0
    total_copied = 0
    total_links = 0

    for _, mat in iter_node_materials(obj):
        for master_node, override_node in _iter_override_pairs(mat.node_tree):
            total_pairs += 1
            log.info(
                f"Material '{mat.name}': master '{master_node.node_tree.name}', "
                f"override '{override_node.node_tree.name}'"
            )

            if do_sync_values:
                copied = sync_master_inputs_to_override(master_node, override_node.node_tree)
                total_copied += copied
                log.info(f"{copied} value(s) copied")

            if do_link_override:
                links = link_override_to_master(mat.node_tree, master_node, override_node)
                total_links += links
                log.info(f"{links} link(s) created")

    if not total_pairs:
        expected = [(s["master_name"], f"*{s['override_suffix']}") for s in config.Shader_Pairs]
        log.warning(f"No master/override pair in any material on '{obj.name}'; looking for: {expected}")

    return total_pairs, total_copied, total_links
# Example: run_override_sync(do_sync_values=True) -> (2, 44, 0)
