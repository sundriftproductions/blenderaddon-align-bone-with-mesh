#====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
#======================= END GPL LICENSE BLOCK ========================

from mathutils import *
from bpy.props import *
import bpy
import bmesh
import os

# Version history
# 1.0.0 - 2021-11-29: Original version.
# 1.0.1 - 2021-11-29: Added ability to select armature or object.
# 1.0.2 - 2021-11-30: Added ability to move cursor X to 0. This is important when dealing with a mirrored object; you may want to get in the middle of something that goes across the Z axis.
# 1.0.3 - 2021-12-01: Added controls to move the 3D Cursor.
# 1.0.4 - 2022-05-11: Fixed armature dropdown so it shows actual OBJECTS (unfortunately, both armature objects and mesh objects) instead of the armature "sub-object", which could be a different name.
# 1.0.5 - 2022-05-15: Before it executes the main function, the add-on now checks to make sure we're feeding it an armature object (since we can't filter it at the UI level).
# 1.0.6 - 2022-08-07: Misc formatting cleanup before uploading to GitHub.

###############################################################################
SCRIPT_NAME = 'align_bone_with_mesh'

# An add-on to help with rigging. Intended to be used to speed up the following
# foolproof way to get bone joints to be where they need to be (in the middle
# of a loop):
#           1. Alt+Click on a loop on the body.
#           2. Do a Cursor to Selected.
#           3. Select a bone joint.
#           4. Do a Selected to 3D Cursor.
#
# Instead, this add-on makes the user select the object and the armature, then
# facilitates this workflow (see the instructions on the add-on panel).
#
###############################################################################

bl_info = {
    "name": "Align Bone with Mesh",
    "author": "Jeff Boller",
    "version": (1, 0, 6),
    "blender": (2, 93, 0),
    "location": "View3D > Properties > Rigging",
    "description": 'Helps speed up the process of selecting a mesh loop and making a bone move to the middle of it.',
    "wiki_url": "https://github.com/sundriftproductions/blenderaddon-align-bone-with-mesh/wiki",
    "tracker_url": "https://github.com/sundriftproductions/blenderaddon-align-bone-with-mesh",
    "category": "3D View"}

def select_name( name = "", extend = True ):
    if extend == False:
        bpy.ops.object.select_all(action='DESELECT')
    ob = bpy.data.objects.get(name)
    ob.select_set(state=True)
    bpy.context.view_layer.objects.active = ob

class ALIGNBONEWITHMESH_PT_ToObject(bpy.types.Operator):
    bl_idname = "abwm.to_object"
    bl_label = ""

    def execute(self, context):
        stored_object_name = bpy.context.preferences.addons['align_bone_with_mesh'].preferences.object_name

        # Do a Selection to Cursor.
        bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)

        # Now that we moved the bone, get out of Edit Mode and deselect all objects.
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        # ...and select the object.
        select_name(stored_object_name)

        # ...and go into Edit Mode.
        bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}

class ALIGNBONEWITHMESH_PT_ToArmature(bpy.types.Operator):
    bl_idname = "abwm.to_armature"
    bl_label = ""

    def execute(self, context):
        # Make sure we have valid parameters.
        stored_armature_name = bpy.context.preferences.addons['align_bone_with_mesh'].preferences.armature_name

        if bpy.data.objects.get(stored_armature_name) is None:
            self.report({'ERROR'}, '  ERROR: The armature "' + stored_armature_name + '" in not in the scene. Aborting.')
            return {'CANCELLED'}

        if bpy.data.objects.get(stored_armature_name).type != "ARMATURE":
            self.report({'ERROR'}, '  ERROR: The object "' + stored_armature_name + '" in not an armature. Aborting.')
            return {'CANCELLED'}

        # Set the 3D cursor location.
        bpy.ops.view3d.snap_cursor_to_selected()

        # Now that we've got the cursor in the right place, deselect everything...
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        # ...and select the armature.
        select_name(stored_armature_name)

        # ...and go into Edit Mode.
        bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}

class ALIGNBONEWITHMESH_PT_SelectObject(bpy.types.Operator):
    bl_idname = "abwm.select_object"
    bl_label = ""

    def execute(self, context):
        stored_object_name = bpy.context.preferences.addons['align_bone_with_mesh'].preferences.object_name

        # Get out of Edit Mode and deselect all objects.
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        # ...and select the object.
        select_name(stored_object_name)

        # ...and go into Edit Mode.
        bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}

class ALIGNBONEWITHMESH_PT_SelectArmature(bpy.types.Operator):
    bl_idname = "abwm.select_armature"
    bl_label = ""

    def execute(self, context):
        # Make sure we have valid parameters.
        stored_armature_name = bpy.context.preferences.addons['align_bone_with_mesh'].preferences.armature_name

        if bpy.data.objects.get(stored_armature_name) is None:
            self.report({'ERROR'}, '  ERROR: The armature "' + stored_armature_name + '" in not in the scene. Aborting.')
            return {'CANCELLED'}

        if bpy.data.objects.get(stored_armature_name).type != "ARMATURE":
            self.report({'ERROR'}, '  ERROR: The object "' + stored_armature_name + '" in not an armature. Aborting.')
            return {'CANCELLED'}

        # Deselect everything...
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        # ...and select the armature.
        select_name(stored_armature_name)

        # ...and go into Edit Mode.
        bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}

class ALIGNBONEWITHMESH_PT_3DCursorX0(bpy.types.Operator):
    bl_idname = "abwm.cursorx0"
    bl_label = ""

    def execute(self, context):
        # Set the 3D cursor location.
        bpy.context.scene.cursor.location[0] = 0

        return {'FINISHED'}

class AlignBoneWithMeshPreferencesPanel(bpy.types.AddonPreferences):
    bl_idname = __module__
    object_name: bpy.props.StringProperty(name = 'Object', default = '', description = 'The name of the object we want to align the bone within')
    armature_name: bpy.props.StringProperty(name = 'Armature', default = '', description = 'The name of the armature that has a bone we want to align')

    def draw(self, context):
        self.layout.label(text="Current values")
        self.layout.prop(self, "object_name")

class ALIGNBONEWITHMESH_PT_Main(bpy.types.Panel):
    bl_idname = "ALIGNBONEWITHMESH_PT_Main"
    bl_label = "Align Bone with Mesh"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Rigging"

    def draw(self, context):
        row = self.layout.row(align=True)
        c1a = row.column()
        c2a = row.column()
        c1a.operator("abwm.select_object", text='', icon='TRIA_RIGHT')
        c2a.prop_search(bpy.context.preferences.addons['align_bone_with_mesh'].preferences, "object_name", bpy.data, "objects", icon='OBJECT_DATA')

        row = self.layout.row(align=True)
        row = self.layout.row(align=True)
        c1b = row.column()
        c2b = row.column()
        c1b.operator("abwm.to_object", text='To Object', icon='TRIA_UP')
        c2b.operator("abwm.to_armature", text='To Armature', icon='TRIA_DOWN')

        row = self.layout.row(align=True)
        row = self.layout.row(align=True)

        c1c = row.column()
        c2c = row.column()
        c1c.operator("abwm.select_armature", text='', icon='TRIA_RIGHT')
        c2c.prop_search(bpy.context.preferences.addons['align_bone_with_mesh'].preferences, "armature_name", bpy.data, "objects", icon='OUTLINER_OB_ARMATURE')
        armature = bpy.data.armatures.get(bpy.context.preferences.addons['align_bone_with_mesh'].preferences.armature_name)

        stored_armature_name = bpy.context.preferences.addons['align_bone_with_mesh'].preferences.armature_name
        stored_object_name = bpy.context.preferences.addons['align_bone_with_mesh'].preferences.object_name

        c1b.enabled = False
        c2b.enabled = False
        c1a.enabled = False
        c1c.enabled = False

        editing_object_or_armature = False
        if len(bpy.context.selected_objects) == 1:
            if bpy.data.objects.get(stored_armature_name) is not None and bpy.data.objects.get(stored_object_name) is not None:
                if bpy.context.active_object.mode == 'EDIT':
                    for o in bpy.context.selected_objects:
                        if o.name == stored_armature_name:
                            c1b.enabled = True
                            c1a.enabled = True
                            editing_object_or_armature = True
                        elif o.name == stored_object_name:
                            c2b.enabled = True
                            c1c.enabled = True
                            editing_object_or_armature = True
            if editing_object_or_armature == False:
                if bpy.data.objects.get(stored_armature_name) is not None:
                    c1a.enabled = True
                if bpy.data.objects.get(stored_object_name) is not None:
                    c1c.enabled = True
        else: # We should be allowed to just SELECT either the armature or object if they exist in the scene.
            if bpy.data.objects.get(stored_armature_name) is not None:
                c1a.enabled = True
            if bpy.data.objects.get(stored_object_name) is not None:
                c1c.enabled = True

        row = self.layout.row(align=True)
        row = self.layout.row(align=True)
        box = self.layout.box()
        row = box.row()
        cursor = context.scene.cursor
        row.column().prop(cursor, "location", text="3D Cursor Location")
        row = box.row()
        row = box.row()
        row.operator("abwm.cursorx0", text='Set 3D Cursor X=0', icon='CURSOR')

        row = self.layout.row(align=True)
        row = self.layout.row(align=True)
        box = self.layout.box()
        row = box.row()
        row.scale_y = 0.6
        row.label(text="Select a loop in Object (in Edit")
        row = box.row()
        row.scale_y = 0.6
        row.label(text="   Mode), click 'To Armature' to do")
        row = box.row()
        row.scale_y = 0.6
        row.label(text="   a Cursor to Selected and switch")
        row = box.row()
        row.scale_y = 0.6
        row.label(text="   to Armature (in Edit Mode).")
        row = box.row()
        row.scale_y = 0.6
        row.label(text="Select a bone in Armature, click")
        row = box.row()
        row.scale_y = 0.6
        row.label(text="   'To Object' to do a Selected to")
        row = box.row()
        row.scale_y = 0.6
        row.label(text="   Cursor and switch to Object (in")
        row = box.row()
        row.scale_y = 0.6
        row.label(text="   Edit Mode).")
        row = box.row()
        row.scale_y = 0.6
        row.label(text="Press the > icon next to Object or")
        row = box.row()
        row.scale_y = 0.6
        row.label(text="   Armature to select and jump")
        row = box.row()
        row.scale_y = 0.6
        row.label(text="   into Edit Mode.")

def register():
    bpy.utils.register_class(AlignBoneWithMeshPreferencesPanel)
    bpy.utils.register_class(ALIGNBONEWITHMESH_PT_ToArmature)
    bpy.utils.register_class(ALIGNBONEWITHMESH_PT_ToObject)
    bpy.utils.register_class(ALIGNBONEWITHMESH_PT_SelectArmature)
    bpy.utils.register_class(ALIGNBONEWITHMESH_PT_SelectObject)
    bpy.utils.register_class(ALIGNBONEWITHMESH_PT_3DCursorX0)
    bpy.utils.register_class(ALIGNBONEWITHMESH_PT_Main)

def unregister():
    bpy.utils.unregister_class(AlignBoneWithMeshPreferencesPanel)
    bpy.utils.unregister_class(ALIGNBONEWITHMESH_PT_ToArmature)
    bpy.utils.unregister_class(ALIGNBONEWITHMESH_PT_ToObject)
    bpy.utils.unregister_class(ALIGNBONEWITHMESH_PT_SelectArmature)
    bpy.utils.unregister_class(ALIGNBONEWITHMESH_PT_SelectObject)
    bpy.utils.unregister_class(ALIGNBONEWITHMESH_PT_3DCursorX0)
    bpy.utils.unregister_class(ALIGNBONEWITHMESH_PT_Main)

if __name__ == "__main__":
    register()
