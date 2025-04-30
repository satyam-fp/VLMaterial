import bpy

def shader_material(material: bpy.types.Material):
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    # Create nodes
    material_output = nodes.new('ShaderNodeOutputMaterial')
    principled_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    colorramp = nodes.new('ShaderNodeValToRGB')
    voronoi_texture = nodes.new('ShaderNodeTexVoronoi')
    mapping = nodes.new('ShaderNodeMapping')
    texture_coordinate = nodes.new('ShaderNodeTexCoord')
    bump = nodes.new('ShaderNodeBump')
    noise_texture = nodes.new('ShaderNodeTexNoise')
    displacement = nodes.new('ShaderNodeDisplacement')
    colorramp_1 = nodes.new('ShaderNodeValToRGB')

    # Create links to connect nodes
    links.new(principled_bsdf.outputs[0], material_output.inputs[0])
    links.new(displacement.outputs[0], material_output.inputs[2])
    links.new(colorramp.outputs[0], principled_bsdf.inputs[0])
    links.new(bump.outputs[0], principled_bsdf.inputs[22])
    links.new(voronoi_texture.outputs[0], colorramp.inputs[0])
    links.new(mapping.outputs[0], voronoi_texture.inputs[0])
    links.new(texture_coordinate.outputs[3], mapping.inputs[0])
    links.new(noise_texture.outputs[0], bump.inputs[2])
    links.new(mapping.outputs[0], noise_texture.inputs[0])
    links.new(colorramp_1.outputs[0], displacement.inputs[0])
    links.new(voronoi_texture.outputs[0], colorramp_1.inputs[0])

    # Set parameters for each node
    principled_bsdf.inputs[1].default_value = 0.4
    principled_bsdf.inputs[3].default_value = [0.8, 0.12, 0.002, 1.0]
    principled_bsdf.inputs[9].default_value = 0.3
    colorramp.color_ramp.elements[0].position = 0.082
    colorramp.color_ramp.elements[0].color = [0.766, 0.206, 0.037, 1.0]
    colorramp.color_ramp.elements[1].position = 0.95
    colorramp.color_ramp.elements[1].color = [1.0, 0.37, 0.042, 1.0]
    voronoi_texture.inputs[2].default_value = 3.0
    bump.inputs[0].default_value = 0.03
    noise_texture.inputs[3].default_value = 15.0
    displacement.inputs[1].default_value = 0.8
    displacement.inputs[2].default_value = 0.15
    colorramp_1.color_ramp.elements[1].position = 0.314

mat = bpy.data.materials.new(name = "new material")
shader_material(mat)
