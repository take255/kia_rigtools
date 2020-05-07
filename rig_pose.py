import bpy
import imp
from mathutils import ( Vector , Matrix )

if bpy.app.version < (2, 80, 0):
    from .. import Utils as Utils
else:
    from .. import Utils28 as Utils

    imp.reload(Utils)


from . import lib
imp.reload(lib)

def register():
    bpy.utils.register_class(GetSwitchBones)
    bpy.utils.register_class(SwitchInfluence_0)
    bpy.utils.register_class(SwitchInfluence_100)
    bpy.utils.register_class(KeySwitchBones)
    bpy.utils.register_class(Return_Matrix_UncheckedBones)
    bpy.utils.register_class(RigTool_Pose_Panel)

    bpy.utils.register_class(Matrix_Copy)
    bpy.utils.register_class(Matrix_Paste)
    bpy.utils.register_class(Matrix_Keep)
    bpy.utils.register_class(Matrix_Return)
    bpy.utils.register_class(Matrix_Paste_Mirror)
    bpy.utils.register_class(Matrix_Auto_Mirror)


def unregister():
    bpy.utils.unregister_class(GetSwitchBones)
    bpy.utils.unregister_class(SwitchInfluence_0)
    bpy.utils.unregister_class(SwitchInfluence_100)
    bpy.utils.unregister_class(KeySwitchBones)
    bpy.utils.unregister_class(Return_Matrix_UncheckedBones)
    bpy.utils.unregister_class(RigTool_Pose_Panel)

    bpy.utils.unregister_class(Matrix_Copy)
    bpy.utils.unregister_class(Matrix_Paste)
    bpy.utils.unregister_class(Matrix_Keep)
    bpy.utils.unregister_class(Matrix_Return)
    bpy.utils.unregister_class(Matrix_Paste_Mirror)
    bpy.utils.unregister_class(Matrix_Auto_Mirror)

    

SWITCHBONE_MATRIX_ARRAY = {}
SWITCHBONE_MATRIX = []

#マトリックスコピペ用の配列
BONE_MATRIX_ARRAY = {}
BONE_DATA_ARRAY = []
BONE_MATRIX = []


def copy_matrix():
    amt = bpy.context.object
    BONE_MATRIX.clear()
    bonematrixarray  = {}

    bpy.ops.object.mode_set(mode = 'POSE')
    for bone in bpy.context.selected_pose_bones:
        
        m = Matrix(bone.matrix)
        pos =(m[0][3] , m[1][3] , m[2][3]  )
        bonematrixarray[bone.name] = [Matrix(bone.matrix) , pos]

    bpy.ops.object.mode_set(mode = 'EDIT')
    for bone in bpy.context.active_object.data.bones:
        if bone.name in bonematrixarray:
            initmat = Matrix(bone.matrix_local)
            initmat.invert()
            print(bone.matrix_local)
            m = bonematrixarray[bone.name][0] * initmat

            BONE_MATRIX.append([bonematrixarray[bone.name][0] , m ,bonematrixarray[bone.name][1]])

    bpy.ops.object.mode_set(mode = 'POSE')



class BoneData:
    def __init__(self,bone):
        self.amt = bpy.context.object
        self.name = bone.name
        self.m = Matrix(bone.matrix)
        self.pos =(self.m[0][3] , self.m[1][3] , self.m[2][3])
        #bonematrixarray[bone.name] = [Matrix(bone.matrix) , pos]

    def setup(self):
        bone = self.amt.data.edit_bones[self.name]
        initmat = Matrix(bone.matrix)
        initmat.invert()

        self.diff = Utils.m_mul(self.m , initmat)
        #self.diff = self.m * initmat #初期姿勢からの差分マトリックス
        #self.diff = self.m @ initmat #初期姿勢からの差分マトリックス


    def mirror_auto(self):

        #変化の差分の反転
        m0 = self.diff
        m0.transpose()

        m_sym =Matrix(
            (
            ( m0[0][0],-m0[0][1],-m0[0][2], 0 ), 
            (-m0[1][0], m0[1][1], m0[1][2], 0 ),
            (-m0[2][0], m0[2][1], m0[2][2], 0 ),
            (0,0,0,1)
            ))

        m_sym.transpose()


        #反対のボーン名 (L_ R_)　, (.l .r)
        if self.name[0:2] == 'L_':
            symmetric_bonename = 'R_' + self.name[2:]
        elif self.name[0:2] == 'R_':
            symmetric_bonename = 'L_' + self.name[2:]
        elif self.name[-2:] == '.l':
            symmetric_bonename = self.name[:-2] + '.r'
        elif self.name[-2:] == '.r':
            symmetric_bonename = self.name[:-2] + '.l'


        #反対のボーンの初期姿勢マトリックスを取得し、そこに反転差分マトリックスを掛ける

        bpy.ops.object.mode_set(mode = 'EDIT')
        symmetric_bone = self.amt.data.edit_bones[symmetric_bonename]
        initmat = Matrix(symmetric_bone.matrix)


        bpy.ops.object.mode_set(mode = 'POSE')
        symmetric_posebone = self.amt.pose.bones[symmetric_bonename]

        m = Utils.m_mul(m_sym , initmat)
        #m = m_sym * initmat
        #m = m_sym @ initmat

        m[0][3] = -self.pos[0]
        m[1][3] = self.pos[1]
        m[2][3] = self.pos[2]

        symmetric_posebone.matrix = m        






class RigTool_Pose_Panel(Utils.Panel_):
    bl_label = "リグポーズツール"
    bl_idname = "rig_pose_tools"

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=False)
        box = row.box()
        box.label(text = 'IKFKスイッチ')
        row = box.row()
        row.operator("rigtool.get_switch_bones" , icon='CURVE_DATA' )
        row.operator("rigtool.switchinfluence_0" , icon='CURVE_DATA' )
        row.operator("rigtool.switchinfluence_100" , icon='CURVE_DATA' )
        row.operator("rigtool.key_switch_bones" , icon='CURVE_DATA' )

        row = box.row()
        row.operator("rigtool.return_matrix_uncheckedbones" , icon='CURVE_DATA' )

        row = self.layout.row(align=False)
        box = row.box()
        box.label(text = 'マトリックス')

        row = box.row()
        row.operator("rigtool.matrix_copy")
        row.operator("rigtool.matrix_paste")
        row.operator("rigtool.matrix_keep")
        row.operator("rigtool.matrix_return")
        row.operator("rigtool.matrix_paste_mirror")
        box.operator("rigtool.matrix_auto_mirror")


class BoneInf:
    def __init__(self , bonename ,val):
        self.bonename = bonename
        self.val = val

        amt = bpy.context.object

        bone = amt.pose.bones[bonename]
        self.bone_matrix = Matrix(bone.matrix)

        subtarget = bpy.context.object.pose.bones[bone.constraints[0].subtarget]
        self.subtarget_matrix = Matrix(subtarget.matrix)


    def mcopy(self):
        amt = bpy.context.object
        bone = amt.pose.bones[self.bonename]

        for const in bone.constraints:
            const.influence = self.val
            subtarget = amt.pose.bones[const.subtarget]

            if self.val == 1.0:
                subtarget.matrix = self.bone_matrix
            elif self.val == 0:
                bone.matrix = self.subtarget_matrix



#インフルエンスの値を変更し、マトリックスをコピーする
def setInfluenceValue(val):
    amt = bpy.context.object
    biarray = []
    for bonename in lib.list_get_checked():
        print(bonename)
        biarray.append(BoneInf(bonename,val))

    for bi in biarray:
        bi.mcopy()



#インフルエンスの値を変更し、マトリックスをコピーする
def setInfluenceValue_(val):
    amt = bpy.context.object
    for bonename in lib.list_get_checked():
        bone = amt.pose.bones[bonename]

        for const in bone.constraints:
            const.influence = val
            subtarget = amt.pose.bones[const.subtarget]

            if val == 1.0:
                subtarget.matrix = bone.matrix
            elif val == 0:
                bone.matrix = subtarget.matrix



#スイッチボーンチェックされていないマトリックス保持。
#コンストレインのターゲットボーンも同時に保持する
def keep_matrix():
    SWITCHBONE_MATRIX.clear()
    amt = bpy.context.object

    for bonename in lib.list_get_unchecked():
        bone = amt.pose.bones[bonename]
        if len(bone.constraints) > 0:
            subtarget = amt.pose.bones[bone.constraints[0].subtarget]

        SWITCHBONE_MATRIX.append([bone.name,Matrix(bone.matrix)])
        SWITCHBONE_MATRIX.append([subtarget.name,Matrix(subtarget.matrix)])
    

def keep_matrix_():
    SWITCHBONE_MATRIX_ARRAY.clear()
    amt = bpy.context.object

    for bonename in lib.list_get_all():
        bone = amt.pose.bones[bonename]
        subtarget = amt.pose.bones[bone.constraints[0].subtarget]

        SWITCHBONE_MATRIX_ARRAY[bone.name] = Matrix(bone.matrix)
        SWITCHBONE_MATRIX_ARRAY[subtarget.name] = Matrix(subtarget.matrix)


#チェックされていないボーンのマトリックスを返す
def return_matrix_unchecked():
    amt = bpy.context.object

    # for bonename in lib.list_get_unchecked():
        
    #     bone = amt.pose.bones[bonename]
    #     if (bone.name in SWITCHBONE_MATRIX_ARRAY):
    #         bone.matrix =SWITCHBONE_MATRIX_ARRAY[bone.name]
    #         print(bonename)
    #         print(bone.matrix)

    for b in SWITCHBONE_MATRIX:        
        bone = amt.pose.bones[b[0]]
        bone.matrix =b[1]



#IKFKを切り替える。まず切り替えたいノードをボーングループの"Switch"にアサイン
#ボーングループのメンバを選択しリストに表示
class GetSwitchBones(bpy.types.Operator):
    bl_idname = "rigtool.get_switch_bones"
    bl_label = "Get"

    def execute(self, context):
        ui_list = context.window_manager.rig_ui_list

        # if bpy.context.object.mode == 'POSE':
        #     bpy.ops.pose.select_all(action='DESELECT')
        #     for node in self.itemlist:
        #         if node.bool_val == True:
        #             amt.pose.bones[node.name].bone.select = True

        # elif bpy.context.object.mode == 'EDIT':
        #     bpy.ops.armature.select_all(action='DESELECT')
        #     for node in self.itemlist:
        #         if node.bool_val == True:
        #             amt.data.edit_bones[node.name].select = True

        amt=bpy.context.object
        bpy.ops.object.mode_set(mode='POSE')


        #現在選択されているノードをとっておく
        selected = []
        for pose in bpy.context.selected_pose_bones:
            selected.append(pose)

        bpy.ops.pose.select_all(action='DESELECT')
        bone_groups = amt.pose.bone_groups

        bone_groups.active = bone_groups["Switch"]
        bpy.ops.pose.group_select()        
        ui_list.add()

        bpy.ops.pose.select_all(action='DESELECT')

        for pose in selected:
            pose.bone.select = True

        return {'FINISHED'}


#インフルエンスを０に
class SwitchInfluence_0(bpy.types.Operator):
    bl_idname = "rigtool.switchinfluence_0"
    bl_label = "inf0"

    def execute(self, context):
        keep_matrix()
        setInfluenceValue(0)
        return {'FINISHED'}


#インフルエンスを1.０に
class SwitchInfluence_100(bpy.types.Operator):
    bl_idname = "rigtool.switchinfluence_100"
    bl_label = "inf100"

    def execute(self, context):
        keep_matrix()
        setInfluenceValue(1.0)
        return {'FINISHED'}

class Return_Matrix_UncheckedBones(bpy.types.Operator):
    """チェックされていないボーンのマトリックスを復帰させる。\nスイッチしたときにポーズが変わってしまったボーンがあった場合このボタンを押せば修正される。"""
    bl_idname = "rigtool.return_matrix_uncheckedbones"
    bl_label = "Return"

    def execute(self, context):
        return_matrix_unchecked()
        return {'FINISHED'}



#キーを打つ
class KeySwitchBones(bpy.types.Operator):
    bl_idname = "rigtool.key_switch_bones"
    bl_label = "Key"

    def execute(self, context):
        amt = bpy.context.object
        for bonename in lib.list_get_checked():
            bone = amt.pose.bones[bonename]

            for const in bone.constraints:
                const.keyframe_insert(data_path="influence")


        return {'FINISHED'}




#マトリックスのコピペをミラーにも使いたいため、初期マトリックスからの差分を持っておく
#マトリックスの掛け算だけだと位置のミラーがうまくいかないので、ポジション情報も持たせておく
#BONE_MATRIX ( matrix , 差分matrix , ポジション )
class Matrix_Copy(bpy.types.Operator):
    """マトリックスコピー\n"""
    bl_idname = "rigtool.matrix_copy"
    bl_label = "コピー"

    def execute(self, context):
        copy_matrix()
        return {'FINISHED'}



class Matrix_Paste(bpy.types.Operator):
    """マトリックスペースト"""
    bl_idname = "rigtool.matrix_paste"
    bl_label = "ペースト"

    def execute(self, context):
        for bone in bpy.context.selected_pose_bones:
                bone.matrix =BONE_MATRIX[0]

        return {'FINISHED'}


#エディットモードに入ればマトリックスの初期値が得られることを利用
class Matrix_Paste_Mirror(bpy.types.Operator):
    """マトリックスミラーペースト"""
    bl_idname = "rigtool.matrix_paste_mirror"
    bl_label = "ミラーペースト"

    def execute(self, context):
        m0 = BONE_MATRIX[0][1]  
        m0.transpose()

        l = (-BONE_MATRIX[0][2][0],BONE_MATRIX[0][2][1],BONE_MATRIX[0][2][2])
        m1 =Matrix(((m0[0][0],-m0[0][1],-m0[0][2],0),(-m0[1][0],m0[1][1],m0[1][2],0),(-m0[2][0],m0[2][1],m0[2][2],0),(0,0,0,1)))
        m1.transpose()


        bonematrixarray = {}
        initmatrixarray = {}

        for bone in bpy.context.selected_pose_bones:
            bonematrixarray[bone.name] = bone.matrix


        bpy.ops.object.mode_set(mode = 'EDIT')
        for bone in bpy.context.active_object.data.bones:
            if bone.name in bonematrixarray:
                initmatrixarray[bone.name] = Matrix(bone.matrix_local)



        bpy.ops.object.mode_set(mode = 'POSE')
        for bone in bpy.context.selected_pose_bones:

            m =     m1 * initmatrixarray[bone.name]

            print(m)
            m[0][3] = l[0]
            m[1][3] = l[1]
            m[2][3] = l[2]

            bone.matrix = m


        return {'FINISHED'}



#----------------------------------------------------
#マトリックスのコピペ
#選択したボーンのマトリックスを保持して書き戻す
#別の骨にコピーするコマンドではない
#----------------------------------------------------
class Matrix_Keep(bpy.types.Operator):
    """マトリックス保持\n選択したボーンのマトリックスを保持して書き戻す\n別の骨にコピーするコマンドではない"""
    bl_idname = "rigtool.matrix_keep"
    bl_label = "保持"

    def execute(self, context):
        global BONE_MATRIX_ARRAY
        BONE_MATRIX_ARRAY.clear()
        amt = bpy.context.object

        for bone in bpy.context.selected_pose_bones:
            BONE_MATRIX_ARRAY[bone.name] = Matrix(bone.matrix)
        return {'FINISHED'}


class Matrix_Return(bpy.types.Operator):
    """選択したボーンのマトリックス復帰"""
    bl_idname = "rigtool.matrix_return"
    bl_label = "復帰"

    def execute(self, context):
        global BONE_MATRIX_ARRAY
        for bone in bpy.context.selected_pose_bones:
            if (bone.name in BONE_MATRIX_ARRAY):
                bone.matrix =BONE_MATRIX_ARRAY[bone.name]

        return {'FINISHED'}




#姿勢のミラーコピー
class Matrix_Auto_Mirror(bpy.types.Operator):
    """命名規則を元に姿勢をミラーリング\nコピーしたいボーンを選択して実行する。"""
    bl_idname = "rigtool.matrix_auto_mirror"
    bl_label = "反転コピー"

    def execute(self, context):
        amt = bpy.context.object
        BONE_DATA_ARRAY.clear()
        bonematrixarray  = {}

        


        bpy.ops.object.mode_set(mode = 'POSE')
        for bone in bpy.context.selected_pose_bones:
            BONE_DATA_ARRAY.append(BoneData(bone))
            
        
        bpy.ops.object.mode_set(mode = 'EDIT')
        for b in BONE_DATA_ARRAY:
            b.setup()

        bpy.ops.object.mode_set(mode = 'POSE')        
        for b in BONE_DATA_ARRAY:
            b.mirror_auto()

        return {'FINISHED'}