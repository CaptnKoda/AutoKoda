from .prefs import get_shaders_blend_path
from .material_io import (
    link_material_with_koda_group,
    assign_linked_material,
    remap_old_material_references,
    finalize_material_swap,
)
from .node_utils import find_group_node, get_group_output_node, find_koda_group_node
from .hero_gravitas import transfer_textures, copy_node_inputs
from .hero_engine import find_hero_engine_node, transfer_hero_engine_textures, transfer_hero_engine_properties
from .conversion import process_object
from .overrides import sync_master_inputs_to_override, link_override_to_master, run_override_sync
from .mesh_utils import toggle_subsurf_viewport_display, prepare_meshes
from .prefs import get_shaders_blend_path, get_resources_folder_path
from .garment_hue import list_garment_hue_files, refresh_garment_hue_collection
from .garment_hue_xml import parse_garment_hue_file, apply_palette_to_koda_node, apply_garment_hue_to_objects