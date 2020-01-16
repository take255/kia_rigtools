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

