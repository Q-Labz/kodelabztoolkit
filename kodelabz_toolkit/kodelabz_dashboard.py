import bpy

class KDLZ_PT_MainPanel(bpy.types.Panel):
    bl_label = "KodeLabz Toolkit"
    bl_idname = "KDLZ_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KodeLabz"

    def draw(self, context):
        layout = self.layout
        
        # Toolkit Logo/Header
        box = layout.box()
        row = box.row()
        row.label(text="KodeLabz Toolkit v0.1", icon="TOOL_SETTINGS")
        
        # Modules Section
        layout.label(text="Modules")
        
        # AI Texture Lab
        box = layout.box()
        row = box.row()
        row.operator("kdlz.ai_texture_lab", icon="TEXTURE_DATA")
        row.label(text="AI Texture Lab")
        
        # AutoMesh Pro
        box = layout.box()
        row = box.row()
        row.operator("kdlz.auto_mesh_pro", icon="MOD_REMESH")
        row.label(text="AutoMesh Pro")
        
        # ScatterCraft
        box = layout.box()
        row = box.row()
        row.operator("kdlz.scatter_craft", icon="PARTICLES")
        row.label(text="ScatterCraft")
        
        # Settings
        layout.separator()
        layout.operator("kdlz.open_preferences", icon="PREFERENCES")

class KDLZ_OT_OpenPreferences(bpy.types.Operator):
    bl_idname = "kdlz.open_preferences"
    bl_label = "Toolkit Settings"
    
    def execute(self, context):
        bpy.ops.preferences.addon_show(module="kodelabz_toolkit")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(KDLZ_PT_MainPanel)
    bpy.utils.register_class(KDLZ_OT_OpenPreferences)

def unregister():
    bpy.utils.unregister_class(KDLZ_PT_MainPanel)
    bpy.utils.unregister_class(KDLZ_OT_OpenPreferences)
