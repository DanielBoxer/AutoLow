import bpy
import math


# utility functions


def calc_avg_voxel_size(obj):
    samples = get_props().samples

    obj_mesh = obj.data
    obj_vertices = obj_mesh.vertices
    obj_edges = obj_mesh.edges

    edge_count = len(obj_edges)
    edge_sum = 0.0

    # how many edges will be used to calculate average
    accuracy_count = samples

    for interval in range(accuracy_count):
        # get edge number at spaced out intervals for better estimation
        edge_number = int(edge_count * interval / accuracy_count)
        # get vertex numbers of chosen edge
        vert1 = obj_edges[edge_number].vertices[0]
        vert2 = obj_edges[edge_number].vertices[1]
        # calculate distance between vertices to get edge length
        edge_sum += math.dist(obj_vertices[vert1].co, obj_vertices[vert2].co)

    # calculate average
    avg_voxel_size = edge_sum / accuracy_count

    return avg_voxel_size


def new_node(nodes, location, name="ShaderNodeTexImage", non_color=False, image=None):
    node = nodes.new(type=name)
    node.location = location
    if image is not None:
        node.image = image
        if non_color:
            node.image.colorspace_settings.name = "Non-Color"
    return node


def make_cage(lowpoly):
    # make cage for baking
    cage = copy_obj(lowpoly)
    cage.name = "cage"
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.transform.shrink_fatten(value=2)
    bpy.ops.object.editmode_toggle()
    cage.select_set(False)
    return cage


def copy_obj(object):
    new = object.copy()
    # copy data so new obj is not an instance
    new.data = object.data.copy()
    new.animation_data_clear()
    bpy.context.collection.objects.link(new)
    deselect_all()
    set_active(new)
    return new


def deselect_all():
    for obj in bpy.context.selected_objects:
        obj.select_set(False)


def set_active(object):
    object.select_set(True)
    bpy.context.view_layer.objects.active = object


def get_props():
    return bpy.context.scene.autolow_props


# main functions


def remesh(highpoly, lowpoly):
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


def uv_unwrap():
    method = get_props().unwrap_method

    if method == "SMART":
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(island_margin=0.05)
        bpy.ops.object.editmode_toggle()


def bake(highpoly, lowpoly):
    props = get_props()
    method = props.bake_method
    resolution = props.resolution
    cage_settings = props.cage_settings
    extrusion = props.extrusion
    ray_dist = props.ray_distance
    is_normal_bake_on = props.is_normal_bake_on
    is_diffuse_bake_on = props.is_diffuse_bake_on

    if method == "TRANSFER":
        # make new material
        material = bpy.data.materials.new(name="Autolow_Material")
        lowpoly.active_material = material
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        principled = nodes.get("Principled BSDF")

        # bake settings
        bpy.context.scene.render.engine = "CYCLES"
        bpy.context.scene.render.bake.use_pass_direct = False
        bpy.context.scene.render.bake.use_pass_indirect = False
        bpy.context.scene.render.bake.use_selected_to_active = True

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
            normal_image = bpy.data.images.new(
                name="normal",
                width=int(resolution),
                height=int(resolution),
                alpha=False,
                float_buffer=True,
            )
            normal_texture = new_node(nodes, (-500, -150), image=normal_image)
            normal_map = new_node(nodes, (-200, -175), "ShaderNodeNormalMap")
            links.new(normal_texture.outputs[0], normal_map.inputs[1])
            links.new(normal_map.outputs[0], principled.inputs[22])

            # bake settings
            bpy.context.scene.render.use_bake_multires = True
            bpy.context.scene.render.bake_type = "NORMALS"

            # bake normals
            set_active(lowpoly)
            nodes.active = normal_texture
            bpy.ops.object.bake_image()
            # turn off multires
            bpy.context.scene.render.use_bake_multires = False

        # diffuse
        if is_diffuse_bake_on:
            # setup nodes
            diffuse_image = bpy.data.images.new(
                name="diffuse",
                width=int(resolution),
                height=int(resolution),
            )
            diffuse_texture = new_node(nodes, (-500, 300), image=diffuse_image)
            links.new(diffuse_texture.outputs[0], principled.inputs[0])

            # bake diffuse
            highpoly.select_set(True)
            set_active(lowpoly)
            nodes.active = diffuse_texture
            bpy.ops.object.bake(type="DIFFUSE")

        # remove cage
        if cage_settings == "AUTO":
            bpy.data.objects.remove(cage, do_unlink=True)


class AUTOLOW_OT_start(bpy.types.Operator):
    bl_idname = "autolow.start"
    bl_label = "Start Process"
    bl_description = "Start process"

    def execute(self, context):
        autolow_queue = context.scene.queue
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
            lowpoly = copy_obj(highpoly)
            lowpoly.name = highpoly.name + "_LP"

            # shade smooth and turn off autosmooth
            bpy.ops.object.shade_smooth()
            highpoly.data.use_auto_smooth = False
            lowpoly.data.use_auto_smooth = False

            remesh(highpoly, lowpoly)
            uv_unwrap()
            bake(highpoly, lowpoly)

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
