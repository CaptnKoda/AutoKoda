import logging
import bpy  # type: ignore
import bmesh # type: ignore
import math
from .prefs import get_clear_custom_normals, get_auto_smooth, get_merge_sharp_from_normals

# Merge by distance threshold, in Blender units (1e-5).
MERGE_DISTANCE = 0.00001

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


def _merge_by_distance_keeping_sharp(obj):
    """Merges `obj`'s vertices by distance with the Edit Mode operator's
    use_sharp_edge_from_normals option, which is the only route to that
    option (the bmesh op doesn't expose it, as far as I know). Changes the
    selection and active object; the caller restores them. Returns True on
    success."""
    entered_edit = False
    try:
        for selected in list(bpy.context.selected_objects):
            selected.select_set(False)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        bpy.ops.object.mode_set(mode='EDIT')
        entered_edit = True
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=MERGE_DISTANCE, use_sharp_edge_from_normals=True)
        return True
    except (RuntimeError, TypeError) as e:
        log.warning(f"Merge by distance with sharp edges from normals failed on '{obj.name}': {e}")
        return False
    finally:
        if entered_edit:
            bpy.ops.object.mode_set(mode='OBJECT')
# Example: _merge_by_distance_keeping_sharp(body) -> True


def _restore_selection(selected, active):
    """Re-selects exactly `selected` and makes `active` the active object."""
    for obj in list(bpy.context.selected_objects):
        obj.select_set(False)
    for obj in selected:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = active


def _merge_and_quadify(mesh, merge=True):
    """Merges vertices by distance (unless `merge` is False because that
    already happened), then joins triangles into quads."""
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)

        if merge:
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=MERGE_DISTANCE)
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
    """For each mesh object: merge vertices by distance (optionally keeping
    sharp edges from custom normals), clear custom split normals data
    (unless turned off in the addon preferences), convert triangles to
    quads, and enable Shade Auto Smooth (unless turned off). A mesh that
    fails doesn't stop the others. Returns how many meshes had every step
    succeed."""
    clear_normals = get_clear_custom_normals()
    use_auto_smooth = get_auto_smooth()
    merge_sharp = get_merge_sharp_from_normals()
    if not clear_normals:
        log.info("Clear Custom Split Normals is off in preferences, keeping custom normals")
    if not use_auto_smooth:
        log.info("Shade Auto Smooth is off in preferences, leaving shading untouched")

    prev_selected = list(bpy.context.selected_objects)
    prev_active = bpy.context.view_layer.objects.active

    prepared = 0
    try:
        for obj in objects:
            try:
                # Before the normals are cleared, so they can become sharp edges
                merged_with_sharp = merge_sharp and _merge_by_distance_keeping_sharp(obj)
                normals_cleared = _clear_custom_normals(obj) if clear_normals else True
                _merge_and_quadify(obj.data, merge=not merged_with_sharp)
                smoothed = _shade_auto_smooth(obj) if use_auto_smooth else True
            except Exception:
                log.exception(f"Failed to prepare mesh on '{obj.name}'")
                continue

            if normals_cleared and smoothed and (merged_with_sharp or not merge_sharp):
                prepared += 1
                log.info(f"Prepared mesh on '{obj.name}'")
            else:
                log.warning(
                    f"Mesh on '{obj.name}' only partly prepared (normals cleared: {normals_cleared}, "
                    f"auto smooth: {smoothed}, sharp-edge merge: {merged_with_sharp if merge_sharp else 'off'})"
                )
    finally:
        if merge_sharp:
            _restore_selection(prev_selected, prev_active)

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
