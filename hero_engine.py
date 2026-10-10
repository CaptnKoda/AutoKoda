"""Locates Atroxa SWTOR node-group materials for conversion.py's pipeline."""

from . import config
from .node_utils import iter_group_nodes
from .socket_utils import coerce_value_for_socket


def find_atroxa_group_node(node_tree):
    """Locate the first Atroxa SWTOR group node in a material's tree, if
    present, along with its derived-type key (matching KODA_NODE_NAMES).
    Returns (node, key) or (None, None)."""
    for node in iter_group_nodes(node_tree):
        key = next(
            (k for k, name in config.ATROXA_NODE_NAMES.items() if name == node.node_tree.name),
            None
        )
        if key:
            return node, key
    return None, None
# Example: find_atroxa_group_node(mat.node_tree) -> (<ShaderNodeGroup "Group">, "GARMENT")


def transfer_hero_engine_properties(hero_node, koda_node):
    """Copies HeroEngine's custom scalar/color properties onto matching
    input sockets of a Koda group node, using HERO_ENGINE_PROP_TO_KODA_INPUT."""
    if not koda_node:
        return 0

    koda_inputs = {inp.name: inp for inp in koda_node.inputs}
    copied = 0

    for hero_prop, koda_input_name in config.HERO_ENGINE_PROP_TO_KODA_INPUT.items():
        if not hasattr(hero_node, hero_prop):
            continue

        koda_input = koda_inputs.get(koda_input_name)
        if not koda_input:
            continue

        value = getattr(hero_node, hero_prop)

        if coerce_value_for_socket(value, koda_input):
            copied += 1
        else:
            print(f"[Auto Koda] Failed to copy '{hero_prop}' -> '{koda_input_name}'")

    return copied
# Example: transfer_hero_engine_properties(hero_node, koda_node) -> 13
