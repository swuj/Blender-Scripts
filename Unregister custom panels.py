import bpy

# List all registered classes
for cls_name in dir(bpy.types):
    cls = getattr(bpy.types, cls_name)
    
    # Check if it's a panel in the 'Item' category
    if (hasattr(cls, 'bl_space_type') and 
        hasattr(cls, 'bl_category') and 
        getattr(cls, 'bl_category', None)):
        
        try:
            bpy.utils.unregister_class(cls)
            print(f"Unregistered: {cls_name}")
        except:
            print(f"Failed to unregister: {cls_name}")