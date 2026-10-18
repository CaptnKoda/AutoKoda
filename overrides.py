import bpy # type: ignore
from . import config
from .node_utils import iter_node_materials, find_group_node, get_group_output_node


def sync_master_inputs_to_override(master_node, override_tree):
    override_output = get_group_output_node(override_tree)
    if not override_output:
        return 0

    copied = 0
    for master_input in master_node.inputs:
        if not isinstance(master_input, config.Allowed_Socket_Types):
            continue
        override_input = override_output.inputs.get(master_input.name)
        if not override_input:
            continue
        if type(master_input) is not type(override_input):
            continue
        try:
            override_input.default_value = master_input.default_value
            copied += 1
            print(f"[COPY] {master_input.name} = {master_input.default_value}")
        except Exception:
            print(f"[SKIP] {master_input.name} (non-writable)")

    return copied
# Example: sync_master_inputs_to_override(master_node, override_node.node_tree) -> 22


def link_override_to_master(node_tree, master_node, override_node):
    linked_count = 0

    for master_input in master_node.inputs:
        override_output = override_node.outputs.get(master_input.name)
        if override_output:
            try:
                node_tree.links.new(override_output, master_input)
                print(f"[LINK] {master_input.name}")
                linked_count += 1
            except RuntimeError:
                print(f"[FAIL LINK] {master_input.name} - incompatible socket type")

    return linked_count
# Example: link_override_to_master(mat.node_tree, master_node, override_node) -> 22


def _iter_override_pairs(node_tree):
    """Yields (master_node, override_node) for every Shader_Pairs entry
    with both nodes present in `node_tree`."""
    for shader in config.Shader_Pairs:
        master_node = find_group_node(node_tree, exact_name=shader["master_name"])
        override_node = find_group_node(node_tree, suffix=shader["override_suffix"])
        if master_node and override_node:
            yield master_node, override_node
# Example: list(_iter_override_pairs(mat.node_tree)) -> [(<ShaderNodeGroup "Group">, <ShaderNodeGroup "Group.001">)]


def run_override_sync(do_sync_values=True, do_link_override=False):
    obj = bpy.context.object
    if not obj:
        print("❌ No active object selected")
        return

    print(f"▶ Processing object: {obj.name}")

    total_copied = 0
    total_links = 0

    for _, mat in iter_node_materials(obj):
        for master_node, override_node in _iter_override_pairs(mat.node_tree):
            print(f"\n● Material: {mat.name}")
            print(f"  Master:   {master_node.node_tree.name}")
            print(f"  Override: {override_node.node_tree.name}")

            if do_sync_values:
                copied = sync_master_inputs_to_override(master_node, override_node.node_tree)
                total_copied += copied
                print(f"  → {copied} value(s) copied")

            if do_link_override:
                links = link_override_to_master(mat.node_tree, master_node, override_node)
                total_links += links
                print(f"  → {links} link(s) created")

    print("\n✔ Done")
    if do_sync_values:
        print(f"✔ Total values copied: {total_copied}")
    if do_link_override:
        print(f"✔ Total links created: {total_links}")
