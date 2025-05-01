

import bpy

def shader_material(material: bpy.types.Material):
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    # Create nodes
    material_output = nodes.new('ShaderNodeOutputMaterial')
    mix_shader = nodes.new('ShaderNodeMixShader')
    group = nodes.new('ShaderNodeGroup')
    group.node_tree = bpy.data.node_groups['Procedural_Sci_fi_Tiles']
    multiply = nodes.new('ShaderNodeMath')
    noise_texture = nodes.new('ShaderNodeTexNoise')
    mapping = nodes.new('ShaderNodeMapping')
    texture_coordinate = nodes.new('ShaderNodeTexCoord')
    group_001 = nodes.new('ShaderNodeGroup')
    group_001.node_tree = bpy.data.node_groups['Cliff_Rock']
    normal_map = nodes.new('ShaderNodeNormalMap')
    displacement = nodes.new('ShaderNodeDisplacement')
    bump = nodes.new('ShaderNodeBump')
    colorramp = nodes.new('ShaderNodeValToRGB')

    # Create links to connect nodes
    links.new(mix_shader.outputs[0], material_output.inputs[0])
    links.new(displacement.outputs[0], material_output.inputs[2])
    links.new(group.outputs[1], mix_shader.inputs[1])
    links.new(group_001.outputs[0], mix_shader.inputs[2])
    links.new(multiply.outputs[0], group.inputs[2])
    links.new(noise_texture.outputs[0], multiply.inputs[0])
    links.new(mapping.outputs[0], noise_texture.inputs[0])
    links.new(texture_coordinate.outputs[3], mapping.inputs[0])
    links.new(normal_map.outputs[0], group_001.inputs[6])
    links.new(bump.outputs[0], displacement.inputs[3])
    links.new(colorramp.outputs[0], bump.inputs[2])
    links.new(noise_texture.outputs[1], colorramp.inputs[0])

    # Set parameters for each node
    mix_shader.inputs[0].default_value = 0.592
    group.inputs[0].default_value = 0.592
    group.inputs[1].default_value = [0.415, 0.523, 0.842, 0.591]
    group.inputs[5].default_value = -0.005
    multiply.inputs[1].default_value = 0.926
    multiply.operation = 'MULTIPLY'
    noise_texture.inputs[1].default_value = 4.56
    noise_texture.inputs[2].default_value = 0.375
    noise_texture.inputs[3].default_value = 12.4
    mapping.inputs[1].default_value = [-0.006, -0.024, -0.013]
    mapping.inputs[2].default_value = [0.039, -0.035, -0.038]
    group_001.inputs[1].default_value = [0.005, -0.021, -0.021]
    group_001.inputs[7].default_value = 0.898
    group_001.inputs[8].default_value = 0.732
    group_001.inputs[10].default_value = 12.9
    group_001.inputs[11].default_value = 0.77
    normal_map.space = 'BLENDER_WORLD'
    displacement.inputs[1].default_value = 0.13
    displacement.inputs[2].default_value = 0.951
    bump.inputs[0].default_value = 0.788
    colorramp.color_ramp.elements[0].position = 0.223
    colorramp.color_ramp.elements[0].color = [0.342, 0.344, 0.34, 0.921]
    colorramp.color_ramp.elements[1].position = 0.447
    colorramp.color_ramp.elements[1].color = [0.574, 0.568, 0.563, 0.638]

mat = bpy.data.materials.new('Material')
shader_material(mat)





import bpy

def shader_material(material: bpy.types.Material):
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    # Create nodes
    material_output = nodes.new('ShaderNodeOutputMaterial')
    mix_shader = nodes.new('ShaderNodeMixShader')
    group = nodes.new('ShaderNodeGroup')
    group.node_tree = bpy.data.node_groups['Procedural Sci-fi Panels']
    group_001 = nodes.new('ShaderNodeGroup')
#    group_001.node_tree = bpy.data.node_groups['Giants_Rock']
    texture_coordinate = nodes.new('ShaderNodeTexCoord')
    displacement = nodes.new('ShaderNodeDisplacement')

    # Create links to connect nodes
    links.new(mix_shader.outputs[0], material_output.inputs[0])
    links.new(displacement.outputs[0], material_output.inputs[2])
    links.new(group.outputs[0], mix_shader.inputs[1])
#    links.new(group_001.outputs[0], mix_shader.inputs[2])
#    links.new(texture_coordinate.outputs[1], group_001.inputs[0])
#    links.new(texture_coordinate.outputs[3], group_001.inputs[1])
#    links.new(group_001.outputs[2], displacement.inputs[0])

    # Set parameters for each node
#    group.inputs[4].default_value = 0.726
#    group.inputs[7].default_value = [0.54, 0.506, 0.247, 0.705]
#    group.inputs[8].default_value = [0.166, 0.179, 0.144, 0.898]
#    group_001.inputs[2].default_value = 0.7
#    group_001.inputs[3].default_value = 0.96
#    group_001.inputs[4].default_value = 0.609
#    group_001.inputs[6].default_value = 1.24
#    group_001.inputs[7].default_value = 0.957
#    group_001.inputs[8].default_value = 1.04
#    group_001.inputs[9].default_value = 2.78
#    group_001.inputs[10].default_value = 1.74
#    group_001.inputs[12].default_value = 1.11
#    group_001.inputs[13].default_value = 0.774
#    group_001.inputs[14].default_value = 0.837
#    displacement.inputs[1].default_value = 0.047
#    displacement.inputs[2].default_value = 0.072

mat = bpy.data.materials.new('New Material')
shader_material(mat)
