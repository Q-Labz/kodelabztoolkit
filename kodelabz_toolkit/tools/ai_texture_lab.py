import bpy
import requests
import tempfile
import os
import time
from bpy.props import StringProperty, EnumProperty, BoolProperty, FloatProperty, IntProperty

# Get API token from preferences
def get_api_token(context):
    preferences = context.preferences
    addon_prefs = preferences.addons["kodelabz_toolkit"].preferences
    return addon_prefs.api_token

class KDLZ_PT_AiTextureLabPanel(bpy.types.Panel):
    bl_label = "AI Texture Lab"
    bl_idname = "KDLZ_PT_ai_texture_lab"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KodeLabz"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.kdlz_texture_props
        
        # Main settings
        box = layout.box()
        box.label(text="Texture Generation", icon="TEXTURE_DATA")
        box.prop(props, "prompt")
        box.prop(props, "material_type")
        box.prop(props, "seamless")
        
        # Advanced settings
        box = layout.box()
        row = box.row()
        row.prop(props, "show_advanced", icon="PREFERENCES", toggle=True)
        
        if props.show_advanced:
            box.prop(props, "guidance_scale")
            box.prop(props, "num_inference_steps")
            box.prop(props, "seed")
            box.prop(props, "use_random_seed")
        
        # Generate button
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("kdlz.generate_texture", icon="RENDER_STILL")
        
        # Status
        if props.is_generating:
            row = layout.row()
            row.label(text="Generating texture...", icon="SORTTIME")

class KDLZ_OT_AiTextureLab(bpy.types.Operator):
    bl_idname = "kdlz.ai_texture_lab"
    bl_label = "AI Texture Lab"
    
    def execute(self, context):
        # Switch to AI Texture Lab panel
        bpy.context.space_data.context = 'VIEW_3D'
        return {'FINISHED'}

class KDLZ_OT_GenerateTexture(bpy.types.Operator):
    bl_idname = "kdlz.generate_texture"
    bl_label = "Generate Texture"
    
    _timer = None
    _prediction_id = None
    
    def modal(self, context, event):
        props = context.scene.kdlz_texture_props
        
        if event.type == 'TIMER':
            # Check prediction status
            if self._prediction_id:
                try:
                    headers = {
                        "Authorization": f"Token {get_api_token(context)}",
                        "Content-Type": "application/json"
                    }
                    
                    check = requests.get(
                        f"https://api.replicate.com/v1/predictions/{self._prediction_id}", 
                        headers=headers
                    )
                    result = check.json()
                    status = result.get("status")
                    
                    if status == "succeeded":
                        # Get the image URL
                        image_url = result.get("output")
                        if image_url:
                            # Download the image
                            image_data = requests.get(image_url).content
                            
                            # Save to temp file
                            tmp_path = os.path.join(tempfile.gettempdir(), "kodelabz_texture.png")
                            with open(tmp_path, 'wb') as f:
                                f.write(image_data)
                            
                            # Load into Blender
                            img = bpy.data.images.load(tmp_path)
                            img.name = f"KDLZ_{props.material_type}_{int(time.time())}"
                            
                            # Create material
                            mat_name = f"KDLZ_{props.material_type}_{int(time.time())}"
                            mat = bpy.data.materials.new(name=mat_name)
                            mat.use_nodes = True
                            
                            # Set up nodes
                            nodes = mat.node_tree.nodes
                            links = mat.node_tree.links
                            
                            # Clear default nodes
                            for node in nodes:
                                nodes.remove(node)
                            
                            # Create nodes
                            output = nodes.new(type='ShaderNodeOutputMaterial')
                            bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
                            tex_image = nodes.new(type='ShaderNodeTexImage')
                            
                            # Set image
                            tex_image.image = img
                            
                            # Connect nodes
                            links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
                            links.new(tex_image.outputs['Color'], bsdf.inputs['Base Color'])
                            
                            # Position nodes
                            output.location = (300, 0)
                            bsdf.location = (0, 0)
                            tex_image.location = (-300, 0)
                            
                            # Apply to object if selected
                            if context.active_object and context.active_object.type == 'MESH':
                                if context.active_object.data.materials:
                                    context.active_object.data.materials[0] = mat
                                else:
                                    context.active_object.data.materials.append(mat)
                            
                            self.report({'INFO'}, f"Texture generated and applied as {mat_name}")
                        else:
                            self.report({'ERROR'}, "No output image URL found")
                        
                        # End modal
                        props.is_generating = False
                        return self.cancel(context)
                    
                    elif status == "failed":
                        self.report({'ERROR'}, "Texture generation failed")
                        props.is_generating = False
                        return self.cancel(context)
                    
                    # Continue checking
                    return {'PASS_THROUGH'}
                
                except Exception as e:
                    self.report({'ERROR'}, f"Error checking status: {str(e)}")
                    props.is_generating = False
                    return self.cancel(context)
        
        return {'PASS_THROUGH'}
    
    def execute(self, context):
        props = context.scene.kdlz_texture_props
        
        # Check if we have an API token
        api_token = get_api_token(context)
        if not api_token:
            self.report({'ERROR'}, "API token not set. Please check the add-on preferences.")
            return {'CANCELLED'}
        
        # Set generating flag
        props.is_generating = True
        
        # Get parameters
        prompt = props.prompt
        if not prompt:
            self.report({'ERROR'}, "Please enter a prompt")
            props.is_generating = False
            return {'CANCELLED'}
        
        # Enhance prompt with material type
        material_type = props.material_type
        if material_type != 'OTHER':
            prompt = f"{prompt}, {material_type.lower()} material, PBR texture"
        
        # Prepare API request
        model_url = "https://api.replicate.com/v1/predictions"
        
        headers = {
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json"
        }
        
        # Set seed
        seed = props.seed if not props.use_random_seed else None
        
        data = {
            "version": "cf40add0d299df23819762a7e3045e990e045d18f6ed25630e6e5583be68827f",
            "input": {
                "prompt": prompt,
                "seamless": props.seamless,
                "guidance_scale": props.guidance_scale,
                "num_inference_steps": props.num_inference_steps
            }
        }
        
        if seed is not None:
            data["input"]["seed"] = seed
        
        try:
            # Send request
            response = requests.post(model_url, headers=headers, json=data)
            prediction = response.json()
            
            if "id" not in prediction:
                self.report({'ERROR'}, f"Failed to start texture generation: {prediction.get('detail', 'Unknown error')}")
                props.is_generating = False
                return {'CANCELLED'}
            
            # Store prediction ID
            self._prediction_id = prediction["id"]
            
            # Start timer
            wm = context.window_manager
            self._timer = wm.event_timer_add(2.0, window=context.window)
            wm.modal_handler_add(self)
            
            return {'RUNNING_MODAL'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            props.is_generating = False
            return {'CANCELLED'}
    
    def cancel(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        
        return {'CANCELLED'}

class KDLZ_TextureProps(bpy.types.PropertyGroup):
    prompt: StringProperty(
        name="Prompt",
        description="Describe the texture (e.g. rusty sci-fi panel)",
        default=""
    )
    
    material_type: EnumProperty(
        name="Material Type",
        items=[
            ("WOOD", "Wood", "Wood material"),
            ("METAL", "Metal", "Metal material"),
            ("STONE", "Stone", "Stone material"),
            ("FABRIC", "Fabric", "Fabric material"),
            ("PLASTIC", "Plastic", "Plastic material"),
            ("ORGANIC", "Organic", "Organic material"),
            ("SCIFI", "Sci-Fi", "Science fiction material"),
            ("OTHER", "Other", "Custom material"),
        ],
        default="METAL"
    )
    
    seamless: BoolProperty(
        name="Seamless",
        description="Generate a seamless tileable texture",
        default=True
    )
    
    show_advanced: BoolProperty(
        name="Advanced Settings",
        description="Show advanced generation settings",
        default=False
    )
    
    guidance_scale: FloatProperty(
        name="Guidance Scale",
        description="Higher values make the output more closely match the prompt",
        default=7.5,
        min=1.0,
        max=20.0
    )
    
    num_inference_steps: IntProperty(
        name="Steps",
        description="Number of denoising steps (more steps = higher quality but slower)",
        default=50,
        min=20,
        max=100
    )
    
    seed: IntProperty(
        name="Seed",
        description="Random seed for reproducible results",
        default=42
    )
    
    use_random_seed: BoolProperty(
        name="Random Seed",
        description="Use a random seed for each generation",
        default=True
    )
    
    is_generating: BoolProperty(
        name="Is Generating",
        description="Whether texture is currently being generated",
        default=False
    )

def register():
    bpy.utils.register_class(KDLZ_PT_AiTextureLabPanel)
    bpy.utils.register_class(KDLZ_OT_AiTextureLab)
    bpy.utils.register_class(KDLZ_OT_GenerateTexture)
    bpy.utils.register_class(KDLZ_TextureProps)
    bpy.types.Scene.kdlz_texture_props = bpy.props.PointerProperty(type=KDLZ_TextureProps)

def unregister():
    bpy.utils.unregister_class(KDLZ_PT_AiTextureLabPanel)
    bpy.utils.unregister_class(KDLZ_OT_AiTextureLab)
    bpy.utils.unregister_class(KDLZ_OT_GenerateTexture)
    bpy.utils.unregister_class(KDLZ_TextureProps)
    del bpy.types.Scene.kdlz_texture_props
