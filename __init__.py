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
)
from .autolow_op import (
    AUTOLOW_OT_start,
    AUTOLOW_OT_queue_actions,
)


class AUTOLOW_PG_properties(bpy.types.PropertyGroup):
    # remesh properties
    remesher: bpy.props.EnumProperty(
        name="",
        description="Remesher",
        items=[
            ("VOXEL", "Voxel", "Use the voxel remesher"),
            ("QUAD", "Quad", "Use the quad remesher"),
            ("DECIMATE", "Decimate", "Apply a decimate modifier"),
            ("NONE", "None", ""),
        ],
    )
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
    # UV properties
    unwrap_method: bpy.props.EnumProperty(
        name="",
        description="UV Unwrap Method",
        items=[
            ("SMART", "Smart UV Project", "Use smart UV project to unwrap mesh"),
            ("NONE", "None", ""),
        ],
    )
    # baking properties
    bake_method: bpy.props.EnumProperty(
        name="",
        description="Bake Method",
        items=[
            ("ACTIVE", "Active", "Bake from active object"),
            ("NONE", "None", ""),
        ],
    )
    cage_settings: bpy.props.EnumProperty(
        name="",
        description="Cage Settings",
        items=[
            (
                "AUTO",
                "Auto Cage",
                "Automatically generate a cage for baking. "
                "The cage is sometimes inaccurate.",
            ),
            ("MANUAL", "Manual", "Manually input extrusion and ray distance."),
        ],
    )
    extrusion: bpy.props.FloatProperty(
        name="",
        description="Inflate the active object by the specified distance for baking",
        max=1,
        min=0,
        unit="LENGTH",
    )
    ray_distance: bpy.props.FloatProperty(
        name="", description="The maximum ray distance", max=1, min=0, unit="LENGTH"
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
    is_normal_bake_on: bpy.props.BoolProperty(
        name="Normals", description="Bake normal map", default=True
    )
    is_diffuse_bake_on: bpy.props.BoolProperty(
        name="Diffuse", description="Bake diffuse map", default=True
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
    AUTOLOW_PT_uv_unwrap,
    AUTOLOW_PT_baking,
    AUTOLOW_PT_maps,
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
