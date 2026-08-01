import __main__
from JOW_ui.JOW_ui import JOWWindow
from JOW_ui.JOW_ui import maya_main_window

def show():
    old_window = getattr(
        __main__,
        "JOW_WINDOW",
        None
    )

    if old_window:
        try:
            if hasattr(old_window, "cleanup_before_delete"):
                old_window.cleanup_before_delete()
        except Exception:
            pass

        try:
            old_window.close()
        except Exception:
            pass

        try:
            old_window.deleteLater()
        except Exception:
            pass

    __main__.JOW_WINDOW = JOWWindow(
        parent=maya_main_window()
    )

    __main__.JOW_WINDOW.show()