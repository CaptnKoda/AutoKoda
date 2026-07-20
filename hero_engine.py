from . import config
from .socket_utils import coerce_value_for_socket


def find_hero_engine_node(node_tree):
    """Locate a ShaderNodeHeroEngine node, if present."""
    for node in node_tree.nodes:
        if node.bl_idname == config.HERO_ENGINE_NODE_TYPE:
            return node
    return None


def transfer_hero_engine_textures(hero_node, target_tree):
    """Reads images directly off the HeroEngine node's custom pointer
    properties and assigns them to matching Image Texture nodes by name."""
    target_images = {
        node.name: node
        for node in target_tree.nodes
        if node.type == 'TEX_IMAGE'
    }

    for hero_field, koda_node_name in config.HERO_ENGINE_TEX_FIELDS.items():
        image = getattr(hero_node, hero_field, None)
        if not image:
            continue

        target_node = target_images.get(koda_node_name)
        if not target_node:
            continue

        try:
            target_node.image = image
        except Exception as e:
            print(f"[Auto Koda] Failed to transfer '{hero_field}' -> '{koda_node_name}': {e}")


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