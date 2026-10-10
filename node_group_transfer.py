"""Generic transfer of inputs (values + linked textures) from a source
Atroxa SWTOR node-group instance to the equivalent Koda SWTOR node-group
instance, matching purely by input socket *name*. Both shader families
now use identical socket names, so no per-field mapping table is needed
here -- the only remaining per-type mapping is ATROXA_NODE_NAMES <->
KODA_NODE_NAMES in config.py."""

from .socket_utils import copy_socket_to_socket, get_source_image_node


def transfer_group_inputs(source_node, target_node):
    if not source_node or not target_node:
        return 0, 0

    source_inputs = {inp.name: inp for inp in source_node.inputs}
    values_copied = 0
    images_copied = 0

    for target_input in target_node.inputs:
        source_input = source_inputs.get(target_input.name)
        if not source_input:
            continue

        if source_input.is_linked:
            source_img_node = get_source_image_node(source_input)
            if not source_img_node or not source_img_node.image:
                print(
                    f"[Auto Koda] '{target_input.name}' is linked on the source "
                    f"but not to an image texture -- skipping"
                )
                continue

            if not target_input.is_linked:
                print(
                    f"[Auto Koda] '{target_input.name}' is linked on the source "
                    f"but not on the Koda shader -- skipping image transfer"
                )
                continue

            target_img_node = get_source_image_node(target_input)
            if not target_img_node:
                print(
                    f"[Auto Koda] '{target_input.name}' on the Koda shader is not "
                    f"fed by an image texture node -- skipping image transfer"
                )
                continue

            try:
                target_img_node.image = source_img_node.image
                images_copied += 1
            except Exception as e:
                print(f"[Auto Koda] Failed to transfer image for '{target_input.name}': {e}")
        else:
            if copy_socket_to_socket(source_input, target_input):
                values_copied += 1
            else:
                print(f"[Auto Koda] Failed to copy socket '{target_input.name}'")

    return values_copied, images_copied
# Example: transfer_group_inputs(atroxa_node, koda_node) -> (14, 5)  # (values copied, images copied)
