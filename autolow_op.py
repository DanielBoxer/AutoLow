import bpy
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
import math
import pathlib


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


def new_node(nodes, location, name="ShaderNodeTexImage", image=None):
    node = nodes.new(type=name)
    node.location = location
    if image is not None:
        node.image = image
    node.select = False
    return node


def new_image(name: str, non_color=False, use_float=False):
    resolution = get_props().resolution
    image = bpy.data.images.new(
        name=name,
        width=int(resolution),
        height=int(resolution),
        float_buffer=use_float,
    )
    if non_color:
        image.colorspace_settings.name = "Non-Color"
    return image


def save_image(image):
    props = get_props()
    is_image_saved = props.is_image_saved

    if is_image_saved:
        path = props.image_path
        if path == ".\\Autolow\\":
            # save images in 'AutoLow' folder
            path = pathlib.Path(bpy.path.abspath("//") + "AutoLow")
            path.mkdir(exist_ok=True)
            path = str(path)

        image.filepath_raw = path + "\\" + image.name + ".png"
        image.file_format = "PNG"
        image.save()


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


def bake(bake_type, highpoly, lowpoly):
    props = get_props()
    bake_method = props.bake_method
    remesher = props.remesher

    # check if multires normal baking should be done
    is_bake_multires = remesher != "NONE" and bake_type == "NORMAL"

    # select objects for baking
    if bake_method == "TRANSFER" and not is_bake_multires:
        highpoly.select_set(True)
    set_active(lowpoly)

    # bake
    if is_bake_multires:
        # multires bake (only for normals)
        bpy.context.scene.render.use_bake_multires = True
        bpy.context.scene.render.bake_type = "NORMALS"
        bpy.ops.object.bake_image()
        bpy.context.scene.render.use_bake_multires = False
    else:
        # regular bake
        bpy.ops.object.bake(type=bake_type)


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


class AUTOLOW_OT_start(Operator):
    bl_idname = "autolow.start"
    bl_label = "Start Process"
    bl_description = "Start process"

    def execute(self, context):
        props = get_props()
        is_image_saved = props.is_image_saved

        # check if image path exists
        if is_image_saved:
            path = props.image_path
            default = ".\\Autolow\\"
            if path != default:
                if not pathlib.Path(path).is_dir():
                    self.report(
                        {"ERROR"},
                        (
                            "The set path doesn't exist."
                            " Path has been reset to the default"
                        ),
                    )
                    props.image_path = default
                    return {"CANCELLED"}

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
            if len(active_object.data.polygons) == 0:
                self.report({"ERROR"}, "The mesh must have more than 0 polygons")
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

            remesh_process(highpoly, lowpoly)
            if (props.unwrap_method != "NONE" or props.bake_method != "NONE") and len(
                lowpoly.data.polygons
            ) == 0:
                self.report({"ERROR"}, "The mesh has 0 polygons after remeshing")
                return {"CANCELLED"}
            uv_unwrap_process()
            bake_process(highpoly, lowpoly)

            highpoly.hide_set(True)
            lowpoly.modifiers.clear()

        # remove all items from queue
        context.scene.queue.clear()

        return {"FINISHED"}


class AUTOLOW_OT_OpenFilebrowser(Operator, ImportHelper):
    bl_idname = "autolow.open_filebrowser"
    bl_label = "Set Path"
    bl_description = (
        "Set path of saved images."
        " If path is not set, images will be saved in a folder called 'AutoLow'"
    )

    def execute(self, context):
        new_path = self.filepath
        if pathlib.Path(new_path).is_dir():
            get_props().image_path = new_path
        else:
            self.report({"ERROR"}, "The path must end with a folder")
            return {"CANCELLED"}

        return {"FINISHED"}


class AUTOLOW_OT_queue_actions(Operator):
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
