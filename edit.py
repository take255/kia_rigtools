import bpy
import imp
import math
from mathutils import ( Vector , Matrix )


#from . import lib
from . import utils

imp.reload(utils)


#選択されたチェインのルートから先端までのボーンを作成
#ロールは一番目のボーンに合わせる
def genarate_bone_from_chain( first , second , bonename):
    utils.mode_e()
    amt = bpy.context.object
    target = amt.data.edit_bones.new(bonename)
    target.head = amt.data.edit_bones[first].head
    target.tail = amt.data.edit_bones[second].tail
    target.roll = amt.data.edit_bones[first].roll
    #target.parent = root
    return target.name


#---------------------------------------------------------------------------------------
#長さ調整
#---------------------------------------------------------------------------------------

#最後に選択されたアクティブなボーンに長さをそろえる
def length_uniform():
    amt = bpy.context.object
    utils.mode_e()
    selected = utils.get_selected_bones()
    active = utils.get_active_bone()

    #utils.mode_e()
    #act_bone = amt.data.edit_bones[ props.allbones[-1].name ]
    vec = Vector(active.head) - Vector(active.tail)
    length = vec.length

    for b in selected:
        bone = amt.data.edit_bones[b.name]
        vec = Vector(bone.head) - Vector(bone.tail)
        bone.tail = -(length/vec.length)*vec + bone.head

#選択されたボーンの長さを半分に
def length_half():
    amt = bpy.context.object
    utils.mode_e()
    selected = utils.get_selected_bones()
    
    for b in selected:
        bone = amt.data.edit_bones[b.name]
        head = Vector(bone.head)
        vec = Vector(bone.tail) - head
        length = vec.length/2
        vec.normalize()
        bone.tail = length * vec + head


#---------------------------------------------------------------------------------------
#最初に選択したボーンの根本から、最後に選択したボーンの先端までのボーンを生成する
#---------------------------------------------------------------------------------------
def genarate_bone_from2():
    props = bpy.context.scene.kiarigtools_props
    print(props.handler_through)

    first = props.allbones[0].name
    last = props.allbones[-1].name

    props.handler_through = True
    #root = utils.rigroot()
    target = genarate_bone_from_chain(first , last , 'ctr.Bone')

    props.handler_through = False
    

#---------------------------------------------------------------------------------------
#選択したボーンの名前を取得、LR入れ替えた骨を探し　LRの候補を数種類使えるように改良
#最初か最後に識別子があるかどうかに限定する
#---------------------------------------------------------------------------------------
Lsign = ('L_' , '_l')
Rsign = ('R_' , '_r')

def genarate_symmetry():
    amt = bpy.context.active_object
    
    oppositeBones = []
    for bone in bpy.context.selected_bones:
        name = bone.name
        head = bone.head
        tail = bone.tail
        roll = bone.roll

        for L ,R in zip( Lsign , Rsign ):
            notTrue = True

            if name[-2:] == L:
                newname = name[:-2] + R
            elif name[-2:] == R:
                newname = name[:-2] + L
            elif name[:2] == L:
                newname = R + name[2:] 
            elif name[:2] == R:
                newname = L + name[2:]
            else:
                notTrue = False
        
            if notTrue:
                newbone = amt.data.edit_bones[newname]
                newbone.head = (-head[0],head[1], head[2])
                newbone.tail = (-tail[0],tail[1], tail[2])
                newbone.roll = -roll + math.pi #反転したあと１８０°回転させる


#---------------------------------------------------------------------------------------
#Bone direction
#---------------------------------------------------------------------------------------

#ジョイント向きを近いグローバルの軸に合わせる用定数
AXIS ={'x':(1,0,0),'y':(0,1,0),'z':(0,0,1)}

def Normal2bone(bone1,bone2):
    va = []
    #ボーンのベクトルを求め法線を割り出す
    for bone in (bone1,bone2):
        bone.roll = 0 #ボーンのロールを０にする
        v0 = Vector(bone.head) - Vector(bone.tail)
        v0.normalize()
        va.append(v0)

    nor = va[0].cross(va[1])
    nor.normalize()
    return nor


#平面の法線からボーンのロールを修正する
def AdjustRoll(bone,nor):
    mat = bone.matrix
    z = Vector((mat[0][2],mat[1][2],mat[2][2]))
    z.normalize()

    #Xvectorを回転の正負判定に使う
    #Ｘ軸と法線の内積が正なら＋、負ならー
    x = Vector((mat[0][0],mat[1][0],mat[2][0]))
    sign= x.dot(nor)/math.fabs(x.dot(nor))

    cos_sita= z.dot(nor)
    sita = math.acos( cos_sita );
    bone.roll = sita*sign


class VecComp:
    def __init__(self,axis,vec):
        self.axis = axis
        d = Vector(AXIS[axis]).dot(vec)
        self.dot =abs(d)

        if self.dot != 0:
            self.sign = d/self.dot
        else:
            self.sign = 1

    def __repr__(self):
        """
        representaion method
        """
        return self.axis


# class BoneDirectionTools(bpy.types.Operator):
#     bl_idname = "rigtool.bonedirectiontools"
#     bl_label = "ボーン向きツール"

#     def execute(self, context):
#         return {'FINISHED'}

#     def invoke(self, context, event):
#         return context.window_manager.invoke_props_dialog(self)

#     def draw(self, context):
#         scn = context.scene

#         row = self.layout.row(align=False)
#         box = row.box()
#         box.label(text = 'シングルボーン')

#         box.operator("rigtool.position_at_joint")
#         box.operator("rigtool.direct_at_joint")
#         box.operator("rigtool.align_bone_on_firstbone")
#         box.operator("rigtool.aim_near_global_axis")


#         row = self.layout.row(align=False)
#         box = row.box()
#         box.label(text = '複数ボーン')

#         box.operator("rigtool.setup_twobone_plane")
#         box.operator("rigtool.align_bone_on_plane")
#         box.operator("rigtool.adjust_roll_value")
#         box.operator("rigtool.align_bone_at_flontview")


#         row = self.layout.row(align=False)
#         box = row.box()
#         box.label(text = 'ロール')

#         row = box.row(align=True)
#         row.operator("rigtool.roll_90degree")
#         row.operator("rigtool.roll_90degree_neg")
#         row.operator("rigtool.roll_180degree")
#         row.operator("rigtool.roll_fit_grobal_plane")



#---------------------------------------------------------------------------------------
#アクティブなボーンに位置をあわせる
#---------------------------------------------------------------------------------------
def align_position():
    selected = [x.name for x in utils.get_selected_bones() ]
    act = utils.get_active_bone().name
    amt=bpy.context.object
    utils.mode_e()
    
    if len(selected ) > 0 :

        for b in selected:
            bone = amt.data.edit_bones[b]
            bone.head = amt.data.edit_bones[act].head

#---------------------------------------------------------------------------------------
#アクティブなボーンに向きをあわせる
#---------------------------------------------------------------------------------------
def align_direction():
    selected = [x.name for x in utils.get_selected_bones() ]
    act_name = utils.get_active_bone().name
    amt=bpy.context.object
    utils.mode_e()
    
    act = amt.data.edit_bones[act_name]
    matrix = Matrix(act.matrix)

    if len(selected ) > 0 :
        for bonename in selected:                
            tgt = amt.data.edit_bones[bonename]
            head = Vector(tgt.head)
            tgt.matrix = matrix

            l = tgt.length
            vec = Vector(act.tail)-Vector(act.head)
            vec.normalize()

            tgt.head = head
            tgt.tail = Vector(tgt.head) +vec * l
                
#---------------------------------------------------------------------------------------
#アクティブボーン上にそれ以外のボーンを並べる
#元ボーンのベクトルはheadとtailからもとめられる
#ターゲットボーンの近接点は元ボーンの単位ベクトルとの内積で求められる。
#---------------------------------------------------------------------------------------
def align_along():
    act_name = utils.get_active_bone().name
    selected = [x.name for x in utils.get_selected_bones() if x.name != act_name]
    amt=bpy.context.object
    utils.mode_e()

    act = amt.data.edit_bones[act_name]
    p = Vector( act.head )
    vec_act = Vector(act.tail) - p
    vec_act.normalize()

    for b in selected:
        bone = amt.data.edit_bones[b]
        a = Vector(bone.head)
        tail = Vector(bone.tail - bone.head)
        bone.head =p + vec_act * (a - p).dot( vec_act )
        bone.tail =bone.head + tail


#---------------------------------------------------------------------------------------
#近いグローバル軸に向ける
#---------------------------------------------------------------------------------------
def align_near_axis():
    selected = [x.name for x in utils.get_selected_bones()]
    amt=bpy.context.object
    utils.mode_e()

    for b in selected:
        bone = amt.data.edit_bones[b]
        v = Vector(bone.tail - bone.head)
        v.normalize()

        foolist = [ VecComp('x',v), VecComp('y',v), VecComp('z',v)]

        ax = max(foolist, key=lambda x:x.dot)
        vec = bone.length*ax.sign*Vector(AXIS[ax.axis])
        bone.tail = bone.head
        bone.tail += vec


#---------------------------------------------------------------------------------------
#２ボーンの平面を出して軸向きを合わせる
#ポールベクター設定の前処理
#根本、先の順に2軸を選択する。選択はリストで行う。
#2番目に選択される骨にＩＫが設定されている
#---------------------------------------------------------------------------------------
def along_2axis_plane():
    selected = utils.bone.sort()

    # selected = [x.name for x in utils.get_selected_bones()]
    amt = bpy.context.object

    utils.mode_e()

    bone1 = amt.data.edit_bones[selected[0]]
    bone2 = amt.data.edit_bones[selected[1]]

    nor = Normal2bone(bone1,bone2)

    #デバッグ用ボーン-----
##        b = amt.data.edit_bones.new('ctr.Bone')
##        b.head = Vector(bone.head)
##        b.tail = Vector(bone.head) + nor
    #デバッグ用ボーン----- ここまで

    #平面の法線からボーンのロールを修正する
    AdjustRoll(bone1,nor)
    AdjustRoll(bone2,nor)



#---------------------------------------------------------------------------------------
#２ボーンの平面を出して軸向きを合わせる
#平面の法線からボーン先端の最近点を求める
#---------------------------------------------------------------------------------------
def align_on_plane():
    #selected = [x.name for x in utils.get_selected_bones()]
    selected = utils.bone.sort()
    amt = bpy.context.object
    utils.mode_e()

    bone1 = amt.data.edit_bones[selected[0]]
    bone2 = amt.data.edit_bones[selected[1]]

    nor = Normal2bone( bone1 , bone2 )

    #３本目からのボーンの先端を平面に合わせていく
    #必要な値：
    # 平面上の１点 Vector(bone[0].head)
    # 法線 nor
    # 先端位置 Vector(bone.tail)

    # 平面上の最近点 = A - N * ( PA ・ N )
    # A 先端位置
    # N 面法線 
    # P 平面上の点
    # PA・N　内積

    p = bone1.head

    for b in selected[2:]:
        bone = amt.data.edit_bones[b]
        a = Vector(bone.tail)
        pos =a + nor * (p - a).dot(nor)
        bone.tail = pos

    #平面の法線からボーンのロールを修正する
    for b in selected:
        bone = amt.data.edit_bones[b]
        AdjustRoll(bone,nor)


#---------------------------------------------------------------------------------------
#最初のheadと最後のtailを含む平面の法線を割り出し、中間の関節をその平面の最近点に移動する
#選択順が必要なのでポーズモードで
#---------------------------------------------------------------------------------------
def align_at_flontview():
    #props = bpy.context.scene.kiarigtools_props
    #selected = [x.name for x in props.allbones ]
    amt = bpy.context.object
    utils.mode_e()

    selected = utils.bone.sort()
    bone1 = amt.data.edit_bones[selected[0]]
    bone2 = amt.data.edit_bones[selected[-1]]

    #法線を割り出す　normal.y = 0
    #vecのｘ、ｚを入れ替えればよい(どちらかにー符号をつける)
    vec0 = Vector(bone1.head) - Vector(bone2.tail) 
    nor = Vector((vec0.z ,0 ,-vec0.x) )
    nor.normalize()

    p = Vector(bone1.head)

    for b in selected[1:]:
        bone = amt.data.edit_bones[b]
        a = Vector(bone.head)
        pos =a + nor * (p - a).dot(nor)
        bone.head = pos


#---------------------------------------------------------------------------------------
#ロール値をボーン平面に合わせて修正。
#複数のボーンを同時に修正がどうしてもうまくいかない。
#なので、妥協案として2本づつおこなう
#選択はポーズモードで
#---------------------------------------------------------------------------------------
def adjust_roll():
    props = bpy.context.scene.kiarigtools_props
    amt = bpy.context.object
    selected = [x.name for x in props.allbones ]
    utils.mode_e()

    bone1 = amt.data.edit_bones[selected[0]]
    bone2 = amt.data.edit_bones[selected[1]]

    nor = Normal2bone(bone1,bone2)

    #平面の法線からボーンのロールを修正する
    AdjustRoll(bone1,nor)
    AdjustRoll(bone2,nor)


def roll_degree(op):
    for bone in bpy.context.selected_bones:
        if op == '90d':
            bone.roll += math.pi/2
        if op == '-90d':
            bone.roll -= math.pi/2
        if op == '180d':
             bone.roll += math.pi


# #X-axis MirrorがＯＮになっているとうまく実行できないので注意
# class Roll_90degree(bpy.types.Operator):
#     """ロールを90°回転させる。"""
#     bl_idname = "rigtool.roll_90degree"
#     bl_label = "90°"

#     def execute(self, context):
#         for bone in bpy.context.selected_bones:
#             bone.roll += math.pi/2
#         return {'FINISHED'}

# class Roll_90degree_neg(bpy.types.Operator):
#     """ロールを-90°回転させる。"""
#     bl_idname = "rigtool.roll_90degree_neg"
#     bl_label = "-90°"

#     def execute(self, context):
#         for bone in bpy.context.selected_bones:
#             bone.roll -= math.pi/2
#         return {'FINISHED'}

# class Roll_180degree(bpy.types.Operator):
#     """ロールを-90°回転させる。"""
#     bl_idname = "rigtool.roll_180degree"
#     bl_label = "180°"

#     def execute(self, context):
#         for bone in bpy.context.selected_bones:
#             bone.roll += math.pi
#         return {'FINISHED'}


#---------------------------------------------------------------------------------------
#ロールをグローバル平面上にそろえる
# ラジオボタンで選択
# ボーン軸(X,Z)　グローバル軸　(x,y,z,x,y,z) 
#y軸とグローバル軸の外積から直行するベクトルをだし、そのベクトルとY軸との外積でグローバル軸に沿ったベクトルを割り出す
#---------------------------------------------------------------------------------------
def align_roll_global():
    bpy.ops.object.mode_set(mode = 'EDIT')
    for bone in bpy.context.selected_bones:
        m = Matrix(bone.matrix)
        m.transpose()
        y_axis = Vector(m[1][:-1])

        #グローバル軸との外積
        vec0 = y_axis.cross(Vector((0,0,1.0)))
        vec1 = y_axis.cross(vec0)
        new_m = Matrix(( (vec0[0],vec0[1],vec0[2],0.0) ,(y_axis[0],y_axis[1],y_axis[2],0.0),(vec1[0],vec1[1],vec1[2],0.0) ,m[3]))

        new_m.transpose()

        bone.matrix = new_m


#---------------------------------------------------------------------------------------
#コンストレイン
#---------------------------------------------------------------------------------------
def constraint_cleanup():        
    for bone in bpy.context.selected_pose_bones:
        for const in bone.constraints:
            bone.constraints.remove( const )

def constraint_cleanup_empty():
    for bone in bpy.context.selected_pose_bones:
        
        for const in bone.constraints:
            isempty = False
            
            if hasattr(const, 'target'):
                if const.target is None:
                    isempty = True

            if hasattr(const, 'subtarget'):
                if const.subtarget == '':
                    isempty = True

            const.driver_remove('influence')
            if isempty is True:
                bone.constraints.remove( const )

def constraint_showhide(self,state):
    for bone in bpy.context.selected_pose_bones:
        for const in bone.constraints:
            const.mute = self.const_disp_hide

def constraint_change_influence(self,context):
    bpy.ops.object.mode_set(mode = 'POSE')
    for bone in bpy.context.selected_pose_bones:
        for const in bone.constraints:
            const.influence = self.const_influence                    

#---------------------------------------------------------------------------------------
#connect chain 
#---------------------------------------------------------------------------------------
def connect_chain():
    utils.mode_e()
    for b in utils.bone.get_selected_bones():
        b.use_connect = True

#---------------------------------------------------------------------------------------
#delete rig
#---------------------------------------------------------------------------------------
def delete_rig_loop(bone,root):
    p = bone.parent
    if p == None:
        return False

    elif p.name == root:
        return True

    else:
        return delete_rig_loop(p,root)
    
    

def delete_rig():
    utils.mode_p()
    bpy.context.object.data.layers[8] = True

    amt = bpy.context.object
    root = 'rig_root'


    #delete all driver
    utils.mode_p()
    for b in amt.pose.bones:
        b.driver_remove("ik_stretch")
        for c in b.constraints:
            c.driver_remove("influence")
            b.constraints.remove( c )


    utils.mode_e()
    bpy.ops.armature.select_all(action='DESELECT')

    result = []
    for b in amt.data.edit_bones:
        if delete_rig_loop( b , root ):
            result.append(b)


    for b in result:
        b.select = True
    
    bpy.ops.armature.delete()