import bpy
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
from .autolow_main import remesh_process, uv_unwrap_process, bake_process
from .autolow_utils import get_props, save, copy_obj
import pathlib


class AUTOLOW_OT_start(Operator):
    bl_idname = "autolow.start"
    bl_label = "Start Process"
    bl_description = "Start process"

    def execute(self, context):
        props = get_props()

        if not save():
            self.report({"WARNING"}, "Save file before activating autosave")
            return {"CANCELLED"}

        if props.is_image_saved:
            path = props.image_path
            default = ".\\Autolow\\"
            if path != default:
                # check if image path exists
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
            elif bpy.data.filepath == "":
                # check if file has been saved
                self.report(
                    {"ERROR"},
                    (
                        "Image path unknown."
                        " Either save the blender file or set the path in settings"
                    ),
                )
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
            if props.autosave_after:
                save()

        # remove all items from queue
        context.scene.queue.clear()

        return {"FINISHED"}


class AUTOLOW_OT_set_workflow(Operator):
    bl_idname = "autolow.set_workflow"
    bl_label = "Set Workflow"
    bl_description = (
        "Change addon settings to the workflow selected. "
        "This is not necessary when using the addon and is only a shortcut. "
        "If you would like to customize the settings, this panel can be ignored"
    )

    def execute(self, context):
        props = get_props()
        workflow = props.workflow
        remesher = props.remesher

        if workflow == "FULL":
            if remesher == "NONE":
                props.remesher = "VOXEL"
            props.unwrap_method = "SMART"
            props.bake_method = "TRANSFER"

        elif workflow == "TRANSFER_BAKE":
            props.remesher = "NONE"
            props.unwrap_method = "SMART"
            props.bake_method = "TRANSFER"

        elif workflow == "ACTIVE_BAKE":
            props.remesher = "NONE"
            props.unwrap_method = "SMART"
            props.bake_method = "ACTIVE"

        else:
            props.remesher = "NONE"
            props.unwrap_method = "NONE"
            props.bake_method = "NONE"

        return {"FINISHED"}


class AUTOLOW_OT_open_filebrowser(Operator, ImportHelper):
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
            self.report({"INFO"}, "Path: " + new_path)
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
