"""Generic transfer of inputs (values + linked textures) from a source
HeroEngine SWTOR node-group instance to the equivalent Koda SWTOR node-group
instance, matching purely by input socket *name*. Both shader families
now use identical socket names, so no per-field mapping table is needed
here -- the only remaining per-type mapping is HERO_ENGINE_NODE_NAMES <->
KODA_NODE_NAMES in config.py."""

import logging
from .socket_utils import copy_socket_to_socket, get_source_image_node

log = logging.getLogger(__name__)


def _transfer_linked_image(source_input, target_input):
    """Copies the image feeding `source_input` onto the image node feeding
    `target_input`. Returns True if an image was transferred."""
    name = target_input.name

    source_img_node = get_source_image_node(source_input)
    if not source_img_node:
        log.warning(f"'{name}' is linked on the source but not to an image texture -- skipping")
        return False
    if not source_img_node.image:
        log.warning(f"'{name}': source image node '{source_img_node.name}' has no image assigned -- skipping")
        return False

    target_img_node = get_source_image_node(target_input)
    if not target_img_node:
        log.warning(f"'{name}' is not fed by an image texture on the Koda shader -- skipping image transfer")
        return False

    try:
        target_img_node.image = source_img_node.image
        return True
    except Exception:
        log.exception(f"Failed to transfer image for '{name}'")
        return False
# Example: _transfer_linked_image(hero_engine_node.inputs["DiffuseMap Color"], koda_node.inputs["DiffuseMap Color"]) -> True


def transfer_group_inputs(source_node, target_node):
    """Returns (values_copied, images_copied)."""
    source_inputs = {inp.name: inp for inp in source_node.inputs}
    target_names = {inp.name for inp in target_node.inputs}
    values_copied = 0
    images_copied = 0

    # Both shader families should share socket names, so a linked source
    # socket without a match means a texture is being lost.
    for name, source_input in source_inputs.items():
        if name not in target_names:
            if source_input.is_linked:
                log.warning(f"'{source_node.node_tree.name}' input '{name}' is linked, but '{target_node.node_tree.name}' has no such input")
            else:
                log.debug(f"'{target_node.node_tree.name}' has no input '{name}'")

    for target_input in target_node.inputs:
        source_input = source_inputs.get(target_input.name)
        if not source_input:
            log.debug(f"'{source_node.node_tree.name}' has no input '{target_input.name}'")
            continue

        if source_input.is_linked:
            images_copied += _transfer_linked_image(source_input, target_input)
        elif copy_socket_to_socket(source_input, target_input):
            values_copied += 1
        else:
            log.warning(f"Failed to copy socket '{target_input.name}'")

    return values_copied, images_copied
# Example: transfer_group_inputs(hero_engine_node, koda_node) -> (14, 5)  # (values copied, images copied)
