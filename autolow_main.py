from .autolow_utils import *


# main functions


def remesh_process(highpoly, lowpoly):
    props = get_props()
    remesher = props.remesher
    remesh_percent = props.remesh_percent

    if remesher == "VOXEL":
        # voxel remesh
        avg_voxel_size = calc_avg_voxel_size(lowpoly)
        lowpoly.data.remesh_voxel_size = avg_voxel_size * (100 / remesh_percent)
        bpy.ops.object.voxel_remesh()

    elif remesher == "QUAD":
        # quad remesh
        lowpoly_mesh = lowpoly.data
        lowpoly_vertices = lowpoly_mesh.vertices
        lowpoly_facecount = len(lowpoly_mesh.polygons)
        lowpoly_target_faces = int(lowpoly_facecount * (remesh_percent / 100))
        vertex_count = len(lowpoly_vertices)

        bpy.ops.object.quadriflow_remesh(target_faces=lowpoly_target_faces)

        # if the vertex count is the same after remeshing, the remesh probably failed
        # it's likely that the reason is that the mesh isn't manifold
        if len(lowpoly_vertices) == vertex_count:
            # voxel remesh to make mesh manifold
            lowpoly.data.remesh_voxel_size = calc_avg_voxel_size(lowpoly)
            bpy.ops.object.voxel_remesh()
            bpy.ops.object.quadriflow_remesh(target_faces=lowpoly_target_faces)

    elif remesher == "DECIMATE":
        # decimate
        decimate = lowpoly.modifiers.new("Autolow_Decimate", "DECIMATE")
        decimate.ratio = remesh_percent / 100
        bpy.ops.object.modifier_apply(modifier=decimate.name)

    if remesher != "NONE":
        # add multires and shrinkwrap modifiers for better result
        multires = lowpoly.modifiers.new("AutoLow_Multires", "MULTIRES")
        shrinkwrap = lowpoly.modifiers.new("AutoLow_Shrinkwrap", "SHRINKWRAP")
        shrinkwrap.wrap_method = "PROJECT"
        shrinkwrap.target = highpoly
        shrinkwrap.use_negative_direction = True

        # subdivide multires modifier 3 times
        for _ in range(3):
            bpy.ops.object.multires_subdivide(
                modifier="AutoLow_Multires", mode="CATMULL_CLARK"
            )
        bpy.ops.object.modifier_apply(modifier="AutoLow_Shrinkwrap")
        multires.levels = 0


def uv_unwrap_process():
    method = get_props().unwrap_method

    if method == "SMART":
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(island_margin=0.05)
        bpy.ops.object.editmode_toggle()


def bake_process(highpoly, lowpoly):
    props = get_props()
    method = props.bake_method
    cage_settings = props.cage_settings
    extrusion = props.extrusion
    ray_dist = props.ray_distance
    is_normal_bake_on = props.is_normal_bake_on
    is_diffuse_bake_on = props.is_diffuse_bake_on

    if method != "NONE":
        # make new material
        material = bpy.data.materials.new(name="Autolow_Material")
        lowpoly.active_material = material
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        principled = nodes.get("Principled BSDF")
        principled.select = False
        output = nodes.get("Material Output")
        output.select = False

        # bake settings
        bpy.context.scene.render.engine = "CYCLES"
        bpy.context.scene.render.bake.use_pass_direct = False
        bpy.context.scene.render.bake.use_pass_indirect = False

        if method == "TRANSFER":
            bpy.context.scene.render.bake.use_selected_to_active = True
        else:
            bpy.context.scene.render.bake.use_selected_to_active = False

        # make cage
        if cage_settings == "AUTO":
            cage = make_cage(lowpoly)
            bpy.context.scene.render.bake.use_cage = True
            bpy.context.scene.render.bake.cage_object = cage
            bpy.context.scene.render.bake.cage_extrusion = 0
            bpy.context.scene.render.bake.max_ray_distance = 0
        else:
            bpy.context.scene.render.bake.use_cage = False
            bpy.context.scene.render.bake.cage_extrusion = extrusion
            bpy.context.scene.render.bake.max_ray_distance = ray_dist

        # normals
        if is_normal_bake_on:
            # setup nodes
            normal_image = new_image("normal", non_color=True, use_float=False)
            normal_texture = new_node(nodes, (-500, -150), image=normal_image)
            normal_map = new_node(nodes, (-200, -175), "ShaderNodeNormalMap")
            links.new(normal_texture.outputs[0], normal_map.inputs[1])
            links.new(normal_map.outputs[0], principled.inputs[22])
            nodes.active = normal_texture

            # bake normals
            bake("NORMAL", highpoly, lowpoly)
            save_image(normal_image)

        # diffuse
        if is_diffuse_bake_on:
            # setup nodes
            diffuse_image = new_image("diffuse")
            diffuse_texture = new_node(nodes, (-500, 300), image=diffuse_image)
            links.new(diffuse_texture.outputs[0], principled.inputs[0])
            nodes.active = diffuse_texture

            # bake diffuse
            bake("DIFFUSE", highpoly, lowpoly)
            save_image(diffuse_image)

        # remove cage
        if cage_settings == "AUTO":
            bpy.data.objects.remove(cage, do_unlink=True)
