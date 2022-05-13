from bpy.types import PropertyGroup
from bpy.props import (
    EnumProperty,
    IntProperty,
    FloatProperty,
    BoolProperty,
    StringProperty,
)


class AUTOLOW_PG_properties(PropertyGroup):

    # remesh properties

    remesher: EnumProperty(
        name="",
        description="Remesher",
        items=[
            ("VOXEL", "Voxel", "Use the voxel remesher"),
            ("QUAD", "Quad", "Use the quad remesher"),
            ("DECIMATE", "Decimate", "Apply a decimate modifier"),
            ("NONE", "None", ""),
        ],
    )
    remesh_percent: IntProperty(
        name="%",
        default=15,
        max=100,
        min=1,
        description=(
            "Percentage used for remeshing. "
            "A lower percent will result in a lower poly mesh"
        ),
    )
    samples: IntProperty(
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

    unwrap_method: EnumProperty(
        name="",
        description="UV Unwrap Method",
        items=[
            ("SMART", "Smart UV Project", "Use smart UV project to unwrap mesh"),
            ("NONE", "None", ""),
        ],
    )

    # baking properties

    bake_method: EnumProperty(
        name="",
        description="Bake Method",
        items=[
            (
                "TRANSFER",
                "Transfer",
                "Bake textures from one object to another",
            ),
            ("ACTIVE", "Active", "Bake textures of active object"),
            ("NONE", "None", ""),
        ],
    )
    cage_settings: EnumProperty(
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
    extrusion: FloatProperty(
        name="",
        description="Inflate the active object by the specified distance for baking",
        max=1,
        min=0,
        unit="LENGTH",
    )
    ray_distance: FloatProperty(
        name="", description="The maximum ray distance", max=1, min=0, unit="LENGTH"
    )
    resolution: EnumProperty(
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

    # maps properties

    is_normal_bake_on: BoolProperty(
        name="Normals", description="Bake normal map", default=True
    )
    is_diffuse_bake_on: BoolProperty(
        name="Diffuse", description="Bake diffuse map", default=True
    )

    # settings properties

    is_image_saved: BoolProperty(
        name="", description="Save images after baking", default=True
    )
    image_path: StringProperty(
        name="Path",
        description="Images will be saved at this path.",
        default=".\\Autolow\\",
    )


class AUTOLOW_PG_queue_properties(PropertyGroup):
    obj_id: IntProperty()
