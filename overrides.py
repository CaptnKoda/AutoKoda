import bpy # type: ignore
from . import config
from .node_utils import find_group_node, get_group_output_node


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


def link_override_to_master(material, master_node, override_node):
    if not material.use_nodes:
        print(f"[ERROR] Material '{material.name}' has no node tree.")
        return 0

    nt = material.node_tree
    linked_count = 0

    for master_input in master_node.inputs:
        override_output = override_node.outputs.get(master_input.name)
        if override_output:
            try:
                nt.links.new(override_output, master_input)
                print(f"[LINK] {master_input.name}")
                linked_count += 1
            except RuntimeError:
                print(f"[FAIL LINK] {master_input.name} - incompatible socket type")

    return linked_count


def run_override_sync(do_sync_values=True, do_link_override=False):
    obj = bpy.context.object
    if not obj:
        print("❌ No active object selected")
        return

    print(f"▶ Processing object: {obj.name}")

    total_copied = 0
    total_links = 0

    for slot in obj.material_slots:
        mat = slot.material
        if not mat or not mat.use_nodes:
            continue
        nt = mat.node_tree

        for shader in config.Shader_Pairs:
            master_node = find_group_node(nt, exact_name=shader["master_name"])
            override_node = find_group_node(nt, suffix=shader["override_suffix"])

            if not master_node or not override_node:
                continue

            print(f"\n● Material: {mat.name}")
            print(f"  Master:   {master_node.node_tree.name}")
            print(f"  Override: {override_node.node_tree.name}")

            if do_sync_values:
                copied = sync_master_inputs_to_override(master_node, override_node.node_tree)
                total_copied += copied
                print(f"  → {copied} value(s) copied")

            if do_link_override:
                links = link_override_to_master(mat, master_node, override_node)
                total_links += links
                print(f"  → {links} link(s) created")

    print("\n✔ Done")
    if do_sync_values:
        print(f"✔ Total values copied: {total_copied}")
    if do_link_override:
        print(f"✔ Total links created: {total_links}")