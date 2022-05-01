import bpy


class AUTOLOW_PT_main(bpy.types.Panel):
    bl_label = "Autolow"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AutoLow"

    def draw(self, context):
        layout = self.layout
        props = context.scene.autolow_props

        row = layout.row()
        row.operator("autolow.start", text="Start")

        row = layout.row()
        row.label(text="Voxel Size")
        row.prop(props, "voxel_percent", slider=True)

        row = layout.row()
        row.label(text="Resolution")
        row.prop(props, "resolution")


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


class AUTOLOW_PT_other(bpy.types.Panel):
    bl_label = "Other Settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AutoLow"
    bl_parent_id = "AUTOLOW_PT_main"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        props = context.scene.autolow_props
        layout = self.layout

        row = layout.row()
        row.label(text="Samples")
        row.prop(props, "samples", slider=True)


class AUTOLOW_UL_queue_items(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        layout.label(text=item.name)
