import bpy
import re

def copy_org_transforms_to_def(change_subtarget):
    """
    I forgot where I got this originally, maybe Pierrick Picaut, but its modified to be able to use it several times on an armature
    as you make changes since it will only add the constraint if it doesnt exist.
    """
    armature = bpy.context.active_object
    bones = armature.pose.bones

    for bone in bones:
        def_name = bone.name
        
        match = re.match(r'^(DEF)(.*?)$', def_name)
        
        if match:
            
            prefix = match.group(1)
            basename = match.group(2)
            org_name = f'ORG{basename}'
            
            if armature.pose.bones.get(org_name) is not None:
                def_bone = armature.pose.bones.get(def_name)
                has_copy_transforms = False
                for existing_constraint in def_bone.constraints:
                    if existing_constraint.type == 'COPY_TRANSFORMS':
                        print(f'{def_name} already has COPY_TRANSFORMS constraint')
                        if existing_constraint.subtarget == org_name:
                            print(f'{def_name} COPY_TRANSFORMS constraint already targeting {org_name}')
                            has_copy_transforms = True  
                            break
                        else:
                            if change_subtarget:
                                print(f'Retargeting')
                                constraint.target = armature
                                existing_constraint.subtarget = org_name
                                has_copy_transforms = True  
                                break
                                
            else:
               print(f'{org_name} not found')

            if not has_copy_transforms:
                constraint = def_bone.constraints.new('COPY_TRANSFORMS')
                constraint.target = armature
                constraint.subtarget = org_name
                print(f'Added COPY_TRANSFORMS constraint to {def_name} targeting {org_name}')
            
if __name__ == "__main__":
    
    change_subtarget = True
    copy_org_transforms_to_def(change_subtarget)