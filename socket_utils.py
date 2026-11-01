import logging

log = logging.getLogger(__name__)


def _describe_socket(socket):
    return f"'{socket.name}' ({type(socket).__name__}) on node '{socket.node.name}'"
# Example: _describe_socket(socket) -> "'Palette1 Hue' (NodeSocketFloat) on node 'Group'"


def coerce_value_for_socket(value, target_socket):
    """Coerce `value` to fit the shape expected by target_socket.default_value
    (e.g. RGBA list truncated/padded to match a 3 or 4 component socket, or
    a vector reduced to its first float for a scalar socket).

    Returns True if the value was successfully assigned, False otherwise.
    The reason for a failure is logged here; callers add whatever context
    (property names) they have available.
    """
    if not hasattr(target_socket, "default_value"):
        log.debug(f"Socket {_describe_socket(target_socket)} has no default_value to set")
        return False

    try:
        target_default = target_socket.default_value

        if isinstance(value, (list, tuple)):
            value = list(value)
            if hasattr(target_default, "__len__"):
                target_len = len(target_default)
                while len(value) < target_len:
                    value.append(1.0)
                value = value[:target_len]
            else:
                value = float(value[0])

        target_socket.default_value = value
        return True
    except Exception as e:
        log.warning(f"Could not set socket {_describe_socket(target_socket)} to {value!r}: {type(e).__name__}: {e}")
        return False
# Example: coerce_value_for_socket([0.61, 0.92, 1.0], color_socket) -> True (socket set to (0.61, 0.92, 1.0, 1.0))


def copy_socket_to_socket(source_socket, target_socket):
    """Copy source_socket.default_value onto target_socket, coercing shape."""
    if not hasattr(source_socket, "default_value"):
        log.debug(f"Socket {_describe_socket(source_socket)} has no default_value to copy")
        return False
    return coerce_value_for_socket(source_socket.default_value, target_socket)
# Example: copy_socket_to_socket(hero_engine_node.inputs["Palette1 Hue"], koda_node.inputs["Palette1 Hue"]) -> True


def resolve_source_socket(socket, max_depth=32):
    """Follow a linked input back through Reroute nodes to the real source socket."""
    if not socket.is_linked:
        return None
    src = socket.links[0].from_socket
    for _ in range(max_depth):
        if src.node.type != 'REROUTE':
            return src
        inp = src.node.inputs[0]
        if not inp.is_linked:
            log.debug(f"Reroute '{src.node.name}' feeding '{socket.name}' has no input")
            return None
        src = inp.links[0].from_socket
    log.warning(f"Gave up following reroutes into '{socket.name}' after {max_depth} nodes")
    return None
# Example: resolve_source_socket(node.inputs["DiffuseMap Color"]) -> <NodeSocketColor "Color"> on "Image Texture.002"


def get_source_image_node(socket):
    """Follow `socket` back through any Reroute nodes and return the
    TEX_IMAGE node feeding it, or None if it isn't fed by an image."""
    src = resolve_source_socket(socket)
    if src and src.node.type == 'TEX_IMAGE':
        return src.node
    if src:
        log.debug(f"'{socket.name}' is fed by a {src.node.type} node ('{src.node.name}'), not an image texture")
    return None
# Example: get_source_image_node(node.inputs["DiffuseMap Color"]) -> <ShaderNodeTexImage "Image Texture.002">
