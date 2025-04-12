import bpy
from bpy.props import FloatProperty, BoolProperty, EnumProperty, IntProperty, StringProperty

class KDLZ_PT_AutoMeshProPanel(bpy.types.Panel):
    bl_label = "AutoMesh Pro"
    bl_idname = "KDLZ_PT_auto_mesh_pro"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KodeLabz"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.kdlz_automesh_props
        
        # Check if an object is selected
        if not context.active_object or context.active_object.type != 'MESH':
            layout.label(text="Select a mesh object", icon="ERROR")
            return
        
        # Quick Actions
        box = layout.box()
        box.label(text="Quick Actions", icon="PLAY")
        
        row = box.row(align=True)
        row.scale_y = 1.5
        row.operator("kdlz.auto_optimize_mesh", icon="SHADERFX")
        
        # Remeshing Section
        box = layout.box()
        box.label(text="Remeshing", icon="MOD_REMESH")
        
        col = box.column(align=True)
        row = col.row(align=True)
        row.prop(props, "remesh_method", expand=True)
        
        if props.remesh_method == 'VOXEL':
            col.prop(props, "voxel_size")
            col.prop(props, "voxel_adaptivity")
            col.prop(props, "voxel_preserve_volume")
        elif props.remesh_method == 'QUAD':
            col.prop(props, "quad_target_faces")
            col.prop(props, "quad_preserve_sharp")
            col.prop(props, "quad_preserve_mesh_boundary")
            col.prop(props, "quad_preserve_paint_mask")
        elif props.remesh_method == 'DECIMATE':
            col.prop(props, "decimate_ratio")
            col.prop(props, "decimate_use_symmetry")
            col.prop(props, "decimate_symmetry_axis")
        elif props.remesh_method == 'SMOOTH':
            col.prop(props, "smooth_iterations")
            col.prop(props, "smooth_factor")
        
        col.separator()
        row = col.row(align=True)
        row.scale_y = 1.2
        row.operator("kdlz.apply_remesh", icon="MOD_REMESH")
        
        # Mesh Cleanup Section
        box = layout.box()
        box.label(text="Mesh Cleanup", icon="BRUSH_DATA")
        
        col = box.column(align=True)
        col.prop(props, "remove_doubles")
        if props.remove_doubles:
            col.prop(props, "merge_distance")
        
        col.prop(props, "fix_non_manifold")
        col.prop(props, "recalculate_normals")
        col.prop(props, "remove_loose")
        col.prop(props, "triangulate")
        
        col.separator()
        row = col.row(align=True)
        row.scale_y = 1.2
        row.operator("kdlz.apply_cleanup", icon="BRUSH_DATA")
        
        # UV Unwrap Section
        box = layout.box()
        box.label(text="UV Unwrap", icon="MOD_UVPROJECT")
        
        col = box.column(align=True)
        col.prop(props, "unwrap_method")
        
        if props.unwrap_method == 'SMART':
            col.prop(props, "angle_limit")
            col.prop(props, "island_margin")
        elif props.unwrap_method == 'LIGHTMAP':
            col.prop(props, "pack_quality")
            col.prop(props, "margin")
        
        col.separator()
        row = col.row(align=True)
        row.scale_y = 1.2
        row.operator("kdlz.apply_unwrap", icon="MOD_UVPROJECT")
        
        # 3D Print Preparation
        box = layout.box()
        box.label(text="3D Print Prep", icon="MESH_CUBE")
        
        col = box.column(align=True)
        col.prop(props, "make_solid")
        col.prop(props, "wall_thickness")
        col.prop(props, "intersect_cleanup")
        col.prop(props, "check_watertight")
        
        col.separator()
        row = col.row(align=True)
        row.scale_y = 1.2
        row.operator("kdlz.apply_3d_print_prep", icon="MESH_CUBE")
        
        # Export Section
        box = layout.box()
        box.label(text="Export Optimized Mesh", icon="EXPORT")
        
        col = box.column(align=True)
        col.prop(props, "export_format")
        
        if props.export_format == 'FBX':
            col.prop(props, "export_scale")
            col.prop(props, "apply_transforms")
        
        col.separator()
        row = col.row(align=True)
        row.scale_y = 1.2
        row.operator("kdlz.export_optimized_mesh", icon="EXPORT")

class KDLZ_OT_AutoMeshPro(bpy.types.Operator):
    bl_idname = "kdlz.auto_mesh_pro"
    bl_label = "AutoMesh Pro"
    
    def execute(self, context):
        # Switch to AutoMesh Pro panel
        bpy.context.space_data.context = 'VIEW_3D'
        return {'FINISHED'}

class KDLZ_OT_ApplyRetopology(bpy.types.Operator):
    bl_idname = "kdlz.apply_remesh"
    bl_label = "Apply Remesh"
    
    def execute(self, context):
        props = context.scene.kdlz_automesh_props
        obj = context.active_object
        
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "No mesh object selected")
            return {'CANCELLED'}
        
        # Store original object
        original_obj = obj
        
        # Make a copy of the object for retopology
        bpy.ops.object.duplicate()
        retopo_obj = context.active_object
        
        # Apply modifiers to ensure clean mesh
        for modifier in retopo_obj.modifiers:
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        
        # Apply retopology based on method
        if props.remesh_method == 'VOXEL':
            # Voxel remesh
            retopo_obj.data.remesh_voxel_size = props.voxel_size
            retopo_obj.data.remesh_voxel_adaptivity = props.voxel_adaptivity
            retopo_obj.data.remesh_preserve_volume = props.voxel_preserve_volume
            bpy.ops.object.voxel_remesh()
            
        elif props.remesh_method == 'QUAD':
            # Quad remesh
            bpy.ops.object.quadriflow_remesh(
                target_faces=props.quad_target_faces,
                preserve_sharp=props.quad_preserve_sharp,
                preserve_boundary=props.quad_preserve_mesh_boundary,
                preserve_paint_mask=props.quad_preserve_paint_mask
            )
            
        elif props.remesh_method == 'DECIMATE':
            # Decimate
            bpy.ops.object.modifier_add(type='DECIMATE')
            retopo_obj.modifiers["Decimate"].ratio = props.decimate_ratio
            
            if props.decimate_use_symmetry:
                retopo_obj.modifiers["Decimate"].use_symmetry = True
                retopo_obj.modifiers["Decimate"].symmetry_axis = props.decimate_symmetry_axis
                
            bpy.ops.object.modifier_apply(modifier="Decimate")
        
        elif props.remesh_method == 'SMOOTH':
            # Smooth
            bpy.ops.object.modifier_add(type='SMOOTH')
            retopo_obj.modifiers["Smooth"].factor = props.smooth_factor
            retopo_obj.modifiers["Smooth"].iterations = props.smooth_iterations
            bpy.ops.object.modifier_apply(modifier="Smooth")
        
        # Rename the retopologized object
        retopo_obj.name = original_obj.name + "_remeshed"
        
        self.report({'INFO'}, f"Remesh applied: {retopo_obj.name}")
        return {'FINISHED'}

class KDLZ_OT_AutoOptimizeMesh(bpy.types.Operator):
    bl_idname = "kdlz.auto_optimize_mesh"
    bl_label = "Auto-Optimize Mesh"
    
    def execute(self, context):
        props = context.scene.kdlz_automesh_props
        obj = context.active_object
        
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "No mesh object selected")
            return {'CANCELLED'}
        
        # Store original object
        original_obj = obj
        
        # Make a copy of the object
        bpy.ops.object.duplicate()
        optimized_obj = context.active_object
        
        # Apply modifiers to ensure clean mesh
        for modifier in optimized_obj.modifiers:
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        
        # Step 1: Remesh if needed (for high-poly meshes)
        if len(optimized_obj.data.vertices) > 100000:
            # Apply decimate to reduce complexity
            bpy.ops.object.modifier_add(type='DECIMATE')
            optimized_obj.modifiers["Decimate"].ratio = 0.5
            bpy.ops.object.modifier_apply(modifier="Decimate")
        
        # Step 2: Clean up mesh
        # Enter edit mode
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Select all vertices
        bpy.ops.mesh.select_all(action='SELECT')
        
        # Merge vertices
        bpy.ops.mesh.remove_doubles(threshold=0.001)
        
        # Fix non-manifold
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.fill_holes()
        
        # Recalculate normals
        bpy.ops.mesh.normals_make_consistent(inside=False)
        
        # Remove loose geometry
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete_loose()
        
        # Return to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Step 3: UV unwrap if no UVs exist
        if not optimized_obj.data.uv_layers:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
            bpy.ops.object.mode_set(mode='OBJECT')
        
        # Rename the optimized object
        optimized_obj.name = original_obj.name + "_optimized"
        
        self.report({'INFO'}, f"Auto-optimization complete: {optimized_obj.name}")
        return {'FINISHED'}

class KDLZ_OT_ApplyCleanup(bpy.types.Operator):
    bl_idname = "kdlz.apply_cleanup"
    bl_label = "Apply Cleanup"
    
    def execute(self, context):
        props = context.scene.kdlz_automesh_props
        obj = context.active_object
        
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "No mesh object selected")
            return {'CANCELLED'}
        
        # Enter edit mode
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Select all vertices
        bpy.ops.mesh.select_all(action='SELECT')
        
        # Remove doubles if enabled
        if props.remove_doubles:
            bpy.ops.mesh.remove_doubles(threshold=props.merge_distance)
        
        # Fix non-manifold if enabled
        if props.fix_non_manifold:
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.fill_holes()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.delete_loose()
        
        # Recalculate normals if enabled
        if props.recalculate_normals:
            bpy.ops.mesh.normals_make_consistent(inside=False)
        
        # Remove loose geometry if enabled
        if props.remove_loose:
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.delete_loose()
        
        # Triangulate if enabled
        if props.triangulate:
            bpy.ops.mesh.quads_convert_to_tris()
        
        # Return to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        self.report({'INFO'}, "Mesh cleanup completed")
        return {'FINISHED'}

class KDLZ_OT_ApplyUnwrap(bpy.types.Operator):
    bl_idname = "kdlz.apply_unwrap"
    bl_label = "Apply UV Unwrap"
    
    def execute(self, context):
        props = context.scene.kdlz_automesh_props
        obj = context.active_object
        
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "No mesh object selected")
            return {'CANCELLED'}
        
        # Enter edit mode
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Select all faces
        bpy.ops.mesh.select_all(action='SELECT')
        
        # Apply unwrap based on method
        if props.unwrap_method == 'SMART':
            bpy.ops.uv.smart_project(
                angle_limit=props.angle_limit,
                island_margin=props.island_margin
            )
        elif props.unwrap_method == 'LIGHTMAP':
            bpy.ops.uv.lightmap_pack(
                PREF_IMG_PX_SIZE=1024,
                PREF_BOX_DIV=12,
                PREF_MARGIN_DIV=0.1
            )
        elif props.unwrap_method == 'UNWRAP':
            bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
        elif props.unwrap_method == 'CUBE':
            bpy.ops.uv.cube_project()
        elif props.unwrap_method == 'CYLINDER':
            bpy.ops.uv.cylinder_project()
        elif props.unwrap_method == 'SPHERE':
            bpy.ops.uv.sphere_project()
        
        # Return to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        self.report({'INFO'}, f"UV unwrap applied using {props.unwrap_method} method")
        return {'FINISHED'}

class KDLZ_OT_Apply3DPrintPrep(bpy.types.Operator):
    bl_idname = "kdlz.apply_3d_print_prep"
    bl_label = "Apply 3D Print Prep"
    
    def execute(self, context):
        props = context.scene.kdlz_automesh_props
        obj = context.active_object
        
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "No mesh object selected")
            return {'CANCELLED'}
        
        # Make solid if enabled
        if props.make_solid:
            # Add solidify modifier
            bpy.ops.object.modifier_add(type='SOLIDIFY')
            obj.modifiers["Solidify"].thickness = props.wall_thickness
            bpy.ops.object.modifier_apply(modifier="Solidify")
        
        # Intersect cleanup if enabled
        if props.intersect_cleanup:
            # Enter edit mode
            bpy.ops.object.mode_set(mode='EDIT')
            
            # Select all
            bpy.ops.mesh.select_all(action='SELECT')
            
            # Remove internal faces
            bpy.ops.mesh.select_interior_faces()
            bpy.ops.mesh.delete(type='FACE')
            
            # Fix non-manifold edges
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.fill_holes()
            
            # Return to object mode
            bpy.ops.object.mode_set(mode='OBJECT')
        
        # Check watertight if enabled
        if props.check_watertight:
            # Enter edit mode
            bpy.ops.object.mode_set(mode='EDIT')
            
            # Select all
            bpy.ops.mesh.select_all(action='SELECT')
            
            # Check for holes
            bpy.ops.mesh.select_non_manifold()
            
            # Return to object mode
            bpy.ops.object.mode_set(mode='OBJECT')
        
        # Apply 3D print toolbox checks
        if hasattr(bpy.ops, "mesh"):
            if hasattr(bpy.ops.mesh, "print3d_check_all"):
                bpy.ops.mesh.print3d_check_all()
        
        self.report({'INFO'}, "3D print preparation completed")
        return {'FINISHED'}

class KDLZ_OT_ExportOptimizedMesh(bpy.types.Operator):
    bl_idname = "kdlz.export_optimized_mesh"
    bl_label = "Export Mesh"
    
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Path to export the file",
        default="",
        subtype='FILE_PATH'
    )
    
    def invoke(self, context, event):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "No mesh object selected")
            return {'CANCELLED'}
        
        # Set default filename based on object name and format
        props = context.scene.kdlz_automesh_props
        format_ext = props.export_format.lower()
        default_filename = f"{obj.name}.{format_ext}"
        
        # Set filepath
        self.filepath = default_filename
        
        # Open file browser
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        props = context.scene.kdlz_automesh_props
        obj = context.active_object
        
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "No mesh object selected")
            return {'CANCELLED'}
        
        # Store current selection
        original_selection = context.selected_objects.copy()
        active_obj = context.active_object
        
        # Deselect all
        bpy.ops.object.select_all(action='DESELECT')
        
        # Select only the target object
        obj.select_set(True)
        context.view_layer.objects.active = obj
        
        # Apply transforms if needed
        if props.apply_transforms:
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        
        # Export based on format
        if props.export_format == 'OBJ':
            bpy.ops.export_scene.obj(
                filepath=self.filepath,
                use_selection=True,
                use_materials=True,
                use_triangles=True
            )
        elif props.export_format == 'FBX':
            bpy.ops.export_scene.fbx(
                filepath=self.filepath,
                use_selection=True,
                global_scale=props.export_scale,
                apply_scale_options='FBX_SCALE_ALL',
                mesh_smooth_type='FACE'
            )
        elif props.export_format == 'STL':
            bpy.ops.export_mesh.stl(
                filepath=self.filepath,
                use_selection=True,
                global_scale=props.export_scale
            )
        elif props.export_format == 'GLTF':
            bpy.ops.export_scene.gltf(
                filepath=self.filepath,
                use_selection=True,
                export_format='GLTF_EMBEDDED'
            )
        
        # Restore original selection
        bpy.ops.object.select_all(action='DESELECT')
        for obj in original_selection:
            obj.select_set(True)
        context.view_layer.objects.active = active_obj
        
        self.report({'INFO'}, f"Exported mesh to {self.filepath}")
        return {'FINISHED'}

class KDLZ_AutoMeshProps(bpy.types.PropertyGroup):
    # Remeshing properties
    remesh_method: EnumProperty(
        name="Method",
        items=[
            ('VOXEL', "Voxel", "Voxel remeshing for organic models"),
            ('QUAD', "Quad", "Quad remeshing for animation-ready models"),
            ('DECIMATE', "Decimate", "Simple polygon reduction"),
            ('SMOOTH', "Smooth", "Smooth mesh without changing topology")
        ],
        default='VOXEL'
    )
    
    # Voxel remesh properties
    voxel_size: FloatProperty(
        name="Voxel Size",
        description="Size of voxels for remeshing (smaller = more detail)",
        default=0.02,
        min=0.001,
        max=0.5
    )
    
    voxel_adaptivity: FloatProperty(
        name="Adaptivity",
        description="Adaptivity of the remesher (higher = more adaptive)",
        default=0.0,
        min=0.0,
        max=1.0
    )
    
    voxel_preserve_volume: BoolProperty(
        name="Preserve Volume",
        description="Try to preserve the volume of the mesh",
        default=True
    )
    
    # Quad remesh properties
    quad_target_faces: IntProperty(
        name="Target Faces",
        description="Target number of faces for quad remeshing",
        default=5000,
        min=100,
        max=100000
    )
    
    quad_preserve_sharp: BoolProperty(
        name="Preserve Sharp",
        description="Try to preserve sharp features",
        default=True
    )
    
    quad_preserve_mesh_boundary: BoolProperty(
        name="Preserve Boundary",
        description="Try to preserve mesh boundary",
        default=True
    )
    
    quad_preserve_paint_mask: BoolProperty(
        name="Preserve Paint Mask",
        description="Try to preserve paint mask",
        default=True
    )
    
    # Decimate properties
    decimate_ratio: FloatProperty(
        name="Ratio",
        description="Ratio of faces to keep when decimating",
        default=0.5,
        min=0.01,
        max=0.99
    )
    
    decimate_use_symmetry: BoolProperty(
        name="Use Symmetry",
        description="Maintain symmetry when decimating",
        default=False
    )
    
    decimate_symmetry_axis: EnumProperty(
        name="Symmetry Axis",
        items=[
            ('X', "X", "X axis"),
            ('Y', "Y", "Y axis"),
            ('Z', "Z", "Z axis")
        ],
        default='X'
    )
    
    # Smooth properties
    smooth_iterations: IntProperty(
        name="Iterations",
        description="Number of smoothing iterations",
        default=5,
        min=1,
        max=100
    )
    
    smooth_factor: FloatProperty(
        name="Factor",
        description="Smoothing factor",
        default=0.5,
        min=0.0,
        max=1.0
    )
    
    # Cleanup properties
    remove_doubles: BoolProperty(
        name="Merge Vertices",
        description="Merge vertices that are close together",
        default=True
    )
    
    merge_distance: FloatProperty(
        name="Merge Distance",
        description="Maximum distance between vertices to be merged",
        default=0.001,
        min=0.00001,
        max=0.1
    )
    
    fix_non_manifold: BoolProperty(
        name="Fix Non-Manifold",
        description="Attempt to fix non-manifold geometry",
        default=True
    )
    
    recalculate_normals: BoolProperty(
        name="Recalculate Normals",
        description="Make normals consistent",
        default=True
    )
    
    remove_loose: BoolProperty(
        name="Remove Loose",
        description="Remove loose vertices and edges",
        default=True
    )
    
    triangulate: BoolProperty(
        name="Triangulate",
        description="Convert all faces to triangles",
        default=False
    )
    
    # UV Unwrap properties
    unwrap_method: EnumProperty(
        name="Unwrap Method",
        items=[
            ('SMART', "Smart UV Project", "Automatic UV mapping"),
            ('LIGHTMAP', "Lightmap Pack", "Pack all faces for lightmaps"),
            ('UNWRAP', "Unwrap", "Standard angle-based unwrapping"),
            ('CUBE', "Cube Projection", "Unwrap using cube projection"),
            ('CYLINDER', "Cylinder Projection", "Unwrap using cylinder projection"),
            ('SPHERE', "Sphere Projection", "Unwrap using sphere projection")
        ],
        default='SMART'
    )
    
    angle_limit: FloatProperty(
        name="Angle Limit",
        description="Angle limit for Smart UV Project",
        default=66.0,
        min=1.0,
        max=89.0,
        subtype='ANGLE'
    )
    
    island_margin: FloatProperty(
        name="Island Margin",
        description="Margin between UV islands",
        default=0.02,
        min=0.0,
        max=1.0
    )
    
    pack_quality: IntProperty(
        name="Pack Quality",
        description="Quality of the lightmap pack (higher = better but slower)",
        default=12,
        min=1,
        max=48
    )
    
    margin: FloatProperty(
        name="Margin",
        description="Margin between UV islands",
        default=0.01,
        min=0.0,
        max=1.0
    )
    
    # 3D Print properties
    make_solid: BoolProperty(
        name="Make Solid",
        description="Add thickness to the model for 3D printing",
        default=True
    )
    
    wall_thickness: FloatProperty(
        name="Wall Thickness",
        description="Thickness of walls when making solid",
        default=0.02,
        min=0.001,
        max=0.5
    )
    
    intersect_cleanup: BoolProperty(
        name="Intersect Cleanup",
        description="Clean up self-intersections and internal faces",
        default=True
    )
    
    check_watertight: BoolProperty(
        name="Check Watertight",
        description="Check if the mesh is watertight (no holes)",
        default=True
    )
    
    # Export properties
    export_format: EnumProperty(
        name="Format",
        items=[
            ('OBJ', "OBJ", "Wavefront OBJ format"),
            ('FBX', "FBX", "Autodesk FBX format"),
            ('STL', "STL", "STL format for 3D printing"),
            ('GLTF', "glTF", "glTF format for web and real-time")
        ],
        default='OBJ'
    )
    
    export_scale: FloatProperty(
        name="Scale",
        description="Scale factor for export",
        default=1.0,
        min=0.001,
        max=1000.0
    )
    
    apply_transforms: BoolProperty(
        name="Apply Transforms",
        description="Apply object transformations before export",
        default=True
    )

def register():
    bpy.utils.register_class(KDLZ_PT_AutoMeshProPanel)
    bpy.utils.register_class(KDLZ_OT_AutoMeshPro)
    bpy.utils.register_class(KDLZ_OT_ApplyRetopology)
    bpy.utils.register_class(KDLZ_OT_AutoOptimizeMesh)
    bpy.utils.register_class(KDLZ_OT_ApplyCleanup)
    bpy.utils.register_class(KDLZ_OT_ApplyUnwrap)
    bpy.utils.register_class(KDLZ_OT_Apply3DPrintPrep)
    bpy.utils.register_class(KDLZ_OT_ExportOptimizedMesh)
    bpy.utils.register_class(KDLZ_AutoMeshProps)
    bpy.types.Scene.kdlz_automesh_props = bpy.props.PointerProperty(type=KDLZ_AutoMeshProps)

def unregister():
    bpy.utils.unregister_class(KDLZ_PT_AutoMeshProPanel)
    bpy.utils.unregister_class(KDLZ_OT_AutoMeshPro)
    bpy.utils.unregister_class(KDLZ_OT_ApplyRetopology)
    bpy.utils.unregister_class(KDLZ_OT_AutoOptimizeMesh)
    bpy.utils.unregister_class(KDLZ_OT_ApplyCleanup)
    bpy.utils.unregister_class(KDLZ_OT_ApplyUnwrap)
    bpy.utils.unregister_class(KDLZ_OT_Apply3DPrintPrep)
    bpy.utils.unregister_class(KDLZ_OT_ExportOptimizedMesh)
    bpy.utils.unregister_class(KDLZ_AutoMeshProps)
    del bpy.types.Scene.kdlz_automesh_props
