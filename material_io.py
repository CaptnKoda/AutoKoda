import logging
import os
import bpy # type: ignore
from .prefs import get_shaders_blend_path
from .socket_utils import copy_socket_to_socket
from .node_utils import find_group_node

log = logging.getLogger(__name__)


def _link_template_materials(shaders_blend_path, koda_group_name):
    """Links the template material(s) from `shaders_blend_path` and returns
    them. Template materials are named after the Koda group they hold, so
    link just that one rather than every material (and all their node
    groups) in Shaders.blend. A custom Shaders.blend with different
    material names falls back to linking everything.

    The materials are returned straight from the load rather than looked
    up afterwards by comparing library paths: once the .blend has been
    saved, Blender stores the library path relative ("//..\\Shaders.blend"),
    and an already-linked library is reused under that stored path, so a
    string comparison against the absolute path misses a link that worked."""
    with bpy.data.libraries.load(shaders_blend_path, link=True) as (data_from, data_to):
        if koda_group_name in data_from.materials:
            data_to.materials = [koda_group_name]
        else:
            log.warning(
                f"'{shaders_blend_path}' has no material named '{koda_group_name}', "
                f"linking all {len(data_from.materials)} of its materials instead"
            )
            data_to.materials = list(data_from.materials)
    return [mat for mat in data_to.materials if mat is not None]
# Example: _link_template_materials(".../Shaders.blend", "CaptnKoda SWTOR - Garment Shader") -> [<Material "CaptnKoda SWTOR - Garment Shader">]


def _find_template(linked_materials, koda_group_name):
    """Returns the material in `linked_materials` that holds the
    `koda_group_name` group node, or None."""
    for mat in linked_materials:
        if mat.node_tree and find_group_node(mat.node_tree, exact_name=koda_group_name):
            return mat
    return None
# Example: _find_template(linked, "CaptnKoda SWTOR - Garment Shader") -> <Material "CaptnKoda SWTOR - Garment Shader">


def link_material_with_koda_group(koda_group_name):
    """Returns a local copy of the Shaders.blend template material holding
    `koda_group_name`, or None if it can't be found."""
    shaders_blend_path = get_shaders_blend_path()
    if not os.path.isfile(bpy.path.abspath(shaders_blend_path)):
        log.error(f"Shaders file does not exist: {bpy.path.abspath(shaders_blend_path)}")
        return None

    try:
        linked_materials = _link_template_materials(shaders_blend_path, koda_group_name)
    except Exception:
        log.exception(f"Failed to link materials from '{shaders_blend_path}'")
        return None

    template = _find_template(linked_materials, koda_group_name)
    if not template:
        log.error(
            f"No linked template material found for '{koda_group_name}' from '{shaders_blend_path}' "
            f"(linked: {[(m.name, m.library.filepath if m.library else None) for m in linked_materials]}, "
            f"loaded libraries: {[lib.filepath for lib in bpy.data.libraries]})"
        )
        return None

    try:
        return template.copy()
    except Exception:
        log.exception(f"Failed to copy material for '{koda_group_name}'")
        return None
# Example: link_material_with_koda_group("CaptnKoda SWTOR - Garment Shader") -> <Material "Garment Template.001">


def copy_matching_node_inputs(old_mat, new_mat):
    """Copies input values from `old_mat`'s nodes onto the same-named
    inputs of `new_mat`'s same-named nodes."""
    old_nodes_by_name = {node.name: node for node in old_mat.node_tree.nodes}

    for new_node in new_mat.node_tree.nodes:
        old_node = old_nodes_by_name.get(new_node.name)
        if not old_node:
            continue

        old_inputs_by_name = {inp.name: inp for inp in old_node.inputs}
        for new_input in new_node.inputs:
            old_input = old_inputs_by_name.get(new_input.name)
            if old_input and not copy_socket_to_socket(old_input, new_input):
                log.warning(f"Skipping socket '{new_input.name}' on node '{new_node.name}' of '{old_mat.name}'")


def remap_material_references(old_mat, new_mat):
    """Points every object slot using `old_mat` at `new_mat` instead."""
    for obj in bpy.data.objects:
        if not hasattr(obj.data, "materials"):
            continue

        for i, slot_mat in enumerate(obj.data.materials):
            if slot_mat == old_mat:
                obj.data.materials[i] = new_mat
                log.info(f"Remapped material on '{obj.name}' slot {i}")


def _remove_if_unused(mat):
    if mat.users > 1:
        log.warning(f"Keeping '{mat.name}': it still has {mat.users} user(s) after the swap")
        return

    name = mat.name
    try:
        bpy.data.materials.remove(mat)
        log.info(f"Removed unused material '{name}'")
    except Exception:
        log.exception(f"Failed to remove '{name}'")


def finalize_material_swap(mat, new_mat, slot_index, koda_shader_name):
    """Rename/remap/log step run after a replacement Koda material has been
    built: the new material takes over the old one's name, every user of
    the old material is pointed at the new one, and the old one is removed."""
    old_name = mat.name
    mat.name = f"{old_name}_OLD"
    new_mat.name = old_name

    remap_material_references(mat, new_mat)
    _remove_if_unused(mat)

    log.info(
        f"Replaced HeroEngine material '{old_name}' "
        f"with Koda shader '{koda_shader_name}' in slot {slot_index}"
    )
