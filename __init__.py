import bpy
from bpy.props import StringProperty                   
from bpy.types import AddonPreferences

def getNodeGroup(materials, group_name):
    for mat in materials:
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == 'GROUP' and node.node_tree.name == group_name:
                    print('Analysing node group ' + node.node_tree.name)
                    return node.node_tree

    return None

def find_key_by_value(dict, target_value):
    for key, value in dict.items():
        if value == target_value:
            return key  # Returns the first matching key
    print('Did not find key for value ' + target_value)
    return None  # If not found

def replace_existing_node_group(obj, old_group_name, new_group_name):
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
                    # Store node properties
                    node_location = node.location
                    node_label = node.label

                    # Store links and socket values
                    input_links = {}
                    output_links = {}
                    input_values = {}

                    for input_socket in node.inputs:
                        if input_socket.is_linked:
                            input_links[input_socket.name] = [link.from_socket for link in input_socket.links]
                        else:
                            input_values[input_socket.name] = input_socket.default_value

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
                        elif input_socket.name in input_values:
                            try:
                                input_socket.default_value = input_values[input_socket.name]
                            except Exception as e:
                                print(f"Failed to restore value for {input_socket.name}: {e}")

                    # Restore output links if matching sockets exist
                    for output_socket in node.outputs:
                        if output_socket.name in output_links:
                            for to_socket in output_links[output_socket.name]:
                                try:
                                    links.new(output_socket, to_socket)
                                except Exception as e:
                                    print(f"Failed to reconnect output {output_socket.name}: {e}")


class Auto_Koda(bpy.types.Operator):
    bl_idname = "example.func_4" #load-bearing idname DO NOT RENAME
    bl_label = "Auto Koda"
    def execute(self, context):
        kodaNodeNames = {
            "EYE": "CaptnKoda SWTOR - Eye Shader",
            "GARMENT": "CaptnKoda SWTOR - Garment Shader",
            "HAIRC": "CaptnKoda SWTOR - HairC Shader",
            "SKINB": "CaptnKoda SWTOR - SkinB Shader",
            "UBER": "CaptnKoda SWTOR - Uber Shader",
        }

        heroGravitasNodeNames = {
            "EYE": "SWTOR - Eye Shader",
            "GARMENT": "SWTOR - Garment Shader",
            "HAIRC": "SWTOR - HairC Shader",
            "SKINB": "SWTOR - SkinB Shader",
            "UBER": "SWTOR - Uber Shader",
        }

        prefs = bpy.context.preferences.addons[__name__].preferences
        shadersBlend = prefs.shadersPath
        if not shadersBlend:
            self.report({'ERROR'}, "Shaders Blend file path not set in preferences!")
            return {'CANCELLED'}

        selectedObj = bpy.context.active_object
        if not selectedObj:
            self.report({'ERROR'}, "No active object selected!")
            return {'CANCELLED'}

        print(f'The selected object is {selectedObj.name}')

        detectedShader = None
        detectedNodeGroupName = None

        for node in heroGravitasNodeNames.values():
            print(f'Trying to find {node}')
            detectedNodeGroup = getNodeGroup(selectedObj.data.materials, node)
            if detectedNodeGroup:
                detectedNodeGroupName = detectedNodeGroup.name
                print(f'Found {detectedNodeGroupName}')
                detectedShader = find_key_by_value(heroGravitasNodeNames, detectedNodeGroupName)
                break  # Stop looping once a valid shader is found

        if not detectedShader or not detectedNodeGroupName:
            self.report({'ERROR'}, "No matching shader found in the object's materials.")
            return {'CANCELLED'}

        kodaShaderName = kodaNodeNames.get(detectedShader)
        if not kodaShaderName:
            self.report({'ERROR'}, f"No Koda shader found for detected shader '{detectedShader}'.")
            return {'CANCELLED'}

        # Check if already linked
        kodaNodeGroup = bpy.data.node_groups.get(kodaShaderName)

        if kodaNodeGroup and kodaNodeGroup.library:
            print(f"Koda shader '{kodaShaderName}' is already linked. Skipping re-linking.")
        else:
            print(f"Koda shader '{kodaShaderName}' not found or not linked. Attempting to link...")

            # **Link (not append) the node group**
            with bpy.data.libraries.load(shadersBlend, link=True) as (data_from, data_to):
                if kodaShaderName in data_from.node_groups:
                    data_to.node_groups = [kodaShaderName]  # Link instead of copying
                else:
                    self.report({'ERROR'}, f"Koda shader '{kodaShaderName}' not found in Shaders.blend!")
                    return {'CANCELLED'}

            # **Retrieve the linked node group**
            kodaNodeGroup = bpy.data.node_groups.get(kodaShaderName)

            if not kodaNodeGroup or not kodaNodeGroup.library:
                self.report({'ERROR'}, f"Node group '{kodaShaderName}' was not linked correctly!")
                return {'CANCELLED'}

        print(f"Successfully linked node group: {kodaNodeGroup.name}, from {kodaNodeGroup.library.filepath}")

        # **Replace the existing node group with the linked one**
        replace_existing_node_group(selectedObj, detectedNodeGroupName, kodaNodeGroup.name)

        return {'FINISHED'}


class Auto_Koda_Button(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_auto_koda"

    bl_category = "Auto Koda"
    bl_label = "Auto Koda"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    #bl_context = 'object'

    def draw(self, context):
        layout = self.layout
        shadersBlend = bpy.context.preferences.addons[__name__].preferences.shadersPath
        if 'Shaders.blend' in shadersBlend:
            statusText = 'Shaders.blend Set Correctly!'
        else:
            statusText = 'Shaders.blend Not Set Correctly!'   

        layout.label(text = statusText)
        layout.operator(Auto_Koda.bl_idname)


class Auto_Koda_Preferences(AddonPreferences):
    bl_idname = __name__

    shadersPath: StringProperty(
        name="",
        subtype='FILE_PATH',) # type: ignore

    def draw(self, context):
        layout = self.layout
        layout.label(text="Select your Shaders.blend file below")
        layout.prop(self, "shadersPath")

classes = [Auto_Koda, Auto_Koda_Button, Auto_Koda_Preferences]

def register():
    print('wagwan world')
    print(__name__)
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    print('killin on myself fr')
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)