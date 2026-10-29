from . import config

_HERO_ENGINE_NAME_TO_KEY = {name: key for key, name in config.HERO_ENGINE_NODE_NAMES.items()}


def iter_node_materials(obj):
    """Yields (slot_index, material) for every slot on `obj` holding a
    node-based material."""
    for slot_index, slot in enumerate(obj.material_slots):
        mat = slot.material
        if mat and mat.use_nodes:
            yield slot_index, mat
# Example: list(iter_node_materials(body)) -> [(0, <Material "skin">), (2, <Material "chest">)]


def iter_group_nodes(node_tree):
    """Yields every Group node in `node_tree` that has a node tree assigned."""
    for node in node_tree.nodes:
        if node.type == 'GROUP' and node.node_tree:
            yield node
# Example: list(iter_group_nodes(mat.node_tree)) -> [<ShaderNodeGroup "Group">, <ShaderNodeGroup "Group.001">]


def find_group_node(node_tree, exact_name=None, suffix=None):
    for node in iter_group_nodes(node_tree):
        name = node.node_tree.name
        if exact_name and name == exact_name:
            return node
        if suffix and name.endswith(suffix):
            return node
    return None
# Example: find_group_node(nt, suffix="Skin Override") -> <ShaderNodeGroup "Group.001"> (tree "Ashara Skin Override")


def find_hero_engine_group_node(node_tree):
    """Locate the first HeroEngine SWTOR group node in a material's tree, if
    present, along with its derived-type key (matching KODA_NODE_NAMES).
    Returns (node, key) or (None, None)."""
    for node in iter_group_nodes(node_tree):
        key = _HERO_ENGINE_NAME_TO_KEY.get(node.node_tree.name)
        if key:
            return node, key
    return None, None
# Example: find_hero_engine_group_node(mat.node_tree) -> (<ShaderNodeGroup "Group">, "GARMENT")


def is_koda_group_node(node):
    """True if `node` is a Group node using one of the Koda shader groups."""
    return (
        node.type == 'GROUP'
        and node.node_tree is not None
        and node.node_tree.name in config.KODA_NODE_NAMES.values()
    )
# Example: is_koda_group_node(node) -> True (tree "CaptnKoda SWTOR - Garment Shader")


def get_group_output_node(group_tree):
    for node in group_tree.nodes:
        if node.type == 'GROUP_OUTPUT':
            return node
    return None
# Example: get_group_output_node(override_tree) -> <NodeGroupOutput "Group Output">
