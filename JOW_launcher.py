import __main__

from JOW_ui.JOW_ui import JOWWindow
from JOW_ui.JOW_ui import maya_main_window


def show():
    try:
        __main__.JOW_WINDOW.close()
        __main__.JOW_WINDOW.deleteLater()

    except Exception:
        pass
    __main__.JOW_WINDOW = JOWWindow(parent=maya_main_window())
    __main__.JOW_WINDOW.show()