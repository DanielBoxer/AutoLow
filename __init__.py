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
)
from .autolow_op import (
    AUTOLOW_OT_start,
    AUTOLOW_OT_queue_actions,
)


class AUTOLOW_PG_properties(bpy.types.PropertyGroup):
    remesh_percent: bpy.props.IntProperty(
        name="%",
        default=15,
        max=100,
        min=1,
        description=(
            "Percentage used for remeshing. "
            "A lower percent will result in a lower poly mesh"
        ),
    )
    samples: bpy.props.IntProperty(
        name="",
        default=10,
        max=50,
        min=5,
        description=(
            "More samples will give a better estimation of the voxel size. "
            "This is usually unnecessary"
        ),
    )
    resolution: bpy.props.EnumProperty(
        name="",
        description="Image resolution",
        items=[
            ("256", "256 px", ""),
            ("512", "512 px", ""),
            ("1024", "1024 px", ""),
            ("2048", "2048 px", ""),
            ("4096", "4096 px", ""),
            ("8192", "8192 px", ""),
        ],
        default=3,
    )
    remesher: bpy.props.EnumProperty(
        name="",
        description="Remesher",
        items=[
            ("0", "Voxel", ""),
            ("1", "Quad", ""),
            ("2", "Decimate", ""),
            ("3", "None", ""),
        ],
    )


class AUTOLOW_PG_queue_properties(bpy.types.PropertyGroup):
    obj_id: bpy.props.IntProperty()


classes = (
    AUTOLOW_OT_start,
    AUTOLOW_PT_main,
    AUTOLOW_PG_properties,
    AUTOLOW_PG_queue_properties,
    AUTOLOW_UL_queue_items,
    AUTOLOW_OT_queue_actions,
    AUTOLOW_PT_remesh,
    AUTOLOW_PT_queue,
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
