import bpy
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


def save():
    if get_props().autosave:
        if bpy.data.filepath == "":
            # open file browser and save as
            bpy.ops.wm.save_mainfile("INVOKE_AREA")
            return False
        else:
            # save
            bpy.ops.wm.save_mainfile()
    return True


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
