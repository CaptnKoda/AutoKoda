"""Parsing of garmenthue XML palette files, and applying their values onto
Koda group node inputs (palette1_* for Primary, palette2_* for Secondary)."""

import os
import xml.etree.ElementTree as ET
from . import config


def _parse_float_list(text):
    """Parses a comma-separated string of floats, e.g. '0.611765, 0.921569, 1, 1'."""
    return [float(v.strip()) for v in text.split(",") if v.strip() != ""]


def parse_garment_hue_file(filepath):
    """Parses a garmenthue XML file into a dict of raw values keyed by the
    same field names used in HERO_ENGINE_PROP_TO_KODA_INPUT (without the
    palette1_/palette2_ prefix), e.g.:
        {
            "hue": 0.2802,
            "saturation": 0.5842...,
            "brightness": -0.0822...,
            "contrast": 0.4494,
            "specular": [1.0, 0.909804, 0.666667, 1.0],
            "metallic_specular": [0.611765, 0.921569, 1.0, 1.0],
        }
    Returns None on parse failure.
    """
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
    except Exception as e:
        print(f"[Auto Koda] Failed to parse garment hue file '{filepath}': {e}")
        return None

    def get_text(tag):
        el = root.find(tag)
        return el.text.strip() if el is not None and el.text else None

    values = {}

    for tag, key in (
        ("Hue", "hue"),
        ("Saturation", "saturation"),
        ("Brightness", "brightness"),
        ("Contrast", "contrast"),
    ):
        text = get_text(tag)
        if text is not None:
            try:
                values[key] = float(text)
            except ValueError:
                print(f"[Auto Koda] Could not parse float for <{tag}> in '{filepath}'")

    for tag, key in (
        ("Specular", "specular"),
        ("Metallicspecular", "metallic_specular"),
    ):
        text = get_text(tag)
        if text is not None:
            try:
                values[key] = _parse_float_list(text)
            except ValueError:
                print(f"[Auto Koda] Could not parse color for <{tag}> in '{filepath}'")

    return values


def apply_palette_to_koda_node(values, koda_node, slot):
    """Writes parsed palette `values` onto a Koda group node's palette1_* or
    palette2_* inputs (slot=1 or slot=2). For each field, tries the mapped
    Koda input name from HERO_ENGINE_PROP_TO_KODA_INPUT first; if that socket
    doesn't exist on this node, falls back to the raw property key itself
    (e.g. 'palette1_hue') in case the group's socket wasn't renamed."""
    if not koda_node or not values:
        return 0

    from .socket_utils import coerce_value_for_socket

    koda_inputs = {inp.name: inp for inp in koda_node.inputs}
    copied = 0

    for field_key, value in values.items():
        hero_prop = f"palette{slot}_{field_key}"
        mapped_name = config.HERO_ENGINE_PROP_TO_KODA_INPUT.get(hero_prop)

        koda_input = None
        if mapped_name:
            koda_input = koda_inputs.get(mapped_name)

        if koda_input is None:
            # Fallback: try the raw property key directly
            koda_input = koda_inputs.get(hero_prop)

        if not koda_input:
            continue

        if coerce_value_for_socket(value, koda_input):
            copied += 1
        else:
            attempted_name = mapped_name or hero_prop
            print(f"[Auto Koda] Failed to apply '{hero_prop}' -> '{attempted_name}'")

    return copied


def apply_garment_hue_to_objects(objects, filename, slot):
    """For each selected mesh object, finds every Koda group node in its
    materials and applies the parsed palette file onto palette{slot}_*
    inputs. Returns (files_applied_count, nodes_updated_count)."""
    from .prefs import get_resources_folder_path

    resources_path = get_resources_folder_path()
    if not resources_path:
        print("[Auto Koda] Resources folder not configured.")
        return 0, 0

    filepath = os.path.join(resources_path, config.GARMENT_HUE_SUBPATH, filename)
    if not os.path.isfile(filepath):
        print(f"[Auto Koda] Garment hue file not found: {filepath}")
        return 0, 0

    values = parse_garment_hue_file(filepath)
    if not values:
        return 0, 0

    nodes_updated = 0

    for obj in objects:
        if obj.type != 'MESH':
            continue

        for slot_ref in obj.material_slots:
            mat = slot_ref.material
            if not mat or not mat.use_nodes:
                continue

            for node in mat.node_tree.nodes:
                if (
                    node.type == 'GROUP'
                    and node.node_tree
                    and node.node_tree.name in config.KODA_NODE_NAMES.values()
                ):
                    copied = apply_palette_to_koda_node(values, node, slot)
                    if copied:
                        nodes_updated += 1

    return 1, nodes_updated