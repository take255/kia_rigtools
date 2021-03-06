# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
import bpy
import imp
from bpy.app.handlers import persistent


from bpy.types import( 
    PropertyGroup,
    Panel,
    Operator,
    UIList,
    AddonPreferences
    )

from bpy.props import(
    FloatProperty,
    PointerProperty,
    CollectionProperty,
    EnumProperty,
    BoolProperty,
    StringProperty,
    IntProperty
    )

from . import utils
from . import cmd
from . import setup_ik
from . import edit
from . import renamer
from . import duplicator
from . import constraint

imp.reload(utils)
imp.reload(cmd)
imp.reload(setup_ik)
imp.reload(edit)
imp.reload(renamer)
imp.reload(duplicator)
imp.reload(constraint)


bl_info = {
"name": "kia_rigtools",
"author": "kisekiakeshi",
"version": (0, 1),
"blender": (2, 80, 0),
"description": "kia_rigtools",
"category": "Object"}

RIGSHAPEPATH = "E:\data\googledrive\lib\model/rig.blend"

#---------------------------------------------------------------------------------------
#アーマチュアを拾ってリグコントロールに使う
#
#---------------------------------------------------------------------------------------
#
#ボーンを選択順で拾うためのハンドラ <<　ボーンを選択順で拾う必要がなくなった
#エディットモードだと更新されないので、選択順をとるならポーズモードでとるしかない
#ツールの基本的な処理は、ポーズモードならallbonesで処理、エディットモードなら現在の選択をcontextから取得して処理する
#---------------------------------------------------------------------------------------

@persistent
def kiarigtools_handler(scene):
    return
    props = bpy.context.scene.kiarigtools_props
    amt = utils.getActiveObj()
    if amt == None:
        props.armature_name = ''
        return
    elif amt.type != 'ARMATURE':
        props.armature_name = ''
        return

    props.armature_name = amt.name


    #amt = bpy.data.objects["Armature"]
    # for b in amt.pose.bones:
    #     if b.name == 'ctr.arm.l':
    #         val = b.get('ikfk_l')
    #         if val != None:
    #             props.arm_ikfk_l = val
            # arm_stretch_l : FloatProperty( name = "stretch_l", min=0.001 , max=1.0, default=1.0)
            # arm_ikfk_l : FloatProperty( name = "ikfk_l", min=0.0 , max=1.0, default=1.0)

            #print(b.ikfk_l)


    # if props.handler_through:
    #     return

    # if utils.current_mode() == 'OBJECT':
    #     return

    selected = utils.get_selected_bones()
    #ボーンが何も選択されていなければリストをクリアする
    if selected == []:
        props.allbones.clear()

    else:
        if utils.current_mode() == 'POSE':
            act_bone = bpy.context.active_pose_bone.name
        elif utils.current_mode() == 'EDIT':
            #print(bpy.context.active_bone.name)
            act_bone = bpy.context.active_bone.name
            

        index_notExists = []
        #すでに選択されているものをアクティブにした場合、リストにあるものを削除して最後に追加する
        for i , bone in enumerate(props.allbones):
            if act_bone == bone.name:
                index_notExists.append(i)
            
        props.allbones.add().name = act_bone

        #選択されていなければリストから外す removeはインデックスで指定        
        for i , bone in enumerate(props.allbones):
            if not bone.name in [x.name for x in selected]:
                index_notExists.append(i)


        for index in reversed(index_notExists):
             props.allbones.remove(index)


        # print(utils.get_selected_bones())
        # for bone in props.allbones:
        #     print(bone.name)


#---------------------------------------------------------------------------------------
#Props
#---------------------------------------------------------------------------------------        
class KIARIGTOOLS_Props_OA(PropertyGroup):
    handler_through : BoolProperty(default = False)

    allbones : CollectionProperty(type=PropertyGroup)
    rigshape_scale : FloatProperty( name = "scale", min=0.01,default=1.0, update = cmd.rigshape_change_scale )
    setupik_lr : EnumProperty(items= (('l', 'l', 'L'),('r', 'r', 'R')))
    setupik_number : IntProperty(name="count", default=2)
    ploc_number : IntProperty(name="count", default=2)
    setup_chain_baseame : StringProperty( name = 'name' )
    parent_polevector : BoolProperty()

    #コンストレイン関連
    const_influence : FloatProperty( name = "influence", min=0.00 , max=1.0, default=1.0, update= edit.constraint_showhide )
    const_showhide : BoolProperty( name = 'mute', update = edit.constraint_change_influence )

    #リグのコントロール
    armature_name : StringProperty( name = 'armature' )

    axismethod : EnumProperty(items= (('new', 'new', 'new'),('old', 'old', 'old')))

    for r in cmd.RIGARRAY:
        for p in cmd.PROPARRAY[r]:
            for lr in ('l' , 'r'):
                prop_val = '%s_%s_%s' % (r,p,lr)
                exec('%s : FloatProperty(  name = \"%s\",min=0.0 , max=1.0, default=1.0 , update = cmd.rig_change_ctr )' % ( prop_val ,lr ) )

    # arm_stretch_l : FloatProperty(  name = "l",min=0.0 , max=1.0, default=1.0 , update = cmd.rig_change_ctr )
    # arm_stretch_r : FloatProperty( name = "r", min=0.0 , max=1.0, default=1.0 , update = cmd.rig_change_ctr )
    # arm_ikfk_l : FloatProperty( name = "l", min=0.0 , max=1.0, default=1.0 , update = cmd.rig_change_ctr )
    # arm_ikfk_r : FloatProperty( name = "r", min=0.0 , max=1.0, default=1.0 , update = cmd.rig_change_ctr )

    # leg_stretch_l : FloatProperty(  name = "l",min=0.0 , max=1.0, default=1.0 , update = cmd.rig_change_ctr )
    # leg_stretch_r : FloatProperty( name = "r", min=0.0 , max=1.0, default=1.0 , update = cmd.rig_change_ctr )
    # leg_ikfk_l : FloatProperty( name = "l", min=0.0 , max=1.0, default=1.0 , update = cmd.rig_change_ctr )
    # leg_ikfk_r : FloatProperty( name = "r", min=0.0 , max=1.0, default=1.0 , update = cmd.rig_change_ctr )




#---------------------------------------------------------------------------------------
#UI
#---------------------------------------------------------------------------------------
class KIARIGTOOLS_PT_ui(utils.panel):
    bl_label = "kia rigtools"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        props = bpy.context.scene.kiarigtools_props        

        col = self.layout.column(align=False)
        col.label(text = 'select bone into ! Posemode !')        
        col.operator("kiarigtools.rigsetuptools",icon = 'OBJECT_DATA')
        col.operator("kiarigtools.edittools",icon = 'OBJECT_DATA')
        col.operator("kiarigtools.renamer",icon = 'OBJECT_DATA')
        col.operator("kiarigtools.duplicator",icon = 'OBJECT_DATA')
        col.operator("kiarigtools.constrainttools",icon = 'OBJECT_DATA')
        col.operator("kiarigtools.rigcontrolpanel",icon = 'OBJECT_DATA')


#---------------------------------------------------------------------------------------
#リグセットアップツール
#---------------------------------------------------------------------------------------
class KIARIGTOOLS_MT_rigcontrolpanel(bpy.types.Operator):
    bl_idname = "kiarigtools.rigcontrolpanel"
    bl_label = "rig control panel"

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        props = bpy.context.scene.kiarigtools_props
        amt = utils.getActiveObj()
        if amt == None:
            props.armature_name = ''
            return
        elif amt.type != 'ARMATURE':
            props.armature_name = ''
            return

        props.armature_name = amt.name

        for part in ('arm', 'leg'):
            for lr in ('l', 'r'):
                name = 'ctr.%s.%s' % (part , lr)

                if name in [b.name for b in amt.pose.bones]:
                    bone = amt.pose.bones[name]
                    val = bone.get('ikfk_%s' % lr )
                    if val != None:
                        exec('props.%s_ikfk_%s = val' % ( part , lr ))

        # for b in amt.pose.bones:
        #     if b.name == 'ctr.arm.l':
        #         val = b.get('ikfk_l')
        #         if val != None:
        #             props.arm_ikfk_l = val
        #         val = b.get('stretch_l')
        #         if val != None:
        #             props.arm_ikfk_l = val


        #     elif b.name == 'ctr.arm.r':
        #         val = b.get('ikfk_r')
        #         if val != None:
        #             props.arm_ikfk_r = val

        return context.window_manager.invoke_props_dialog(self , width=400)


    def draw(self, context):
        props = bpy.context.scene.kiarigtools_props        

        col = self.layout.column(align=False)

        box = col.box()
        #box.label(text = 'rigtool')

        box.prop(props, "armature_name")
        row = box.row()
        row.operator("kiarigtools.posetool_copy_matrix",icon = 'OBJECT_DATA')
        row.operator("kiarigtools.posetool_paste_matrix",icon = 'OBJECT_DATA')

        row  = col.column()
        # rig_ui( props ,  row , 'arm' , 'l')
        # rig_ui( props ,  row , 'leg' , 'l')

        box = row.box()
        row = box.row()

        for r in cmd.RIGARRAY:
            box1 = row.box()
            box1.label(text = r )

            for p in cmd.PROPARRAY[ r ]:
                box2 = box1.box()
                box2.label(text = p )

                for lr in ('l' , 'r'):
                    propname = "%s_%s_%s"  % (r , p , lr)
                    col = box2.column()
                    row1 = col.row()
                    row1.prop(props, propname )

                    cmd1 = row1.operator("kiarigtools.modify_rig_control_panel",icon = 'TRIA_DOWN')
                    cmd1.rig = r
                    cmd1.lr = lr
                    cmd1.propname = p
                    cmd1.value = 0.0

                    cmd1 = row1.operator("kiarigtools.modify_rig_control_panel",icon = 'TRIA_UP')
                    cmd1.rig = r
                    cmd1.lr = lr
                    cmd1.propname = p
                    cmd1.value = 100.0

                    cmd1 = row1.operator("kiarigtools.modify_rig_control_panel_key",icon = 'REC')
                    cmd1.rig = r
                    cmd1.lr = lr
                    cmd1.propname = p


def rig_ui_( props , row , parts , lr ):
    #row = box.row()
    box1 = row.box()
    box1.label(text = '%s' % parts )

    box2 = box1.box()
    box2.label(text = 'ikfk')

    col = box2.column()
    row = col.row()
    row.prop(props, "%s_ikfk_%s"  % (parts , 'l') )
    row.operator("kiarigtools.rigctr_arm",icon = 'OBJECT_DATA')
    row.operator("kiarigtools.rigctr_arm",icon = 'OBJECT_DATA')

    col = box2.column()
    row = col.row()
    row.prop(props, "%s_ikfk_%s"  % (parts , 'r') )
    row.operator("kiarigtools.rigctr_arm",icon = 'OBJECT_DATA')
    row.operator("kiarigtools.rigctr_arm",icon = 'OBJECT_DATA')


    box2 = box1.box()
    box2.label(text = 'stretch')

    col = box2.column()
    row = col.row()
    row.prop(props, "%s_stretch_%s"  % (parts , 'l') )
    row.operator("kiarigtools.rigctr_arm",icon = 'OBJECT_DATA')
    row.operator("kiarigtools.rigctr_arm",icon = 'OBJECT_DATA')

    col = box2.column()
    row = col.row()
    row.prop(props, "%s_stretch_%s"  % (parts , 'r') )
    row.operator("kiarigtools.rigctr_arm",icon = 'OBJECT_DATA')
    row.operator("kiarigtools.rigctr_arm",icon = 'OBJECT_DATA')



    # box3 = box1.box()
    # box3.label(text = 'ikfk')
    # row = box3.row()
    # row.prop(props, "%s_ikfk_%s"  % (parts , lr) )
    # row.operator("kiarigtools.rigctr_arm",icon = 'OBJECT_DATA')
    # row.operator("kiarigtools.rigctr_arm",icon = 'OBJECT_DATA')

    # box3 = box1.box()
    # box3.label(text = 'ikfk')
    # row = box3.row()
    # row.prop(props, "%s_ikfk_%s"  % (parts , lr) )
    # row.operator("kiarigtools.rigctr_arm",icon = 'OBJECT_DATA')
    # row.operator("kiarigtools.rigctr_arm",icon = 'OBJECT_DATA')



#---------------------------------------------------------------------------------------
#UI Preference
#---------------------------------------------------------------------------------------
class KIARIGTOOLS_MT_addonpreferences(AddonPreferences):
    bl_idname = __name__
 
    shape_path : StringProperty(default = RIGSHAPEPATH )

    def draw(self, context):
        layout = self.layout
        layout.label(text='Rig Shape Path')
        col = layout.column()
        col.prop(self, 'shape_path',text = 'shape_path', expand=True)


#---------------------------------------------------------------------------------------
#リグセットアップツール
#---------------------------------------------------------------------------------------
class KIARIGTOOLS_MT_rigsetuptools(bpy.types.Operator):
    bl_idname = "kiarigtools.rigsetuptools"
    bl_label = "rig setup"

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        props = bpy.context.scene.kiarigtools_props        

        col_root = self.layout.column(align=False)
        box = col_root.box()
        box.prop(props,'axismethod')



        #row = self.layout.row(align=False)
        row = col_root.row(align=False)
        box = row.box()

        box.label(text = 'rigshape')
        #row1 = box.row(align=True)
        #row1.alignment = 'EXPAND'
        box.operator("kiarigtools.rigshape_selector",icon = 'OBJECT_DATA')
        box.operator("kiarigtools.rigshape_revert",icon = 'BONE_DATA')
        box.prop(props, "rigshape_scale", icon='BLENDER', toggle=True)
        box.operator("kiarigtools.rigshape_append")
        box.operator("kiarigtools.make_the_same_size")
    

        col = row.column()

        box = col.box()
        box.label(text = 'rig')
        box.prop(props,'setup_chain_baseame')
        row1 = box.row()
        row1.operator("kiarigtools.setupik_customrig",text = 'ik').mode = 'ik'
        row1.prop(props, "parent_polevector")

        row1 = box.row()
        row1.operator("kiarigtools.setupik_customrig",text = 'knee').mode = 'knee'
        row1.operator("kiarigtools.setupik_customrig",text = 'transform').mode = 'transform'

        row1 = box.row()
        row1.operator("kiarigtools.setupik_customrig",text = 'ploc').mode = 'ploc'
        row1.prop(props, "ploc_number")


        box.operator("kiarigtools.setupik_setup_rig_chain")


        box = col.box()
        box.label(text = 'setup ik')
        row1 = box.row()
        row1.operator("kiarigtools.setupik_ik").mode = 1
        row1.prop(props, "setupik_number")

        box.operator("kiarigtools.setupik_polevector")
        box.operator("kiarigtools.setupik_spline_ik")
        box.operator("kiarigtools.setupik_hook")


        box = col.box()
        box.label(text = 'setup for UE')
        box.operator("kiarigtools.setupik_ue")


        box = row.box()
        box.label(text = 'body')
        box.operator("kiarigtools.setupik_rig_arm")
        box.operator("kiarigtools.setupik_rig_leg")
        box.operator("kiarigtools.setupik_rig_spine")
        box.operator("kiarigtools.setupik_rig_spine_v2")
        box.operator("kiarigtools.setupik_rig_spine_v3")
        box.operator("kiarigtools.setupik_rig_neck")
        box.operator("kiarigtools.setupik_rig_neck_v2")
        box.operator("kiarigtools.setupik_rig_finger")
        box.prop(props, "setupik_lr", expand=True)


#---------------------------------------------------------------------------------------
#エディットツール
#---------------------------------------------------------------------------------------
class KIARIGTOOLS_MT_edittools(bpy.types.Operator):
    bl_idname = "kiarigtools.edittools"
    bl_label = "edit"

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        props = bpy.context.scene.kiarigtools_props        
        props.handler_through = False
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        props = bpy.context.scene.kiarigtools_props        

        col_root = self.layout.column(align=False)
        box = col_root.box()
        box.prop(props,'axismethod')

        row = col_root.split(factor = 0.3, align = False)

        #row = col_root.row()
        col = row.box()

        box = col.box()
        box.label(text = 'length')
        box.operator("kiarigtools.edit_length_uniform")
        box.operator("kiarigtools.edit_length_half")

        box = col.box()
        box.label(text = 'modify')
        box.operator("kiarigtools.edit_genarate_symmetry")


        box = col.box()
        box.label(text = 'generate')
        box.operator("kiarigtools.edit_genarate_bone_from2")

        box = row.box()
        col1 = box.column()
        row1 = col1.row()
        box1 = row1.box()
        box1.label(text = 'align')
        box1.operator("kiarigtools.edit_align_position")
        box1.operator("kiarigtools.edit_align_direction")
        box1.operator("kiarigtools.edit_align_along")
        box1.operator("kiarigtools.edit_align_near_axis")

        box1 = row1.box()
        box1.label(text = 'align plane')
        box1.operator("kiarigtools.edit_align_2axis_plane")
        box1.operator("kiarigtools.edit_align_on_plane")
        box1.operator("kiarigtools.edit_align_at_flontview")


        #box = col_root.box()
        box = col1.box()
        box.label(text = 'direction')
        col = box.column()

        box1 = col.box()
        box1.label(text = 'roll')

        row = box1.row()
        for x in ( '90d' , '-90d' , '180d'):
            row.operator("kiarigtools.edit_roll_degree" ,text = x ).op = x

        box1 = col.box()
        box1.label(text = 'axis swap')

        row = box1.row()
        for x in ( 'x' , 'y' , 'z' ,'invert'):
            row.operator("kiarigtools.edit_axis_swap" ,text = x ).op = x


        row = col.row()
        row.operator("kiarigtools.edit_adjust_roll")
        row.operator("kiarigtools.edit_align_roll_global")
            
        box = col_root.box()
        box.label(text = 'constraint')
        split = box.split(factor = 0.5, align = False)
        col = split.column()
        col.prop(props,"const_influence")
        col.prop(props,"const_showhide")

        box = split.box()
        box.label(text = 'delete')
        row = box.row()
        row.operator("kiarigtools.edit_constraint_cleanup")
        row.operator("kiarigtools.edit_constraint_empty_cleanup")

        box = col_root.box()
        box.label(text = 'other commands')
        row = box.row()
        row.operator("kiarigtools.edit_connect_chain")
        row.operator("kiarigtools.edit_delete_rig")


#---------------------------------------------------------------------------------------
#リグシェイプUI : シーンからリグシェイプを検索してポップアップに登録
#---------------------------------------------------------------------------------------
class KIARIGTOOLS_PT_rigshape_selector(bpy.types.Operator):
    """選択した骨をリストのシェイプに置き換える"""
    bl_idname = "kiarigtools.rigshape_selector"
    bl_label = "replace"
    bl_options = {'REGISTER', 'UNDO'}

    prop : bpy.props.StringProperty(name="RigShape", maxlen=63)
    rigshapes : bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)

    def execute(self, context):
        utils.mode_p()
        for bone in bpy.context.selected_pose_bones:
            obj = bpy.data.objects[self.prop]
            bone.custom_shape = obj

        utils.mode_e()
        for bone in bpy.context.selected_bones:
            bone.show_wire = True

        utils.mode_p()
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.prop_search(self, "prop", self, "rigshapes", icon='MESH_DATA')

    def invoke(self, context, event):
        self.rigshapes.clear()
        for obj in bpy.data.objects:
            if obj.name.find('rig.shape.') != -1:
                self.rigshapes.add().name = obj.name
        return context.window_manager.invoke_props_dialog(self)


#---------------------------------------------------------------------------------------
# Operator
#---------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------
# Rig Shape
#---------------------------------------------------------------------------------------
#リグシェイプを通常のボーンに戻す
class KIARIGTOOLS_OT_rigshape_revert(bpy.types.Operator):
    """リグシェイプを通常のボーンに戻す"""
    bl_idname = "kiarigtools.rigshape_revert"
    bl_label = "revert"
    def execute(self, context):
        cmd.rigshape_revert()
        return {'FINISHED'}

#リグシェイプをRigShape_Scnに入れる
class KIARIGTOOLS_OT_rigshape_append(bpy.types.Operator):
    """リグシェイプをシーンにアペンドする"""
    bl_idname = "kiarigtools.rigshape_append"
    bl_label = "append"
    def execute(self, context):
        prefs = bpy.context.preferences.addons[__name__].preferences
        cmd.rigshape_append( prefs.shape_path )
        return {'FINISHED'}

#Make selected rig shape the same size. The active is the size basis.
class KIARIGTOOLS_OT_make_the_same_size(bpy.types.Operator):
    """Make selected rig shape the same size. The active is the size basis."""
    bl_idname = "kiarigtools.make_the_same_size"
    bl_label = "same size"
    def execute(self, context):
        cmd.make_the_same_size()
        return {'FINISHED'}


#---------------------------------------------------------------------------------------
# setup custom rig
#---------------------------------------------------------------------------------------
class KIARIGTOOLS_OT_setupik_customrig(bpy.types.Operator):
    """Allow you to set up custom rigs.
    ik:
    Add ik controller and pole vector.
    First ,select 2 joint bones, and execute this command.
    
    knee:
    Add knee bone and constraint knee to leg bone.
    First ,select 2 joint bones, and execute this command.

    transform:
    Add simple transform constraint node.
    First ,select a single bone, and execute this command.

    ploc:
    Add procedural rotation node.
    First ,select a single bone, and decide procedural bone number.
    next exeute this command."""

    bl_idname = "kiarigtools.setupik_customrig"
    bl_label = ""
    mode : StringProperty()
    def execute(self, context):
        setup_ik.customrig(self.mode)
        return {'FINISHED'}

#---------------------------------------------------------------------------------------
# setup ik
#---------------------------------------------------------------------------------------
class KIARIGTOOLS_OT_setupik_ik(bpy.types.Operator):
    """IKのセットアップ。ＩＫの先端とコントローラの順にリストに加えて実行する。"""
    bl_idname = "kiarigtools.setupik_ik"
    bl_label = "ik"
    mode : IntProperty()
    def execute(self, context):
        setup_ik.ik(self.mode)
        return {'FINISHED'}

class KIARIGTOOLS_OT_setupik_polevector(bpy.types.Operator):
    """ポールベクターのセットアップ\n根本、先の順に選択する"""
    bl_idname = "kiarigtools.setupik_polevector"
    bl_label = "pole vec"
    def execute(self, context):
        setup_ik.polevector()
        return {'FINISHED'}

class KIARIGTOOLS_OT_setupik_spline_ik(bpy.types.Operator):
    """リストに根本から先端までのボーンを入力する。\nコントローラは自動で生成される。\n先頭のボーンを選択しておくこと。\nベジェカーブが生成されるのでそれでコントロールする。"""
    bl_idname = "kiarigtools.setupik_spline_ik"
    bl_label = "spline ik"  
    def execute(self, context):
        setup_ik.spline_ik()
        return {'FINISHED'}

class KIARIGTOOLS_OT_setupik_hook(bpy.types.Operator):
    """カーブとアーマチュアを選択して実行\nコントローラは自動で生成される"""
    bl_idname = "kiarigtools.setupik_hook"
    bl_label = "hook"
    def execute(self, context):
        setup_ik.hook()
        return {'FINISHED'}

class KIARIGTOOLS_OT_setupik_rig_arm(bpy.types.Operator):
    """腕のリグの自動設定\n鎖骨、上腕、前腕、手の順でリストに並べる"""
    bl_idname = "kiarigtools.setupik_rig_arm"
    bl_label = "arm"
    def execute(self, context):
        setup_ik.setup_rig_arm()
        return {'FINISHED'}

class KIARIGTOOLS_OT_setupik_rig_leg(bpy.types.Operator):
    """脚足のリグの自動設定\n腰、太もも、すね、足、つま先の順でリストに並べる"""
    bl_idname = "kiarigtools.setupik_rig_leg"
    bl_label = "leg"
    def execute(self, context):
        setup_ik.setupik_rig_leg()
        return {'FINISHED'}

class KIARIGTOOLS_OT_setupik_rig_spine(bpy.types.Operator):
    """背骨のリグの自動設定\n腰から胸までの骨を順番にリストに登録して実行"""
    bl_idname = "kiarigtools.setupik_rig_spine"
    bl_label = "spine"
    def execute(self, context):
        setup_ik.setup_rig_spine()
        return {'FINISHED'}

class KIARIGTOOLS_OT_setupik_rig_spine_v2(bpy.types.Operator):
    """背骨のリグの自動設定\n腰から胸までの骨を順番にリストに登録して実行"""
    bl_idname = "kiarigtools.setupik_rig_spine_v2"
    bl_label = "spine v2"
    def execute(self, context):
        setup_ik.setup_rig_spine_v2()
        return {'FINISHED'}

class KIARIGTOOLS_OT_setupik_rig_spine_v3(bpy.types.Operator):
    """背骨のリグの自動設定\n腰から胸までの骨を順番にリストに登録して実行"""
    bl_idname = "kiarigtools.setupik_rig_spine_v3"
    bl_label = "spine v3"
    def execute(self, context):
        setup_ik.setup_rig_spine_v3()
        return {'FINISHED'}

class KIARIGTOOLS_OT_setupik_rig_neck(bpy.types.Operator):
    """首骨のリグの自動設定\n胸の骨、首、頭までの骨を順番にリストに登録して実行"""    
    bl_idname = "kiarigtools.setupik_rig_neck"
    bl_label = "neck"
    def execute(self, context):
        setup_ik.setup_rig_neck()
        return {'FINISHED'}

class KIARIGTOOLS_OT_setupik_rig_neck_v2(bpy.types.Operator):
    """首骨のリグの自動設定:
        胸の骨、首、頭までの骨を順番にリストに登録して実行"""    

    bl_idname = "kiarigtools.setupik_rig_neck_v2"
    bl_label = "neck v2"
    def execute(self, context):
        setup_ik.setup_rig_neck_v2()
        return {'FINISHED'}

class KIARIGTOOLS_OT_setupik_rig_finger(bpy.types.Operator):
    """指のリグの自動設定:
    指のルートボーンを選択して実行する。
    ボーンのフォーマットはindex_01_lで最初と最後の要素を使う。
    できあがるコントローラ名は ctr.index.lとなる。
    tweakノードはctr.tweak.index_01.lとなる。"""    

    bl_idname = "kiarigtools.setupik_rig_finger"
    bl_label = "finger"
    def execute(self, context):
        setup_ik.setup_rig_finger()
        return {'FINISHED'}


class KIARIGTOOLS_OT_setupik_setup_rig_chain(bpy.types.Operator):
    """setup Unreal Engine Rig"""    
    bl_idname = "kiarigtools.setupik_setup_rig_chain"
    bl_label = "assign chain rig"
    def execute(self, context):
        setup_ik.setup_rig_chain()
        return {'FINISHED'}


#setup Unreal Engine Rig
class KIARIGTOOLS_OT_setupik_ue(bpy.types.Operator):
    """setup Unreal Engine Rig"""    
    bl_idname = "kiarigtools.setupik_ue"
    bl_label = "create ue rig"
    def execute(self, context):
        setup_ik.setup_ue()
        return {'FINISHED'}




#---------------------------------------------------------------------------------------
# edit tool
#---------------------------------------------------------------------------------------
class KIARIGTOOLS_OT_edit_length_uniform(bpy.types.Operator):
    """ボーンの長さをそろえる。\n最後に選択されたボーンに他のを合わせる"""
    bl_idname = "kiarigtools.edit_length_uniform"
    bl_label = "uniform"

    def execute(self, context):
        edit.length_uniform()
        return {'FINISHED'}


class KIARIGTOOLS_OT_edit_length_half(bpy.types.Operator):
    """選択されたボーンの長さを半分にする"""
    bl_idname = "kiarigtools.edit_length_half"
    bl_label = "half"
    def execute(self, context):
        edit.length_half()
        return {'FINISHED'}

class KIARIGTOOLS_OT_edit_genarate_bone_from2(bpy.types.Operator):
    """最初に選択したボーンの根本から、最後に選択したボーンの先端までのボーンを生成する"""
    bl_idname = "kiarigtools.edit_genarate_bone_from2"
    bl_label = "gen from 2"
    def execute(self, context):
        edit.genarate_bone_from2()
        return {'FINISHED'}

#複製ではない
class KIARIGTOOLS_OT_edit_genarate_symmetry(bpy.types.Operator):
    """ネーミングルールでミラーリングする。エディットモードでコピー元のボーンを選択して実行する。"""
    bl_idname = "kiarigtools.edit_genarate_symmetry"
    bl_label = "symmetry"
    def execute(self, context):
        edit.genarate_symmetry()
        return {'FINISHED'}

class KIARIGTOOLS_OT_edit_align_position(bpy.types.Operator):
    """アクティブなジョイントの位置に、それ以外のジョイントの位置を合わせる。"""
    bl_idname = "kiarigtools.edit_align_position"
    bl_label = "position"
    def execute(self, context):
        edit.align_position()
        return {'FINISHED'}

class KIARIGTOOLS_OT_edit_align_direction(bpy.types.Operator):
    """アクティブなジョイントの向きに、それ以外のジョイントの向きを合わせる。"""
    bl_idname = "kiarigtools.edit_align_direction"
    bl_label = "direction"
    def execute(self, context):
        edit.align_direction()
        return {'FINISHED'}

class KIARIGTOOLS_OT_edit_align_along(bpy.types.Operator):
    """リストの最初のボーン上に以降のボーンを並べる"""
    bl_idname = "kiarigtools.edit_align_along"
    bl_label = "along"
    def execute(self, context):
        edit.align_along()
        return {'FINISHED'}

class KIARIGTOOLS_OT_edit_aling_near_axis(bpy.types.Operator):
    """近いグローバルび軸にボーンを向ける。\nボーンを選択して実行する。"""
    bl_idname = "kiarigtools.edit_align_near_axis"
    bl_label = "near axis"
    def execute(self, context):
        edit.align_near_axis()
        return {'FINISHED'}

class KIARIGTOOLS_OT_edit_align_2axis_plane(bpy.types.Operator):
    """２ボーンの平面を出して軸向きを合わせる"""
    bl_idname = "kiarigtools.edit_align_2axis_plane"
    bl_label = "2axis plane"
    def execute(self, context):
        edit.along_2axis_plane()
        return {'FINISHED'}

class KIARIGTOOLS_OT_edit_align_on_plane(bpy.types.Operator):
    """リストの1番目と２番目の基準平面にそれ以下のボーンをそろえる。"""
    bl_idname = "kiarigtools.edit_align_on_plane"
    bl_label = "on plane"
    def execute(self, context):
        edit.align_on_plane()
        return {'FINISHED'}

class KIARIGTOOLS_OT_edit_align_at_flontview(bpy.types.Operator):
    """正面から見たときにジョイントが直線に並ぶようにそろえる\nポーズモードで選択すること"""
    bl_idname = "kiarigtools.edit_align_at_flontview"
    bl_label = "frontview"
    def execute(self, context):
        edit.align_at_flontview()
        return {'FINISHED'}

class KIARIGTOOLS_OT_edit_adjust_roll(bpy.types.Operator):
    """リストから選択したものとその下のボーンでロール値を調整。\nいっぺんにすべてのボーンのロール修正ができないので２本ずつおこなう。"""
    bl_idname = "kiarigtools.edit_adjust_roll"
    bl_label = "adjust"
    def execute(self, context):
        edit.adjust_roll()
        return {'FINISHED'}

class KIARIGTOOLS_OT_edit_roll_degree(bpy.types.Operator):
    """ロールを90°回転させる。"""
    bl_idname = "kiarigtools.edit_roll_degree"
    bl_label = ""
    op : StringProperty()
    def execute(self, context):
        edit.roll_degree(self.op)
        return {'FINISHED'}

class KIARIGTOOLS_OT_edit_align_roll_global(bpy.types.Operator):
    """グローバル軸にX,Z軸向きをそろえる"""
    bl_idname = "kiarigtools.edit_align_roll_global"
    bl_label = "align global"
    def execute(self, context):
        edit.align_roll_global
        return {'FINISHED'}

class KIARIGTOOLS_OT_edit_axis_swap(bpy.types.Operator):
    """ロールを90°回転させる。"""
    bl_idname = "kiarigtools.edit_axis_swap"
    bl_label = ""
    op : StringProperty()
    def execute(self, context):
        edit.axis_swap(self.op)
        return {'FINISHED'}

#---------------------------------------------------------------------------------------
# rig control panel
#---------------------------------------------------------------------------------------
class KIARIGTOOLS_OT_rigctr_arm(bpy.types.Operator):
    """リグ"""
    bl_idname = "kiarigtools.rigctr_arm"
    bl_label = ""
    def execute(self, context):
        edit.align_roll_global
        return {'FINISHED'}

class KIARIGTOOLS_OT_modify_rig_control_panel(bpy.types.Operator):
    """modify rig control panel value"""
    bl_idname = "kiarigtools.modify_rig_control_panel"
    bl_label = ""
    rig : StringProperty()
    lr : StringProperty()
    propname : StringProperty()
    value : FloatProperty()
    def execute(self, context):
        cmd.modify_rig_control_panel( self.rig , self.lr , self.propname , self.value )
        return {'FINISHED'}

class KIARIGTOOLS_OT_modify_rig_control_panel_key(bpy.types.Operator):
    """keying rig custom property"""
    bl_idname = "kiarigtools.modify_rig_control_panel_key"
    bl_label = ""
    rig : StringProperty()
    lr : StringProperty()
    propname : StringProperty()
    def execute(self, context):
        cmd.modify_rig_control_panel_key( self.rig , self.lr , self.propname)
        return {'FINISHED'}

#pose tool : matrix copy paste
class KIARIGTOOLS_OT_posetool_copy_matrix(bpy.types.Operator):
    """keying rig custom property"""
    bl_idname = "kiarigtools.posetool_copy_matrix"
    bl_label = "copy"
    def execute(self, context):
        cmd.copy_matrix()
        return {'FINISHED'}

class KIARIGTOOLS_OT_posetool_paste_matrix(bpy.types.Operator):
    """keying rig custom property"""
    bl_idname = "kiarigtools.posetool_paste_matrix"
    bl_label = "paste"
    def execute(self, context):
        cmd.paste_matrix()
        return {'FINISHED'}


#---------------------------------------------------------------------------------------
# constraint tool
#---------------------------------------------------------------------------------------
class KIARIGTOOLS_OT_edit_constraint_cleanup(bpy.types.Operator):
    """選択された複数ボーンのコンストレインをすべて削除する"""
    bl_idname = "kiarigtools.edit_constraint_cleanup"
    bl_label = "all"
    def execute(self, context):
        edit.constraint_cleanup()
        return {'FINISHED'}

class KIARIGTOOLS_OT_edit_constraint_cleanup_empty(bpy.types.Operator):
    """選択された複数ボーンの空のコンストレインを削除する"""
    bl_idname = "kiarigtools.edit_constraint_empty_cleanup"
    bl_label = "empty"
    def execute(self, context):
        edit.constraint_cleanup_empty()
        return {'FINISHED'}


#---------------------------------------------------------------------------------------
# other tools
#---------------------------------------------------------------------------------------
class KIARIGTOOLS_OT_edit_connect_chain(bpy.types.Operator):
    """First,select some bones, then execute this command."""
    bl_idname = "kiarigtools.edit_connect_chain"
    bl_label = "connect chain"
    def execute(self, context):
        edit.connect_chain()
        return {'FINISHED'}

class KIARIGTOOLS_OT_edit_delete_rig(bpy.types.Operator):
    """Delete automaticaly root_rig and it's children ."""
    bl_idname = "kiarigtools.edit_delete_rig"
    bl_label = "delete rig"
    def execute(self, context):
        edit.delete_rig()
        return {'FINISHED'}


classes = (
    KIARIGTOOLS_Props_OA,
    KIARIGTOOLS_PT_ui,
    KIARIGTOOLS_MT_addonpreferences,

    KIARIGTOOLS_MT_rigsetuptools,
    KIARIGTOOLS_MT_edittools,
    KIARIGTOOLS_MT_rigcontrolpanel,

    #RigShape-Related
    KIARIGTOOLS_PT_rigshape_selector,
    KIARIGTOOLS_OT_rigshape_revert,
    KIARIGTOOLS_OT_rigshape_append,
    KIARIGTOOLS_OT_make_the_same_size,
    
    #setup ik rig
    KIARIGTOOLS_OT_setupik_ik,
    KIARIGTOOLS_OT_setupik_polevector,
    KIARIGTOOLS_OT_setupik_spline_ik,
    KIARIGTOOLS_OT_setupik_hook,

    KIARIGTOOLS_OT_setupik_rig_arm,
    KIARIGTOOLS_OT_setupik_rig_leg,
    KIARIGTOOLS_OT_setupik_rig_spine,
    KIARIGTOOLS_OT_setupik_rig_spine_v2,
    KIARIGTOOLS_OT_setupik_rig_spine_v3,
    KIARIGTOOLS_OT_setupik_rig_neck,
    KIARIGTOOLS_OT_setupik_rig_neck_v2,
    KIARIGTOOLS_OT_setupik_setup_rig_chain,
    KIARIGTOOLS_OT_setupik_rig_finger,

    KIARIGTOOLS_OT_setupik_ue,
    KIARIGTOOLS_OT_setupik_customrig,

    #edit
    KIARIGTOOLS_OT_edit_length_uniform,
    KIARIGTOOLS_OT_edit_length_half,
    KIARIGTOOLS_OT_edit_genarate_bone_from2,
    KIARIGTOOLS_OT_edit_genarate_symmetry,

    KIARIGTOOLS_OT_edit_align_position,
    KIARIGTOOLS_OT_edit_align_direction,
    KIARIGTOOLS_OT_edit_align_along,
    KIARIGTOOLS_OT_edit_aling_near_axis,
    KIARIGTOOLS_OT_edit_align_2axis_plane,
    KIARIGTOOLS_OT_edit_align_on_plane,
    KIARIGTOOLS_OT_edit_align_at_flontview,
    KIARIGTOOLS_OT_edit_adjust_roll,
    KIARIGTOOLS_OT_edit_roll_degree,
    KIARIGTOOLS_OT_edit_align_roll_global,
    KIARIGTOOLS_OT_edit_axis_swap,

    #other tools
    KIARIGTOOLS_OT_edit_connect_chain,
    KIARIGTOOLS_OT_edit_delete_rig,

    #constraint
    KIARIGTOOLS_OT_edit_constraint_cleanup,
    KIARIGTOOLS_OT_edit_constraint_cleanup_empty,

    #rig control panel
    KIARIGTOOLS_OT_rigctr_arm,
    KIARIGTOOLS_OT_modify_rig_control_panel,
    KIARIGTOOLS_OT_modify_rig_control_panel_key,
    KIARIGTOOLS_OT_posetool_copy_matrix,
    KIARIGTOOLS_OT_posetool_paste_matrix
    
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.kiarigtools_props = PointerProperty(type=KIARIGTOOLS_Props_OA)
    bpy.app.handlers.depsgraph_update_post.append(kiarigtools_handler)

    renamer.register()
    duplicator.register()
    constraint.register()


def unregister():
    
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.kiarigtools_props
    bpy.app.handlers.depsgraph_update_post.remove(kiarigtools_handler)

    renamer.unregister()
    duplicator.unregister()
    constraint.unregister()
