import bpy
import math


def remesh(self, highpoly, lowpoly, remesher, remesh_percent, samples):
    if remesher == "VOXEL":
        # voxel remesh
        avg_voxel_size = calc_avg_voxel_size(lowpoly, samples)
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
            self.report(
                {"WARNING"}, "Mesh is non manifold and will be voxel remeshed first"
            )
            # voxel remesh to make mesh manifold
            lowpoly.data.remesh_voxel_size = calc_avg_voxel_size(lowpoly, samples)
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


def calc_avg_voxel_size(lowpoly, samples):
    lowpoly_mesh = lowpoly.data
    lowpoly_vertices = lowpoly_mesh.vertices
    lowpoly_edges = lowpoly_mesh.edges

    edge_count = len(lowpoly_edges)
    edge_sum = 0.0

    # how many edges will be used to calculate average
    accuracy_count = samples

    for interval in range(accuracy_count):
        # get edge number at spaced out intervals for better estimation
        edge_number = int(edge_count * interval / accuracy_count)
        # get vertex numbers of chosen edge
        vert1 = lowpoly_edges[edge_number].vertices[0]
        vert2 = lowpoly_edges[edge_number].vertices[1]
        # calculate distance between vertices to get edge length
        edge_sum += math.dist(lowpoly_vertices[vert1].co, lowpoly_vertices[vert2].co)

    # calculate average
    avg_voxel_size = edge_sum / accuracy_count

    return avg_voxel_size


def uv_unwrap(method):
    if method == "SMART":
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(island_margin=0.05)
        bpy.ops.object.editmode_toggle()


def bake_normals(material, resolution):
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    principled = nodes.get("Principled BSDF")

    # normal map node
    normal_texture = nodes.new(type="ShaderNodeTexImage")
    normal_texture.location = (-500, -150)
    normal_map = nodes.new(type="ShaderNodeNormalMap")
    normal_map.location = (-200, -175)
    links.new(normal_texture.outputs[0], normal_map.inputs[1])
    links.new(normal_map.outputs[0], principled.inputs[22])
    normal_image = bpy.data.images.new(
        name="normal",
        width=int(resolution),
        height=int(resolution),
        alpha=False,
        float_buffer=True,
    )
    normal_texture.image = normal_image
    normal_texture.image.colorspace_settings.name = "Non-Color"

    # bake normal map
    bpy.context.scene.render.use_bake_multires = True
    bpy.context.scene.render.bake_type = "NORMALS"
    nodes.active = normal_texture
    bpy.ops.object.bake_image()


def bake_diffuse(highpoly, lowpoly, cage, extrusion, ray_dist, material, resolution):
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    principled = nodes.get("Principled BSDF")

    # diffuse node
    diffuse_texture = nodes.new(type="ShaderNodeTexImage")
    diffuse_texture.location = (-500, 300)
    links.new(diffuse_texture.outputs[0], principled.inputs[0])
    diffuse_image = bpy.data.images.new(
        name="diffuse",
        width=int(resolution),
        height=int(resolution),
    )
    diffuse_texture.image = diffuse_image

    # bake diffuse map
    bpy.context.scene.render.use_bake_multires = False
    nodes.active = diffuse_texture
    bpy.context.scene.render.bake.use_pass_direct = False
    bpy.context.scene.render.bake.use_pass_indirect = False
    bpy.context.scene.render.bake.use_selected_to_active = True

    if cage != None:
        bpy.context.scene.render.bake.use_cage = True
        bpy.context.scene.render.bake.cage_object = cage
        bpy.context.scene.render.bake.cage_extrusion = 0
        bpy.context.scene.render.bake.max_ray_distance = 0
    else:
        bpy.context.scene.render.bake.use_cage = False
        bpy.context.scene.render.bake.cage_extrusion = extrusion
        bpy.context.scene.render.bake.max_ray_distance = ray_dist

    highpoly.select_set(True)
    set_active(lowpoly)
    bpy.ops.object.bake(type="DIFFUSE")


def make_cage(context, lowpoly):
    # make cage for baking
    cage = copy_obj(context, lowpoly)
    cage.name = "cage"
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.transform.shrink_fatten(value=2)
    bpy.ops.object.editmode_toggle()
    cage.select_set(False)
    return cage


def bake(
    context,
    highpoly,
    lowpoly,
    method,
    cage_settings,
    extrusion,
    ray_dist,
    resolution,
    is_normal_bake_on,
    is_diffuse_bake_on,
):
    if method == "ACTIVE":
        # make new material
        material = bpy.data.materials.new(name="Autolow_Material")
        lowpoly.active_material = material
        material.use_nodes = True

        bpy.context.scene.render.engine = "CYCLES"
        if is_normal_bake_on:
            bake_normals(material, resolution)
        if cage_settings == "AUTO":
            cage = make_cage(context, lowpoly)
        else:
            cage = None
        if is_diffuse_bake_on:
            bake_diffuse(
                highpoly, lowpoly, cage, extrusion, ray_dist, material, resolution
            )
        if cage_settings == "AUTO":
            bpy.data.objects.remove(cage, do_unlink=True)


def deselect_all():
    for obj in bpy.context.selected_objects:
        obj.select_set(False)


def set_active(object):
    object.select_set(True)
    bpy.context.view_layer.objects.active = object


def copy_obj(context, object):
    new = object.copy()
    # copy data so new obj is not an instance
    new.data = object.data.copy()
    new.animation_data_clear()
    context.collection.objects.link(new)
    deselect_all()
    set_active(new)
    return new


class AUTOLOW_OT_start(bpy.types.Operator):
    bl_idname = "autolow.start"
    bl_label = "Start Process"
    bl_description = "Start process"

    def execute(self, context):
        scn = context.scene
        props = scn.autolow_props
        # remesh props
        remesher = props.remesher
        remesh_percent = props.remesh_percent
        samples = props.samples
        # UV props
        uv_method = props.unwrap_method
        # baking props
        bake_method = props.bake_method
        cage_settings = props.cage_settings
        extrusion = props.extrusion
        ray_dist = props.ray_distance
        resolution = props.resolution
        is_normal_bake_on = props.is_normal_bake_on
        is_diffuse_bake_on = props.is_diffuse_bake_on

        autolow_queue = scn.queue
        objects = []

        if len(autolow_queue) > 0:
            for object in autolow_queue:
                current = bpy.data.objects[object.name]
                current.select_set(False)
                objects.append(current)
        else:
            active_object = bpy.context.active_object
            if not active_object:
                self.report({"ERROR"}, "No object selected")
                return {"CANCELLED"}
            if active_object.type != "MESH":
                self.report({"ERROR"}, "Object must be a mesh")
                return {"CANCELLED"}
            objects.append(active_object)

        for highpoly in objects:
            highpoly.hide_set(False)
            lowpoly = copy_obj(context, highpoly)
            lowpoly.name = highpoly.name + "_LP"

            # shade smooth and turn off autosmooth
            bpy.ops.object.shade_smooth()
            highpoly.data.use_auto_smooth = False
            lowpoly.data.use_auto_smooth = False

            remesh(self, highpoly, lowpoly, remesher, remesh_percent, samples)
            uv_unwrap(uv_method)
            bake(
                context,
                highpoly,
                lowpoly,
                bake_method,
                cage_settings,
                extrusion,
                ray_dist,
                resolution,
                is_normal_bake_on,
                is_diffuse_bake_on,
            )

            highpoly.hide_set(True)
            lowpoly.modifiers.clear()

        # remove all items from queue
        context.scene.queue.clear()

        return {"FINISHED"}


class AUTOLOW_OT_queue_actions(bpy.types.Operator):
    bl_idname = "queue.actions"
    bl_label = "Actions"
    bl_description = "Add, remove, move up, move down"
    bl_options = {"REGISTER"}

    action: bpy.props.EnumProperty(
        items=(
            ("UP", "Up", ""),
            ("DOWN", "Down", ""),
            ("REMOVE", "Remove", ""),
            ("ADD", "Add", ""),
        )
    )

    def invoke(self, context, event):
        scn = context.scene
        idx = scn.queue_index
        try:
            item = scn.queue[idx]
        except IndexError:
            pass
        else:
            if self.action == "DOWN" and idx < len(scn.queue) - 1:
                scn.queue.move(idx, idx + 1)
                scn.queue_index += 1
            elif self.action == "UP" and idx >= 1:
                scn.queue.move(idx, idx - 1)
                scn.queue_index -= 1
            elif self.action == "REMOVE":
                scn.queue_index -= 1
                scn.queue.remove(idx)
        if self.action == "ADD":
            if context.object.type != "MESH":
                self.report({"ERROR"}, "Object must be a mesh")
            elif context.object:
                item = scn.queue.add()
                item.name = context.object.name
                item.obj_id = len(scn.queue)
                scn.queue_index = len(scn.queue) - 1
            else:
                self.report({"INFO"}, "Nothing selected in the Viewport")
        return {"FINISHED"}
