bl_info = {
    "name": "KodeLabz Toolkit",
    "author": "KodeLabz",
    "version": (0, 1),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > KodeLabz Toolkit",
    "description": "Modular Blender add-on with AI tools, retopology, scattering, and more",
    "category": "3D View",
}

import bpy
from . import kodelabz_dashboard
from . import preferences
from .tools import ai_texture_lab, auto_mesh_pro, scatter_craft

modules = [kodelabz_dashboard, preferences, ai_texture_lab, auto_mesh_pro, scatter_craft]

def register():
    for mod in modules:
        mod.register()

def unregister():
    for mod in reversed(modules):
        mod.unregister()

if __name__ == "__main__":
    register()
