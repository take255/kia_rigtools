import bpy
import imp
from mathutils import Vector
import math

from bpy.props import(
    StringProperty,
    CollectionProperty,
    BoolProperty,
    EnumProperty)

from bpy.types import PropertyGroup

from . import utils

from . import duplicator
from . import constraint
from . import edit

imp.reload(utils)
imp.reload(duplicator)
imp.reload(constraint)
imp.reload(edit)

#---------------------------------------------------------------------------------------
#Confirm that rig shape scene exists
#---------------------------------------------------------------------------------------
def confirm_rigshape():
    if not utils.scene.IsExistence:
        prefs = bpy.context.preferences.addons[__name__].preferences
        cmd.rigshape_append( prefs.shape_path )


#---------------------------------------------------------------------------------------
#IKセットアップ
# Select 2bones. first, select tip of bone chain.
# And then select controller is active bone.
#---------------------------------------------------------------------------------------
def ik():
    props = bpy.context.scene.kiarigtools_props 
    bones = utils.bone.get_selected_bones()

    print(len(bones) ) 
    if len(bones) == 2:
        active = utils.bone.get_active_bone()
        bones.remove(active)
        create_ik_modifier( bones[0].name , active.name , props.setupik_number )

    # props = bpy.context.scene.kiarigtools_props        
    # bones = utils.bone.sort()
    # if bones != []:
    #     create_ik_modifier( bones[0] , bones[1] , props.setupik_number )
    # if props.allbones != []:
    #     first = props.allbones[0].name
    #     second = props.allbones[1].name
    #     create_ik_modifier( first , second , props.setupik_number )

#---------------------------------------------------------------------------------------
#ポールベクター設定 : 根本、先の順に2軸を選択 2番目に選択される骨にＩＫが設定されているように
#---------------------------------------------------------------------------------------
def polevector():
    props = bpy.context.scene.kiarigtools_props        
    if props.allbones != []:
        first = props.allbones[0].name
        second = props.allbones[1].name
        create_polevector( first , second ,'ctr.pole')

# class Setup_PoleVector(bpy.types.Operator):
#     """ポールベクターのセットアップ\n根本、先の順に2軸をチェックする。\n選択はリストで行いチェックがついたものを対象とする。\nチェックされたものが３本なら、\n３本目をポールベクタ骨とする\n肘の向きは+X\n"""
#     bl_idname = "rigtool.setup_polevector"
#     bl_label = "ポールベクター生成"

#     def execute(self, context):
#         bones = lib.list_get_checked()
#         num = lib.list_get_checked_number()

#         if num == 2:
#             polevector = 'ctr.pole'
#         elif num == 3:
#             polevector = bones[2]
#         create_polevector( bones[0] , bones[1] ,polevector )
#         return {'FINISHED'}


#親子付け、存在を確認して無ければ
#If parent exists return True ,if not exists return False.
def parent(child , parent):
    utils.mode_e()
    amt = bpy.context.object

    a = child in [x.name for x in amt.data.edit_bones]
    b = parent in [x.name for x in amt.data.edit_bones]

    if a and b:
        amt = bpy.context.object
        child_bone = amt.data.edit_bones[child]
        parent_bone  = amt.data.edit_bones[parent]
        child_bone.parent = parent_bone
        return True
    else:
        print('%s or %s not exist' % (child , parent))
        return False

def connect(child , parent):
    amt = bpy.context.object

    a = child in [x.name for x in amt.data.edit_bones]
    b = parent in [x.name for x in amt.data.edit_bones]

    if a and b:
        amt = bpy.context.object
        child_bone = amt.data.edit_bones[child]
        parent_bone  = amt.data.edit_bones[parent]
        child_bone.parent = parent_bone
        child_bone.use_connect = True
        return True
    else:
        print('%s or %s not exist' % (child , parent))
        return False


def maintain_volume(source_name):
    amt = bpy.context.object
    utils.mode_o()
    #bpy.ops.object.mode_set(mode='POSE')
    amt = bpy.context.object
    source = amt.pose.bones[source_name]
    c = source.constraints.new('MAINTAIN_VOLUME')   
    c.mode = 'SINGLE_AXIS'
    c.volume = amt.scale[0]
    


def move_layer(bone_name,number):
    #まずは移動先をアクティブにする
    bpy.context.object.data.layers[number] = True

    #レイヤをすべてアクティブではない状態にする
    for i in range(32):
        bpy.context.object.data.layers[number] = False
        bpy.context.object.data.bones[bone_name].layers[i] = False    

    bpy.context.object.data.bones[bone_name].layers[number] = True

def genarate_bone_from_chain( first , second , bonename):
    root = utils.rigroot()
    utils.mode_e()
    amt = bpy.context.object
    target = amt.data.edit_bones.new(bonename)
    target.parent = root
    target.head = amt.data.edit_bones[first].head
    target.tail = amt.data.edit_bones[second].tail
    target.roll = amt.data.edit_bones[first].roll
    target.use_deform = False
    #target.parent = root
    return target.name

#２つのボーンのヘッドどうしをつないだボーン作成
def genarate_from_2bonehead( first , second , bonename):
    utils.mode_e()
    amt = bpy.context.object
    target = amt.data.edit_bones.new(bonename)
    target.head = amt.data.edit_bones[first].head
    target.tail = amt.data.edit_bones[second].head
    target.use_deform = False
    #target.roll = amt.data.edit_bones[first].roll
    #target.parent = root
    return target.name


#---------------------------------------------------------------------------------------
#ストレッチプロパティを追加
#---------------------------------------------------------------------------------------

def add_property_stretch( bonearray , ctr ):
    bpy.types.PoseBone.stretch = bpy.props.FloatProperty(name="Stretch", default=0.001, min=0.0, max=1)
    amt.pose.bones[arm_ctr].stretch = 0.001

    for bone in bonearray:
        d = bpy.context.object.pose.bones[ bone ].driver_add("ik_stretch")
        d.driver.type = 'SCRIPTED'
        d.driver.expression = 'var'


        #ドライバ変数の作成
        var = d.driver.variables.new()
        var.name = 'var'
        var.type = 'SINGLE_PROP'
        var.targets[0].id = amt
        var.targets[0].data_path = "pose.bones[\"%s\"].[\"stretch\"]" % ctr



#---------------------------------------------------------------------------------------
#create関数
#---------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------
#前腕、コントローラ、IKチェイン数
#---------------------------------------------------------------------------------------
def create_ik_modifier( first , second , number):
    bpy.ops.object.mode_set(mode = 'POSE')
    amt = bpy.context.object

    jnt = amt.pose.bones[first]
    tgt = amt.pose.bones[second]

    c = jnt.constraints.new('IK')
    c.target = amt
    c.subtarget = tgt.name
    c.chain_count = number

#---------------------------------------------------------------------------------------
#上腕、前腕、ポールベクター : ポールベクターの向きはワールドにする
#---------------------------------------------------------------------------------------
def create_polevector( first , second ,name):
    root = utils.rigroot()
    utils.mode_e()
    #ポールベクター用ボーン生成
    #ＩＫルートボーンのＸ軸の方向につくる。距離はボーンの長さにする
    amt=bpy.context.object

    jnt1 = amt.data.edit_bones[first]
    jnt_ik = amt.pose.bones[second]

    mat = jnt1.matrix
    len = jnt1.length
    #vec_x = len * Vector((mat[0][0],mat[1][0],mat[2][0]))

    #2つのジョイントをヒジから伸ばした２つのベクトルとする
    #２つのベクトルを足し合わせて反転させたものがポールベクタの位置になる
    vec1 = Vector(jnt1.head) - Vector(jnt1.tail)
    vec2 = Vector(jnt_ik.tail) - Vector(jnt_ik.head)

    vec1.normalize()
    vec2.normalize()

    pos  = (vec1 + vec2)
    pos.normalize()

    #リグのコントローラ生成
    b = amt.data.edit_bones.new(name)
    b.head = Vector(jnt_ik.head) - pos*len
    y_sign = math.copysign( 1 , b.head[1] )
    b.tail = b.head + y_sign*Vector( (0, len/4 , 0 ))
    b.use_deform = False

    parent( b.name , root.name )
    #ＩＫにポールベクターを設定する
    utils.mode_p()
    for const in jnt_ik.constraints:
        if const.type == 'IK':
            const.pole_target = amt
            #const.pole_subtarget = b.name
            const.pole_subtarget = name
        
    return name

#---------------------------------------------------------------------------------------
def create_polevector2( first , second ,polevector ):
    bpy.ops.object.mode_set(mode='EDIT')
    #ポールベクター用ボーン生成
    #ＩＫルートボーンのＸ軸の方向につくる。距離はボーンの長さにする
    amt=bpy.context.object

    jnt1 = amt.data.edit_bones[first]
    jnt_ik = amt.pose.bones[second]

    mat = jnt1.matrix
    len = jnt1.length
    vec_x = len * Vector((mat[0][0],mat[1][0],mat[2][0]))

    #リグのコントローラ生成
    if polevector in amt.data.edit_bones: #polevectorの存在チェック
        b = amt.data.edit_bones[polevector]
    else:
        b = amt.data.edit_bones.new(polevector)
        polevector = b.name

    b.head = Vector(jnt1.head) + vec_x
    b.tail = b.head + Vector( (0, len/2 , 0 ))
        
    #ＩＫにポールベクターを設定する
    bpy.ops.object.mode_set(mode='POSE')
    for const in jnt_ik.constraints:
        if const.type == 'IK':
            const.pole_target = amt
            const.pole_subtarget = polevector
        
    return polevector


#---------------------------------------------------------------------------------------
#スプラインＩＫの設定
#ボーンの数を拾いたいので全部の骨を選択する
#現在は背骨用で上に延びる垂直なもの限定。ベジェを引く時ハンドルの向きを限定してしまっているので。
#骨の向きからハンドル用のベクトルを出せばどの方向でも行けると思う。
#背骨が湾曲しているとカーブ生成によってまっすぐになってしまう問題がある
#スプラインＩＫ作成までにしておく
#フックは別コマンドにする        
#---------------------------------------------------------------------------------------
def spline_ik():
    utils.init_cursor()
    props = bpy.context.scene.kiarigtools_props        

    if props.allbones != []:
        first = props.allbones[0].name
        last = props.allbones[-1].name
        count = len(props.allbones)
    else:
        return

    #リストのボーン（名前）
    # first = lib.get_selected()
    # last = lib.get_last()


    #エディットモードで骨を拾う
    bpy.ops.object.mode_set(mode='EDIT')
    amt = bpy.context.object

    bone0 = amt.data.edit_bones[first]
    bone1 = amt.data.edit_bones[last]
    
    start = bone0.head
    end = bone1.tail - bone0.head
    length = Vector(end).length#ハンドルの長さを決めるため全体の長さを出して置く


    #カーブの生成
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.curve.primitive_bezier_curve_add()


    v = Vector((0,0,1)) * length/2
    curve = bpy.context.object
    obj = curve.data

    curve.location = start

    p0 = obj.splines[0].bezier_points[0]
    p1 = obj.splines[0].bezier_points[1]

    p0.co = (0,0,0)
    p0.handle_right = v
    p0.handle_left = -v

    p1.co = end
    p1.handle_right = end + v
    p1.handle_left = end -v

    #Spline_IK
    objects = bpy.context.scene.objects
    #objects.active = amt
    utils.activeObj(amt)
    #bpy.ops.object.mode_set(mode='POSE')
    utils.mode_p()
    ikbone = amt.pose.bones[last]
    c = ikbone.constraints.new('SPLINE_IK')
    c.target = curve
    c.chain_count = count
    #c.use_y_stretch = False


#---------------------------------------------------------------------------------------
#カーブとアーマチュアを選択して実行
#背骨用の親子構造をもったコントローラにする
#---------------------------------------------------------------------------------------
def hook():
    utils.init_cursor()

    #アーマチュアとカーブの取得
    for ob in bpy.context.selected_objects:
        if ob.type == 'CURVE':
            curve = ob
            obj = curve.data
        if ob.type == 'ARMATURE':
            amt = ob

    curve_pos = curve.location

    p0 = obj.splines[0].bezier_points[0]
    p1 = obj.splines[0].bezier_points[1]

    v = Vector((0,1,0))
    length = Vector(p1.co - p0.co).length/4

    #インフルエンスボーン生成
    #amt = bpy.data.objects['Rig']
    #bpy.context.scene.objects.active = amt
    utils.activeObj(amt)
    bpy.ops.object.mode_set(mode='EDIT')

    bone_ctr0 = amt.data.edit_bones.new('ctr.Bone')
    bone_ctr0.head = curve_pos + p0.co
    bone_ctr0.tail = curve_pos + p0.co + v*length

    bone_ctr1 = amt.data.edit_bones.new('ctr.Bone')
    bone_ctr1.head = curve_pos + p1.co
    bone_ctr1.tail = curve_pos + p1.co + v*length
    bone_ctr1.parent = bone_ctr0
    ctrname = bone_ctr0.name


    m1 = curve.modifiers.new("beta", 'HOOK')
    m1.object = amt
    m1.subtarget = bone_ctr1.name

    m1 = curve.modifiers.new("alpha", 'HOOK')
    m1.object = amt
    m1.subtarget = bone_ctr0.name


    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.scene.objects.active = curve

    bpy.ops.object.mode_set(mode='EDIT')

    p0 = obj.splines[0].bezier_points[0]
    p1 = obj.splines[0].bezier_points[1]

    p1.select_control_point=True
    p1.select_left_handle = True
    p1.select_right_handle = True

    p0.select_control_point=False
    p0.select_left_handle = False
    p0.select_right_handle = False

    bpy.ops.object.hook_assign(modifier="beta")
    bpy.ops.object.hook_reset(modifier='beta')


    p1.select_control_point=False
    p1.select_left_handle = False
    p1.select_right_handle = False

    p0.select_left_handle = True
    p0.select_right_handle = True
    p0.select_control_point=True
    bpy.ops.object.hook_assign(modifier="alpha")
    bpy.ops.object.hook_reset(modifier='alpha')



#---------------------------------------------------------------------------------------
    #腕のリグの自動設定。上腕、前腕、手の順でリストに並べる
    #既存のコントローラを流用したい場合は、そのあとにIKコントローラ、ポールベクターの順に追加
    #2019/9/12 リグを大きく修正するため、流用をいったんオミットする
    #鎖骨から選択する必要あり
    #リグシェイプを読み込んでおかないとエラーになる
#---------------------------------------------------------------------------------------
def setup_rig_arm():
    root = utils.rigroot()
    amt = bpy.context.object
    props = bpy.context.scene.kiarigtools_props        
    lr = props.setupik_lr
    bones = utils.bone.sort()

    #レイヤ８をアクティブにする
    bpy.context.object.data.layers[8] = True

    #ポーズモードにする
    bpy.ops.object.mode_set(mode = 'POSE')
    if len(bones) == 4:
        #選択したもののコンストレインをすべて削除
        edit.constraint_cleanup()

        first = bones[0]
        last = bones[-1]
        num = len(bones)

        #手の位置にコントローラを作成
        arm_med = duplicator.duplicate( bones[3] ,'med.arm.' + lr, 'copy' ,0.25 , 'sel')
        arm_ctr = duplicator.duplicate( bones[3] ,'ctr.arm.' + lr, 'head' ,0.5 , 'y')
        duplicator.constraint(bones[3] ,arm_med , 'COPY_ROTATION' , 'WORLD' ,True , True , True)

        #肩の位置に肩コントローラ作成
        clav_ctr = duplicator.duplicate( bones[0] ,'ctr.clav.' + lr, 'copy' ,1 , 'sel')

        #IKボーンのリグを作成。本骨はストレッチさせる設定をする
        #IKの根本のボーンは鎖骨を複製したものを使用。鎖骨にコンストレインさせる
        #さらにIK作動時に肩も動かしたいので３チェインIKを設定する。肩用なのでclavと命名。

        #2chain
        #arm_med_ik_base = duplicator.duplicate( bones[0] ,'med.arm.ikbase.' + lr, 'copy' , 1 , 'sel')
        arm_med_ik0 = duplicator.duplicate( bones[1] ,'med.arm.ik0.' + lr, 'copy' , 1 , 'sel')
        arm_med_ik1 = duplicator.duplicate( bones[2] ,'med.arm.ik1.' + lr, 'copy' , 1 , 'sel')

        #3chain 肩からik0, ik1 , ik2　と設定
        clav_med_ik0 = duplicator.duplicate( bones[0] ,'med.clav.ik0.' + lr, 'copy' , 1 , 'sel')
        clav_med_ik1 = duplicator.duplicate( bones[1] ,'med.clav.ik1.' + lr, 'copy' , 1 , 'sel')
        clav_med_ik2 = duplicator.duplicate( bones[2] ,'med.clav.ik2.' + lr, 'copy' , 1 , 'sel')
        
        
        bpy.ops.object.mode_set(mode='EDIT')


        parent(arm_med_ik1 , arm_med_ik0)    #親子付け(子供、親)            
        parent(arm_med_ik0 , clav_ctr)    #親子付け(子供、親)            
        #parent(arm_med_ik0 , arm_med_ik_base)    #親子付け(子供、親)            

        parent(clav_med_ik2 , clav_med_ik1)
        parent(clav_med_ik1 , clav_med_ik0)
        parent(clav_ctr , clav_med_ik0)
        #parent(clav_med_ik0 , clav_ctr)
        #parent(clav_med_ik0 , clav_med_ik_base)

        
        #IK骨に本骨をコンストレインする
        #constraint.constraint( arm_med_ik_base , bones[0] ,  'COPY_TRANSFORMS' , 'WORLD' ,(True,True,True) , (False,False,False))
        constraint.constraint( bones[1] , arm_med_ik0 ,  'COPY_TRANSFORMS' , 'WORLD' ,(True,True,True) , (False,False,False))        
        constraint.constraint( bones[2] , arm_med_ik1 ,  'COPY_TRANSFORMS' , 'WORLD' ,(True,True,True) , (False,False,False))

        constraint.constraint( bones[0] , clav_ctr ,  'COPY_ROTATION' , 'WORLD' ,(True,True,True) , (False,False,False))
        
        # constraint.constraint( bones[1] , arm_med_ik0 ,  'COPY_TRANSFORMS' , 'WORLD' ,(True,True,True) , (False,False,False))
        # constraint.constraint( bones[2] , arm_med_ik1 ,  'COPY_TRANSFORMS' , 'WORLD' ,(True,True,True) , (False,False,False))


        #maintain volumeコンストレインの設定
        maintain_volume(bones[1])
        maintain_volume(bones[2])

        
        #IK設定 2chain
        create_ik_modifier(arm_med_ik1, arm_ctr , 2)
        amt.pose.bones[arm_med_ik0].ik_stretch = 0.001
        amt.pose.bones[arm_med_ik1].ik_stretch = 0.001

        #IK設定 3chain arm_ctrを流用する
        create_ik_modifier(clav_med_ik2, arm_ctr , 3)
        #amt.pose.bones[clav_med_ik0].ik_stretch = 0.001
        #amt.pose.bones[clav_med_ik1].ik_stretch = 0.001

        #ポールベクター設定
        pole_ctr = create_polevector(arm_med_ik0,arm_med_ik1,'ctr.arm.pole.' + lr)

        utils.mode_e()

        #親子付け(子供、親)            
        #背骨リグが設定されていたらpole_ctrを子供にする
        parent(arm_med , arm_ctr)
        # if not parent(pole_ctr , 'ctr.chest.c'):
        #     parent(pole_ctr , root)

        #generate arm_switch if not exist. Next parent some node to it.
        arm_switch  = 'med.arm.switch.c'
        if arm_switch not in [b.name for b in amt.data.edit_bones]:            
            p = amt.data.edit_bones[bones[0]].parent
            arm_switch = duplicator.duplicate( p.name , arm_switch , 'copy' , 1 , 'sel')
            constraint.do_const('COPY_TRANSFORMS' , arm_switch , p.name , 'WORLD' )


        utils.mode_e()
        clav_base  = 'med.clav.base.c'
        if clav_base not in [b.name for b in amt.data.edit_bones]:            
            p = amt.data.edit_bones[bones[0]].parent
            clav_base = duplicator.duplicate( p.name , clav_base , 'copy' , 1 , 'sel')
            constraint.do_const('COPY_TRANSFORMS' , clav_base , p.name , 'WORLD' )


        utils.mode_e()
        parent(arm_ctr , arm_switch)
        parent(pole_ctr , arm_switch)
        parent(clav_med_ik0 , clav_base)
        
        
        for bone in (arm_ctr , pole_ctr ,clav_ctr):
            amt.data.edit_bones[bone].show_wire = True


        #シェイプ変更
        bpy.ops.object.mode_set(mode='POSE')
        amt.pose.bones[arm_ctr].custom_shape = bpy.data.objects['rig.shape.cube']
        amt.pose.bones[pole_ctr].custom_shape = bpy.data.objects['rig.shape.pole']
        amt.pose.bones[clav_ctr].custom_shape = bpy.data.objects['rig.shape.clav']

        
        #レイヤの設定
        #直接さわらない補助ボーン
        for bone in ( arm_med_ik0 , arm_med_ik1 , arm_med , clav_med_ik0 ,clav_med_ik1 , clav_med_ik2 , clav_base , arm_switch ):
            move_layer(bone,8)

        #リグ
        bpy.context.object.data.layers[2] = True
        for bone in ( arm_ctr , pole_ctr):
            move_layer(bone,2)

        
        #---------------------------------------------------------------------------------------
        #ストレッチプロパティを追加
        #---------------------------------------------------------------------------------------
        bpy.context.object.pose.bones[arm_ctr]["stretch." + lr] = 0.001
        for bone in (arm_med_ik0,arm_med_ik1):
            d = bpy.context.object.pose.bones[ bone ].driver_add("ik_stretch")
            d.driver.type = 'SCRIPTED'
            d.driver.expression = 'var'

            #ドライバ変数の作成
            var = d.driver.variables.new()
            var.name = 'var'
            var.type = 'SINGLE_PROP'
            var.targets[0].id = amt
            var.targets[0].data_path = "pose.bones[\"%s\"].[\"stretch.%s\"]" % ( arm_ctr , lr )


        #---------------------------------------------------------------------------------------
        #IKFKプロパティ追加
        #---------------------------------------------------------------------------------------
        bpy.context.object.pose.bones[arm_ctr]["ikfk." + lr] = 1.0
        for bone in (bones[1], bones[2]):
            for c in bpy.context.object.pose.bones[ bone ].constraints:
                if c.type == 'COPY_TRANSFORMS':
                    d = c.driver_add("influence")
                    d.driver.type = 'SCRIPTED'
                    d.driver.expression = 'var'

                    # #ドライバ変数の作成
                    var = d.driver.variables.new()
                    var.name = 'var'
                    var.type = 'SINGLE_PROP'
                    var.targets[0].id = amt
                    #var.targets[0].data_path = "pose.bones[\"%s\"].[\"ikfk\"]" % arm_ctr
                    var.targets[0].data_path = "pose.bones[\"%s\"].[\"ikfk.%s\"]" % ( arm_ctr , lr)

        #---------------------------------------------------------------------------------------
        #add clavicle property
        #---------------------------------------------------------------------------------------
        propname = "clav."
        bpy.context.object.pose.bones[arm_ctr][propname + lr] = 0.2
        for c in bpy.context.object.pose.bones[ clav_med_ik2 ].constraints:
            if c.type == 'IK':
                d = c.driver_add("influence")
                d.driver.type = 'SCRIPTED'
                d.driver.expression = 'var'

                # #ドライバ変数の作成
                var = d.driver.variables.new()
                var.name = 'var'
                var.type = 'SINGLE_PROP'
                var.targets[0].id = amt
                var.targets[0].data_path = "pose.bones[\"%s\"].[\"%s%s\"]" % ( arm_ctr , propname , lr )

        #---------------------------------------------------------------------------------------
        #add hand constraint property
        #---------------------------------------------------------------------------------------
        propname = "hand."
        bpy.context.object.pose.bones[arm_ctr][propname + lr] = 1.0
        for c in bpy.context.object.pose.bones[ bones[3] ].constraints:
            if c.type == 'COPY_ROTATION':
                d = c.driver_add("influence")
                d.driver.type = 'SCRIPTED'
                d.driver.expression = 'var'

                # #ドライバ変数の作成
                var = d.driver.variables.new()
                var.name = 'var'
                var.type = 'SINGLE_PROP'
                var.targets[0].id = amt
                var.targets[0].data_path = "pose.bones[\"%s\"].[\"%s%s\"]" % ( arm_ctr , propname , lr )

        #Final Processing
        utils.mode_p()
        bpy.context.object.data.layers[2] = True




#---------------------------------------------------------------------------------------
#脚のリグの自動設定。腰、太もも、すね、足、つま先の順でリストに並べる
#腰骨はIKボーンを作るために追加で必要
#既存のコントローラを流用したい場合は、そのあとにIKコントローラ、ポールベクターの順に追加
#---------------------------------------------------------------------------------------
def setupik_rig_leg():
    amt = bpy.context.object
    props = bpy.context.scene.kiarigtools_props        
    lr = props.setupik_lr    
    #lr = bpy.context.scene.setup_ik_lr
    bones = utils.bone.sort()


    #レイヤ８をアクティブにする
    bpy.context.object.data.layers[8] = True


    #ポーズモードにする
    bpy.ops.object.mode_set(mode = 'POSE')
    # if lib.exists:
    #     bones = lib.list_get_checked()
    #     num = lib.list_get_checked_number()
    if len(bones) == 5:
        #選択したもののコンストレインをすべて削除
        #edit.constraint_cleanup()


        #くるぶしの位置にコントローラを作成
        #リストにあるボーン数が３ならコントローラ作成。でなければ流用する
        #くるぶしはコントローラとして扱わない。 ctr.leg.l >> med.leg.ik.lに改名
        #foor > legに改名
        leg_med_ik = duplicator.duplicate( bones[3] ,'med.leg.ik.' + lr, 'copy' ,0.5 , 'sel')
        duplicator.constraint(bones[3] ,leg_med_ik , 'COPY_ROTATION' , 'WORLD' ,True , True , True)


        #IKボーンのリグを作成。本骨はストレッチさせる設定をする
        #腕と違って鎖骨がないのでベース骨どうするか < HipBoneからふとももの根本に描けて
        #IKの根本のボーンは鎖骨を複製したものを使用。鎖骨にコンストレインさせる
        leg_med_ik_base = duplicator.duplicate( bones[0] ,'med.leg.ikbase.' + lr, 'copy' , 1 , 'sel')
        leg_med_ik0 = duplicator.duplicate( bones[1] ,'med.leg.ik0.' + lr, 'copy' , 1 , 'sel')
        leg_med_ik1 = duplicator.duplicate( bones[2] ,'med.leg.ik1.' + lr, 'copy' , 1 , 'sel')

        parent(leg_med_ik1 , leg_med_ik0)    #親子付け(子供、親)            
        parent(leg_med_ik0 , leg_med_ik_base)

        #IK骨に本骨をコンストレインする
        constraint.constraint( leg_med_ik_base , bones[0] ,  'COPY_TRANSFORMS' , 'WORLD' ,(True,True,True) , (False,False,False))
        constraint.constraint( bones[1] , leg_med_ik0 ,  'COPY_TRANSFORMS' , 'WORLD' ,(True,True,True) , (False,False,False))
        constraint.constraint( bones[2] , leg_med_ik1 ,  'COPY_TRANSFORMS' , 'WORLD' ,(True,True,True) , (False,False,False))
        maintain_volume(bones[1])
        maintain_volume(bones[2])

        #IK設定            
        create_ik_modifier(leg_med_ik1, leg_med_ik , 2)
        amt.pose.bones[leg_med_ik0].ik_stretch = 0.001
        amt.pose.bones[leg_med_ik1].ik_stretch = 0.001

        #ポールベクター設定
        pole_ctr = create_polevector( leg_med_ik0 , leg_med_ik1 , 'ctr.leg.pole.' + lr )

        # #親子付け(子供、親)            
        leg_switch  = 'med.leg.switch.c'
        if leg_switch in amt.data.edit_bones:
            parent(leg_med_ik , leg_switch)

        #足のリグ作成
        #つま先の骨を複製して足のコントローラを作成
        #つま先の骨を複製してかかとのコントローラを作成
        #つま先のコンストレイン用中間ノード

        leg_ctr = duplicator.duplicate( bones[4] ,'ctr.leg.' + lr, 'head' ,0.5 , 'y')
        heel_ctr = duplicator.duplicate( bones[4] ,'ctr.heel.' + lr, 'head' ,0.5 , 'y')
        heel_med = duplicator.duplicate( bones[4] ,'ctr.heel.med.' + lr, 'copy' ,0.25 , 'sel')
        duplicator.constraint(bones[4] ,heel_med , 'COPY_ROTATION' , 'WORLD' ,True , True , True)

        parent(leg_med_ik , heel_ctr)
        parent(heel_ctr , leg_ctr)
        parent(heel_med , leg_ctr)
        parent(pole_ctr , leg_ctr)
        

        #シェイプ変更
        utils.mode_p()
        amt.pose.bones[heel_ctr].custom_shape = bpy.data.objects['rig.shape.circle']
        amt.pose.bones[leg_ctr].custom_shape = bpy.data.objects['rig.shape.foot']
        amt.pose.bones[pole_ctr].custom_shape = bpy.data.objects['rig.shape.pole']

        #レイヤの設定
        #直接さわらない補助ボーン
        for bone in ( heel_med , leg_med_ik0 ,leg_med_ik1 , leg_med_ik_base , leg_med_ik ):
            move_layer(bone,8)

        #リグ
        bpy.context.object.data.layers[2] = True
        for bone in ( pole_ctr , heel_ctr ,leg_ctr ):
            move_layer(bone,2)


        bpy.ops.object.mode_set(mode='EDIT')

        for bone in ( leg_ctr , pole_ctr):
            amt.data.edit_bones[bone].show_wire = True


        #ストレッチプロパティを追加

        #bpy.types.PoseBone.stretch = bpy.props.FloatProperty(name="Stretch", default=0.001, min=0.0, max=1)
        #amt.pose.bones[leg_ctr].stretch = 0.001

        
        #bpy.types.PoseBone.stretch
        #bpy.types.PoseBone.stretch_l = bpy.props.FloatProperty(min = 0.0 , max= 1.0 )
        bpy.context.object.pose.bones[leg_ctr]["stretch_" + lr] = 0.001
        #bpy.ops.wm.properties_edit( data_path="active_pose_bone", property="ikfk_r", min=0, max=1)
        #bpy.context.object.pose.bones[leg_ctr]["stretch_" + lr] = {"min":0.0,"max": 1.0}



        for bone in (leg_med_ik0,leg_med_ik1):
            d = bpy.context.object.pose.bones[ bone ].driver_add("ik_stretch")
            d.driver.type = 'SCRIPTED'
            d.driver.expression = 'var'


            #ドライバ変数の作成
            var = d.driver.variables.new()
            var.name = 'var'
            var.type = 'SINGLE_PROP'
            var.targets[0].id = amt
            var.targets[0].data_path = "pose.bones[\"%s\"].[\"stretch_%s\"]" % ( leg_ctr , lr )


        #IKFKプロパティ追加
        # bpy.types.PoseBone.ikfk = bpy.props.FloatProperty(name="IKFK", default=1.0, min=0.0, max=1)
        # amt.pose.bones[leg_ctr].ikfk = 1.0
        #bpy.context.object.pose.bones[leg_ctr]["ikfk"] = 0.001
        bpy.context.object.pose.bones[leg_ctr]["ikfk." + lr] = 1.0
        bpy.context.object.pose.bones[leg_ctr]["foot." + lr] = 1.0

        for bone in bones[1:3]:
            for c in bpy.context.object.pose.bones[ bone ].constraints:
                print(c.type)
                if c.type == 'COPY_TRANSFORMS':
                    d = c.driver_add("influence")
                    d.driver.type = 'SCRIPTED'
                    d.driver.expression = 'var'

                    # #ドライバ変数の作成
                    var = d.driver.variables.new()
                    var.name = 'var'
                    var.type = 'SINGLE_PROP'
                    var.targets[0].id = amt
                    var.targets[0].data_path = "pose.bones[\"%s\"].[\"ikfk.%s\"]" % ( leg_ctr , lr)

        for bone in bones[3:]:
            for c in bpy.context.object.pose.bones[ bone ].constraints:
                print(c.type)
                if c.type == 'COPY_ROTATION':
                    d = c.driver_add("influence")
                    d.driver.type = 'SCRIPTED'
                    d.driver.expression = 'var'

                    # #ドライバ変数の作成
                    var = d.driver.variables.new()
                    var.name = 'var'
                    var.type = 'SINGLE_PROP'
                    var.targets[0].id = amt
                    var.targets[0].data_path = "pose.bones[\"%s\"].[\"foot.%s\"]" % ( leg_ctr , lr)



        bpy.ops.object.mode_set(mode='POSE')
        bpy.context.object.data.layers[2] = True



#背骨リグのセットアップ
#腰から胸までの骨を順番にリストに登録して実行
def setup_rig_spine():
    bones = utils.bone.sort()
    if bones != []:
        amt = bpy.context.object
        
        
        #まず、背骨のIKジョイントを作成する
        #生成されたIK骨の向きを背骨に合わせる
        med_spine_c = genarate_bone_from_chain( bones[1] , bones[-2] , 'med.spine.c')

        #IKジョイントに背骨の一部を回転拘束 1,2,最後を除く骨
        for bone in bones[2:-1]:
            c = constraint.constraint( bone , med_spine_c , 'COPY_ROTATION' , 'LOCAL' ,(True,True,True) , (False,False,False))
            c.influence = 0.65

        #胸IKコントローラ作成
        chest_med = duplicator.duplicate( bones[-1] ,'med.chest.c', 'copy' ,0.25 , 'sel')
        chest_ctr = duplicator.duplicate( bones[-1] ,'ctr.chest.c', 'head' ,0.5 , 'y')
        constraint.constraint(bones[-1] ,chest_med ,  'COPY_ROTATION' , 'WORLD' ,(True,True,True) , (False,False,False))

        create_ik_modifier( med_spine_c , chest_ctr , 1)

        #背骨のベースコントローラを作成
        chest_base_med = duplicator.duplicate( bones[1] ,'med.chest.base.c', 'copy' ,0.25 , 'sel')
        chest_base_ctr = duplicator.duplicate( bones[1] ,'ctr.chest.base.c', 'head' ,0.5 , 'y')
        constraint.constraint(bones[1] ,chest_base_med ,  'COPY_ROTATION' , 'WORLD' ,(True,True,True) , (False,False,False))
        
        #腰の回転コントローラ
        hip_med = duplicator.duplicate( bones[0] ,'med.hip.c', 'copy' ,0.25 , 'sel')
        hip_ctr = duplicator.duplicate( bones[0] ,'ctr.hip.c', 'head' ,0.5 , 'y')
        constraint.constraint(bones[0] ,hip_med ,  'COPY_ROTATION' , 'WORLD' ,(True,True,True) , (False,False,False))

        #腰のベース
        hip_base_med = duplicator.duplicate( bones[0] ,'med.hip.base.c', 'copy' ,0.25 , 'sel')
        hip_base_ctr = duplicator.duplicate( bones[0] ,'ctr.hip.base.c', 'head' ,0.5 , 'y')
        constraint.constraint(bones[0] ,hip_base_med ,  'COPY_LOCATION' , 'WORLD' ,(True,True,True) , (False,False,False))

        #腕のスイッチノード
        #もし腕のIKコントローラがあれば子供にする
        #medを胸骨にワールドでコンストレイン。ctrをワールドに合わせるのでmedの子供にする。
        arm_switch_med = duplicator.duplicate( bones[-1] ,'med.arm.switch.c', 'copy' ,0.25 , 'sel')
        arm_switch_ctr = duplicator.duplicate( bones[-1] ,'ctr.arm.switch.c', 'head' ,0.5 , 'y')
        constraint.constraint( arm_switch_med ,bones[-1],  'COPY_TRANSFORMS' , 'WORLD' ,(True,True,True) , (False,False,False))

        #背骨のひねりコンストレイン
        for bone in bones[2:-1]:
            c = constraint.constraint_transformation(bone ,chest_ctr ,  'TRANSFORM' , 'LOCAL' ,'ROTATION', 'ROTATION' , ('Mute','Z','Mute'))
            c.influence = 0.33


        #親子付け
        bpy.ops.object.mode_set(mode='EDIT')

        parent(med_spine_c , chest_base_ctr)
        parent(chest_ctr , chest_base_ctr)
        parent(chest_med , chest_ctr)
        parent(chest_base_ctr , hip_base_ctr)
        parent(chest_base_med , chest_base_ctr)
        parent(hip_med , hip_ctr)
        parent(hip_ctr , hip_base_ctr)
        parent(hip_base_med , hip_base_ctr)
        parent(arm_switch_ctr , arm_switch_med)


        #腕のIKコントローラが存在するならarm_switch_ctrの子供にする
        for b in ('ctr.arm.l' , 'ctr.arm.r'):
            if b in amt.data.edit_bones:
                amt.data.edit_bones[b].parent = amt.data.edit_bones[arm_switch_ctr]

        #シェイプ変更
        bpy.ops.object.mode_set(mode='POSE')

        # for bonename in (chest_ctr,hip_base_ctr,hip_ctr , chest_base_ctr):
        #     amt.pose.bones[bonename].custom_shape = bpy.data.objects['rig.shape.circle_z']
        amt.pose.bones[chest_ctr].custom_shape = bpy.data.objects['rig.shape.circle_z']

        amt.pose.bones[hip_base_ctr].custom_shape = bpy.data.objects['rig.shape.circle_z']
        amt.pose.bones[hip_base_ctr].custom_shape_scale = 8.0            

        amt.pose.bones[hip_ctr].custom_shape = bpy.data.objects['rig.shape.circle.z.down']
        amt.pose.bones[hip_base_ctr].custom_shape_scale = 5.0 

        amt.pose.bones[chest_base_ctr].custom_shape = bpy.data.objects['rig.shape.circle.z.up']
        amt.pose.bones[hip_base_ctr].custom_shape_scale = 5.0            


        for bone in (chest_ctr , hip_base_ctr ,hip_ctr ,chest_base_ctr):
            amt.data.edit_bones[bone].show_wire = True



        #レイヤの設定
        #直接さわらない補助ボーン
        for bone in ( med_spine_c ,chest_med, chest_base_med ,arm_switch_med):
            move_layer(bone,8)

        #リグ
        bpy.context.object.data.layers[2] = True
        for bone in ( chest_ctr , chest_base_ctr, hip_base_ctr):
            move_layer(bone,2)



        bpy.ops.object.mode_set(mode = 'EDIT')
        for bonename in (chest_ctr,hip_base_ctr,hip_ctr , chest_base_ctr):
            amt.data.edit_bones[bonename].show_wire = True

        bpy.ops.object.mode_set(mode='POSE')
        bpy.context.object.data.layers[2] = True

#背骨リグのセットアップ
#腰から胸までの骨を順番にリストに登録して実行
def setup_rig_spine_v2():
    bones = utils.bone.sort()
    if bones != []:
        amt = bpy.context.object
               
        #First , generate base and Hip controller.
        base_ctr = duplicator.duplicate( bones[0] ,'ctr.base.c', 'head' ,4.0 , 'z')
        hip_ctr = duplicator.duplicate( bones[0] ,'ctr.hip.c', 'copy' ,1.0 , 'sel')
        #hip_ctr = duplicator.duplicate( bones[0] ,'ctr.hip.c', 'tail' ,2.0 , 'z')
        constraint.do_const('COPY_TRANSFORMS' , bones[0], hip_ctr,  'WORLD')

        #Second, Generate IK bone chain and tweak controller from Spine bones.
        spinearray = []
        tweakarray = []

        for b in bones[1:]:
            sp = duplicator.duplicate( b ,'med.%s.c' % b, 'copy' , 1 , 'sel')
            tw = duplicator.duplicate( b ,'ctr.tweak.%s.c' % b, 'tail' , 1.5 , 'z')

            parent(tw,sp)
            spinearray.append(sp)
            tweakarray.append(tw)


        #connect spine chain
        spine_num = len(spinearray)
        for i in range( spine_num-1 ):
            connect(spinearray[i + 1] , spinearray[i])


        #IK controller
        chest_ctr = duplicator.duplicate( bones[-1] ,'ctr.chest.c', 'tail' ,3.0 , 'z')
        create_ik_modifier( spinearray[-1] , chest_ctr , spine_num )
        
        amt.pose.bones[chest_ctr].rotation_mode = 'XYZ'
        amt.pose.bones[chest_ctr].lock_rotation[0] = True
        amt.pose.bones[chest_ctr].lock_rotation[2] = True

        amt.pose.bones[hip_ctr].lock_location[0] = True
        amt.pose.bones[hip_ctr].lock_location[1] = True
        amt.pose.bones[hip_ctr].lock_location[2] = True


        constraint.do_const('COPY_LOCATION' , spinearray[0], hip_ctr,  'WORLD' ,(True,True,True) , (False,False,False) , 1.0)
        
        inf = 1.0/spine_num
        for i in range( spine_num ):
            constraint.do_const( 'COPY_ROTATION' , bones[i+1], chest_ctr, 'LOCAL' ,(False,True,False) , (False,False,False) , inf)
            #constraint.constraint( bones[ i+1 ], spinearray[i], 'COPY_ROTATION' , 'WORLD' ,(True,True,True) , (False,False,False))
            create_ik_modifier(bones[ i+1 ] , tweakarray[i] ,1)

        utils.mode_p()

        for b in (chest_ctr , base_ctr ,hip_ctr , *tweakarray):
            amt.pose.bones[b].custom_shape = bpy.data.objects['rig.shape.circle']

        #レイヤの設定
        #直接さわらない補助ボーン
        for bone in spinearray:
            move_layer(bone,8)

        #parent
        utils.mode_e()
        parent(hip_ctr,base_ctr)
        parent(chest_ctr,base_ctr)
        for bonename in (chest_ctr , base_ctr ,hip_ctr):
            amt.data.edit_bones[bonename].show_wire = True

        bpy.ops.object.mode_set(mode='POSE')
        bpy.context.object.data.layers[2] = True


#背骨リグのセットアップ
#腰から胸までの骨を順番にリストに登録して実行
def setup_rig_spine_v3():

    bones = utils.bone.sort()
    if bones != []:
        amt = bpy.context.object

        #レイヤ８をアクティブにする
        for i in range(32):
            bpy.context.object.data.layers[i] = False

        bpy.context.object.data.layers[8] = True
        

        med_spine_c = genarate_bone_from_chain( bones[1] , bones[-1] , 'med.spine.c')
        chest_ctr = duplicator.duplicate( bones[-1] ,'ctr.chest.c', 'tail' ,2.0 , 'z')
        create_ik_modifier( med_spine_c , chest_ctr , 1)


        #First , generate base and Hip controller.
        base_ctr = duplicator.duplicate( bones[0] ,'ctr.base.c', 'head' ,4.0 , 'z')
        hip_ctr = duplicator.duplicate( bones[0] ,'ctr.hip.c', 'copy' ,1.0 , 'sel')
        #hip_ctr = duplicator.duplicate( bones[0] ,'ctr.hip.c', 'tail' ,2.0 , 'z')
        constraint.do_const('COPY_TRANSFORMS' , bones[0], hip_ctr,  'WORLD')

        #Second, Generate IK bone chain and tweak controller from Spine bones.
        spinearray = []
        tweakarray = []

        for b in bones[1:]:
            sp = duplicator.duplicate( b ,'med.%s.c' % b, 'copy' , 1 , 'sel')
            tw = duplicator.duplicate( b ,'ctr.tweak.%s.c' % b, 'tail' , 1.5 , 'z')

            parent(tw,sp)
            spinearray.append(sp)
            tweakarray.append(tw)


        #connect spine chain
        spine_num = len(spinearray)
        for i in range( spine_num ):
            parent(spinearray[i] , med_spine_c)


        # constraint.do_const('COPY_LOCATION' , spinearray[0], hip_ctr,  'WORLD' ,(True,True,True) , (False,False,False) , 1.0)
        
        inf = 1.0/spine_num
        for i in range( spine_num ):
            constraint.do_const( 'COPY_ROTATION' , bones[i+1], chest_ctr, 'LOCAL' ,(False,True,False) , (False,False,False) , inf)
            create_ik_modifier(bones[ i+1 ] , tweakarray[i] ,1)

        utils.mode_p()

        for b in ( chest_ctr , base_ctr ):
            amt.pose.bones[b].custom_shape = bpy.data.objects['rig.shape.circle.dir']

        for b in ( hip_ctr , *tweakarray ):
            amt.pose.bones[b].custom_shape = bpy.data.objects['rig.shape.board']


        #レイヤの設定
        #直接さわらない補助ボーン
        for bone in spinearray:
            move_layer(bone,8)
        move_layer(med_spine_c,8)


        for bone in (chest_ctr , base_ctr , hip_ctr , *tweakarray ):
            move_layer(bone,2)
        
        #parent
        utils.mode_e()
        parent(hip_ctr,base_ctr)
        parent(chest_ctr,base_ctr)
        parent(med_spine_c,hip_ctr)

        for bonename in (chest_ctr , base_ctr ,hip_ctr , *tweakarray):
            amt.data.edit_bones[bonename].show_wire = True

        bpy.ops.object.mode_set(mode='POSE')

        bpy.context.object.data.layers[0] = True
        bpy.context.object.data.layers[2] = True
        bpy.context.object.data.layers[8] = False



#首リグのセットアップ
#胸の骨、首、頭までの骨を順番にリストに登録して実行
#胸の骨入れ忘れに注意
def setup_rig_neck():
    bones = utils.bone.sort()
    if bones != []:
        amt = bpy.context.object

        #レイヤ８をアクティブにする
        bpy.context.object.data.layers[8] = True
        root = 'rig_root'#骨が生成されることによりインデックスが変わるためここでrootを取得する必要がある

                    
        #まず、首骨のIKジョイントを作成する
        #生成されたIK骨の向きを背骨に合わせる
        med_neck_c = edit.genarate_bone_from_chain( bones[1] , bones[-2] , 'med.neck.c')

        #IKジョイントに首骨の一部を回転拘束 胸骨,首の1本目、最後を除く骨
        for bone in bones[2:-1]:
            c = constraint.constraint( bone , med_neck_c , 'COPY_ROTATION' , 'LOCAL' ,(True,True,True) , (False,False,False))
            c.influence = 1.0

        #頭IKコントローラ作成
        #constraint(コンスト先、コンスト元)
        #head_med_switch = duplicator.duplicate( bones[-1] ,'med.head.switch.c', 'head' ,0.25 , 'y')#グローバル軸に合わせる。
        head_med_switch = duplicator.duplicate( bones[-1] ,'med.head.switch.c', 'copy' ,0.25 , 'sel')#リグルートと同じ向きにする
        head_med_switchtarget = duplicator.duplicate( bones[-1] ,'med.head.switchtarget.c', 'copy' ,0.25 , 'sel')#リグルートの子供にしてコンストターゲットにする
        #head_med_switch = duplicator.duplicate( root ,'med.head.switch.c', 'copy' ,0.25 , 'sel')#リグルートを複製
        head_med = duplicator.duplicate( bones[-1] ,'med.head.c', 'copy' ,0.2 , 'sel')#コントローラの子供にして、頭の軸向きに合わせる
        #head_ctr = duplicator.duplicate( bones[-1] ,'ctr.head.c', 'head' ,0.5 , 'y')
        head_ctr = duplicator.duplicate( bones[-1] ,'ctr.head.c', 'copy' ,0.5 , 'sel')
        constraint.constraint(bones[-1] ,head_med ,  'COPY_ROTATION' , 'WORLD' ,(True,True,True) , (False,False,False))
        #constraint.constraint_transformation(bones[-1] ,head_med ,  'TRANSFORM' , 'WORLD' ,'ROTATION', 'ROTATION' , (''))

        #  constraint_transformation( tgt , first  ,self.const_type , self.space ,
        #         self.map_from,self.map_to,
        #         (self.transform_x , self.transform_y , self.transform_z) )

        #constraint.constraint(head_med_switch ,'rig_root' ,  'COPY_ROTATION' , 'WORLD' ,(True,True,True) , (False,False,False))
        constraint.constraint(head_med_switch ,head_med_switchtarget ,  'COPY_ROTATION' , 'WORLD' ,(True,True,True) , (False,False,False))
        
        #constraint.constraint(head_med_switch ,root.name ,  'COPY_ROTATION' , 'WORLD' ,(True,True,True) , (False,False,False))
        create_ik_modifier( med_neck_c , head_ctr , 1)

        #頭のコントローラの回転を首に伝える
        # for bone in bones[2:-1]:
        #     c = constraint.constraint( bone , head_ctr , 'COPY_ROTATION' , 'LOCAL' ,(False,True,False) , (False,False,False))
        #     c.influence = 0.33

        
        #首骨のベースコントローラを作成
        neck_base_med = duplicator.duplicate( bones[0] ,'med.neck.base.c', 'copy' ,0.5 , 'sel')
        neck_ctr = duplicator.duplicate( bones[1] ,'ctr.neck.c', 'copy' ,0.5 , 'sel')

        constraint.constraint(neck_base_med ,bones[0] ,  'COPY_TRANSFORMS' , 'WORLD' ,(True,True,True) , (False,False,False))
        constraint.constraint(bones[1] ,neck_ctr ,  'COPY_ROTATION' , 'WORLD' ,(True,True,True) , (False,False,False))


        #首のひねりコンストレイン
        for bone in bones[2:-1]:
            c = constraint.constraint_transformation(bone ,head_ctr ,  'TRANSFORM' , 'LOCAL' ,'ROTATION', 'ROTATION' , ('Mute','Z','Mute'))
            c.influence = 0.33



        # #親子付け(子供、親)
        bpy.ops.object.mode_set(mode='EDIT')

        
        parent(head_med_switchtarget , root)
        parent(head_ctr , head_med_switch)
        parent(head_med_switch , neck_ctr)
        parent(head_med , head_ctr)
        parent(neck_ctr , neck_base_med)        
        parent(med_neck_c , neck_ctr)
        
 


        # #腕のIKコントローラが存在するならarm_switch_ctrの子供にする
        # for b in ('ctr.arm.l' , 'ctr.arm.r'):
        #     if b in amt.data.edit_bones:
        #         amt.data.edit_bones[b].parent = amt.data.edit_bones[arm_switch_ctr]

        # #シェイプ変更
        bpy.ops.object.mode_set(mode='POSE')

        amt.pose.bones[neck_ctr].custom_shape = bpy.data.objects['rig.shape.neck.base']
        amt.pose.bones[head_ctr].custom_shape = bpy.data.objects['rig.shape.head_y']


        #レイヤの設定
        #直接さわらない補助ボーン
        for bone in ( med_neck_c , head_med_switch , head_med , neck_base_med):
            move_layer(bone,8)

        #リグ
        bpy.context.object.data.layers[2] = True
        for bone in ( neck_ctr , neck_ctr):
            move_layer(bone,2)


        bpy.ops.object.mode_set(mode = 'EDIT')
        amt.data.edit_bones[neck_ctr].show_wire = True


        bpy.ops.object.mode_set(mode='POSE')
        bpy.context.object.data.layers[2] = True


        # bpy.ops.object.mode_set(mode = 'EDIT')
        # for bonename in (chest_ctr,hip_base_ctr,hip_ctr , chest_base_ctr):
        #     amt.data.edit_bones[bonename].show_wire = True


#首リグのセットアップ
#胸の骨、首、頭までの骨を順番にリストに登録して実行
#胸の骨入れ忘れに注意
def setup_rig_neck_v2():
    bones = utils.bone.sort()
    if bones != []:
        amt = bpy.context.object

        #レイヤ８をアクティブにする
        for i in range(32):
            bpy.context.object.data.layers[i] = False

        bpy.context.object.data.layers[8] = True


        med_neckbase_c = duplicator.duplicate( bones[0] ,'med.neckbase.c', 'copy' ,1.0 , 'sel')
        med_neck_c = genarate_bone_from_chain( bones[1] , bones[-1] , 'med.neck.c')
        neck_ctr = duplicator.duplicate( bones[-1] ,'ctr.neck.c', 'tail' ,1.0 , 'z')
        create_ik_modifier( med_neck_c , neck_ctr , 1)

        #Head aim 
        med_head01_c = duplicator.duplicate( bones[-1] ,'med.head01.c' , 'head' , 1 , '-y')
        med_head02_c = duplicator.duplicate( bones[-1] ,'med.head02.c' , 'copy' , 1 , 'sel')
        head_ctr = duplicator.duplicate( 'med.head01.c' ,'ctr.head.c', 'tail' ,0.5 , '-y')

        #shape for direction
        head_shape = duplicator.duplicate( 'ctr.head.c' , 'med.headshape.c' , 'copy' ,1.0 , 'sel')
        neck_shape = duplicator.duplicate( 'ctr.neck.c' , 'med.neckshape.c' , 'copy' ,1.0 , 'sel')
        #amt.data.edit_bones[head_shape].hide = True

        #constraint
        constraint.do_const( 'COPY_ROTATION' , bones[-1], med_head02_c, 'WORLD' ,(True,True,True) , (False,False,False))
        constraint.do_track_to( med_head01_c, head_ctr , 'WORLD')
        constraint.do_const( 'COPY_TRANSFORMS', med_neckbase_c , bones[0], 'WORLD')

        constraint.do_const( 'COPY_ROTATION' , head_shape, med_head01_c, 'WORLD' ,(True,True,True) , (False,False,False))
        constraint.do_const( 'COPY_ROTATION' , neck_shape, bones[-1], 'WORLD' ,(True,True,True) , (False,False,False))

        #neck chain
        neck0array = []
        neckarray = []
        tweakarray = []
        

        for b in bones[1:-1]:
            neck0array.append(b)
            sp = duplicator.duplicate( b ,'med.%s.c' % b, 'copy' , 1 , 'sel')
            tw = duplicator.duplicate( b ,'ctr.tweak.%s.c' % b, 'tail' , 1.5 , 'z')

            parent(tw,sp)
            neckarray.append(sp)
            tweakarray.append(tw)

        neck_num = len(neckarray)
        for i in range( neck_num ):
            parent(neckarray[i] , med_neck_c)
        
        parent(med_head02_c , med_head01_c)
        parent(med_head01_c , med_neck_c)
        parent(head_ctr , med_neck_c)
        parent(med_neck_c , med_neckbase_c)
        parent(neck_ctr , med_neckbase_c)

        #parent shape 
        parent(head_shape , head_ctr)
        parent(neck_shape , neck_ctr)


        inf = 1.0/neck_num
        map = ['X','Z','Y']
        range_from = [0 , 0 , 0 , 0 , -180 , 180 ] 
        range_to = [0,0,-180,180,0,0]
        for b,t in zip(neck0array,tweakarray):
            #constraint.do_const( 'COPY_ROTATION' , b, neck_ctr, 'LOCAL' ,(False,True,False) , (False,False,False) , inf)
            constraint.do_transformation(
                b , med_head01_c ,
                'LOCAL' , 'ROTATION' , 'ROTATION',
                map , range_from , range_to , inf ,
                'YXZ','YXZ')
            create_ik_modifier( b, t ,1 )


        #shape
        for i,b in enumerate( tweakarray ):
            amt.pose.bones[b].custom_shape = bpy.data.objects['rig.shape.board']
            amt.pose.bones[b].custom_shape_transform = amt.pose.bones[ bones[ i + 2 ] ]

        amt.pose.bones[head_ctr].custom_shape = bpy.data.objects['rig.shape.aim']
        amt.pose.bones[neck_ctr].custom_shape = bpy.data.objects['rig.shape.circle.dir']

        #directional shape
        amt.pose.bones[head_ctr].custom_shape_transform = amt.pose.bones[head_shape]
        amt.pose.bones[neck_ctr].custom_shape_transform = amt.pose.bones[neck_shape]
        bpy.context.object.data.bones[head_shape].hide = True
        bpy.context.object.data.bones[neck_shape].hide = True


        for bone in ( med_head01_c , med_head02_c , med_neck_c , med_neckbase_c , med_neckbase_c , *neckarray ):
            move_layer(bone,8)

        for bone in ( neck_ctr , head_ctr , *tweakarray):
            move_layer(bone,2)

        utils.mode_e()
        for bonename in (head_ctr , neck_ctr, *tweakarray):
            amt.data.edit_bones[bonename].show_wire = True

        utils.mode_p()

        bpy.context.object.data.layers[2] = True
        bpy.context.object.data.layers[0] = True


#assign chain rig
def setup_rig_chain():
    props = bpy.context.scene.kiarigtools_props        
    basename = props.setup_chain_baseame

    bones = utils.bone.sort()

    if bones != []:
        amt = bpy.context.object

        #レイヤ８をアクティブにする
        for i in range(32):
            bpy.context.object.data.layers[i] = False

        bpy.context.object.data.layers[8] = True
        
        med_spine_c = genarate_bone_from_chain( bones[0] , bones[-1] , 'med.%s.c' % basename)
        chest_ctr = duplicator.duplicate( bones[-1] ,'ctr.%s.c' % basename , 'tail' ,2.0 , 'z')
        #create_ik_modifier( med_spine_c , chest_ctr , 1)

        #First , generate base and Hip controller.
        base = duplicator.duplicate( bones[0] ,'med.%s_base.c' % basename, 'head' ,4.0 , 'z')
        #hip_ctr = duplicator.duplicate( bones[0] ,'ctr.hip.c', 'copy' ,1.0 , 'sel')
        #constraint.do_const('COPY_TRANSFORMS' , bones[0], hip_ctr,  'WORLD')

        #Second, Generate IK bone chain and tweak controller from Spine bones.
        spinearray = []
        tweakarray = []

        for i,b in enumerate(bones):
            sp = duplicator.duplicate( b ,'med.%s_%02d.c' % ( basename , i+1 ), 'copy' , 1 , 'sel')
            tw = duplicator.duplicate( b ,'ctr.tweak.%s_%02d.c' % ( basename , i+1 ) , 'tail' , 1.5 , 'z')

            parent(tw,sp)
            spinearray.append(sp)
            tweakarray.append(tw)

        #connect spine chain
        spine_num = len(spinearray)
        for i in range( spine_num ):
            parent(spinearray[i] , med_spine_c)

        for i in range( spine_num - 1 ):
            parent(spinearray[i + 1 ] , spinearray[i])
            amt.data.edit_bones[ spinearray[i + 1 ] ].use_connect = True

        create_ik_modifier( spinearray[-1] , chest_ctr , spine_num)


        #add tipbone
        tipbone = duplicator.duplicate( bones[-1] ,'med.%s_tip.c' % basename, 'tail' ,1.0 , 'sel')
        constraint.do_const( 'COPY_TRANSFORMS' , tipbone  ,bones[-1] , 'WORLD' , 1.0)
      

        inf = 1.0/spine_num
        for i in range( spine_num ):
            constraint.do_const( 'COPY_ROTATION' , bones[i], chest_ctr, 'LOCAL' ,(False,True,False) , (False,False,False) , inf)
            create_ik_modifier(bones[ i] , tweakarray[i] ,1)

        utils.mode_p()


        #for b in ( chest_ctr , base_ctr ):
        amt.pose.bones[chest_ctr].custom_shape = bpy.data.objects['rig.shape.circle.dir']
        #amt.pose.bones[chest_ctr].custom_shape_transform =amt.pose.bones[ tipbone ]

        for b,shape in zip( tweakarray , (*bones[1:] , tipbone)):
            amt.pose.bones[b].custom_shape = bpy.data.objects['rig.shape.board']
            amt.pose.bones[b].custom_shape_transform = amt.pose.bones[ shape ]

        #レイヤの設定
        #直接さわらない補助ボーン
        for bone in ( *spinearray , med_spine_c, tipbone):
            move_layer(bone,8)
        #move_layer(med_spine_c,8)


        for bone in (chest_ctr  ,  *tweakarray ):
            move_layer(bone,2)
        
        #parent
        utils.mode_e()
        #parent(hip_ctr,base_ctr)
        parent(chest_ctr,base)
        parent(tipbone,base)
        parent(med_spine_c,base)
        #parent(med_spine_c,hip_ctr)

        for bonename in (chest_ctr ,  *tweakarray):
            amt.data.edit_bones[bonename].show_wire = True

        #bpy.ops.object.mode_set(mode='POSE')
        utils.mode_p()
        for bonename in (chest_ctr , *tweakarray):
            amt.pose.bones[bonename].use_custom_shape_bone_size = False


        bpy.context.object.data.layers[0] = True
        bpy.context.object.data.layers[2] = True
        bpy.context.object.data.layers[8] = False


def setup_rig_chain_2():
    props = bpy.context.scene.kiarigtools_props        
    basename = props.setup_chain_baseame

    bones = utils.bone.sort()

    if bones != []:
        amt = bpy.context.object

        #レイヤ８をアクティブにする
        for i in range(32):
            bpy.context.object.data.layers[i] = False

        bpy.context.object.data.layers[8] = True
        
        med_spine_c = genarate_bone_from_chain( bones[0] , bones[-1] , 'med.%s.c' % basename)
        chest_ctr = duplicator.duplicate( bones[-1] ,'ctr.%s.c' % basename , 'tail' ,2.0 , 'z')
        create_ik_modifier( med_spine_c , chest_ctr , 1)

        #First , generate base and Hip controller.
        base = duplicator.duplicate( bones[0] ,'med.%s_base.c' % basename, 'head' ,4.0 , 'z')
        #hip_ctr = duplicator.duplicate( bones[0] ,'ctr.hip.c', 'copy' ,1.0 , 'sel')
        #constraint.do_const('COPY_TRANSFORMS' , bones[0], hip_ctr,  'WORLD')

        #Second, Generate IK bone chain and tweak controller from Spine bones.
        spinearray = []
        tweakarray = []

        for i,b in enumerate(bones):
            sp = duplicator.duplicate( b ,'med.%s_%02d.c' % ( basename , i+1 ), 'copy' , 1 , 'sel')
            tw = duplicator.duplicate( b ,'ctr.tweak.%s_%02d.c' % ( basename , i+1 ) , 'tail' , 1.5 , 'z')

            parent(tw,sp)
            spinearray.append(sp)
            tweakarray.append(tw)

        #connect spine chain
        spine_num = len(spinearray)
        for i in range( spine_num ):
            parent(spinearray[i] , med_spine_c)

        #add tipbone
        tipbone = duplicator.duplicate( bones[-1] ,'med.%s_tip.c' % basename, 'tail' ,1.0 , 'sel')
        constraint.do_const( 'COPY_TRANSFORMS' , tipbone  ,bones[-1] , 'WORLD' , 1.0)
      

        inf = 1.0/spine_num
        for i in range( spine_num ):
            constraint.do_const( 'COPY_ROTATION' , bones[i], chest_ctr, 'LOCAL' ,(False,True,False) , (False,False,False) , inf)
            create_ik_modifier(bones[ i] , tweakarray[i] ,1)

        utils.mode_p()


        #for b in ( chest_ctr , base_ctr ):
        amt.pose.bones[chest_ctr].custom_shape = bpy.data.objects['rig.shape.circle.dir']
        #amt.pose.bones[chest_ctr].custom_shape_transform =amt.pose.bones[ tipbone ]

        for b,shape in zip( tweakarray , (*bones[1:] , tipbone)):
            amt.pose.bones[b].custom_shape = bpy.data.objects['rig.shape.board']
            amt.pose.bones[b].custom_shape_transform = amt.pose.bones[ shape ]

        #レイヤの設定
        #直接さわらない補助ボーン
        for bone in ( *spinearray , med_spine_c, tipbone):
            move_layer(bone,8)
        #move_layer(med_spine_c,8)


        for bone in (chest_ctr  ,  *tweakarray ):
            move_layer(bone,2)
        
        #parent
        utils.mode_e()
        #parent(hip_ctr,base_ctr)
        parent(chest_ctr,base)
        parent(tipbone,base)
        parent(med_spine_c,base)
        #parent(med_spine_c,hip_ctr)

        for bonename in (chest_ctr ,  *tweakarray):
            amt.data.edit_bones[bonename].show_wire = True

        #bpy.ops.object.mode_set(mode='POSE')
        utils.mode_p()
        for bonename in (chest_ctr , *tweakarray):
            amt.pose.bones[bonename].use_custom_shape_bone_size = False


        bpy.context.object.data.layers[0] = True
        bpy.context.object.data.layers[2] = True
        bpy.context.object.data.layers[8] = False

def setup_ue():
    leg_ = ('thigh_l' , )