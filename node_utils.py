def find_group_node(node_tree, exact_name=None, suffix=None):
    for node in node_tree.nodes:
        if node.type == 'GROUP' and node.node_tree:
            name = node.node_tree.name
            if exact_name and name == exact_name:
                return node
            if suffix and name.endswith(suffix):
                return node
    return None


def get_group_output_node(group_tree):
    for node in group_tree.nodes:
        if node.type == 'GROUP_OUTPUT':
            return node
    return None


def find_koda_group_node(node_tree, koda_shader_name):
    """Locate the Koda group node by exact node_tree name. Shared by both
    the Hero Gravitas and HeroEngine conversion paths."""
    return find_group_node(node_tree, exact_name=koda_shader_name)