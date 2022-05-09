import bpy


class AUTOLOW_PT_main(bpy.types.Panel):
    bl_label = "Autolow"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AutoLow"

    def draw(self, context):
        row = self.layout.row()
        row.scale_y = 2
        row.operator("autolow.start", text="Start")


class AUTOLOW_PT_remesh(bpy.types.Panel):
    bl_label = "Remesh"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AutoLow"
    bl_parent_id = "AUTOLOW_PT_main"

    def draw(self, context):
        layout = self.layout
        props = context.scene.autolow_props

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


class AUTOLOW_PT_uv_unwrap(bpy.types.Panel):
    bl_label = "UV Unwrap"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AutoLow"
    bl_parent_id = "AUTOLOW_PT_main"

    def draw(self, context):
        layout = self.layout
        props = context.scene.autolow_props

        row = layout.row()
        row.label(text="Method")
        row.prop(props, "unwrap_method")


class AUTOLOW_PT_baking(bpy.types.Panel):
    bl_label = "Baking"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AutoLow"
    bl_parent_id = "AUTOLOW_PT_main"

    def draw(self, context):
        layout = self.layout
        props = context.scene.autolow_props
        bake_method = props.bake_method

        row = layout.row()
        row.label(text="Method")
        row.prop(props, "bake_method")

        if bake_method != "NONE":
            row = layout.row()
            row.label(text="Resolution")
            row.prop(props, "resolution")


class AUTOLOW_PT_maps(bpy.types.Panel):
    bl_label = "Maps"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AutoLow"
    bl_parent_id = "AUTOLOW_PT_baking"

    def draw(self, context):
        layout = self.layout
        props = context.scene.autolow_props

        col = layout.column(align=True)
        col.prop(props, "is_normal_bake_on")
        col.prop(props, "is_diffuse_bake_on")


class AUTOLOW_PT_queue(bpy.types.Panel):
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
