import bpy  # type: ignore
import bmesh # type: ignore
import math


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
        print("[Auto Koda] No Subdivision Surface modifiers found on selected objects.")
        return 0

    new_state = not any(mod.show_viewport for mod in subsurf_mods)
    for mod in subsurf_mods:
        mod.show_viewport = new_state

    print(f"[Auto Koda] Set {len(subsurf_mods)} Subdivision Surface modifier(s) viewport display to {new_state}")
    return len(subsurf_mods)
# Example: toggle_subsurf_viewport_display(context.selected_objects) -> 3


def _clear_custom_normals(obj):
    try:
        with bpy.context.temp_override(object=obj, active_object=obj):
            bpy.ops.mesh.customdata_custom_splitnormals_clear()
    except RuntimeError as e:
        print(f"[Auto Koda] Failed to clear custom normals on '{obj.name}': {e}")


def _merge_and_quadify(mesh):
    """Merges vertices by distance, then joins triangles into quads."""
    bm = bmesh.new()
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
    bm.free()
    mesh.update()


def _shade_auto_smooth(obj):
    try:
        with bpy.context.temp_override(object=obj, active_object=obj, selected_editable_objects=[obj]):
            if hasattr(bpy.ops.object, "shade_auto_smooth"):
                bpy.ops.object.shade_auto_smooth()
            else:
                bpy.ops.object.shade_smooth(use_auto_smooth=True)
    except RuntimeError as e:
        print(f"[Auto Koda] Failed to enable auto smooth on '{obj.name}': {e}")


def prepare_meshes(objects):
    """For each mesh object: clear custom split normals data, merge
    vertices by distance, convert triangles to quads, and enable Shade
    Auto Smooth."""
    for obj in objects:
        _clear_custom_normals(obj)
        _merge_and_quadify(obj.data)
        _shade_auto_smooth(obj)
        print(f"[Auto Koda] Prepared mesh on '{obj.name}'")

    return len(objects)
# Example: prepare_meshes([body, head, cape]) -> 3
