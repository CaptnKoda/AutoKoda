import logging
import bpy  # type: ignore
import bmesh # type: ignore
import math

log = logging.getLogger(__name__)


def toggle_subsurf_viewport_display(objects):
    """Toggle viewport visibility of all Subdivision Surface modifiers on the
    given objects. If any modifier is currently shown in viewport, all are
    turned off; otherwise all are turned on."""
    subsurf_mods = [
        mod
        for obj in objects
        for mod in obj.modifiers
        if mod.type == 'SUBSURF'
    ]

    if not subsurf_mods:
        log.warning(f"No Subdivision Surface modifiers found on: {[obj.name for obj in objects]}")
        return 0

    new_state = not any(mod.show_viewport for mod in subsurf_mods)
    for mod in subsurf_mods:
        mod.show_viewport = new_state

    log.info(f"Set {len(subsurf_mods)} Subdivision Surface modifier(s) viewport display to {new_state}")
    return len(subsurf_mods)
# Example: toggle_subsurf_viewport_display(context.selected_objects) -> 3


def _clear_custom_normals(obj):
    """Returns False if the clear raised an error. A CANCELLED result is
    only logged: it's what a mesh with no custom normals may return."""
    try:
        with bpy.context.temp_override(object=obj, active_object=obj):
            result = bpy.ops.mesh.customdata_custom_splitnormals_clear()
    except RuntimeError as e:
        log.warning(f"Failed to clear custom normals on '{obj.name}': {e}")
        return False
    log.debug(f"Clear custom normals on '{obj.name}' returned {result}")
    return True


def _merge_and_quadify(mesh):
    """Merges vertices by distance, then joins triangles into quads."""
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)

        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.00001)
        bmesh.ops.join_triangles(
            bm,
            faces=bm.faces,
            cmp_uvs=True,
            cmp_vcols=True,
            cmp_seam=True,
            cmp_sharp=True,
            cmp_materials=True,
            angle_face_threshold=math.radians(40.0),
            angle_shape_threshold=math.radians(40.0),
        )

        bm.to_mesh(mesh)
    finally:
        bm.free()
    mesh.update()


def _shade_auto_smooth(obj):
    """Returns True if auto smooth was enabled."""
    try:
        with bpy.context.temp_override(object=obj, active_object=obj, selected_editable_objects=[obj]):
            if hasattr(bpy.ops.object, "shade_auto_smooth"):
                result = bpy.ops.object.shade_auto_smooth()
            else:
                result = bpy.ops.object.shade_smooth(use_auto_smooth=True)
    except RuntimeError as e:
        log.warning(f"Failed to enable auto smooth on '{obj.name}': {e}")
        return False

    if 'FINISHED' not in result:
        log.warning(f"Auto smooth on '{obj.name}' returned {result}")
        return False
    return True


def prepare_meshes(objects):
    """For each mesh object: clear custom split normals data, merge
    vertices by distance, convert triangles to quads, and enable Shade
    Auto Smooth. A mesh that fails doesn't stop the others. Returns how
    many meshes had every step succeed."""
    prepared = 0
    for obj in objects:
        try:
            normals_cleared = _clear_custom_normals(obj)
            _merge_and_quadify(obj.data)
            smoothed = _shade_auto_smooth(obj)
        except Exception:
            log.exception(f"Failed to prepare mesh on '{obj.name}'")
            continue

        if normals_cleared and smoothed:
            prepared += 1
            log.info(f"Prepared mesh on '{obj.name}'")
        else:
            log.warning(f"Mesh on '{obj.name}' only partly prepared (normals cleared: {normals_cleared}, auto smooth: {smoothed})")

    return prepared
# Example: prepare_meshes([body, head, cape]) -> 3


def assign_material_name(objects, name):
    """Gives every material slot on the given mesh objects a material named
    `name`. Reuses an existing material of that name if there is one;
    otherwise renames the slot's current material (or a copy of it, if
    something else also uses it). Materials left unused by the swap are
    deleted."""
    target = bpy.data.materials.get(name)
    replaced = set()
    assigned = 0

    for obj in objects:
        if obj.type != 'MESH':
            log.debug(f"'{obj.name}' is a {obj.type}, not assigning material '{name}'")
            continue

        if not obj.material_slots:
            log.warning(f"'{obj.name}' has no material slots, so it can't take material '{name}'")

        for slot in obj.material_slots:
            if target is None:
                mat = slot.material
                if mat is None:
                    mat = bpy.data.materials.new(name)
                elif mat.users > 1:
                    mat = mat.copy()
                mat.name = name
                target = mat

            if slot.material and slot.material != target:
                replaced.add(slot.material)
            slot.material = target
            assigned += 1

    for mat in replaced:
        if mat.users == 0:
            bpy.data.materials.remove(mat)

    return assigned
# Example: assign_material_name([archetype, chest], "chest_tight_med_ge_a15mercenary05_m") -> 2
