def coerce_value_for_socket(value, target_socket):
    """Coerce `value` to fit the shape expected by target_socket.default_value
    (e.g. RGBA list truncated/padded to match a 3 or 4 component socket, or
    a vector reduced to its first float for a scalar socket).

    Returns True if the value was successfully assigned, False otherwise.
    Errors are swallowed here; callers are responsible for logging with
    whatever context (node names, property names) they have available.
    """
    if not hasattr(target_socket, "default_value"):
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
        elif isinstance(target_default, float) and isinstance(value, (list, tuple)):
            value = float(value[0])

        target_socket.default_value = value
        return True
    except Exception:
        return False


def copy_socket_to_socket(source_socket, target_socket):
    """Copy source_socket.default_value onto target_socket, coercing shape."""
    if not hasattr(source_socket, "default_value"):
        return False
    return coerce_value_for_socket(source_socket.default_value, target_socket)