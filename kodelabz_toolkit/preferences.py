import bpy

class KDLZ_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = "kodelabz_toolkit"
    
    api_token: bpy.props.StringProperty(
        name="API Token",
        description="API token for cloud services (Replicate)",
        default="",
        subtype='PASSWORD'
    )
    
    theme_mode: bpy.props.EnumProperty(
        name="Theme Mode",
        items=[
            ('LIGHT', "Light", "Light theme mode"),
            ('DARK', "Dark", "Dark theme mode"),
        ],
        default='DARK'
    )
    
    def draw(self, context):
        layout = self.layout
        
        # API Settings
        box = layout.box()
        box.label(text="API Settings", icon="URL")
        box.prop(self, "api_token")
        
        # Theme Settings
        box = layout.box()
        box.label(text="Theme Settings", icon="COLOR")
        box.prop(self, "theme_mode")
        
        # About
        box = layout.box()
        box.label(text="About KodeLabz Toolkit", icon="INFO")
        col = box.column()
        col.label(text="Version: 0.1")
        col.label(text=" 2025 KodeLabz")
        col.operator("wm.url_open", text="Visit Website").url = "https://kodelabz.com"

def register():
    bpy.utils.register_class(KDLZ_AddonPreferences)

def unregister():
    bpy.utils.unregister_class(KDLZ_AddonPreferences)
