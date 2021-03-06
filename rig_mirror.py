# rig_mirror.py: intended to automatically complete an armature
# beginning with one half of an armature. NOT COMPLETE!
# SEE README for updates as to functionality.

#  ***** BEGIN GPL LICENSE BLOCK *****
#
# Copyright (C) 2016 Chris Nicoll zeta@chrisnicoll.net
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#  ***** END GPL LICENSE BLOCK *****

bl_info = {
    "name": "Rig Mirror",
    "category": "Rigging",
    "author": "Chris Nicoll",
    "version": (0, 1),
    "blender": (2, 76, 0)
}
# There is more stuff to put in here.

import bpy

class RigMirror(bpy.types.Operator):

    bl_idname = "object.rig_mirror"
    bl_label = "Rig Mirror" # Human friendly name
    bl_options = {'REGISTER', 'UNDO'} # Enable undo


    # Dict of complementary name suffixes.
    suffixes = {".L":".R", ".R":".L", ".l":".r", ".r":".l"}

    def execute(self, context):

        # Get the active object's name (the armature we're working on, one hopes)
        # Check that the active object is indeed an armature:
        if context.active_object.type == 'ARMATURE':

            # Initialize an empty list to hold the names of created bones.
            new_bone_names = []

            # Make sure we're in edit mode
            bpy.ops.object.mode_set(mode='EDIT')
            # Deselect all bones in the armature
            bpy.ops.armature.select_all(action='DESELECT')
            bone_collection = list(context.object.data.edit_bones) # Now it's a copy
            #print(len(bone_collection))
            epsilon = 0.00001
            side_bones = [bone for bone in bone_collection if not (bone.head[0] < epsilon and bone.tail[0] < epsilon)]

            # Need bones to have side extensions on names:
            self.rename_old_bones(side_bones)

            # Stop if there are already any bones matching names we will give to new bones;
            # this may mean that the armature is already symmetric, or some other complication.
            if self.check_name_conflict(side_bones) == False:
                print("no naming conflicts at all")
                '''At this point can use bpy.ops.armature.symmetrize() in edit mode with all bones selected.'''
                # Select all bones.
                bpy.ops.armature.select_all(action='SELECT')
                bpy.ops.armature.symmetrize()
                context.scene.update() # To show what we've done in the viewport

                # Next we need to manipulate constraints in pose mode.
                bpy.ops.object.mode_set(mode='POSE')

                # The symmetrize() operation left the new bones all selected.
                # Will we need this list? Or just unselect all?
                new_bones = list(context.selected_pose_bones)
                print(new_bones)
                bpy.ops.pose.select_all(action='DESELECT')
                #pose_bone_collection = list(context.object.pose.bones)
                #print(pose_bone_collection)
                #side_pose_bones = [context.object.pose.bones[bone.name] for bone in side_bones]
                #[print(bone.name) for bone in side_pose_bones]
                [self.mirror_constraints(bone) for bone in new_bones]

        else: print("The active object isn't an armature.")
        return {'FINISHED'}

    # Helper function(s)
    def rename_old_bones(self, existing_bones):
        '''If a bone's tail is at x <> 0, and its name has no side indicator,
        this function will give it a .L or .R ending'''
        for bone in existing_bones:
            suffix = bone.name[-2:]
            new_suffix = self.suffixes.get(suffix)
            if not new_suffix: # i.e. wasn't one of the dict keys
                # Assume it's the lhs that's been constructed even if not labelled
                #print("Bone " + bone.name + " has head at " + str(bone.head) + " and tail at " + str(bone.tail) + " and didn't have a .L/.l or .R/.r suffix")
                prefix = bone.name
                if bone.tail[0] > 0: # bone tail is on the LHS
                    bone.name = prefix + ".L"
                elif bone.tail[0] < 0: # bone tail is on the RHS
                    bone.name = prefix + ".R"


    def check_name_conflict(self, existing_bones):
        '''Checks all the names we want to use for mirrored bones against
        existing bone names.'''
        bone_names = [bone.name for bone in existing_bones]
        for bone in existing_bones:
            if self.get_mirrored_name(bone) in bone_names:
                print("There is a naming conflict with an existing bone")
                return True
            else:
                #print("No naming conflict")
                return False

    def get_mirrored_name(self, bone):
        prefix = bone.name[:-2]
        suffix = bone.name[-2:]
        new_suffix = self.suffixes.get(suffix)
        if new_suffix:
            mirrored_name = prefix + new_suffix
            return mirrored_name
        else:
            print("The original bone doesn't have a side suffix")

    def mirror_constraints(self, bone):
        # Only has to change limits depending on how thorough the symmetrize
        # operation was with constraints. This could be pretty simple if the IK targets
        # are already taken care of.

        # I think this is going to be much different from (and easier than)
        # what I'd originally planned, because the armature symmetrize operation already
        # does half the work.
        print("Bone: " + bone.name)
        # bone is the one to copy the constraint FROM.
        for constraint in bone.constraints:
            print("Constraint: " + str(constraint))
            if constraint.type == 'LIMIT_ROTATION':
                print("That's a limit rotation constraint")
                # If it's limit rotation, want to:
                # Keep x min and max the same. For y and z local axes,
                # magnitudes of min and max need to be switched.
                min_y_orig = constraint.min_y
                max_y_orig = constraint.max_y
                min_z_orig = constraint.min_z
                max_z_orig = constraint.max_z
                constraint.min_y = -max_y_orig
                constraint.max_y = -min_y_orig
                constraint.min_z = -max_z_orig
                constraint.max_z = -min_z_orig
            elif constraint.type == 'LIMIT_LOCATION':
                print("That's a limit location constraint")
                # If it's limit location, flip the x limits
                min_x_orig = constraint.min_x
                max_x_orig = constraint.max_x
                constraint.min_x =  -max_x_orig
                constraint.max_x = -min_x_orig

        # For now, ignore all other kinds of constraints.
        # I haven't detected any need to modify IK constraints

class RigMirrorPanel(bpy.types.Panel):
    bl_label = "Rig Mirror"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"


    def draw(self, context):
        self.layout.label(text="Hello World")

def register():
    bpy.utils.register_class(RigMirror)

    bpy.utils.register_class(RigMirrorPanel)


def unregister():
    bpy.utils.unregister_class(RigMirror)
    bpy.utils.unregister_class(RigMirrorPanel)


if __name__ == "__main__":
    register()

# Register the operator class so it can be used in Blender
#bpy.utils.register_class(RigMirror)

# Run it
#bpy.ops.object.rig_mirror()
