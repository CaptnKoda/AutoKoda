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

import logging
import os
import bpy  # type: ignore
from . import config
from .prefs import get_anim_root_path
from .list_utils import list_files, existing_file_in, rebuild_name_collection, active_item_name

log = logging.getLogger(__name__)


class Auto_Koda_JBAItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()  # type: ignore


class Auto_Koda_JBAFolderItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()  # type: ignore


def _log_walk_error(error):
    """os.walk() silently skips folders it can't read unless told otherwise."""
    log.warning(f"Could not read anim subfolder, skipping it: {error}")


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
    if not root_path:
        return []

    qualifying = []
    try:
        for dirpath, dirnames, filenames in os.walk(root_path, onerror=_log_walk_error):
            dirnames[:] = [
                d for d in dirnames
                if d.lower() not in config.IGNORED_JBA_FOLDER_NAMES
            ]

            if any(f.lower().endswith(".jba") for f in filenames):
                qualifying.append(os.path.relpath(dirpath, root_path))
    except Exception:
        log.exception(f"Failed to scan anim root folder '{root_path}'")
        return []

    if not qualifying:
        log.warning(f"No .jba files found anywhere under anim root '{root_path}'")
    return sorted(qualifying)
# Example: list_jba_subfolders("/home/koda/SWTOR/resources/anim") -> [".", "humanoid/bfa", "humanoid/bma"]


def refresh_jba_folder_list(scene):
    """Rebuilds scene.auto_koda_jba_folders -- the search source for the
    Animation Set field. Only called on register/file-load and the
    manual Refresh button -- never on plain panel redraw, unlike the
    old dynamic-Enum approach, since prop_search reads the collection
    directly without calling back into Python per keystroke. This is
    what actually fixed the lag, not caching."""
    folders = list_jba_subfolders(get_anim_root_path())
    rebuild_name_collection(scene.auto_koda_jba_folders, folders)


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

    rel = scene.auto_koda_jba_folder_name.strip()
    if not rel:
        log.debug("No Animation Set selected")
        return None
    if rel not in scene.auto_koda_jba_folders:
        log.warning(
            f"Animation Set '{rel}' is not one of the {len(scene.auto_koda_jba_folders)} "
            f"folder(s) found under '{root}' - pick one from the list or press Refresh"
        )
        return None

    return root if rel == "." else os.path.join(root, rel)
# Example: get_selected_jba_folder_path(scene) -> "/home/koda/SWTOR/resources/anim/humanoid/bfa"


def refresh_jba_collection(scene):
    """Rebuilds scene.auto_koda_jba_files from whichever anim subfolder
    is currently selected. Always fully rebuilds -- cheap, and avoids
    stale-item edge cases from a 'skip if unchanged' shortcut."""
    files = list_files(get_selected_jba_folder_path(scene), ".jba", label="JBA folder")
    rebuild_name_collection(scene.auto_koda_jba_files, files)


def refresh_jba_lists(scene):
    """Rebuilds both the folder search list and the file list."""
    refresh_jba_folder_list(scene)
    refresh_jba_collection(scene)


def get_selected_jba_filename(scene):
    """Returns the filename of the currently active JBA list item, or
    None if nothing is selected."""
    return active_item_name(scene.auto_koda_jba_files, scene.auto_koda_jba_index)
# Example: get_selected_jba_filename(scene) -> "run_fwd.jba"


def get_jba_filepath(scene, filename):
    """Resolves a filename from the list back to a full path within the
    currently selected anim subfolder, verifying it still exists on
    disk (the folder could have changed on-disk since the list was
    last refreshed)."""
    return existing_file_in(get_selected_jba_folder_path(scene), filename, "JBA file")
# Example: get_jba_filepath(scene, "run_fwd.jba") -> "/home/koda/SWTOR/resources/anim/humanoid/bfa/run_fwd.jba"


def on_jba_folder_name_changed(self, context):
    """Update callback for scene.auto_koda_jba_folder_name: repopulate
    the file list to match whichever subfolder was just typed/picked."""
    try:
        refresh_jba_collection(context.scene)
    except Exception:
        log.exception(f"Could not refresh the JBA file list for '{self.auto_koda_jba_folder_name}'")