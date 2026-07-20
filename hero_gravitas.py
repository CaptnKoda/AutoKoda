"""Conversion logic specific to ZeroGravitas's SWTOR node-group materials
('Hero Gravitas'). These materials store their data as node group sockets,
as opposed to the custom properties used by ShaderNodeHeroEngine — see
hero_engine.py for that counterpart."""

from . import config
from .socket_utils import copy_socket_to_socket


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

    for target_input in target_node.inputs:
        source_input = source_inputs.get(target_input.name)
        if not source_input:
            continue

        if not copy_socket_to_socket(source_input, target_input):
            print(f"[Auto Koda] Failed to copy socket '{target_input.name}'")