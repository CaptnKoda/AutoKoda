"""Parsing of garmenthue XML palette files, and applying their values onto
Koda group node inputs (palette1_* for Primary, palette2_* for Secondary)."""

import logging
import xml.etree.ElementTree as ET
from . import config
from .node_utils import iter_node_materials, is_koda_group_node
from .socket_utils import coerce_value_for_socket

log = logging.getLogger(__name__)


def _parse_float_list(text):
    """Parses a comma-separated string of floats, e.g. '0.611765, 0.921569, 1, 1'."""
    return [float(v.strip()) for v in text.split(",") if v.strip() != ""]
# Example: _parse_float_list("0.611765, 0.921569, 1, 1") -> [0.611765, 0.921569, 1.0, 1.0]


# XML tag -> (values key, parser) for parse_garment_hue_file()
_GARMENT_HUE_FIELDS = {
    "Hue"             : ("hue", float),
    "Saturation"      : ("saturation", float),
    "Brightness"      : ("brightness", float),
    "Contrast"        : ("contrast", float),
    "Specular"        : ("specular", _parse_float_list),
    "Metallicspecular": ("metallic_specular", _parse_float_list),
}


def _load_xml_root(filepath, purpose):
    """Parses an XML file and returns its root element, or None (logged)
    if it can't be read."""
    try:
        return ET.parse(filepath).getroot()
    except Exception as e:
        log.warning(f"Failed to parse '{filepath}' for {purpose}: {type(e).__name__}: {e}")
        return None
# Example: _load_xml_root(".../garmenthue_red_light.xml", "garment hue") -> <Element 'GarmentHue'>


def _find_text(root, tag):
    """Stripped text of the `tag` child of `root`, or None if missing/empty."""
    el = root.find(tag)
    return el.text.strip() if el is not None and el.text else None
# Example: _find_text(root, "Hue") -> "0.2802"


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
    root = _load_xml_root(filepath, "garment hue values")
    if root is None:
        return None

    values = {}
    for tag, (key, parse) in _GARMENT_HUE_FIELDS.items():
        text = _find_text(root, tag)
        if text is None:
            log.warning(f"<{tag}> is missing or empty in '{filepath}'")
            continue
        try:
            values[key] = parse(text)
        except ValueError as e:
            log.warning(f"Could not parse <{tag}> value '{text}' in '{filepath}': {e}")

    if not values:
        log.error(f"'{filepath}' (root <{root.tag}>) has no usable values for: {list(_GARMENT_HUE_FIELDS)}")

    return values
# Example: parse_garment_hue_file(".../garmenthue_red_light.xml") -> {"hue": 0.2802, "saturation": 0.58, "brightness": -0.08, "contrast": 0.45, "specular": [1.0, 0.91, 0.67, 1.0], "metallic_specular": [0.61, 0.92, 1.0, 1.0]}


def parse_representative_color(filepath):
    """Parses <Representativecolor> from a garment hue XML file into an
    RGBA tuple. Returns None if missing or unparseable."""
    root = _load_xml_root(filepath, "representative color")
    if root is None:
        return None

    text = _find_text(root, "Representativecolor")
    if text is None:
        log.debug(f"<Representativecolor> is missing or empty in '{filepath}'")
        return None

    try:
        values = _parse_float_list(text)
    except ValueError as e:
        log.warning(f"Could not parse <Representativecolor> value '{text}' in '{filepath}': {e}")
        return None

    if len(values) < 3:
        log.warning(f"<Representativecolor> value '{text}' in '{filepath}' has fewer than 3 components")
        return None
    if len(values) == 3:
        values.append(1.0)

    return tuple(values[:4])
# Example: parse_representative_color(".../garmenthue_red_light.xml") -> (0.8, 0.12, 0.1, 1.0)


def apply_palette_to_koda_node(values, koda_node, slot):
    """Writes parsed palette `values` onto a Koda group node's palette1_* or
    palette2_* inputs (slot=1 or slot=2). For each field, tries the mapped
    Koda input name from HERO_ENGINE_PROP_TO_KODA_INPUT first; if that socket
    doesn't exist on this node, falls back to the raw property key itself
    (e.g. 'palette1_hue') in case the group's socket wasn't renamed."""
    koda_inputs = {inp.name: inp for inp in koda_node.inputs}
    copied = 0

    for field_key, value in values.items():
        hero_prop = f"palette{slot}_{field_key}"
        mapped_name = config.HERO_ENGINE_PROP_TO_KODA_INPUT.get(hero_prop)

        koda_input = koda_inputs.get(mapped_name) or koda_inputs.get(hero_prop)
        if not koda_input:
            log.warning(f"Node '{koda_node.name}' has no input '{mapped_name}' or '{hero_prop}', skipping that value")
            continue

        if coerce_value_for_socket(value, koda_input):
            copied += 1
        else:
            log.warning(f"Failed to apply '{hero_prop}' -> '{koda_input.name}'")

    return copied
# Example: apply_palette_to_koda_node(values, koda_node, slot=1) -> 6


def apply_palette_to_objects(objects, values, slot):
    """Applies parsed palette `values` onto palette{slot}_* inputs of every
    Koda group node in the objects' materials. Returns the number of
    nodes updated."""
    nodes_updated = 0

    for obj in objects:
        updated_on_object = 0
        for _, mat in iter_node_materials(obj):
            for node in mat.node_tree.nodes:
                if is_koda_group_node(node) and apply_palette_to_koda_node(values, node, slot):
                    updated_on_object += 1

        if not updated_on_object:
            log.warning(f"'{obj.name}': no Koda shader node took palette {slot} - has it been through Auto Crunch?")
        nodes_updated += updated_on_object

    return nodes_updated
# Example: apply_palette_to_objects(objects, values, slot=2) -> 4
