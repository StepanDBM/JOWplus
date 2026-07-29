"""import importlib
import sys


def reload_package(package_name):
    modules = []
    for name in sys.modules:
        if (
            name == package_name or
            name.startswith(package_name + ".")
        ):
            modules.append(name)

    modules.sort(
        key=lambda x: x.count("."),
        reverse=True
    )
    for name in modules:
        try:
            importlib.reload(sys.modules[name])

        except Exception as e:
            print(
                "JOW reload failed:",
                name,
                e
            )


def bootstrap():
    reload_package("JOW_core")
    reload_package("JOW_ui")
    
Package-scanning reloaders are elegant until Maya decides to be Maya.
For now I will be using a hardcoded ordered module list.
Deterministic, boring, reliable.
Beautiful stupid little brick.
    """

import importlib


MODULES_TO_RELOAD = [
    "JOW_core.JOW_utils.JOW_undo",
    "JOW_core.JOW_data",
    "JOW_core.JOW_math",
    "JOW_core.JOW_presets",
    "JOW_core.JOW_core",

    "JOW_ui.JOW_gl.JOW_guides",
    "JOW_ui.JOW_gl.JOW_preview",

    "JOW_ui.JOW_widgets.JOW_widget_utils",
    "JOW_ui.JOW_widgets.JOW_tool_panel",
    "JOW_ui.JOW_widgets.JOW_cache_panel",
    "JOW_ui.JOW_widgets.JOW_settings_panel",
    "JOW_ui.JOW_widgets.JOW_action_bar",

    "JOW_ui.JOW_drawables.JOW_grid_drawer",
    "JOW_ui.JOW_drawables.JOW_axis_drawer",
    "JOW_ui.JOW_drawables.JOW_joint_drawer",
    "JOW_ui.JOW_drawables.JOW_guide_drawer",
    "JOW_ui.JOW_drawables.JOW_plane_drawer",
    "JOW_ui.JOW_drawables.JOW_overlay_drawer",

    "JOW_ui.JOW_viewport",
    "JOW_ui.JOW_ui",

    "JOW_launcher"
]


def reload_module(module_name):
    try:
        module = importlib.import_module(module_name)
        importlib.reload(module)
        print("JOW reloaded:", module_name)
        return module

    except Exception as e:
        print("JOW reload failed:", module_name, e)
        raise


def bootstrap():
    for module_name in MODULES_TO_RELOAD:
        reload_module(module_name)