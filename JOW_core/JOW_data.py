from dataclasses import dataclass
from dataclasses import field


@dataclass
class OrientationSettings:
    primary_axis: str = "X"
    secondary_axis: str = "Y"
    secondary_mode: str = "World"
    custom_object: str = None

    flip_plane: bool = False
    average_normals: bool = True

    orient_end_joint: bool = True
    
    roots: list = field(default_factory=list)


@dataclass
class JointOrientation:
    joint: str
    matrix: list