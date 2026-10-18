"""Shared helpers for the file-backed UI lists (garment hue + JBA)."""

import os


def list_files(folder_path, extension=None, label="folder"):
    """Lists files directly inside `folder_path`, sorted, optionally
    filtered to a case-insensitive `extension` (e.g. ".jba"). Returns []
    if the folder is unset, missing or unreadable."""
    if not folder_path:
        return []

    if not os.path.isdir(folder_path):
        print(f"[Auto Koda] {label} not found: {folder_path}")
        return []

    try:
        return sorted(
            f for f in os.listdir(folder_path)
            if (extension is None or f.lower().endswith(extension))
            and os.path.isfile(os.path.join(folder_path, f))
        )
    except Exception as e:
        print(f"[Auto Koda] Failed to list {label} '{folder_path}': {e}")
        return []
# Example: list_files("/anim/humanoid/bfa", ".jba") -> ["idle.jba", "run_fwd.jba", "walk_fwd.jba"]


def existing_file_in(folder_path, filename, label="file"):
    """Joins `folder_path` and a filename picked from a list, verifying it
    still exists on disk (the folder may have changed since the list was
    last refreshed). Returns the path, or None."""
    if not folder_path:
        return None

    filepath = os.path.join(folder_path, filename)
    if not os.path.isfile(filepath):
        print(f"[Auto Koda] {label} not found: {filepath}")
        return None
    return filepath
# Example: existing_file_in("/anim/humanoid/bfa", "run_fwd.jba", "JBA file") -> "/anim/humanoid/bfa/run_fwd.jba"


def rebuild_name_collection(collection, names):
    """Clears a CollectionProperty and refills it with one item per name.

    Deliberately returns nothing: each add() can reallocate the
    collection's storage, so item references from earlier add() calls
    become dangling and writing to them crashes Blender. Callers that
    need to set more fields should re-iterate the collection afterwards."""
    collection.clear()
    for name in names:
        collection.add().name = name


def active_item_name(items, index):
    """Returns items[index].name, or None if index is out of range (e.g.
    -1 when nothing is selected)."""
    if 0 <= index < len(items):
        return items[index].name
    return None
# Example: active_item_name(scene.auto_koda_garment_hue_files, 2) -> "garmenthue_red_dark.xml"
