import bpy
import random
import math
import mathutils
from bpy.props import FloatProperty, BoolProperty, EnumProperty, IntProperty, StringProperty, CollectionProperty, PointerProperty

class KDLZ_ScatterItem(bpy.types.PropertyGroup):
    """Group of properties for a scatter item"""
    object: PointerProperty(
        name="Object",
        type=bpy.types.Object,
        description="Object to scatter"
    )
    
    density: FloatProperty(
        name="Density",
        description="Density of scattered objects",
        default=1.0,
        min=0.01,
        max=10.0
    )
    
    scale_min: FloatProperty(
        name="Min Scale",
        description="Minimum scale factor",
        default=0.8,
        min=0.01,
        max=10.0
    )
    
    scale_max: FloatProperty(
        name="Max Scale",
        description="Maximum scale factor",
        default=1.2,
        min=0.01,
        max=10.0
    )
    
    rotation_min: FloatProperty(
        name="Min Rotation",
        description="Minimum rotation in degrees",
        default=0.0,
        min=0.0,
        max=360.0,
        subtype='ANGLE'
    )
    
    rotation_max: FloatProperty(
        name="Max Rotation",
        description="Maximum rotation in degrees",
        default=360.0,
        min=0.0,
        max=360.0,
        subtype='ANGLE'
    )
    
    align_to_normal: BoolProperty(
        name="Align to Normal",
        description="Align objects to surface normal",
        default=True
    )
    
    random_seed: IntProperty(
        name="Random Seed",
        description="Seed for random generation",
        default=1,
        min=1
    )

class KDLZ_PT_ScatterCraftPanel(bpy.types.Panel):
    bl_label = "ScatterCraft"
    bl_idname = "KDLZ_PT_scatter_craft"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KodeLabz"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.kdlz_scatter_props
        
        # Distribution Settings
        box = layout.box()
        box.label(text="Distribution Settings", icon="PARTICLES")
        
        col = box.column(align=True)
        col.prop(props, "scatter_method")
        
        if props.scatter_method == 'SURFACE':
            col.prop_search(props, "target_object", context.scene, "objects")
        elif props.scatter_method == 'VOLUME':
            col.prop(props, "volume_size")
            col.prop(props, "volume_center")
        elif props.scatter_method == 'PATH':
            col.prop_search(props, "path_object", context.scene, "objects")
            col.prop(props, "path_offset")
        
        col.prop(props, "avoid_overlap")
        if props.avoid_overlap:
            col.prop(props, "min_distance")
        
        # Scatter Items
        box = layout.box()
        box.label(text="Scatter Items", icon="OUTLINER_OB_GROUP_INSTANCE")
        
        # Add/Remove buttons
        row = box.row()
        row.operator("kdlz.add_scatter_item", icon="ADD")
        row.operator("kdlz.remove_scatter_item", icon="REMOVE")
        
        # List scatter items
        for i, item in enumerate(props.scatter_items):
            box = layout.box()
            row = box.row()
            row.label(text=f"Item {i+1}")
            
            row = box.row()
            row.prop(item, "object")
            
            row = box.row(align=True)
            row.prop(item, "density")
            
            row = box.row(align=True)
            row.prop(item, "scale_min")
            row.prop(item, "scale_max")
            
            row = box.row(align=True)
            row.prop(item, "rotation_min")
            row.prop(item, "rotation_max")
            
            row = box.row()
            row.prop(item, "align_to_normal")
            row.prop(item, "random_seed")
        
        # Scatter Controls
        box = layout.box()
        box.label(text="Scatter Controls", icon="PLAY")
        
        row = box.row(align=True)
        row.scale_y = 1.5
        row.operator("kdlz.execute_scatter", icon="PARTICLES")
        
        row = box.row()
        row.operator("kdlz.clear_scatter", icon="X")

class KDLZ_OT_ScatterCraft(bpy.types.Operator):
    bl_idname = "kdlz.scatter_craft"
    bl_label = "ScatterCraft"
    
    def execute(self, context):
        # Switch to ScatterCraft panel
        bpy.context.space_data.context = 'VIEW_3D'
        return {'FINISHED'}

class KDLZ_OT_AddScatterItem(bpy.types.Operator):
    bl_idname = "kdlz.add_scatter_item"
    bl_label = "Add Item"
    
    def execute(self, context):
        props = context.scene.kdlz_scatter_props
        item = props.scatter_items.add()
        
        # Set default random seed
        item.random_seed = random.randint(1, 1000)
        
        return {'FINISHED'}

class KDLZ_OT_RemoveScatterItem(bpy.types.Operator):
    bl_idname = "kdlz.remove_scatter_item"
    bl_label = "Remove Item"
    
    def execute(self, context):
        props = context.scene.kdlz_scatter_props
        
        if len(props.scatter_items) > 0:
            props.scatter_items.remove(len(props.scatter_items) - 1)
        
        return {'FINISHED'}

class KDLZ_OT_ExecuteScatter(bpy.types.Operator):
    bl_idname = "kdlz.execute_scatter"
    bl_label = "Execute Scatter"
    
    def execute(self, context):
        props = context.scene.kdlz_scatter_props
        
        # Check if we have scatter items
        if len(props.scatter_items) == 0:
            self.report({'ERROR'}, "No scatter items defined")
            return {'CANCELLED'}
        
        # Create a new collection for scattered objects
        collection_name = "KDLZ_Scattered_Objects"
        if collection_name in bpy.data.collections:
            collection = bpy.data.collections[collection_name]
        else:
            collection = bpy.data.collections.new(collection_name)
            context.scene.collection.children.link(collection)
        
        # Get target for scatter
        if props.scatter_method == 'SURFACE':
            # Surface scatter
            target_obj = bpy.data.objects.get(props.target_object)
            if not target_obj:
                self.report({'ERROR'}, "No target object selected")
                return {'CANCELLED'}
            
            # Get target mesh data
            if target_obj.type != 'MESH':
                self.report({'ERROR'}, "Target must be a mesh object")
                return {'CANCELLED'}
            
            # Get mesh data
            mesh = target_obj.data
            
            # Get total area of the mesh for density calculations
            total_area = sum(p.area for p in mesh.polygons)
            
            # Create a list of polygons with their accumulated areas
            accumulated_areas = []
            accumulated_area = 0
            for polygon in mesh.polygons:
                accumulated_area += polygon.area
                accumulated_areas.append(accumulated_area)
            
            # Process each scatter item
            for item in props.scatter_items:
                if not item.object:
                    continue
                
                # Set random seed
                random.seed(item.random_seed)
                
                # Calculate number of instances based on density and mesh area
                num_instances = int(total_area * item.density * 10)
                
                # Track placed positions for overlap avoidance
                placed_positions = []
                
                # Create instances
                for i in range(num_instances):
                    # Select a random face weighted by area
                    random_area = random.uniform(0, accumulated_area)
                    polygon_index = 0
                    for index, area in enumerate(accumulated_areas):
                        if area >= random_area:
                            polygon_index = index
                            break
                    
                    polygon = mesh.polygons[polygon_index]
                    
                    # Get a random point on the polygon
                    vertices = [mesh.vertices[v].co for v in polygon.vertices]
                    if len(vertices) == 3:
                        # Triangle - simple barycentric coordinates
                        u = random.random()
                        v = random.random() * (1 - u)
                        w = 1 - u - v
                        point = vertices[0] * u + vertices[1] * v + vertices[2] * w
                    else:
                        # N-gon - use center point for simplicity
                        point = polygon.center
                    
                    # Convert to world space
                    world_point = target_obj.matrix_world @ point
                    
                    # Check for overlap
                    if props.avoid_overlap and placed_positions:
                        too_close = False
                        for pos in placed_positions:
                            if (world_point - pos).length < props.min_distance:
                                too_close = True
                                break
                        if too_close:
                            continue
                    
                    # Add position to placed list
                    placed_positions.append(world_point)
                    
                    # Create instance
                    obj_copy = item.object.copy()
                    obj_copy.data = item.object.data
                    collection.objects.link(obj_copy)
                    
                    # Position at point
                    obj_copy.location = world_point
                    
                    # Random rotation
                    if item.align_to_normal:
                        # Align Z axis to face normal
                        normal = target_obj.matrix_world.to_3x3() @ polygon.normal
                        normal.normalize()
                        
                        # Create rotation to align with normal
                        z_axis = mathutils.Vector((0, 0, 1))
                        angle = z_axis.angle(normal)
                        axis = z_axis.cross(normal)
                        
                        if axis.length > 0.0001:  # Avoid zero-length axis
                            axis.normalize()
                            rot = mathutils.Quaternion(axis, angle)
                            obj_copy.rotation_euler = rot.to_euler()
                            
                            # Add random rotation around normal
                            random_rot_z = math.radians(random.uniform(item.rotation_min, item.rotation_max))
                            obj_copy.rotation_euler.rotate_axis('Z', random_rot_z)
                    else:
                        # Random rotation on all axes
                        obj_copy.rotation_euler.x = math.radians(random.uniform(0, 360))
                        obj_copy.rotation_euler.y = math.radians(random.uniform(0, 360))
                        obj_copy.rotation_euler.z = math.radians(random.uniform(0, 360))
                    
                    # Random scale
                    random_scale = random.uniform(item.scale_min, item.scale_max)
                    obj_copy.scale = (random_scale, random_scale, random_scale)
        
        elif props.scatter_method == 'VOLUME':
            # Volume scatter
            volume_size = props.volume_size
            volume_center = props.volume_center
            
            # Process each scatter item
            for item in props.scatter_items:
                if not item.object:
                    continue
                
                # Set random seed
                random.seed(item.random_seed)
                
                # Calculate number of instances based on density and volume
                volume = volume_size[0] * volume_size[1] * volume_size[2]
                num_instances = int(volume * item.density * 5)
                
                # Track placed positions for overlap avoidance
                placed_positions = []
                
                # Create instances
                for i in range(num_instances):
                    # Random position within volume
                    x = random.uniform(-volume_size[0]/2, volume_size[0]/2) + volume_center[0]
                    y = random.uniform(-volume_size[1]/2, volume_size[1]/2) + volume_center[1]
                    z = random.uniform(-volume_size[2]/2, volume_size[2]/2) + volume_center[2]
                    point = mathutils.Vector((x, y, z))
                    
                    # Check for overlap
                    if props.avoid_overlap and placed_positions:
                        too_close = False
                        for pos in placed_positions:
                            if (point - pos).length < props.min_distance:
                                too_close = True
                                break
                        if too_close:
                            continue
                    
                    # Add position to placed list
                    placed_positions.append(point)
                    
                    # Create instance
                    obj_copy = item.object.copy()
                    obj_copy.data = item.object.data
                    collection.objects.link(obj_copy)
                    
                    # Position at point
                    obj_copy.location = point
                    
                    # Random rotation
                    obj_copy.rotation_euler.x = math.radians(random.uniform(0, 360))
                    obj_copy.rotation_euler.y = math.radians(random.uniform(0, 360))
                    obj_copy.rotation_euler.z = math.radians(random.uniform(item.rotation_min, item.rotation_max))
                    
                    # Random scale
                    random_scale = random.uniform(item.scale_min, item.scale_max)
                    obj_copy.scale = (random_scale, random_scale, random_scale)
        
        elif props.scatter_method == 'PATH':
            # Path scatter
            path_obj = bpy.data.objects.get(props.path_object)
            if not path_obj:
                self.report({'ERROR'}, "No path object selected")
                return {'CANCELLED'}
            
            # Check if path object has splines (is a curve)
            if path_obj.type != 'CURVE':
                self.report({'ERROR'}, "Path object must be a curve")
                return {'CANCELLED'}
            
            # Process each scatter item
            for item in props.scatter_items:
                if not item.object:
                    continue
                
                # Set random seed
                random.seed(item.random_seed)
                
                # Get curve data
                curve = path_obj.data
                
                # Process each spline in the curve
                for spline in curve.splines:
                    # Calculate spline length (approximate)
                    points = []
                    if spline.type == 'BEZIER':
                        points = [p.co for p in spline.bezier_points]
                    else:
                        points = [p.co for p in spline.points]
                    
                    # Calculate segments and total length
                    segments = []
                    total_length = 0
                    for i in range(1, len(points)):
                        segment_length = (points[i] - points[i-1]).length
                        segments.append((points[i-1], points[i], segment_length))
                        total_length += segment_length
                    
                    # Calculate number of instances based on density and path length
                    num_instances = int(total_length * item.density * 2)
                    
                    # Track placed positions for overlap avoidance
                    placed_positions = []
                    
                    # Create instances along path
                    for i in range(num_instances):
                        # Choose a random position along the path
                        random_dist = random.uniform(0, total_length)
                        
                        # Find the segment that contains this position
                        current_dist = 0
                        segment_start = mathutils.Vector((0, 0, 0))
                        segment_end = mathutils.Vector((0, 0, 0))
                        segment_length = 0
                        
                        for start, end, length in segments:
                            if current_dist + length >= random_dist:
                                segment_start = start
                                segment_end = end
                                segment_length = length
                                break
                            current_dist += length
                        
                        # Calculate position on segment
                        segment_pos = (random_dist - current_dist) / segment_length
                        point = segment_start.lerp(segment_end, segment_pos)
                        
                        # Convert to world space
                        world_point = path_obj.matrix_world @ point
                        
                        # Apply path offset
                        if props.path_offset > 0:
                            # Calculate direction vector perpendicular to path
                            direction = segment_end - segment_start
                            if direction.length > 0:
                                direction.normalize()
                                
                                # Create perpendicular vector (in XY plane for simplicity)
                                perp = mathutils.Vector((-direction.y, direction.x, 0))
                                perp.normalize()
                                
                                # Apply random offset
                                random_offset = random.uniform(-props.path_offset, props.path_offset)
                                world_point += perp * random_offset
                        
                        # Check for overlap
                        if props.avoid_overlap and placed_positions:
                            too_close = False
                            for pos in placed_positions:
                                if (world_point - pos).length < props.min_distance:
                                    too_close = True
                                    break
                            if too_close:
                                continue
                        
                        # Add position to placed list
                        placed_positions.append(world_point)
                        
                        # Create instance
                        obj_copy = item.object.copy()
                        obj_copy.data = item.object.data
                        collection.objects.link(obj_copy)
                        
                        # Position at point
                        obj_copy.location = world_point
                        
                        # Rotation - align to path direction
                        if item.align_to_normal and direction.length > 0:
                            # Create rotation to align with path direction
                            z_axis = mathutils.Vector((0, 0, 1))
                            y_axis = mathutils.Vector((0, 1, 0))
                            
                            # Align Y axis with path direction
                            angle_y = y_axis.angle(direction)
                            axis_y = y_axis.cross(direction)
                            
                            if axis_y.length > 0.0001:  # Avoid zero-length axis
                                axis_y.normalize()
                                rot = mathutils.Quaternion(axis_y, angle_y)
                                obj_copy.rotation_euler = rot.to_euler()
                                
                                # Add random rotation around Y axis
                                random_rot_y = math.radians(random.uniform(item.rotation_min, item.rotation_max))
                                obj_copy.rotation_euler.rotate_axis('Y', random_rot_y)
                        else:
                            # Random rotation on all axes
                            obj_copy.rotation_euler.x = math.radians(random.uniform(0, 360))
                            obj_copy.rotation_euler.y = math.radians(random.uniform(0, 360))
                            obj_copy.rotation_euler.z = math.radians(random.uniform(0, 360))
                        
                        # Random scale
                        random_scale = random.uniform(item.scale_min, item.scale_max)
                        obj_copy.scale = (random_scale, random_scale, random_scale)
        
        self.report({'INFO'}, f"Scatter completed. Objects placed in collection '{collection_name}'")
        return {'FINISHED'}

class KDLZ_OT_ClearScatter(bpy.types.Operator):
    bl_idname = "kdlz.clear_scatter"
    bl_label = "Clear Scattered Objects"
    
    def execute(self, context):
        collection_name = "KDLZ_Scattered_Objects"
        
        if collection_name in bpy.data.collections:
            collection = bpy.data.collections[collection_name]
            
            # Remove all objects in the collection
            for obj in list(collection.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            
            # Remove the collection
            bpy.data.collections.remove(collection)
            
            self.report({'INFO'}, "Cleared all scattered objects")
        else:
            self.report({'INFO'}, "No scattered objects to clear")
        
        return {'FINISHED'}

class KDLZ_ScatterProps(bpy.types.PropertyGroup):
    scatter_method: EnumProperty(
        name="Scatter Method",
        items=[
            ('SURFACE', "Surface", "Scatter on object surface"),
            ('VOLUME', "Volume", "Scatter in 3D volume"),
            ('PATH', "Path", "Scatter along a path")
        ],
        default='SURFACE'
    )
    
    target_object: StringProperty(
        name="Target Object",
        description="Object to scatter on"
    )
    
    volume_size: bpy.props.FloatVectorProperty(
        name="Volume Size",
        description="Size of the volume to scatter in",
        default=(10.0, 10.0, 10.0),
        min=0.1
    )
    
    volume_center: bpy.props.FloatVectorProperty(
        name="Volume Center",
        description="Center of the volume to scatter in",
        default=(0.0, 0.0, 0.0)
    )
    
    path_object: StringProperty(
        name="Path Object",
        description="Curve to scatter along"
    )
    
    path_offset: FloatProperty(
        name="Path Offset",
        description="Random offset from path",
        default=0.5,
        min=0.0,
        max=10.0
    )
    
    avoid_overlap: BoolProperty(
        name="Avoid Overlap",
        description="Prevent objects from overlapping",
        default=True
    )
    
    min_distance: FloatProperty(
        name="Min Distance",
        description="Minimum distance between scattered objects",
        default=1.0,
        min=0.01,
        max=10.0
    )
    
    scatter_items: CollectionProperty(
        type=KDLZ_ScatterItem,
        name="Scatter Items"
    )

def register():
    bpy.utils.register_class(KDLZ_ScatterItem)
    bpy.utils.register_class(KDLZ_PT_ScatterCraftPanel)
    bpy.utils.register_class(KDLZ_OT_ScatterCraft)
    bpy.utils.register_class(KDLZ_OT_AddScatterItem)
    bpy.utils.register_class(KDLZ_OT_RemoveScatterItem)
    bpy.utils.register_class(KDLZ_OT_ExecuteScatter)
    bpy.utils.register_class(KDLZ_OT_ClearScatter)
    bpy.utils.register_class(KDLZ_ScatterProps)
    bpy.types.Scene.kdlz_scatter_props = bpy.props.PointerProperty(type=KDLZ_ScatterProps)

def unregister():
    bpy.utils.unregister_class(KDLZ_PT_ScatterCraftPanel)
    bpy.utils.unregister_class(KDLZ_OT_ScatterCraft)
    bpy.utils.unregister_class(KDLZ_OT_AddScatterItem)
    bpy.utils.unregister_class(KDLZ_OT_RemoveScatterItem)
    bpy.utils.unregister_class(KDLZ_OT_ExecuteScatter)
    bpy.utils.unregister_class(KDLZ_OT_ClearScatter)
    bpy.utils.unregister_class(KDLZ_ScatterProps)
    bpy.utils.unregister_class(KDLZ_ScatterItem)
    del bpy.types.Scene.kdlz_scatter_props
