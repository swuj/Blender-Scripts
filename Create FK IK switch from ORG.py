#fakegucci
####################
# FK-IK SWITCH SETUP
####################
# Select an ORG bone chain, ensure PROPERTIES bone exists with appropriate switch property (line 697), run 
# MCH_SWITCH, MCH_IK, MCH_FK chains will be created with appropriate constraints
import bpy
import bmesh
import re
from mathutils import Vector

# Create and set up FK IK SWITCH
def create_fk_ik_switch():

    if bpy.context.active_object is None or bpy.context.active_object.type != 'ARMATURE':
        print("Error: Please select an armature object")
        return
    
    armature = bpy.context.active_object

    bpy.ops.object.mode_set(mode='EDIT')
    
    selected_org_bones = []
    pattern = r'^ORG_(.*)\.([LR])$'
    
    for bone in bpy.context.selected_editable_bones:
        if re.match(pattern, bone.name):
            selected_org_bones.append(bone.name)
    
    if not selected_org_bones:
        print("No selected bones found with pattern ORG_*.L or ORG_*.R")
        bpy.ops.object.mode_set(mode='OBJECT')
        return
    
    print(f"Found {len(selected_org_bones)} ORG bones to duplicate")
    
    # Create the three duplicate sets
    prefixes = ['MCH_SWITCH', 'MCH_IK', 'MCH_FK']
    created_bones = {prefix: [] for prefix in prefixes}
    
    #TODO: parenting
    for org_bone_name in selected_org_bones:
        # Get the suffix and base name
        match = re.match(r'^ORG_(.*)\.([LR])$', org_bone_name)
        if match:
            base_name = match.group(1)
            suffix = match.group(2)
            
            org_bone = armature.data.edit_bones[org_bone_name]

            for prefix in prefixes:
                new_name = f"{prefix}_{base_name}.{suffix}"

                new_bone = armature.data.edit_bones.new(new_name)
                new_bone.head = org_bone.head.copy()
                new_bone.tail = org_bone.tail.copy()
                new_bone.roll = org_bone.roll
                new_bone.parent = org_bone.parent
                
                created_bones[prefix].append((new_name, suffix))
                print(f"Created bone: {new_name}")
    
    bpy.ops.object.mode_set(mode='POSE')
    
    # Add constraints to MCH_SWITCH bones
    for switch_bone_name, suffix in created_bones['MCH_SWITCH']:
        switch_bone = armature.pose.bones[switch_bone_name]
        
        # Find corresponding FK and IK bones
        base_name = switch_bone_name.replace('MCH_SWITCH_', '').replace(f'.{suffix}', '')
        fk_bone_name = f"MCH_FK_{base_name}.{suffix}"
        ik_bone_name = f"MCH_IK_{base_name}.{suffix}"
        
        # Add Copy Transforms constraint for FK bone
        fk_constraint = switch_bone.constraints.new('COPY_TRANSFORMS')
        fk_constraint.name = "Copy FK"
        fk_constraint.target = armature
        fk_constraint.subtarget = fk_bone_name
        print(f"Added FK constraint to {switch_bone_name} -> {fk_bone_name}")
        
        # Add Copy Transforms constraint for IK bone
        ik_constraint = switch_bone.constraints.new('COPY_TRANSFORMS')
        ik_constraint.name = "Copy IK"
        ik_constraint.target = armature
        ik_constraint.subtarget = ik_bone_name
        print(f"Added IK constraint to {switch_bone_name} -> {ik_bone_name}")
        
        # Add driver to IK influence
        driver = ik_constraint.driver_add("influence").driver
        driver.type = 'AVERAGE'
        
        # Add variable for the custom property
        var = driver.variables.new()
        var.name = "switch_value"
        var.type = 'SINGLE_PROP'
        
        # Assign PROPERTIES bone custom property to var
        # TODO: Maybe create the PROPERTIES bone and property without needing to paste it here
        var.targets[0].id = armature
        var.targets[0].data_path = f'pose.bones["PROPERTIES"]["ARM_FK_IK_SWITCH.{suffix}"]'
        
        print(f"Added driver to {switch_bone_name} IK constraint using ARM_FK_IK_SWITCH.{suffix}")
    
    print("FK IK Switch setup complete")

if __name__ == "__main__":
    
    create_fk_ik_switch()