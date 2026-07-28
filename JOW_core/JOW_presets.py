import os
import json


def get_preset_directory():

    base = os.path.dirname(__file__)
    preset_dir = os.path.join(base, "..", "presets")

    if not os.path.exists(preset_dir):
        os.makedirs(preset_dir)

    return os.path.abspath(preset_dir)


def save_preset(name, data):

    path = os.path.join(
        get_preset_directory(),
        "{}.json".format(name)
    )

    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def load_preset(name):

    path = os.path.join(
        get_preset_directory(),
        "{}.json".format(name)
    )

    if not os.path.exists(path):
        return None

    with open(path, "r") as f:
        return json.load(f)