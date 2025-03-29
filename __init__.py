import bpy
from pathlib import Path
import os
from .utils.addon_checks import requirements_checks

def getNodeGroup(materials, group_name):
    for mat in materials:
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == 'GROUP' and node.node_tree.name == group_name:
                    return node.node_tree

    return None

def find_key_by_value(dict, target_value):
    for key, value in dict.items():
        if value == target_value:
            return key  # Returns the first matching key
    return None  # If not found

def replace_existing_node_group(obj, old_group_name, new_group_name):
    """Replace all instances of an existing node group with another in the object's materials."""
    
    if not obj or not obj.active_material:
        print("No active material found on the selected object.")
        return
    
    new_group = bpy.data.node_groups.get(new_group_name)
    if not new_group:
        print(f"New node group '{new_group_name}' not found.")
        return

    for mat in obj.data.materials:
        if mat and mat.use_nodes:
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            
            for node in nodes:
                if node.type == 'GROUP' and node.node_tree and node.node_tree.name == old_group_name:
                    print('gettin dat shit ' + old_group_name + 'outta here')
                    print('dat new shit ' + new_group_name + ' is totally in rn')

                    # Store node properties
                    node_location = node.location
                    node_label = node.label

                    # Store links safely
                    input_links = {}
                    output_links = {}

                    for input_socket in node.inputs:
                        input_links[input_socket.name] = [link.from_socket for link in input_socket.links]

                    for output_socket in node.outputs:
                        output_links[output_socket.name] = [link.to_socket for link in output_socket.links]

                    # Assign new node group
                    node.node_tree = new_group
                    
                    # Restore node properties
                    node.location = node_location
                    node.label = node_label

                    # Restore input links if matching sockets exist
                    for input_socket in node.inputs:
                        if input_socket.name in input_links:
                            for from_socket in input_links[input_socket.name]:
                                try:
                                    links.new(from_socket, input_socket)
                                except Exception as e:
                                    print(f"Failed to reconnect input {input_socket.name}: {e}")

                    # Restore output links if matching sockets exist
                    for output_socket in node.outputs:
                        if output_socket.name in output_links:
                            for to_socket in output_links[output_socket.name]:
                                try:
                                    links.new(output_socket, to_socket)
                                except Exception as e:
                                    print(f"Failed to reconnect output {output_socket.name}: {e}")

class autoKoda(bpy.types.Operator):
    bl_idname = "example.func_4" #load-bearing idname DO NOT RENAME
    bl_label = "button that is well good"

    def execute(self, context):
        kodaNodeNames = {
            "EYE"      : "CaptnKoda SWTOR - Eye Shader",
            "GARMENT"  : "CaptnKoda SWTOR - Garment Shader",
            "HAIRC"    : "CaptnKoda SWTOR - HairC Shader",
            "SKINB"    : "CaptnKoda SWTOR - SkinB Shader",
            "UBER"     : "CaptnKoda SWTOR - Uber Shader",
        }

        heroGravitasNodeNames = {
            "EYE"      : "SWTOR - Eye Shader",
            "GARMENT"  : "SWTOR - Garment Shader",
            "HAIRC"    : "SWTOR - HairC Shader",
            "SKINB"    : "SWTOR - SkinB Shader",
            "UBER"     : "SWTOR - Uber Shader",
        }

        prefs = bpy.context.preferences.addons[__name__].preferences
        shadersBlend = prefs.shaders_blend_path
        if not shadersBlend:
            self.report({'ERROR'}, "Shaders Blend file path not set in preferences!")
            return {'CANCELLED'}

        selectedObj = bpy.context.active_object #Get selected object

        for node in heroGravitasNodeNames.values():
            try:
                detectedNodeGroup = getNodeGroup(selectedObj.data.materials, node)
                if detectedNodeGroup:
                    detectedNodeGroupName = detectedNodeGroup.name
                    detectedShader = find_key_by_value(heroGravitasNodeNames, detectedNodeGroupName)
                    if detectedShader:
                        break  # Stop looping once a valid shader is found
            except:
                continue

        print('node group is ' + detectedNodeGroupName + ' fr')

        print('detected shader is ' + detectedShader + ' fr')

        with bpy.data.libraries.load(shadersBlend) as (data_from, data_to):
            data_to.materials = data_from.materials

        kodaNodeGroup = getNodeGroup(data_to.materials, kodaNodeNames[detectedShader])

        print('omg its ' + kodaNodeGroup.name)

        replace_existing_node_group(selectedObj, detectedNodeGroupName, kodaNodeGroup.name)

        return {'FINISHED'}

class autoKodaButton(bpy.types.Panel):
    bl_idname = "autoKoda"

    bl_category = "Auto Koda"
    bl_label = "label init"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    #bl_context = 'object'

    def draw(self, context):
        self.layout.label(text = "panel what i made")
        self.layout.operator(autoKoda.bl_idname)

class AutoKodaPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__.split('.')[-1]  # Extract the actual module name

    shaders_blend_path: bpy.props.StringProperty(
        name="Shaders Blend File",
        description="Path to the .blend file containing the Koda shaders",
        subtype='FILE_PATH'
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Set the path to your shaders .blend file:")
        layout.prop(self, "shaders_blend_path")  # File path selector



bl_info = {
    "name": "Auto Koda",
    "author": "Koda",
    "version": (1, 0),
    "blender": (4, 2, 8),
    "description": "Converts ZeroGravitas Shaders to Koda Shaders",
    "category": "Material",
}
 
classes = [AutoKodaPreferences, autoKodaButton, autoKoda]

def register():
    print('wagwan world')
    print(__name__)
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    print('killin on myself fr')
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
