"""Resolves an item appearance ('ipp.…') node name to the .gr2 model files
it uses, straight from a TOR resources extraction folder.

Pure Python (no bpy) so it can be tested outside Blender.

Lookup chain:
  1. systemgenerated/buckets/*.bkt  -- find the GOM node named `ipp`.
     The node's payload stores art IDs as GOM ints (0xCA + 3-byte
     big-endian value), e.g. ca 0f 42 9e -> 1000094.
  2. art/dynamic/<slot>/index.xml   -- the <Asset> whose <ID> is in that
     payload gives the base model; its <Attachment>s whose ids are in the
     payload are the extra pieces (all of them if none are listed).
  3. '[bt]' in each model path is swapped for the chosen body type.

The payload is only scanned for 0xCA ints rather than fully decoded, so
stray IDs (color schemes etc.) are expected -- they simply don't match
any asset/attachment and are ignored.
"""

import os
import glob
import struct
import xml.etree.ElementTree as ET

# Garment slot folders under art/dynamic/ searched for the ipp's asset
# (headgear lives in "face", not "head" -- "head" holds character heads)
GARMENT_SLOTS = ("chest", "leg", "boot", "hand", "waist", "bracer", "face")

# Bucket node header layout (offsets from the start of the node)
_NODE_SIZE_OFFSET = 0    # u32 total node size
_NODE_DATA_OFFSET = 38   # u16 offset of the node's payload
_NODE_NAME_OFFSET = 50   # null-terminated node name (FQN)

_GOM_INT24_PREFIX = 0xCA

_index_cache = {}


class IppResolveError(Exception):
    pass


def find_ipp_payload(resources_path, ipp):
    """Returns the raw payload bytes of the bucket node named `ipp`, or
    raises IppResolveError if no bucket contains it."""
    needle = ipp.encode("ascii") + b"\x00"
    bucket_glob = os.path.join(resources_path, "systemgenerated", "buckets", "*.bkt")

    for bucket_path in glob.glob(bucket_glob):
        with open(bucket_path, "rb") as f:
            data = f.read()

        pos = data.find(needle)
        while pos != -1:
            node_start = pos - _NODE_NAME_OFFSET
            if node_start >= 0:
                size = struct.unpack_from("<I", data, node_start + _NODE_SIZE_OFFSET)[0]
                data_offset = struct.unpack_from("<H", data, node_start + _NODE_DATA_OFFSET)[0]
                # Only accept a real node header, not another node referencing this name
                if _NODE_NAME_OFFSET + len(needle) <= data_offset < size and node_start + size <= len(data):
                    return data[node_start + data_offset:node_start + size]
            pos = data.find(needle, pos + 1)

    raise IppResolveError(f"'{ipp}' not found in any bucket under {resources_path}")
# Example: find_ipp_payload("/mnt/TOR/resources", "ipp.class.spy.quest.tdps2.t1x1.chest") -> b"\xcc\x02\xed..."


def extract_art_ids(payload):
    """Every GOM 24-bit int in the payload -- candidate art IDs."""
    ids = set()
    for i in range(len(payload) - 3):
        if payload[i] == _GOM_INT24_PREFIX:
            ids.add(int.from_bytes(payload[i + 1:i + 4], "big"))
    return ids
# Example: extract_art_ids(b"\xca\x0f\x42\x9e") -> {1000094}


def _load_slot_index(resources_path, slot):
    path = os.path.join(resources_path, "art", "dynamic", slot, "index.xml")
    if path not in _index_cache:
        _index_cache[path] = ET.parse(path).getroot() if os.path.isfile(path) else None
    return _index_cache[path]
# Example: _load_slot_index("/mnt/TOR/resources", "chest") -> <Element 'AssetIndex'>


def _resources_file(resources_path, game_path):
    """'/art/dynamic/…' (as written in index.xml) -> absolute path on disk."""
    return os.path.join(resources_path, *game_path.strip("/").split("/"))
# Example: _resources_file("/mnt/TOR/resources", "/art/dynamic/chest/model/a.gr2") -> "/mnt/TOR/resources/art/dynamic/chest/model/a.gr2"


def resolve_ipp(resources_path, ipp, body_type):
    """Resolves `ipp` to its models for `body_type` (e.g. 'bmn').

    Returns a dict:
      slot      -- art/dynamic slot folder the asset was found in
      art_name  -- the asset's ArtName
      gr2_paths -- absolute .gr2 paths that exist on disk (base model first)
      missing   -- absolute .gr2 paths that should exist but don't
      materials -- .mat paths the ipp selects (not applied here)
    """
    ids = extract_art_ids(find_ipp_payload(resources_path, ipp))

    for slot in GARMENT_SLOTS:
        root = _load_slot_index(resources_path, slot)
        if root is None:
            continue

        for asset in root.iter("Asset"):
            asset_id = asset.findtext("ID")
            if not asset_id or int(asset_id) not in ids:
                continue

            attachments = asset.findall("Attachments/Attachment")
            chosen = [a for a in attachments if int(a.get("id", -1)) in ids] or attachments

            model_paths = [asset.findtext("BaseFile")] + [a.get("filename") for a in chosen]
            model_paths = [p.replace("[bt]", body_type) for p in model_paths if p]

            gr2_paths, missing = [], []
            for game_path in model_paths:
                path = _resources_file(resources_path, game_path)
                (gr2_paths if os.path.isfile(path) else missing).append(path)

            materials = [
                m.get("filename") for m in asset.findall("Materials/Material")
                if int(m.get("id", -1)) in ids
            ]

            return {
                "slot": slot,
                "art_name": asset.findtext("ArtName"),
                "gr2_paths": gr2_paths,
                "missing": missing,
                "materials": materials,
            }

    raise IppResolveError(f"No art asset in {', '.join(GARMENT_SLOTS)} matches '{ipp}'")
# Example: resolve_ipp(res, "ipp.class.spy.quest.tdps2.t1x1.chest", "bmn")["gr2_paths"]
#   -> [".../chest_tight_bmn_archetype.gr2", ".../chest_tight_bmn_med_ge_a15_chest.gr2"]
