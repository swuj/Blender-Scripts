import bpy
from rna_prop_ui import rna_idprop_ui_create

"""
Adds given a list of prefixes (could be representing bones or chains) and a list of properties,
creates a version of each property for each prefix and adds them to a specified properties bone
"""

def add_properties_to_properties_bone(armature_name, properties_bone_name, bone_collections):
    
    # Get the armature object
    armature_obj = bpy.data.objects.get(armature_name)
    if not armature_obj or armature_obj.type != 'ARMATURE':
        print(f"Error: Armature '{armature_name}' not found or not an armature")
        return False
    
    # Get the properties bone
    properties_bone = armature_obj.pose.bones.get(properties_bone_name)
    if not properties_bone:
        print(f"Error: Properties bone '{properties_bone_name}' not found in armature '{armature_name}'")
        return False
    
    # Process each bone collection
    for collection in bone_collections:
        bones = collection.get('bones', [])
        properties = collection.get('properties', [])
        symmetrical = collection.get('symmetrical', False)
        
        # Build properties
        all_bones = bones.copy()
        suffixes = ['']
        if symmetrical:
            suffixes = ['.L', '.R']
        for suffix in suffixes:
            for bone_name in all_bones:
                for prop_config in properties:
                    prop_name = prop_config.get('name')
                    prop_type = prop_config.get('type', 'FLOAT')
                    default_value = prop_config.get('default', 0.0)
                    min_value = prop_config.get('min', 0.0)
                    max_value = prop_config.get('max', 1.0)
                    description = prop_config.get('description', '')
                    library_overridable = prop_config.get('library_overridable', True)
                    
                    # Build property name
                    if prop_name:
                        full_prop_name = f"{bone_name}_{prop_name}{suffix}"
                    else:
                        print(f"Error: Property name is required for bone '{bone_name}'")
                        continue
                    
                    # Set the custom property based on type
                    if prop_type.upper() == 'FLOAT':
                        properties_bone[full_prop_name] = float(default_value)
                    elif prop_type.upper() == 'INT':
                        properties_bone[full_prop_name] = int(default_value)
                    elif prop_type.upper() == 'BOOL':
                        properties_bone[full_prop_name] = bool(default_value)
                    elif prop_type.upper() == 'STRING':
                        properties_bone[full_prop_name] = str(default_value)
                    elif prop_type.upper() == 'VECTOR':
                        properties_bone[full_prop_name] = list(default_value) if isinstance(default_value, (list, tuple)) else [0.0, 0.0, 0.0]
                    else:
                        print(f"Warning: Unknown property type '{prop_type}' for property '{full_prop_name}'")
                        properties_bone[full_prop_name] = default_value
                    
                    # Set library overridable
                    if hasattr(properties_bone, 'property_overridable_library_set'):
                        properties_bone.property_overridable_library_set(f'["{full_prop_name}"]', library_overridable)
                    
                    print(f"Added property '{full_prop_name}' ({prop_type}) to properties bone '{properties_bone_name}'")

    return True


if __name__ == "__main__":
    
    # Define bone collections with shared properties
    bone_collections = [
        {
            'bones': ['INDEX'],
            'symmetrical': True,
            'properties': [
                {
                    'name': 'IK_FOLLOWS_FK',
                    'type': 'FLOAT',
                    'default': 1.0,
                    'min': 0.0,
                    'max': 1.0,
                    'description': 'IK chain influence for finger',
                    'library_overridable': True
                },
                {
                    'name': 'FK_FOLLOWS_IK',
                    'type': 'FLOAT',
                    'default': 1.0,
                    'min': 0.0,
                    'max': 1.0,
                    'description': 'IK chain influence for finger',
                    'library_overridable': True
                }
            ]
        }
    ]
    
    armature_name = "WitchArmature"
    properties_bone_name = "PROPERTIES"
    
    # Add properties to bones
    add_properties_to_properties_bone(armature_name, properties_bone_name, bone_collections)
    
    print("\nScript completed!")
    print("Properties created with naming pattern: BONE_NAME_PROPERTY_NAME")