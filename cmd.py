import numpy as np
import bpy
from bpy.props import FloatProperty

from mathutils import Vector
from mathutils import Matrix
import pickle
import imp

from . import utils
imp.reload(utils)

#RIGSHAPEPATH = "E:\data\googledrive\lib\model/rig.blend"

#---------------------------------------------------------------------------------------
#リグシェイプ
#---------------------------------------------------------------------------------------
def rigshape_change_scale(self,context):
    props = bpy.context.scene.kiarigtools_props        

    utils.mode_p()
    for bone in utils.get_selected_bones():
        bone.custom_shape_scale = props.rigshape_scale/bone.length

def rigshape_revert():
    utils.mode_p()
    #bpy.ops.object.mode_set(mode = 'POSE')
    for bone in utils.get_:
        bone.custom_shape = None

def rigshape_append(filepath):
    #filepath = RIGSHAPEPATH
    current_scene_name = bpy.context.scene.name

    #RigShape_Scn 無ければ作成する
    scene = 'RigShape_Scn'
    if bpy.data.scenes.get(scene) is None:
        bpy.ops.scene.new(type='EMPTY')     
        bpy.context.scene.name = scene

    utils.sceneActive(scene)

    #append object from .blend file
    with bpy.data.libraries.load(filepath) as (data_from, data_to):
        data_to.objects = data_from.objects

    #link object to current scene
    for obj in data_to.objects:
        if obj is not None:
            utils.sceneLink(obj)

    utils.sceneActive(current_scene_name)

# make rig shepe size the same. It makes active bone  basis.
def make_the_same_size():
    selected = utils.bone.get_selected_bones()
    act = utils.bone.get_active_bone()

    basesize = act.length * act.custom_shape_scale
    for b in selected:
        b.custom_shape_scale = basesize/b.length
        #print(b.length)


#---------------------------------------------------------------------------------------
#Change rig control value
#---------------------------------------------------------------------------------------
RIGARRAY = ('arm','leg')
PROPARRAY = {
    # 'arm': ('ikfk','stretch'),
    # 'leg': ('ikfk','stretch')
    'arm': ('ikfk','clav','hand','stretch'),
    'leg': ('ikfk','foot','stretch')

}

def rig_change_ctr(self,context):
    amt = bpy.context.object
    props = bpy.context.scene.kiarigtools_props

    for r in RIGARRAY:
        for p in PROPARRAY[r]:
            for lr in ('l' , 'r'):
                
                ctr = 'ctr.%s.%s' % ( r , lr )

                #if ctr in [o.name for o in bpy.data.objects]:
                if ctr in [b.name for b in amt.pose.bones]:
                    prop ='%s.%s' % (p,lr)
                    prop_val = '%s_%s_%s' % (r,p,lr)
                    #print(ctr , prop , prop_val)
                    exec('amt.pose.bones[\'%s\'][\'%s\'] = props.%s' % ( ctr , prop , prop_val ) ) #amt.pose.bones[ctr.arm.l]['ikfk.l'] = props.arm_ikfk_l'
                    exec('amt.pose.bones[\'%s\'].matrix = amt.pose.bones[\'%s\'].matrix' % (ctr,ctr))  # There is a need to update matrix. 
 
    bpy.context.view_layer.update()


def modify_rig_control_panel( rig , lr , propname , value ):
    amt = bpy.context.object
    props = bpy.context.scene.kiarigtools_props

    ctr = 'ctr.%s.%s' % ( rig , lr )

    if ctr in [b.name for b in amt.pose.bones]:    
        prop = '%s.%s' % ( propname , lr )
        prop_val = '%s_%s_%s' % ( rig , propname , lr )
        print( ctr , prop , prop_val )
        exec('props.%s = %f' % ( prop_val ,value ) ) #amt.pose.bones[ctr.arm.l]['ikfk.l'] = props.arm_ikfk_l'
        exec('amt.pose.bones[\'%s\'][\'%s\'] = %f ' % ( ctr , prop , value ) ) #amt.pose.bones[ctr.arm.l]['ikfk.l'] = props.arm_ikfk_l'
    

def modify_rig_control_panel_key( rig , lr , propname ):
    amt = bpy.context.object
    #props = bpy.context.scene.kiarigtools_props

    ctr = 'ctr.%s.%s' % ( rig , lr )
    prop = '%s.%s' % ( propname , lr )

    bone = amt.pose.bones[ ctr ]
    bone.keyframe_insert(data_path='["%s"]' % prop)

    bpy.context.view_layer.update()
