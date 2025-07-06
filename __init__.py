import bpy
from bpy.props import StringProperty                   
from bpy.types import AddonPreferences

#Global Consts
KODA_NODE_NAMES = {
    "EYE"       : "CaptnKoda SWTOR - Eye Shader",
    "GARMENT"   : "CaptnKoda SWTOR - Garment Shader",
    "HAIRC"     : "CaptnKoda SWTOR - HairC Shader",
    "SKINB"     : "CaptnKoda SWTOR - SkinB Shader",
    "UBER"      : "CaptnKoda SWTOR - Uber Shader",
}

HERO_GRAVITAS_NODE_NAMES = {
    "EYE"       : "SWTOR - Eye Shader",
    "GARMENT"   : "SWTOR - Garment Shader",
    "HAIRC"     : "SWTOR - HairC Shader",
    "SKINB"     : "SWTOR - SkinB Shader",
    "UBER"      : "SWTOR - Uber Shader",
}

#Functions
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

def load_and_link_texture(shaders_blend_path, node, image_name):
    with bpy.data.libraries.load(shaders_blend_path, link=True) as (data_from, data_to):
        if image_name in data_from.images:
            print(f"Found image: {image_name}")
            data_to.images = [image_name]
        else:
            print(f"Image '{image_name}' not found in Shaders.blend.")
            return

    image = bpy.data.images.get(image_name)
    if not image:
        print(f"Failed to load image '{image_name}' into current file.")
        return

    if hasattr(node, 'image'):
        node.image = image
        print(f"Linked image '{image_name}' to node '{node.name}'")
    else:
        print(f"Node '{node.name}' does not support image assignment.")

def createNewImageNode(nodes, label, x, y, minimize):
    newImageNode = nodes.new(type='ShaderNodeTexImage')
    newImageNode.name = newImageNode.label = label
    newImageNode.location = (x, y)
    newImageNode.hide = minimize
    return newImageNode

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

                    # Inject wrinkle map images for SkinB Shader
                    if old_group_name == "SWTOR - SkinB Shader" and new_group_name == "CaptnKoda SWTOR - SkinB Shader":
                        # Create image texture nodes for wrinkle map and mask
                        wrinkle_map_node = createNewImageNode(nodes, 'animatedWrinklesMap', node.location[0] - 800, node.location[1] - 200, True)
                        wrinkle_mask_node = createNewImageNode(nodes, 'animatedWrinkleMask', node.location[0] - 800, node.location[1], True)

                        scarMapNode = createNewImageNode(nodes, 'ScarMap', node.location[0] - 800, node.location[1] - 400, False)

                        # Manually setting defaults
                        node.inputs["Holographic"].default_value = 0.0
                        node.inputs["Maximum Roughness"].default_value = 0.4

                        # Load the wrinkle map image from the Shaders.blend
                        shaders_blend_path = get_shaders_blend_path()
                        if shaders_blend_path:
                            load_and_link_texture(shaders_blend_path, wrinkle_map_node, 'wrinkles_compressed_bmn_c01_wrinkles_stretched_bmn_c01_w.dd')
                            load_and_link_texture(shaders_blend_path, wrinkle_mask_node, 'wrinkles_colormask01_wrinkles_colormask02_wm.dds')
                            load_and_link_texture(shaders_blend_path, scarMapNode, 'age_non_non_none_u.dds')

                        # Link to the new node group if inputs exist
                        if "animatedWrinkleMap Color" in node.inputs:
                            links.new(wrinkle_map_node.outputs['Color'], node.inputs["animatedWrinkleMap Color"])
                        if "animatedWrinkleMap Alpha" in node.inputs:
                            links.new(wrinkle_map_node.outputs['Alpha'], node.inputs["animatedWrinkleMap Alpha"])

                        if "animatedWrinkleMask Color" in node.inputs:
                            links.new(wrinkle_mask_node.outputs['Color'], node.inputs["animatedWrinkleMask Color"])
                        if "animatedWrinkleMask Alpha" in node.inputs:
                            links.new(wrinkle_mask_node.outputs['Alpha'], node.inputs["animatedWrinkleMask Alpha"])

                        if "Scar RotationMap Color" in node.inputs:
                            links.new(scarMapNode.outputs['Color'], node.inputs["Scar RotationMap Color"])
                        if "Scar RotationMap Alpha" in node.inputs:
                            links.new(scarMapNode.outputs['Alpha'], node.inputs["Scar RotationMap Alpha"])                         

def process_object(obj):
            detectedShader = None
            detectedNodeGroupName = None
            shadersBlend = get_shaders_blend_path()

            for node in HERO_GRAVITAS_NODE_NAMES.values():
                detectedNodeGroup = getNodeGroup(obj.data.materials, node)
                if detectedNodeGroup:
                    detectedNodeGroupName = detectedNodeGroup.name
                    detectedShader = find_key_by_value(HERO_GRAVITAS_NODE_NAMES, detectedNodeGroupName)
                    break

            if not detectedShader or not detectedNodeGroupName:
                print(f"No matching shader for {obj.name}")
                return

            kodaShaderName = KODA_NODE_NAMES.get(detectedShader)
            if not kodaShaderName:
                print(f"No Koda shader for {obj.name}")
                return

            kodaNodeGroup = bpy.data.node_groups.get(kodaShaderName)

            if not kodaNodeGroup or not kodaNodeGroup.library:
                with bpy.data.libraries.load(shadersBlend, link=True) as (data_from, data_to):
                    if kodaShaderName in data_from.node_groups:
                        data_to.node_groups = [kodaShaderName]
                    else:
                        print(f"Koda shader '{kodaShaderName}' not found for {obj.name}")
                        return

            kodaNodeGroup = bpy.data.node_groups.get(kodaShaderName)
            if not kodaNodeGroup:
                print(f"Failed to link {kodaShaderName} for {obj.name}")
                return

            print(f"[{obj.name}] Replacing {detectedNodeGroupName} with {kodaNodeGroup.name}")
            replace_existing_node_group(obj, detectedNodeGroupName, kodaNodeGroup.name)

def get_shaders_blend_path():
    try:
        return bpy.context.preferences.addons[__name__].preferences.shadersPath
    except Exception as e:
        print(f"Could not retrieve shaders path: {e}")
        return ""

#Classes
class Auto_Koda_Selected(bpy.types.Operator):
    bl_idname = "autokoda.convert_selected" #load-bearing idname DO NOT RENAME
    bl_label = "Auto Koda"
    bl_description = "Convert the shader of the selected object to a Koda shader"

    def execute(self, context):
        shadersBlend = get_shaders_blend_path()
        if not shadersBlend:
            self.report({'ERROR'}, "Shaders Blend file path not set in preferences!")
            return {'CANCELLED'}

        selectedObj = bpy.context.active_object
        if not selectedObj:
            self.report({'ERROR'}, "No active object selected!")
            return {'CANCELLED'}

        print(f'The selected object is {selectedObj.name}')

        process_object(selectedObj)

        return {'FINISHED'}
    
class Auto_Koda_All(bpy.types.Operator):
    bl_idname = "autokoda.convert_all" #load-bearing idname DO NOT RENAME
    bl_label = "Auto Koda (All Objects)"
    bl_description = "Convert the shaders of all objects in the scene to Koda shaders"

    def execute(self, context):
        shadersBlend = get_shaders_blend_path()
        if not shadersBlend:
            self.report({'ERROR'}, "Shaders Blend file path not set in preferences!")
            return {'CANCELLED'}

        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj.data.materials:
                process_object(obj)

        return {'FINISHED'}
    

class Crunchs_Secret_Button(bpy.types.Operator):
    bl_idname = "autokoda.crunch" #load-bearing idname DO NOT RENAME
    bl_label = "Crunch's Secret Button"
    bl_description = "deploy the goon squad"

    def execute(self, context):
        print('its goonin time')

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
        prefs = bpy.context.preferences.addons[__name__].preferences
        shadersBlendLoc = prefs.shadersPath

        # STATUS BLOCK
        box = layout.box()
        row = box.row()

        if 'Shaders.blend' not in shadersBlendLoc:
            row.alert = True
            row.label(text="Shaders.blend path not set!", icon='ERROR')
            box.operator("preferences.addon_show", text="Set Shaders.blend", icon='FILE_FOLDER').module = __name__
        else:
            row.label(text="Shaders.blend path OK", icon='CHECKMARK')

        # ACTION BUTTONS
        layout.operator(Auto_Koda_Selected.bl_idname, text="Auto Koda (Selected)", icon='RESTRICT_SELECT_OFF')
        layout.operator(Auto_Koda_All.bl_idname, text="Auto Koda (All)", icon='SCENE_DATA')
        layout.operator(Crunchs_Secret_Button.bl_idname, text="Crunch's Secret Button", icon='POSE_HLT')




class Auto_Koda_Preferences(AddonPreferences):
    bl_idname = __name__

    shadersPath: StringProperty(
        name="",
        subtype='FILE_PATH',) # type: ignore

    def draw(self, context):
        layout = self.layout
        layout.label(text="Select your Shaders.blend file below")
        layout.prop(self, "shadersPath")

classes = [Auto_Koda_Selected, Auto_Koda_All, Crunchs_Secret_Button, Auto_Koda_Button, Auto_Koda_Preferences]

def register():
    print('wagwan world')
    print(__name__)
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    print('killin on myself fr')
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)