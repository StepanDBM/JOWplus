import maya.cmds as cmds
from JOW_core.JOW_utils.JOW_undo import undo_chunk


GUIDE_NAME = "JOW_Guide_LOC"

@undo_chunk
def create_guide():

    if cmds.objExists(GUIDE_NAME):
        return GUIDE_NAME

    locator = cmds.spaceLocator(
        name=GUIDE_NAME
    )[0]

    return locator
