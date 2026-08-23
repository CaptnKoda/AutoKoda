"""Generic transfer of inputs (values + linked textures) from a source
Atroxa SWTOR node-group instance to the equivalent Koda SWTOR node-group
instance, matching purely by input socket *name*. Both shader families
now use identical socket names, so no per-field mapping table is needed
here -- the only remaining per-type mapping is ATROXA_NODE_NAMES <->
KODA_NODE_NAMES in config.py."""


from .socket_utils import copy_socket_to_socket


def transfer_group_inputs(source_node, target_node):
    """For every input socket on target_node, finds the same-named input
    on source_node and copies it across:
      - If the source input is linked (to a TEX_IMAGE node's Color/Alpha
        output) and the matching target input is also linked to a
        TEX_IMAGE node, the target node's image is set to match the
        source node's image -- node *names* don't need to match, only
        the socket name does.
      - Otherwise, copies default_value across (coerced to fit).

    Returns (values_copied, images_copied).
    """
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
            source_from_node = source_input.links[0].from_node
            if source_from_node.type != 'TEX_IMAGE' or not source_from_node.image:
                continue

            if not target_input.is_linked:
                print(
                    f"[Auto Koda] '{target_input.name}' is linked on the source "
                    f"but not on the Koda shader -- skipping image transfer"
                )
                continue

            target_from_node = target_input.links[0].from_node
            if target_from_node.type != 'TEX_IMAGE':
                continue

            try:
                target_from_node.image = source_from_node.image
                images_copied += 1
            except Exception as e:
                print(f"[Auto Koda] Failed to transfer image for '{target_input.name}': {e}")
        else:
            if copy_socket_to_socket(source_input, target_input):
                values_copied += 1
            else:
                print(f"[Auto Koda] Failed to copy socket '{target_input.name}'")

    return values_copied, images_copied