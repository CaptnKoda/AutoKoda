"""Lists .jba animation folders/files for the Animations panel.

scene.auto_koda_jba_folders is a searchable collection of every
subfolder (relative to the configured anim root) that directly
contains at least one .jba file -- the source collection for
layout.prop_search() on scene.auto_koda_jba_folder_name, which is
Blender's native "type to filter" searchable text field (the same
mechanism used for vertex group / UV map / bone name pickers), rather
than a plain EnumProperty dropdown.

scene.auto_koda_jba_files is the plain file listing (feeding the
UIList) for whichever folder auto_koda_jba_folder_name currently
resolves to.

Both collections are only rebuilt on demand (register/file-load, the
manual Refresh button, and whenever auto_koda_jba_folder_name changes)
rather than on every panel redraw, so the recursive folder scan -- the
expensive part on a large anim tree -- only actually touches the
filesystem when something has actually changed.
"""

import os
import bpy  # type: ignore
from . import config
from .prefs import get_anim_root_path


class Auto_Koda_JBAItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()  # type: ignore


class Auto_Koda_JBAFolderItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()  # type: ignore


def list_jba_subfolders(root_path):
    """Recursively walks `root_path` and returns the relative path (from
    root_path) of every folder that directly contains at least one .jba
    file, sorted. The root folder itself is represented as "." when it
    qualifies. Folders whose only .jba files live in a *deeper*
    subfolder do not themselves qualify -- only that deeper subfolder
    does.

    Folders named in config.IGNORED_JBA_FOLDER_NAMES (case-insensitive)
    are pruned from traversal entirely, wherever they appear in the
    tree -- not just skipped from the results, but never walked into at
    all, since one of them ('placeable') is large enough to be the main
    cost of this scan."""
    if not root_path or not os.path.isdir(root_path):
        return []

    qualifying = []
    try:
        for dirpath, dirnames, filenames in os.walk(root_path):
            dirnames[:] = [
                d for d in dirnames
                if d.lower() not in config.IGNORED_JBA_FOLDER_NAMES
            ]

            if os.path.basename(dirpath).lower() in config.IGNORED_JBA_FOLDER_NAMES:
                continue

            if any(f.lower().endswith(".jba") for f in filenames):
                qualifying.append(os.path.relpath(dirpath, root_path))
    except Exception as e:
        print(f"[Auto Koda] Failed to scan anim root folder '{root_path}': {e}")
        return []

    return sorted(qualifying)


def refresh_jba_folder_list(scene):
    """Rebuilds scene.auto_koda_jba_folders -- the search source for the
    Animation Set field. Only called on register/file-load and the
    manual Refresh button -- never on plain panel redraw, unlike the
    old dynamic-Enum approach, since prop_search reads the collection
    directly without calling back into Python per keystroke. This is
    what actually fixed the lag, not caching."""
    root = get_anim_root_path()
    folders = list_jba_subfolders(root) if root else []

    scene.auto_koda_jba_folders.clear()
    for rel in folders:
        item = scene.auto_koda_jba_folders.add()
        item.name = rel


def list_jba_files(folder_path):
    """Lists .jba files directly inside `folder_path` (an absolute
    path -- typically the anim root joined with a selected subfolder)."""
    if not folder_path or not os.path.isdir(folder_path):
        return []

    try:
        files = sorted(
            f for f in os.listdir(folder_path)
            if f.lower().endswith(".jba") and os.path.isfile(os.path.join(folder_path, f))
        )
    except Exception as e:
        print(f"[Auto Koda] Failed to list JBA folder '{folder_path}': {e}")
        return []

    return files


def get_selected_jba_folder_path(scene):
    """Resolves scene.auto_koda_jba_folder_name back to an absolute
    folder path. Returns None if the anim root isn't configured, or the
    typed/picked name doesn't match a real entry in
    scene.auto_koda_jba_folders -- prop_search's target StringProperty
    accepts arbitrary free-typed text too, not just a picked
    suggestion, so this guards against garbage input."""
    root = get_anim_root_path()
    if not root:
        return None

    rel = getattr(scene, "auto_koda_jba_folder_name", "").strip()
    if not rel or rel not in scene.auto_koda_jba_folders:
        return None

    return root if rel == "." else os.path.join(root, rel)


def refresh_jba_collection(scene):
    """Rebuilds scene.auto_koda_jba_files from whichever anim subfolder
    is currently selected. Always fully rebuilds -- cheap, and avoids
    stale-item edge cases from a 'skip if unchanged' shortcut."""
    folder_path = get_selected_jba_folder_path(scene)
    files = list_jba_files(folder_path) if folder_path else []

    scene.auto_koda_jba_files.clear()
    for f in files:
        item = scene.auto_koda_jba_files.add()
        item.name = f


def get_selected_jba_filename(scene):
    """Returns the filename of the currently active JBA list item, or
    None if nothing is selected."""
    idx = scene.auto_koda_jba_index
    items = scene.auto_koda_jba_files
    if 0 <= idx < len(items):
        return items[idx].name
    return None


def get_jba_filepath(scene, filename):
    """Resolves a filename from the list back to a full path within the
    currently selected anim subfolder, verifying it still exists on
    disk (the folder could have changed on-disk since the list was
    last refreshed)."""
    folder_path = get_selected_jba_folder_path(scene)
    if not folder_path:
        return None

    filepath = os.path.join(folder_path, filename)
    if not os.path.isfile(filepath):
        print(f"[Auto Koda] JBA file not found: {filepath}")
        return None
    return filepath


def on_jba_folder_name_changed(self, context):
    """Update callback for scene.auto_koda_jba_folder_name: repopulate
    the file list to match whichever subfolder was just typed/picked."""
    refresh_jba_collection(context.scene)