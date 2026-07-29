import maya.cmds as cmds

def exists(node):
    if not node:
        return False

    return cmds.objExists(node)

def attr_exists(attribute):
    if not attribute:
        return False

    return cmds.objExists(attribute)

def node_type(node):
    if not exists(node):
        return None

    return cmds.nodeType(node)

def is_type(node, type_name):
    if not exists(node):
        return False

    return node_type(node) == type_name

def short_name(node):
    if not node:
        return ""

    return node.split("|")[-1]

def clean_existing_nodes(nodes):
    clean_nodes = []

    for node in nodes or []:
        if not exists(node):
            continue

        clean_nodes.append(node)

    return clean_nodes

def unique_nodes(nodes):
    unique = []

    for node in nodes or []:
        if not node:
            continue

        if node in unique:
            continue

        unique.append(node)

    return unique

def unique_existing_nodes(nodes):
    return clean_existing_nodes(unique_nodes(nodes))