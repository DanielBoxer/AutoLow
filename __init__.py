bl_info = {
    "name": "AutoLow",
    "author": "Daniel Boxer",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > AutoLow",
    "description": "Automated high to low poly workflow",
    "category": "Mesh",
}

import bpy
from .autolow_ui import (
    AUTOLOW_PT_main,
    AUTOLOW_UL_queue_items,
    AUTOLOW_PT_queue,
    AUTOLOW_PT_remesh,
    AUTOLOW_PT_uv_unwrap,
    AUTOLOW_PT_baking,
    AUTOLOW_PT_maps,
    AUTOLOW_PT_settings,
    AUTOLOW_PT_save_image,
    AUTOLOW_PT_autosave,
)
from .autolow_op import (
    AUTOLOW_OT_start,
    AUTOLOW_OT_queue_actions,
    AUTOLOW_OT_OpenFilebrowser,
)
from .autolow_props import (
    AUTOLOW_PG_properties,
    AUTOLOW_PG_queue_properties,
)


classes = (
    AUTOLOW_OT_start,
    AUTOLOW_OT_queue_actions,
    AUTOLOW_OT_OpenFilebrowser,
    AUTOLOW_PT_main,
    AUTOLOW_PG_properties,
    AUTOLOW_PG_queue_properties,
    AUTOLOW_UL_queue_items,
    AUTOLOW_PT_remesh,
    AUTOLOW_PT_uv_unwrap,
    AUTOLOW_PT_baking,
    AUTOLOW_PT_maps,
    AUTOLOW_PT_queue,
    AUTOLOW_PT_settings,
    AUTOLOW_PT_save_image,
    AUTOLOW_PT_autosave,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.autolow_props = bpy.props.PointerProperty(
        type=AUTOLOW_PG_properties
    )
    bpy.types.Scene.queue = bpy.props.CollectionProperty(
        type=AUTOLOW_PG_queue_properties
    )
    bpy.types.Scene.queue_index = bpy.props.IntProperty(name="Object Index")


def unregister():
    del bpy.types.Scene.queue_index
    del bpy.types.Scene.queue
    del bpy.types.Scene.autolow_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
