import bpy
from bpy.types import Panel
from .autolow_op import get_props


class AUTOLOW_PT_main(Panel):
    bl_label = "Autolow"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AutoLow"

    def draw(self, context):
        row = self.layout.row()
        row.scale_y = 2
        row.operator("autolow.start", text="Start")


class AUTOLOW_PT_remesh(Panel):
    bl_label = "Remesh"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AutoLow"
    bl_parent_id = "AUTOLOW_PT_main"

    def draw(self, context):
        layout = self.layout
        props = get_props()

        remesher = props.remesher

        row = layout.row()
        row.label(text="Remesher")
        row.prop(props, "remesher")

        row = layout.row()

        if remesher != "NONE":
            row.label(text="Percent")
            row.prop(props, "remesh_percent", slider=True)

        if remesher == "VOXEL":
            row = layout.row()
            row.label(text="Samples")
            row.prop(props, "samples", slider=True)


class AUTOLOW_PT_uv_unwrap(Panel):
    bl_label = "UV Unwrap"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AutoLow"
    bl_parent_id = "AUTOLOW_PT_main"

    def draw(self, context):
        layout = self.layout
        props = get_props()

        row = layout.row()
        row.label(text="Method")
        row.prop(props, "unwrap_method")


class AUTOLOW_PT_baking(Panel):
    bl_label = "Baking"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AutoLow"
    bl_parent_id = "AUTOLOW_PT_main"

    def draw(self, context):
        layout = self.layout
        props = get_props()
        bake_method = props.bake_method
        cage_settings = props.cage_settings

        row = layout.row()
        row.label(text="Method")
        row.prop(props, "bake_method")

        if bake_method != "NONE":
            row = layout.row()
            row.prop(props, "cage_settings", text=" ", expand=True)

            if cage_settings == "MANUAL":
                row = layout.row()
                row.label(text="Extrusion")
                row.prop(props, "extrusion")

                row = layout.row()
                row.label(text="Ray Distance")
                row.prop(props, "ray_distance")


class AUTOLOW_PT_maps(Panel):
    bl_label = "Maps"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AutoLow"
    bl_parent_id = "AUTOLOW_PT_baking"

    def draw(self, context):
        layout = self.layout
        props = get_props()
        bake_method = props.bake_method

        row = layout.row()
        row.label(text="Resolution")
        row.prop(props, "resolution")

        row = layout.row(align=True)
        row.prop(props, "is_normal_bake_on")
        row.prop(props, "is_diffuse_bake_on")
        if bake_method == "NONE":
            row.active = False
            row.active = False


class AUTOLOW_PT_settings(Panel):
    bl_label = "Settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AutoLow"
    bl_parent_id = "AUTOLOW_PT_main"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        pass


class AUTOLOW_PT_save_image(Panel):
    bl_label = "Save Images"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "AUTOLOW_PT_settings"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        self.layout.prop(get_props(), "is_image_saved", text="")

    def draw(self, context):
        layout = self.layout
        props = get_props()
        image_path = props.image_path
        is_image_saved = props.is_image_saved

        row = layout.row()
        row.operator("autolow.open_filebrowser", icon="FILEBROWSER")
        if not is_image_saved:
            row.active = False

        row = layout.row()
        row.label(text="Path: " + image_path)
        if not is_image_saved:
            row.active = False


class AUTOLOW_PT_autosave(Panel):
    bl_label = "Autosave"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "AUTOLOW_PT_settings"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        self.layout.prop(get_props(), "autosave", text="")

    def draw(self, context):
        layout = self.layout
        props = get_props()
        autosave = props.autosave

        row = layout.row()
        row.prop(get_props(), "autosave_after")
        if not autosave:
            row.active = False


class AUTOLOW_PT_queue(Panel):
    bl_label = "Queue"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AutoLow"
    bl_parent_id = "AUTOLOW_PT_main"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.template_list(
            "AUTOLOW_UL_queue_items", "", scene, "queue", scene, "queue_index"
        )

        col = row.column(align=True)
        col.operator("queue.actions", icon="ADD", text="").action = "ADD"
        col.operator("queue.actions", icon="REMOVE", text="").action = "REMOVE"
        col.separator()
        col.operator("queue.actions", icon="TRIA_UP", text="").action = "UP"
        col.operator("queue.actions", icon="TRIA_DOWN", text="").action = "DOWN"


class AUTOLOW_UL_queue_items(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        layout.label(text=item.name)
