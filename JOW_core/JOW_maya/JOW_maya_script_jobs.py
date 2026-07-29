import maya.cmds as cmds


def exists(script_job_id):
    if not script_job_id:
        return False

    return cmds.scriptJob(exists=script_job_id)


def kill(script_job_id, force=True):
    if not exists(script_job_id):
        return False

    cmds.scriptJob(
        kill=script_job_id,
        force=force
    )

    return True


def create_selection_changed_job(callback, protected=True):
    return cmds.scriptJob(
        event=[
            "SelectionChanged",
            callback
        ],
        protected=protected
    )