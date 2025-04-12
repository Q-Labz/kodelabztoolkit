import bpy
from bpy.props import FloatProperty, BoolProperty, EnumProperty, IntProperty

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
        
        # Retopology Section
        box = layout.box()
        box.label(text="Retopology", icon="MOD_REMESH")
        
        col = box.column(align=True)
        row = col.row(align=True)
        row.prop(props, "retopo_method", expand=True)
        
        if props.retopo_method == 'VOXEL':
            col.prop(props, "voxel_size")
        elif props.retopo_method == 'QUAD':
            col.prop(props, "quad_target_faces")
        elif props.retopo_method == 'DECIMATE':
            col.prop(props, "decimate_ratio")
        
        col.separator()
        row = col.row(align=True)
        row.scale_y = 1.2
        row.operator("kdlz.apply_retopology", icon="MOD_REMESH")
        
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
        
        col.separator()
        row = col.row(align=True)
        row.scale_y = 1.2
        row.operator("kdlz.apply_3d_print_prep", icon="MESH_CUBE")

class KDLZ_OT_AutoMeshPro(bpy.types.Operator):
    bl_idname = "kdlz.auto_mesh_pro"
    bl_label = "AutoMesh Pro"
    
    def execute(self, context):
        # Switch to AutoMesh Pro panel
        bpy.context.space_data.context = 'VIEW_3D'
        return {'FINISHED'}

class KDLZ_OT_ApplyRetopology(bpy.types.Operator):
    bl_idname = "kdlz.apply_retopology"
    bl_label = "Apply Retopology"
    
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
        if props.retopo_method == 'VOXEL':
            # Voxel remesh
            retopo_obj.data.remesh_voxel_size = props.voxel_size
            bpy.ops.object.voxel_remesh()
            
        elif props.retopo_method == 'QUAD':
            # Quad remesh
            retopo_obj.data.remesh_mode = 'QUAD'
            retopo_obj.data.remesh_voxel_size = 0.01  # Small voxel size for better detail
            retopo_obj.data.remesh_voxel_adaptivity = 0.0  # No adaptivity for uniform quads
            bpy.ops.object.quadriflow_remesh(target_faces=props.quad_target_faces)
            
        elif props.retopo_method == 'DECIMATE':
            # Decimate
            bpy.ops.object.modifier_add(type='DECIMATE')
            retopo_obj.modifiers["Decimate"].ratio = props.decimate_ratio
            bpy.ops.object.modifier_apply(modifier="Decimate")
        
        # Rename the retopologized object
        retopo_obj.name = original_obj.name + "_retopo"
        
        self.report({'INFO'}, f"Retopology applied: {retopo_obj.name}")
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
        
        # Apply 3D print toolbox checks
        if hasattr(bpy.ops, "mesh"):
            if hasattr(bpy.ops.mesh, "print3d_check_all"):
                bpy.ops.mesh.print3d_check_all()
        
        self.report({'INFO'}, "3D print preparation completed")
        return {'FINISHED'}

class KDLZ_AutoMeshProps(bpy.types.PropertyGroup):
    # Retopology properties
    retopo_method: EnumProperty(
        name="Method",
        items=[
            ('VOXEL', "Voxel", "Voxel remeshing for organic models"),
            ('QUAD', "Quad", "Quad remeshing for animation-ready models"),
            ('DECIMATE', "Decimate", "Simple polygon reduction")
        ],
        default='VOXEL'
    )
    
    voxel_size: FloatProperty(
        name="Voxel Size",
        description="Size of voxels for remeshing (smaller = more detail)",
        default=0.02,
        min=0.001,
        max=0.5
    )
    
    quad_target_faces: IntProperty(
        name="Target Faces",
        description="Target number of faces for quad remeshing",
        default=5000,
        min=100,
        max=100000
    )
    
    decimate_ratio: FloatProperty(
        name="Ratio",
        description="Ratio of faces to keep when decimating",
        default=0.5,
        min=0.01,
        max=0.99
    )
    
    # Cleanup properties
    remove_doubles: BoolProperty(
        name="Remove Doubles",
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

def register():
    bpy.utils.register_class(KDLZ_PT_AutoMeshProPanel)
    bpy.utils.register_class(KDLZ_OT_AutoMeshPro)
    bpy.utils.register_class(KDLZ_OT_ApplyRetopology)
    bpy.utils.register_class(KDLZ_OT_ApplyCleanup)
    bpy.utils.register_class(KDLZ_OT_ApplyUnwrap)
    bpy.utils.register_class(KDLZ_OT_Apply3DPrintPrep)
    bpy.utils.register_class(KDLZ_AutoMeshProps)
    bpy.types.Scene.kdlz_automesh_props = bpy.props.PointerProperty(type=KDLZ_AutoMeshProps)

def unregister():
    bpy.utils.unregister_class(KDLZ_PT_AutoMeshProPanel)
    bpy.utils.unregister_class(KDLZ_OT_AutoMeshPro)
    bpy.utils.unregister_class(KDLZ_OT_ApplyRetopology)
    bpy.utils.unregister_class(KDLZ_OT_ApplyCleanup)
    bpy.utils.unregister_class(KDLZ_OT_ApplyUnwrap)
    bpy.utils.unregister_class(KDLZ_OT_Apply3DPrintPrep)
    bpy.utils.unregister_class(KDLZ_AutoMeshProps)
    del bpy.types.Scene.kdlz_automesh_props
