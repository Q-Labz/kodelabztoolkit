import bpy
import requests
import tempfile
import os
import time
import json
import threading
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
        
        # PBR Options
        box = layout.box()
        box.label(text="PBR Options", icon="MATERIAL")
        box.prop(props, "pbr_mode")
        box.prop(props, "resolution")
        
        # Maps to generate
        if props.pbr_mode == 'FULL':
            box.label(text="Maps to Generate:")
            row = box.row()
            row.prop(props, "gen_base_color")
            row.prop(props, "gen_normal")
            
            row = box.row()
            row.prop(props, "gen_roughness")
            row.prop(props, "gen_height")
            
            row = box.row()
            row.prop(props, "gen_ao")
            row.enabled = False  # Placeholder for future expansion
        
        # Advanced settings
        box = layout.box()
        row = box.row()
        row.prop(props, "show_advanced", icon="PREFERENCES", toggle=True)
        
        if props.show_advanced:
            box.prop(props, "guidance_scale")
            box.prop(props, "num_inference_steps")
            box.prop(props, "seed")
            box.prop(props, "use_random_seed")
            
            if props.pbr_mode == 'FULL':
                box.prop(props, "normal_strength")
                box.prop(props, "roughness_contrast")
                box.prop(props, "height_strength")
        
        # Generate button
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("kdlz.generate_texture", icon="RENDER_STILL")
        
        # Status
        if props.is_generating:
            row = layout.row()
            row.label(text="Generating texture...", icon="SORTTIME")
            
            # Progress bar
            if props.pbr_mode == 'FULL' and props.progress > 0:
                box = layout.box()
                row = box.row()
                row.label(text=f"Progress: {props.progress_message}")
                row = box.row()
                row.prop(props, "progress", text="")

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
    _pbr_prediction_ids = {}
    _pbr_images = {}
    _base_image_path = None
    
    def generate_base_texture(self, context):
        """Generate the base color texture using Replicate API"""
        props = context.scene.kdlz_texture_props
        api_token = get_api_token(context)
        
        # Prepare API request
        model_url = "https://api.replicate.com/v1/predictions"
        
        headers = {
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json"
        }
        
        # Enhance prompt with material type
        prompt = props.prompt
        material_type = props.material_type
        if material_type != 'OTHER':
            prompt = f"{prompt}, {material_type.lower()} material, PBR texture"
        
        # Set seed
        seed = props.seed if not props.use_random_seed else None
        
        # Select resolution
        resolution_map = {
            '512': 512,
            '1024': 1024,
            '2048': 2048,
            '4096': 4096
        }
        resolution = resolution_map[props.resolution]
        
        data = {
            "version": "cf40add0d299df23819762a7e3045e990e045d18f6ed25630e6e5583be68827f",
            "input": {
                "prompt": prompt,
                "seamless": props.seamless,
                "guidance_scale": props.guidance_scale,
                "num_inference_steps": props.num_inference_steps,
                "width": resolution,
                "height": resolution
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
                return None
            
            # Store prediction ID
            return prediction["id"]
            
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            return None
    
    def generate_pbr_maps(self, context, base_image_url):
        """Generate PBR maps from base color texture using convert-texture-to-pbr model"""
        props = context.scene.kdlz_texture_props
        api_token = get_api_token(context)
        
        # Prepare API request
        model_url = "https://api.replicate.com/v1/predictions"
        
        headers = {
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json"
        }
        
        # Model for PBR conversion
        data = {
            "version": "1e30e5c8c08d3056c9a1e2f48a2c6b2d4b57e33e9c0a4e2c2a30f2a7b25cb1f5",
            "input": {
                "image": base_image_url,
                "normal_strength": props.normal_strength,
                "roughness_contrast": props.roughness_contrast,
                "height_strength": props.height_strength
            }
        }
        
        try:
            # Send request
            response = requests.post(model_url, headers=headers, json=data)
            prediction = response.json()
            
            if "id" not in prediction:
                self.report({'ERROR'}, f"Failed to start PBR map generation: {prediction.get('detail', 'Unknown error')}")
                return None
            
            # Store prediction ID
            return prediction["id"]
            
        except Exception as e:
            self.report({'ERROR'}, f"Error generating PBR maps: {str(e)}")
            return None
    
    def download_image(self, url, filename):
        """Download image from URL and save to temp directory"""
        try:
            image_data = requests.get(url).content
            tmp_path = os.path.join(tempfile.gettempdir(), filename)
            with open(tmp_path, 'wb') as f:
                f.write(image_data)
            return tmp_path
        except Exception as e:
            print(f"Error downloading image: {str(e)}")
            return None
    
    def create_material_with_pbr(self, context, image_paths):
        """Create a material with PBR maps"""
        props = context.scene.kdlz_texture_props
        
        # Create material name
        mat_name = f"KDLZ_{props.material_type}_{int(time.time())}"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        
        # Clear default nodes
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        for node in nodes:
            nodes.remove(node)
        
        # Create nodes
        output = nodes.new(type='ShaderNodeOutputMaterial')
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        
        # Position nodes
        output.location = (300, 0)
        bsdf.location = (0, 0)
        
        # Connect BSDF to output
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
        
        # Add texture nodes based on available maps
        texture_nodes = {}
        
        # Base Color
        if 'base_color' in image_paths and os.path.exists(image_paths['base_color']):
            base_color = nodes.new(type='ShaderNodeTexImage')
            base_color.location = (-300, 300)
            base_color.image = bpy.data.images.load(image_paths['base_color'])
            base_color.image.colorspace_settings.name = 'sRGB'
            links.new(base_color.outputs['Color'], bsdf.inputs['Base Color'])
            texture_nodes['base_color'] = base_color
        
        # Normal Map
        if 'normal' in image_paths and os.path.exists(image_paths['normal']):
            normal_tex = nodes.new(type='ShaderNodeTexImage')
            normal_tex.location = (-300, 0)
            normal_tex.image = bpy.data.images.load(image_paths['normal'])
            normal_tex.image.colorspace_settings.name = 'Non-Color'
            
            # Add Normal Map node
            normal_map = nodes.new(type='ShaderNodeNormalMap')
            normal_map.location = (-50, 0)
            normal_map.inputs['Strength'].default_value = 1.0
            
            # Connect nodes
            links.new(normal_tex.outputs['Color'], normal_map.inputs['Color'])
            links.new(normal_map.outputs['Normal'], bsdf.inputs['Normal'])
            texture_nodes['normal'] = normal_tex
        
        # Roughness
        if 'roughness' in image_paths and os.path.exists(image_paths['roughness']):
            roughness = nodes.new(type='ShaderNodeTexImage')
            roughness.location = (-300, -150)
            roughness.image = bpy.data.images.load(image_paths['roughness'])
            roughness.image.colorspace_settings.name = 'Non-Color'
            links.new(roughness.outputs['Color'], bsdf.inputs['Roughness'])
            texture_nodes['roughness'] = roughness
        
        # Height/Displacement
        if 'height' in image_paths and os.path.exists(image_paths['height']) and props.gen_height:
            height = nodes.new(type='ShaderNodeTexImage')
            height.location = (-300, -300)
            height.image = bpy.data.images.load(image_paths['height'])
            height.image.colorspace_settings.name = 'Non-Color'
            
            # Add displacement node
            displacement = nodes.new(type='ShaderNodeDisplacement')
            displacement.location = (0, -300)
            displacement.inputs['Scale'].default_value = 0.1
            
            # Connect to material output
            links.new(height.outputs['Color'], displacement.inputs['Height'])
            links.new(displacement.outputs['Displacement'], output.inputs['Displacement'])
            texture_nodes['height'] = height
        
        # AO (if available in the future)
        if 'ao' in image_paths and os.path.exists(image_paths['ao']) and props.gen_ao:
            ao = nodes.new(type='ShaderNodeTexImage')
            ao.location = (-300, -450)
            ao.image = bpy.data.images.load(image_paths['ao'])
            ao.image.colorspace_settings.name = 'Non-Color'
            
            # Mix with base color using mix RGB node
            if 'base_color' in texture_nodes:
                mix = nodes.new(type='ShaderNodeMixRGB')
                mix.location = (-50, 300)
                mix.blend_type = 'MULTIPLY'
                mix.inputs['Fac'].default_value = 0.5
                
                links.new(texture_nodes['base_color'].outputs['Color'], mix.inputs[1])
                links.new(ao.outputs['Color'], mix.inputs[2])
                links.new(mix.outputs['Color'], bsdf.inputs['Base Color'])
            
            texture_nodes['ao'] = ao
        
        # Apply to object if selected
        if context.active_object and context.active_object.type == 'MESH':
            if context.active_object.data.materials:
                context.active_object.data.materials[0] = mat
            else:
                context.active_object.data.materials.append(mat)
        
        return mat
    
    def modal(self, context, event):
        props = context.scene.kdlz_texture_props
        
        if event.type == 'TIMER':
            # Check prediction status
            if props.pbr_mode == 'COLOR':
                # Single texture mode
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
                                tmp_path = self.download_image(image_url, "kodelabz_texture.png")
                                
                                if tmp_path:
                                    # Create material with single texture
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
                                    self.report({'ERROR'}, "Failed to download image")
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
            
            else:
                # Full PBR mode
                try:
                    headers = {
                        "Authorization": f"Token {get_api_token(context)}",
                        "Content-Type": "application/json"
                    }
                    
                    # Step 1: Check base color generation
                    if self._prediction_id and not self._base_image_path:
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
                                # Update progress
                                props.progress = 25
                                props.progress_message = "Base color generated, creating PBR maps..."
                                
                                # Download the base image
                                self._base_image_path = self.download_image(image_url, "kodelabz_base_color.png")
                                self._pbr_images['base_color'] = self._base_image_path
                                
                                # Start PBR map generation
                                pbr_id = self.generate_pbr_maps(context, image_url)
                                if pbr_id:
                                    self._pbr_prediction_ids['pbr'] = pbr_id
                                else:
                                    self.report({'ERROR'}, "Failed to start PBR map generation")
                                    props.is_generating = False
                                    return self.cancel(context)
                            else:
                                self.report({'ERROR'}, "No output image URL found")
                                props.is_generating = False
                                return self.cancel(context)
                        
                        elif status == "failed":
                            self.report({'ERROR'}, "Base texture generation failed")
                            props.is_generating = False
                            return self.cancel(context)
                    
                    # Step 2: Check PBR map generation
                    elif 'pbr' in self._pbr_prediction_ids:
                        check = requests.get(
                            f"https://api.replicate.com/v1/predictions/{self._pbr_prediction_ids['pbr']}", 
                            headers=headers
                        )
                        result = check.json()
                        status = result.get("status")
                        
                        if status == "succeeded":
                            # Get the PBR maps
                            output = result.get("output")
                            if output:
                                # Update progress
                                props.progress = 75
                                props.progress_message = "Downloading PBR maps..."
                                
                                # Download PBR maps
                                if props.gen_normal and 'normal' in output:
                                    self._pbr_images['normal'] = self.download_image(output['normal'], "kodelabz_normal.png")
                                
                                if props.gen_roughness and 'roughness' in output:
                                    self._pbr_images['roughness'] = self.download_image(output['roughness'], "kodelabz_roughness.png")
                                
                                if props.gen_height and 'height' in output:
                                    self._pbr_images['height'] = self.download_image(output['height'], "kodelabz_height.png")
                                
                                if props.gen_ao and 'ao' in output:
                                    self._pbr_images['ao'] = self.download_image(output['ao'], "kodelabz_ao.png")
                                
                                # Update progress
                                props.progress = 90
                                props.progress_message = "Creating material..."
                                
                                # Create material with PBR maps
                                mat = self.create_material_with_pbr(context, self._pbr_images)
                                
                                # Update progress
                                props.progress = 100
                                props.progress_message = "Complete!"
                                
                                self.report({'INFO'}, f"PBR texture set generated and applied as {mat.name}")
                                
                                # End modal
                                props.is_generating = False
                                return self.cancel(context)
                            else:
                                self.report({'ERROR'}, "No PBR maps found in output")
                                props.is_generating = False
                                return self.cancel(context)
                        
                        elif status == "failed":
                            self.report({'ERROR'}, "PBR map generation failed")
                            props.is_generating = False
                            return self.cancel(context)
                    
                    # Continue checking
                    return {'PASS_THROUGH'}
                
                except Exception as e:
                    self.report({'ERROR'}, f"Error in PBR generation: {str(e)}")
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
        props.progress = 0
        props.progress_message = "Starting texture generation..."
        
        # Get parameters
        prompt = props.prompt
        if not prompt:
            self.report({'ERROR'}, "Please enter a prompt")
            props.is_generating = False
            return {'CANCELLED'}
        
        # Reset tracking variables
        self._prediction_id = None
        self._pbr_prediction_ids = {}
        self._pbr_images = {}
        self._base_image_path = None
        
        # Generate base texture
        self._prediction_id = self.generate_base_texture(context)
        if not self._prediction_id:
            props.is_generating = False
            return {'CANCELLED'}
        
        # Start timer
        wm = context.window_manager
        self._timer = wm.event_timer_add(2.0, window=context.window)
        wm.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}
    
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
    
    pbr_mode: EnumProperty(
        name="Texture Mode",
        items=[
            ("COLOR", "Base Color Only", "Generate only the base color texture"),
            ("FULL", "Full PBR", "Generate complete PBR texture set"),
        ],
        default="COLOR"
    )
    
    resolution: EnumProperty(
        name="Resolution",
        items=[
            ("512", "512×512", "Low resolution"),
            ("1024", "1024×1024", "Medium resolution"),
            ("2048", "2048×2048", "High resolution"),
            ("4096", "4096×4096", "Ultra high resolution"),
        ],
        default="1024"
    )
    
    seamless: BoolProperty(
        name="Seamless",
        description="Generate a seamless tileable texture",
        default=True
    )
    
    # PBR map options
    gen_base_color: BoolProperty(
        name="Base Color",
        description="Generate base color map",
        default=True
    )
    
    gen_normal: BoolProperty(
        name="Normal",
        description="Generate normal map",
        default=True
    )
    
    gen_roughness: BoolProperty(
        name="Roughness",
        description="Generate roughness map",
        default=True
    )
    
    gen_height: BoolProperty(
        name="Height",
        description="Generate height/displacement map",
        default=False
    )
    
    gen_ao: BoolProperty(
        name="AO",
        description="Generate ambient occlusion map",
        default=False
    )
    
    # Advanced settings
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
    
    # PBR specific settings
    normal_strength: FloatProperty(
        name="Normal Strength",
        description="Strength of the normal map effect",
        default=1.0,
        min=0.1,
        max=2.0
    )
    
    roughness_contrast: FloatProperty(
        name="Roughness Contrast",
        description="Contrast of the roughness map",
        default=1.0,
        min=0.1,
        max=2.0
    )
    
    height_strength: FloatProperty(
        name="Height Strength",
        description="Strength of the height map effect",
        default=1.0,
        min=0.1,
        max=2.0
    )
    
    # Status tracking
    is_generating: BoolProperty(
        name="Is Generating",
        description="Whether texture is currently being generated",
        default=False
    )
    
    progress: FloatProperty(
        name="Progress",
        description="Generation progress",
        default=0.0,
        min=0.0,
        max=100.0,
        subtype='PERCENTAGE'
    )
    
    progress_message: StringProperty(
        name="Progress Message",
        description="Current status of generation",
        default=""
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
