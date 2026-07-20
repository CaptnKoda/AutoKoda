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
        if obj.type == 'MESH'
        for mod in obj.modifiers
        if mod.type == 'SUBSURF'
    ]

    if not subsurf_mods:
        print("[Auto Koda] No Subdivision Surface modifiers found on selected objects.")
        return 0

    any_visible = any(mod.show_viewport for mod in subsurf_mods)
    new_state = not any_visible

    for mod in subsurf_mods:
        mod.show_viewport = new_state

    print(f"[Auto Koda] Set {len(subsurf_mods)} Subdivision Surface modifier(s) viewport display to {new_state}")
    return len(subsurf_mods)


def prepare_meshes(objects):
    """For each selected mesh object: merge vertices by distance, convert
    triangles to quads, clear custom split normals data, and enable Shade
    Auto Smooth."""
    processed = 0

    for obj in objects:
        if obj.type != 'MESH':
            continue

        mesh = obj.data

        try:
            with bpy.context.temp_override(object=obj, active_object=obj):
                bpy.ops.mesh.customdata_custom_splitnormals_clear()
        except RuntimeError as e:
            print(f"[Auto Koda] Failed to clear custom normals on '{obj.name}': {e}")

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

        try:
            with bpy.context.temp_override(object=obj, active_object=obj, selected_editable_objects=[obj]):
                if hasattr(bpy.ops.object, "shade_auto_smooth"):
                    bpy.ops.object.shade_auto_smooth()
                else:
                    bpy.ops.object.shade_smooth(use_auto_smooth=True)
        except RuntimeError as e:
            print(f"[Auto Koda] Failed to enable auto smooth on '{obj.name}': {e}")

        processed += 1
        print(f"[Auto Koda] Prepared mesh on '{obj.name}'")

    return processed