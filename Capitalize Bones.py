import bpy

def make_bone_names_uppercase():
    """Convert all bone names in selected armatures to uppercase"""
    
    print("Capitalizing bone names of all armatures in selection")
    
    selected_objects = bpy.context.selected_objects
    armatures = [obj for obj in selected_objects if obj.type == 'ARMATURE']
    
    if not armatures:
        print("No armature objects selected")
        return
    
    for armature_obj in armatures:
        print(f"Processing armature: {armature_obj.name}")
        
        bpy.context.view_layer.objects.active = armature_obj
        bpy.ops.object.mode_set(mode='EDIT')
        
        armature_data = armature_obj.data
        
        changes_made = 0
        
        # Iterate through all bones
        for bone in armature_data.edit_bones:
            original_name = bone.name
            uppercase_name = original_name.upper()
            
            if original_name != uppercase_name:
                bone.name = uppercase_name
                print(f"Renamed: '{original_name}' -> '{uppercase_name}'")
                changes_made += 1
        
        print(f"Bones renamed: {changes_made}")
        #bpy.ops.object.mode_set(mode='OBJECT')

def make_all_armature_bones_uppercase():
    """Convert bone names to uppercase for ALL armatures in the scene"""
    
    print("Capitalizing bone names of all armatures in scene")
    
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE']
    
    if not armatures:
        print("No armature objects found")
        return
    
    for armature_obj in armatures:
        print(f"Processing armature: {armature_obj.name}")
        
        bpy.context.view_layer.objects.active = armature_obj
        armature_obj.select_set(True)
        
        bpy.ops.object.mode_set(mode='EDIT')
        
        armature_data = armature_obj.data
        changes_made = 0
        
        for bone in armature_data.edit_bones:
            original_name = bone.name
            uppercase_name = original_name.upper()
            
            if original_name != uppercase_name:
                bone.name = uppercase_name
                print(f"Renamed: '{original_name}' -> '{uppercase_name}'")
                changes_made += 1
        
        print(f"Bones renamed: {changes_made}")
        bpy.ops.object.mode_set(mode='OBJECT')

if __name__ == "__main__":

    """ SELECTED ARMATURES """
    make_bone_names_uppercase()

    """ ALL ARMATURES """
    #make_all_armature_bones_uppercase()