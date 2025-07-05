#fakegucci
##################################
# CLOTH SIMULATION MECHANISM SETUP
##################################
# Select an ORG bone chain that you want to have physics (hair strand, loose fabric, shoelace, etc)
# run script
# Ribbon mesh will be created with cloth simulation along with PHYS bone chain to track the mesh, FK bones to tweak
# ORG bones will copy transforms of FK bones
# Can select many chains at once but its slightly buggy so go a few at a time to verify it succeeded.
# If it bugs out just undo and try again, I found clicking to select the last bone helps instead of just box selecting and hitting run
 
import bpy
import bmesh
import re
from mathutils import Vector

def setup_cloth_chain():
    """
    Create a mesh consisting of connected vertices positioned at each joint
    in the selected ORG bone chain
    """
    
    # Get the active armature
    if bpy.context.active_object is None or bpy.context.active_object.type != 'ARMATURE':
        print("Error: Please select an armature object")
        return
    
    armature = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Get selected bones that match the pattern ORG_*.[LR]
    selected_org_bones = []
    pattern_with_suffix = r'^ORG_(.*)\.([LR])$'
    pattern_without_suffix = r'^ORG_(.+)$'

    for bone in bpy.context.selected_editable_bones:
        print(f"Checking bone: {bone.name}")
        
        match_with_suffix = re.match(pattern_with_suffix, bone.name)
        if match_with_suffix:
            print(f"  Matched with suffix pattern")
            selected_org_bones.append(bone)
        else:
            match_without_suffix = re.match(pattern_without_suffix, bone.name)
            if match_without_suffix and '.' not in bone.name:
                print(f"  Matched without suffix pattern")
                selected_org_bones.append(bone)
            else:
                print(f"  No match, unrecognized suffix or ends in .")  # Debug line
        
    if not selected_org_bones:
        print("No selected bones found with pattern ORG_*.L or ORG_*.R")
        bpy.ops.object.mode_set(mode='OBJECT')
        return
        
    print(f"Found {len(selected_org_bones)} ORG bones to process")
    
    # Group bones
    bone_chains = {}
    chain_parents = {}

    # identify all unique chain names
    chain_names = set()
    for bone in selected_org_bones:
        match_with_suffix = re.match(pattern_with_suffix, bone.name)
        match_without_suffix = re.match(pattern_without_suffix, bone.name)
        
        if match_with_suffix: #L/R chains
            full_name = match_with_suffix.group(1)
            suffix = match_with_suffix.group(2)
            
            # Extract chain name (remove _number)
            chain_match = re.match(r'^(.+)_\d+$', full_name)
            
            if chain_match:
                chain_name = chain_match.group(1)
                chain_key = f"{chain_name}.{suffix}"
            else:
                chain_key = f"{full_name}.{suffix}"
                
        elif match_without_suffix and '.' not in bone.name: #Center or unique chains
            full_name = match_without_suffix.group(1)
            
            # Extract chain name (remove _number)
            chain_match = re.match(r'^(.+)_\d+$', full_name)
            if chain_match:
                chain_name = chain_match.group(1)
                chain_key = chain_name
            else:
                chain_key = full_name
        else:
            continue
        
        chain_names.add(chain_key)

    # group bones by their actual chains
    for chain_key in chain_names:
        bone_chains[chain_key] = []

    for bone in selected_org_bones:
        match_with_suffix = re.match(pattern_with_suffix, bone.name)
        match_without_suffix = re.match(pattern_without_suffix, bone.name)
        
        if match_with_suffix:
            full_name = match_with_suffix.group(1)
            suffix = match_with_suffix.group(2)
            chain_match = re.match(r'^(.+)_\d+$', full_name)
            if chain_match:
                chain_name = chain_match.group(1)
                chain_key = f"{chain_name}.{suffix}"
            else:
                chain_key = f"{full_name}.{suffix}"
        elif match_without_suffix and '.' not in bone.name:
            full_name = match_without_suffix.group(1)
            chain_match = re.match(r'^(.+)_\d+$', full_name)
            if chain_match:
                chain_name = chain_match.group(1)
                chain_key = chain_name
            else:
                chain_key = full_name
        else:
            continue
        
        bone_chains[chain_key].append(bone)

    # Sort each chain and find parents
    for chain_key in bone_chains:
        bone_chains[chain_key] = sort_bone_chain(bone_chains[chain_key])
        
        if bone_chains[chain_key]:
            first_bone = bone_chains[chain_key][0]
            chain_parents[chain_key] = first_bone.parent
            if first_bone.parent:
                print(f"Chain {chain_key}: First bone {first_bone.name} has parent {first_bone.parent.name}")
            else:
                print(f"Chain {chain_key}: First bone {first_bone.name} has no parent")
    
    # Create meshes
    bpy.ops.object.mode_set(mode='OBJECT')
    created_meshes = []
    
    for chain_key, bone_chain in bone_chains.items():
        #TODO: allow 1 bone "chains"
        if len(bone_chain) < 2:
            print(f"Skipping chain {chain_key}: needs at least 2 bones")
            continue
        
        if '.' in chain_key:
            name_part, suffix = chain_key.rsplit('.', 1)
            mesh_name = f"{name_part}_PHYSICS_OBJECT.{suffix}"
        else:
            name_part = chain_key
            mesh_name = f"{name_part}_PHYSICS_OBJECT"
        
        mesh = create_chain_mesh(bone_chain, armature, mesh_name)
        
        if mesh:
            created_meshes.append(mesh)
            print(f"Created mesh: {mesh_name} with {len(bone_chain)} joints")
            
            # Add Child Of constraint to the mesh so it follows the armature
            parent_bone = chain_parents.get(chain_key)
            if parent_bone:
                bpy.context.view_layer.objects.active = mesh
                mesh.select_set(True)

                child_of_constraint = mesh.constraints.new('CHILD_OF')
                child_of_constraint.name = "Child Of Parent Bone"
                child_of_constraint.target = armature
                child_of_constraint.subtarget = parent_bone.name
                
                # Set the inverse matrix
                # TODO: this is where the bug always happens
                with bpy.context.temp_override(active_object=mesh):
                    bpy.ops.constraint.childof_set_inverse(constraint="Child Of Parent Bone", owner='OBJECT')
            
                print(f"Added Child Of constraint to {mesh_name} targeting {parent_bone.name}")
            else:
                print(f"No parent bone found for chain {suffix}")
    
    print(f"Created {len(created_meshes)} mesh objects")

    bpy.ops.object.select_all(action='DESELECT')

    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')
    
    selected_org_bone_names = []
    pattern_with_suffix = r'^ORG_(.*)\.([LR])$'
    pattern_without_suffix = r'^ORG_(.+)$'

    for bone in bpy.context.selected_editable_bones:
        print(f"Checking bone: {bone.name}")
        
        match_with_suffix = re.match(pattern_with_suffix, bone.name)
        if match_with_suffix:
            print(f"  Matched with suffix pattern")
            selected_org_bone_names.append(bone.name)
        else:
            match_without_suffix = re.match(pattern_without_suffix, bone.name)
            if match_without_suffix and '.' not in bone.name:
                print(f"  Matched without suffix pattern")
                selected_org_bone_names.append(bone.name)
            else:
                print(f"  No match - has dot: {'.' in bone.name}, pattern match: {match_without_suffix is not None}")

    if not selected_org_bone_names:
        print("No selected bones found with pattern ORG_")
        bpy.ops.object.mode_set(mode='OBJECT')
        return

    print(f"Found {len(selected_org_bone_names)} ORG bones to duplicate")

    # Create the duplicate sets
    prefixes = ['PHYS', 'FK']
    created_bones = {prefix: [] for prefix in prefixes}
    
    last_created_bone = {}

    for org_bone_name in selected_org_bone_names:

        match_with_suffix = re.match(r'^ORG_(.*)\.([LR])$', org_bone_name)
        match_without_suffix = re.match(r'^ORG_(.*)$', org_bone_name)
        
        if match_with_suffix:
            base_name = match_with_suffix.group(1)
            suffix = match_with_suffix.group(2)
            suffix_part = f".{suffix}"
        elif match_without_suffix and '.' not in org_bone_name:
            base_name = match_without_suffix.group(1)
            suffix = "C"  # Use "C" for center or unique
            suffix_part = ""  # No suffix in the actual name
        else:
            print(f"Pattern mismatch for {org_bone_name} when creating FK/Physics chains")
            continue  # Skip if no pattern matches
        
        
        org_bone = armature.data.edit_bones[org_bone_name]
            
        # Check if this is the first bone in the chain
        is_first_bone = "_01" in base_name
    
        # Create PHYS/FK chains
        for prefix in prefixes:
            new_name = f"{prefix}_{base_name}{suffix_part}"
        
            # Duplicate the bone
            new_bone = armature.data.edit_bones.new(new_name)
            new_bone.head = org_bone.head.copy()
            new_bone.tail = org_bone.tail.copy()
            new_bone.roll = org_bone.roll
            
            # Set parent based on whether this is the first bone or not
            if is_first_bone:
                # First bone: use the original parent
                new_bone.parent = org_bone.parent
            else:
                # Subsequent bones: use the previous bone of the same prefix/suffix
                key = f"{prefix}.{suffix}"
                if key in last_created_bone:
                    new_bone.parent = last_created_bone[key]
                else:
                    new_bone.parent = org_bone.parent
            
            # Store this bone as the last created for this prefix/suffix
            key = f"{prefix}.{suffix}"
            last_created_bone[key] = new_bone
        
            created_bones[prefix].append((new_name, suffix))
            print(f"Created bone: {new_name} with parent: {new_bone.parent.name if new_bone.parent else 'None'}")

    bpy.ops.object.mode_set(mode='POSE')

    # Assign bones to collections
    for prefix in prefixes:
        if prefix == 'FK':
            collection_name = 'FK'
        elif prefix == 'PHYS':
            collection_name = 'PHYSICS'
        else:
            continue
        
        # Get or create the bone collection
        bone_collection = None
        for collection in armature.data.collections:
            if collection.name == collection_name:
                bone_collection = collection
                break
        
        if bone_collection is None:
            # Create the collection if it doesn't exist
            bone_collection = armature.data.collections.new(collection_name)
            print(f"Created bone collection: {collection_name}")
        
        # Assign bones to the collection
        for bone_name, suffix in created_bones[prefix]:
            bone = armature.data.bones[bone_name]
            bone_collection.assign(bone)
            print(f"Assigned {bone_name} to collection {collection_name}")
        
    for org_bone_name in selected_org_bone_names:
        # Get the suffix for THIS specific bone
        match_with_suffix = re.match(r'^ORG_(.*)\.([LR])$', org_bone_name)
        match_without_suffix = re.match(r'^ORG_(.*)$', org_bone_name)
        if match_with_suffix:
            base_name = match_with_suffix.group(1)
            suffix = match_with_suffix.group(2)  # Get the suffix for this specific bone
            
            org_bone = armature.pose.bones[org_bone_name]
            fk_bone_name = f"FK_{base_name}.{suffix}"
            constraint = org_bone.constraints.new('COPY_TRANSFORMS')
            constraint.name = "Copy FK transform"
            constraint.target = armature
            constraint.subtarget = fk_bone_name
            print(f"Added Copy transform constraint to {org_bone_name} -> {fk_bone_name}")
        else:
            if match_without_suffix:
                base_name = match_without_suffix.group(1)
            
                org_bone = armature.pose.bones[org_bone_name]
                fk_bone_name = f"FK_{base_name}"
                constraint = org_bone.constraints.new('COPY_TRANSFORMS')
                constraint.name = "Copy FK transform"
                constraint.target = armature
                constraint.subtarget = fk_bone_name
                print(f"Added Copy transform constraint to {org_bone_name} -> {fk_bone_name}")
            else:
                print(f"failed to find FK bone for copy transform constraint")
            
            
    # Add Copy Rotation constraint to FK bones targeting PHYS bones
    for fk_bone_name, suffix in created_bones['FK']:
        fk_bone = armature.pose.bones[fk_bone_name]
        base_name = fk_bone_name.replace('FK_', '').replace(f'.{suffix}', '')
        
        if suffix == 'C':
            phys_bone_name = f"PHYS_{base_name}"
        else:
            phys_bone_name = f"PHYS_{base_name}.{suffix}"
        
        
        constraint = fk_bone.constraints.new('COPY_ROTATION')
        constraint.name = "Copy Phys Rotation"
        constraint.target = armature
        constraint.subtarget = phys_bone_name
        
        constraint.mix_mode = 'BEFORE'
        constraint.target_space = 'LOCAL'
        constraint.owner_space = 'LOCAL'
        
        print(f"Added Copy rotation constraint to {fk_bone_name} -> {phys_bone_name}")
        
    # Add damped track constraint to PHYS bones targeting physics vert groups on PHYSICS_OBJECT mesh    
    for phys_bone_name, suffix in created_bones['PHYS']:
        phys_bone = armature.pose.bones[phys_bone_name]
        base_name = phys_bone_name.replace('PHYS_', '').replace(f'.{suffix}', '')
        
        # Extract the bone index from the bone name
        name_match = re.match(r'^(.+)_\d+$', base_name)
        if name_match:
            name_part = name_match.group(1)
        else:
            name_part = base_name 

        # Find the corresponding mesh object
        mesh_name = f"{name_part}_PHYSICS_OBJECT.{suffix}"
        target_mesh = bpy.data.objects.get(mesh_name)
        
        # Center or Unique mesh wont have a suffix
        if not target_mesh:
            mesh_name = f"{name_part}_PHYSICS_OBJECT"
            target_mesh = bpy.data.objects.get(mesh_name)
        
        if target_mesh:
            number_match = re.search(r'_(\d+)$', base_name)
            if number_match:

                # Physics vertex groups are physics.00n naming convention while bones are _0n
                bone_number = int(number_match.group(1)) 
                vertex_group_name = f"physics.{bone_number:03d}"
            
                constraint = phys_bone.constraints.new('DAMPED_TRACK')
                constraint.name = "TRACK PHYS MESH"
                constraint.target = target_mesh
                constraint.subtarget = vertex_group_name
            
                print(f"Added Damped track constraint to {phys_bone_name} -> {mesh_name}.{vertex_group_name}")
            else:
                print(f"Could not extract bone number from {phys_bone_name}")
        else:
            print(f"Could not find mesh object: {mesh_name}")

    # Set custom shapes for FK bones
    wgt_object = bpy.data.objects.get("WGT-PHYS-FK")
    if wgt_object is None:
        print("Warning: WGT-PHYS-FK object not found for custom bone shapes")

    for fk_bone_name, suffix in created_bones['FK']:
        fk_pose_bone = armature.pose.bones[fk_bone_name]
        
        # Set custom shape
        if wgt_object:
            fk_pose_bone.custom_shape = wgt_object
            
            bone_length = fk_pose_bone.bone.length
            
            # Set custom shape transform properties
            fk_pose_bone.custom_shape_translation[1] = 0.5 * bone_length  # Translate halfway down Y axis
            fk_pose_bone.custom_shape_scale_xyz[0] = 0.4
            fk_pose_bone.custom_shape_scale_xyz[1] = 1.0
            fk_pose_bone.custom_shape_scale_xyz[2] = 0.4
            
            print(f"Set custom shape for {fk_bone_name}")
        
        # I set them to yellow
        fk_pose_bone.color.palette = 'THEME09'
        print(f"Set color theme for {fk_bone_name}")
        
    return created_meshes

# Sort bones from parent to child
def sort_bone_chain(bones):

    bone_dict = {bone.name: bone for bone in bones}
    sorted_chain = []
    
    # Find the root bone (top of chain, not the root of armature)
    root_bones = []
    for bone in bones:
        if bone.parent is None or bone.parent.name not in bone_dict:
            root_bones.append(bone)
    
    if len(root_bones) != 1:
        print(f"Warning: Found {len(root_bones)} root bones in chain")
    
    # Build the chain from root to tip
    def add_children_recursive(parent_bone):
        sorted_chain.append(parent_bone)
        for bone in bones:
            if bone.parent and bone.parent.name == parent_bone.name:
                add_children_recursive(bone)
    
    for root in root_bones:
        add_children_recursive(root)
    
    return sorted_chain


# Create ribbon mesh, vertices will be aligned with corresponding bones Z axis, the center vert being at the bones head
def create_chain_mesh(bone_chain, armature, mesh_name):
    
    # Create new mesh and object
    mesh = bpy.data.meshes.new(mesh_name)
    obj = bpy.data.objects.new(mesh_name, mesh)
    
    # Get or create PHYSICS_OBJECTS collection
    physics_collection = None
    for collection in bpy.data.collections:
        if collection.name == "PHYSICS_OBJECTS":
            physics_collection = collection
            break
    
    if physics_collection is None:
        physics_collection = bpy.data.collections.new("PHYSICS_OBJECTS")
        bpy.context.scene.collection.children.link(physics_collection)
        print("Created PHYSICS_OBJECTS collection")
    
    physics_collection.objects.link(obj)
    print(f"Added {mesh_name} to PHYSICS_OBJECTS collection")
    
    # Create bmesh instance
    bm = bmesh.new()
    
    arm_matrix = armature.matrix_world
    
    # Add vertices at each bone joint
    all_vertices = []
    ribbon_width = 0.1
    
    # TODO: Bug here as well I think
    for i, bone in enumerate(bone_chain):
        # Get bone head position and Z-axis in world space
        head_pos = arm_matrix @ bone.head
        bone_z_axis = arm_matrix.to_3x3() @ bone.z_axis
        bone_z_axis.normalize()
        
        # Create 3 vertices: center, left, right
        center_vert = bm.verts.new(head_pos)
        left_vert = bm.verts.new(head_pos - bone_z_axis * ribbon_width)
        right_vert = bm.verts.new(head_pos + bone_z_axis * ribbon_width)
        
        all_vertices.append([left_vert, center_vert, right_vert])
        
        # For the last bone, also add the tail vertices
        if i == len(bone_chain) - 1:
            tail_pos = arm_matrix @ bone.tail
            
            tail_center_vert = bm.verts.new(tail_pos)
            tail_left_vert = bm.verts.new(tail_pos - bone_z_axis * ribbon_width)
            tail_right_vert = bm.verts.new(tail_pos + bone_z_axis * ribbon_width)
            
            all_vertices.append([tail_left_vert, tail_center_vert, tail_right_vert])
    
    # Ensure face index validity
    bm.verts.ensure_lookup_table()
    
    # Create edges connecting the ribbon segments
    for i in range(len(all_vertices) - 1):
        current_row = all_vertices[i]
        next_row = all_vertices[i + 1]
        
        # Connect corresponding vertices between rows
        for j in range(3):  # 3 vertices per row (left, center, right)
            bm.edges.new((current_row[j], next_row[j]))
        
        # Connect vertices within each row to form the ribbon structure
        if i == 0:  # Only create cross-connections for the first row
            bm.edges.new((current_row[0], current_row[1]))  # left to center
            bm.edges.new((current_row[1], current_row[2]))  # center to right
        
        # Create cross-connections for the next row
        bm.edges.new((next_row[0], next_row[1]))  # left to center
        bm.edges.new((next_row[1], next_row[2]))  # center to right
        
        # Create faces for the ribbon segments
        # Left strip
        bm.faces.new([current_row[0], next_row[0], next_row[1], current_row[1]])
        # Right strip  
        bm.faces.new([current_row[1], next_row[1], next_row[2], current_row[2]])
    
    # Update mesh
    bm.to_mesh(mesh)
    bm.free()
    
    # Create vertex groups for physics simulation
    total_vertices = len(all_vertices) * 3  # 3 vertices per row
    pin_group = None
    
    vertex_index = 0
    for row_index, vertex_row in enumerate(all_vertices):
        for vert_in_row in range(3):
            group_name = f"physics.{row_index:03d}"
            
            # Create vert group for current row
            vertex_group = None
            for vg in obj.vertex_groups:
                if vg.name == group_name:
                    vertex_group = vg
                    break
            
            if vertex_group is None:
                vertex_group = obj.vertex_groups.new(name=group_name)
                print(f"Created vertex group: {group_name}")
            
            # Assign vertex to the group with weight 1.0
            vertex_group.add([vertex_index], 1.0, 'REPLACE')
            
            # physics.000 is for pinning
            if row_index == 0 and pin_group is None:
                pin_group = vertex_group
            
            # For rows after the first, also add 0.2 weight to physics.000 for stability
            #TODO: I kinda dont like how this behaves when gravity points in a different direction
            if row_index > 0 and pin_group is not None:
                pin_group.add([vertex_index], 0.2, 'ADD')
                print(f"Added 0.2 weight to physics.000 for vertex {vertex_index}")
            
            vertex_index += 1
    
    # Enable cloth physics simulation
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    
    # Add cloth modifier
    cloth_modifier = obj.modifiers.new(name="Cloth", type='CLOTH')
    
    # Cloth settings
    cloth_settings = cloth_modifier.settings
    cloth_settings.quality = 5
    cloth_settings.mass = 0.3
    cloth_settings.tension_stiffness = 15
    cloth_settings.compression_stiffness = 15
    cloth_settings.shear_stiffness = 5
    cloth_settings.bending_stiffness = 0.5
    cloth_settings.tension_damping = 5
    cloth_settings.compression_damping = 5
    cloth_settings.shear_damping = 5
    cloth_settings.air_damping = 1
    
    # Set pin group
    if pin_group:
        cloth_settings.vertex_group_mass = pin_group.name
        cloth_settings.pin_stiffness = 1.0
        print(f"Set pin group to: {pin_group.name}")
    
    print(f"Enabled cloth simulation on {mesh_name}")
    
    return obj

if __name__ == "__main__":
    
    setup_cloth_chain()
