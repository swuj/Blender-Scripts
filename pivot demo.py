#fakegucci
"""
Demonstration of arbitrary pivot resetting

Basic Idea:
Transfer the transform into the affected bones local space, then reset the rotation of the pivot
returning it to be aligned so that the child bones counter movements no longer drift

How to use, sorry if its confusing its kinda jank:
run the script obviously
RESET button automatically keyframes affected on current and previous frame so:
Keyframe starting positions
advance at least 1 frame
Place pivot, make sure all channels are keyframed
advance at least 1 frame
rotate pivot, keyframe
advance 1 frame
click reset
"""
import bpy
from bpy.props import StringProperty, EnumProperty, PointerProperty, BoolProperty
from mathutils import Euler, Matrix, Vector, Quaternion
from bpy.types import PropertyGroup
from bpy.app.handlers import persistent
import mathutils

rig_id = "Arig"

class A_rig_OT_reset_dynamic_pivot(bpy.types.Operator):
    """
    Resets the Pivots rotation while maintaining the effect of the rotation on affected bone to allow
    moving the pivot to another location without affecting anything
    """
    bl_idname = "a_rig.reset_dynamic_pivot"
    bl_label = "Reset Dynamic Pivot"
    bl_description = "Resets pivot rotation while maintaining effect, to allow moving of the pivot after a rotation"
    bl_options = {'UNDO', 'INTERNAL'}
    parent: StringProperty(name="Parent", description="Name of Parent pivot bone")
    child: StringProperty(name="Child", description="Name of Child pivot bone")
    affected: StringProperty(name="Affected", description="Name of Affected bone")
    
    @classmethod 
    def poll(cls, context):
        try:
            return (context.active_object.data.get("rig_id") == rig_id)
        except (AttributeError, KeyError, TypeError):
            return False
    
    def execute(self, context):
        print(f"Resetting pivot: {self.parent}")
        armature = context.active_object
        pose_bones = armature.pose.bones
        scene = context.scene
        current_frame = scene.frame_current
    
        # Bones
        parent_bone = pose_bones[f'{self.parent}']
        affected_bone = pose_bones[f'{self.affected}']
        child_bone_name = f'{self.child}' 
        
        child_bone = pose_bones.get(child_bone_name)
        
        select_set = [affected_bone, parent_bone]
    
        if not parent_bone:
            self.report({'ERROR'}, "Parent bone not found")
            return {'CANCELLED'}
    
        if not child_bone:
            self.report({'ERROR'}, "Child bone not found")
            return {'CANCELLED'}
            
        if not affected_bone:
            self.report({'ERROR'}, f"Affected bone not found")
            return {'CANCELLED'}
    
        # Update to make sure matrices are current
        context.view_layer.update()
        
        # Need to keyframe the affected bone on the previous frame or it will have extra movement and then snap back on this frame
        print(f"frame {current_frame}")
        if current_frame > 0:
            current_affected_loc = affected_bone.location.copy()
            current_affected_rot = affected_bone.rotation_quaternion.copy()
            current_affected_scale = affected_bone.scale.copy()
            
            self.keyframe_previous_frame(
                scene, 
                affected_bone, 
                current_affected_loc, 
                current_affected_rot, 
                current_affected_scale
            )
        
        # Get affected bones matrix
        affected_world_matrix = armature.matrix_world @ affected_bone.matrix
        affected_loc, affected_rot, affected_scale = affected_world_matrix.decompose()
        
        # Reset pivot rotation
        parent_bone.rotation_quaternion = mathutils.Quaternion((1, 0, 0, 0))
        parent_bone.rotation_euler = mathutils.Euler((0, 0, 0), 'XYZ')

        context.view_layer.update()
        
        # Calculate new averaged effect after reset
        new_parent_world_matrix = armature.matrix_world @ parent_bone.matrix
        new_child_world_matrix = armature.matrix_world @ child_bone.matrix
        
        new_parent_loc, new_parent_rot, new_parent_scale = new_parent_world_matrix.decompose()
        new_child_loc, new_child_rot, new_child_scale = new_child_world_matrix.decompose()
        
        new_averaged_loc = (new_parent_loc + new_child_loc) * 0.5
        new_averaged_rot = new_parent_rot.slerp(new_child_rot, 0.5)
        new_averaged_scale = (new_parent_scale + new_child_scale) * 0.5
        
        new_averaged_world_matrix = mathutils.Matrix.LocRotScale(new_averaged_loc, new_averaged_rot, new_averaged_scale)
        target_affected_local_matrix = new_averaged_world_matrix.inverted() @ affected_world_matrix
        
        
        # Apply to affected bone
        loc, rot, scale = target_affected_local_matrix.decompose()
        
        affected_bone.location = loc
        affected_bone.rotation_quaternion = rot
        affected_bone.scale = scale
        
        context.view_layer.update()
        
        #bpy.ops.pose.select_all(action='DESELECT')
        for pbone in select_set:
            try:
                pbone.keyframe_insert("location")
                pbone.keyframe_insert("rotation_quaternion")
                pbone.keyframe_insert("scale")
            except RuntimeError:
                self.report({'WARNING'}, f'{pbone.name} failed to keyframe')
                pass
        
        #put pivot back at rest pose
        #nvm this is cancer
        #parent_bone.location = loc
        
        # Final update
        context.view_layer.update()
        
        self.report({'INFO'}, "Dynamic pivot reset successfully")
        return {'FINISHED'}
    
    def keyframe_previous_frame(self, scene, affected_bone, prev_loc, prev_rot, prev_scale):
        """Keyframe the affected bone on the previous frame with its original transform"""
        current_frame = scene.frame_current
        
        try:
            # Go to previous frame
            scene.frame_set(current_frame - 1)
            
            # Set the bone to its previous transform
            affected_bone.location = prev_loc
            affected_bone.rotation_quaternion = prev_rot
            affected_bone.scale = prev_scale
            
            bpy.context.view_layer.update()
            
            # Keyframe the bone on this frame
            affected_bone.keyframe_insert("location")
            affected_bone.keyframe_insert("rotation_quaternion")
            affected_bone.keyframe_insert("scale")
            
            print(f"✅ Keyframed {affected_bone.name} on frame {current_frame - 1}")
            
        except Exception as e:
            print(f"Failed to keyframe previous frame: {e}")
        
        finally:
            # Go back to current frame
            scene.frame_set(current_frame)
            bpy.context.view_layer.update()
    
class A_PT_rigui(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Item'
    bl_label = "A Rig UI"
    bl_idname = "a_PT_rigui"
    
    @classmethod
    def poll(cls, context):
        try:
            return (context.active_object.data.get("rig_id") == rig_id)
        except (AttributeError, KeyError, TypeError):
            return False
        
        

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        """
        # Check if properties exist before accessing
        if not hasattr(context.scene, 'A_rig_props'):
            col.label(text="Properties not loaded. Re-register the addon.")
            return
            
        # Get the properties
        A_props = context.scene.A_rig_props
        """
        # Get pose bones for accessing custom properties
        armature = context.active_object
        pose_bones = armature.pose.bones
        #props_bone = context.object.pose.bones.get("PROPERTIES")
        
        # Use collections_all to access all collections including nested ones
        all_collections = bpy.data.armatures["Armature"].collections_all
        
        box = layout.box()
        row = box.row()
    
        row = box.row(align=True)
        op = row.operator("A_rig.reset_dynamic_pivot", emboss=True, text="RESET PIVOT", icon='SNAP_ON')
        op.parent = 'PIVOT'
        op.child = 'MCH_PIVOT_CHILD'
        op.affected = 'AFFECTED'
    
if __name__ == "__main__":
    bpy.utils.register_class(A_rig_OT_reset_dynamic_pivot)
    bpy.utils.register_class(A_PT_rigui)