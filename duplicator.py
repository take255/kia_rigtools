import bpy
from bpy.props import ( EnumProperty , FloatProperty , BoolProperty)
from mathutils import Vector
import imp

from . import utils
imp.reload(utils)


UNIT_VECTOR={
    'x':(1,0,0),
    '-x':(-1,0,0),
    'y':(0,1,0),
    '-y':(0,-1,0),
    'z':(0,0,1),
    '-z':(0,0,-1),
}

#ボーンをコピーして新ボーンの名前を返す
#def duplicate(bonename , bonename , mode ,length_ratio , direction , use_deform):
def duplicate(*args):
    bonename = args[0]
    new_name = args[1]
    mode = args[2]
    length_ratio  = args[3]
    direction  = args[4]

    use_deform = False
    if len(args) > 5:
        use_deform = args[5]

    amt = bpy.context.object
    utils.mode_e()
    root = utils.rigroot()

    bone = amt.data.edit_bones[bonename]

    length = bone.length
    bonehead = Vector(bone.head)#Vectorで新規にしないと内容が書き換わることがある
    bonetail = Vector(bone.tail)
    vec = Vector(bonetail-bonehead)
    vec.normalize()
    boneroll = bone.roll

    #ボーン生成
    target = amt.data.edit_bones.new( new_name )
    target.parent = root
    target.use_deform = use_deform

    #new_name = target.name

    #radioでボーンの位置や姿勢を決める
    #Length 選択された骨の長さ
    #self.length_ratio　入力から取得
    if mode == 'copy':
        target.head = bonehead
        target.tail = bonehead + vec*length * length_ratio
        #target.roll = boneroll

    if mode == 'head':
        target.head = bonehead

        if direction != 'sel':
            target.tail = bonehead + Vector(UNIT_VECTOR[direction])*length * length_ratio
        else:
            target.tail = bonehead + vec*length * length_ratio

    if mode == 'tail':
        target.head = bonetail

        if direction != 'sel':
            target.tail = bonetail + Vector(UNIT_VECTOR[direction])*length * length_ratio
        else:
            target.tail = bonetail + vec*length * length_ratio

    target.roll = boneroll

    #utils.mode_p()
    #amt.data.bones[new_name].use_deform = False
    
    #utils.mode_e()
    return target.name

def constraint(source_name , target_name , const_type , space ,axis_x , axis_y , axis_z):
    bpy.ops.object.mode_set(mode='POSE')
    amt = bpy.context.object
    source = amt.pose.bones[source_name]
    target = target_name

    c =source.constraints.new(const_type)
    c.target = amt
    c.subtarget = target
    c.target_space = space
    c.owner_space = space

    if const_type != 'COPY_TRANSFORMS':
        if axis_x:
            c.use_x = True
        else:
            c.use_x = False

        if axis_y:
            c.use_y = True
        else:
            c.use_y = False

        if axis_z:
            c.use_z = True
        else:
            c.use_z = False    


class KIARIGTOOLS_MT_duplicator(bpy.types.Operator):
    """リストに入っているボーンを対象に複製を行う"""
    bl_idname = "kiarigtools.duplicator"
    bl_label = "duplicator"

    bool_const : BoolProperty(name="コンストレインする")
    bool_parent : BoolProperty(name="ペアレントを保持")

    radio : EnumProperty(items= (('copy', 'COPY', '選択ボーンをそのまま複製'),
                                           ('head', 'HEAD', '選択ボーンのheadの位置に生成'),
                                           ('tail', 'TAIL', '選択ボーンのtailの位置に生成'),
                                           ('mirror', 'MIRROR', 'Xミラーコピー')),
                                            name = "radio buttons")

    radio2 : EnumProperty(items= ( ('sel','SEL','選択したボーンの向きに合わせる'),
                                            ('x', 'X',''),
                                            ('y','Y',''),
                                            ('z','Z',''),
                                            ('-x', '-X',''),
                                            ('-y','-Y',''),
                                            ('-z','-Z',''),
                                            ),
                                   name = "radio buttons2")

    const_type : EnumProperty(items = (
    ('COPY_TRANSFORMS','TRANSFORM',''),
    ('COPY_ROTATION','ROTATION',''),
    ('COPY_LOCATION','LOCATION',''),
    ),name = 'const_type')

    space : EnumProperty(items = (
    ('WORLD','WORLD',''),
    ('LOCAL','LOCAL',''),
    ),name = 'space')

    axis_x : BoolProperty(name="X" ,  default = True)
    axis_y : BoolProperty(name="Y" ,  default = True)
    axis_z : BoolProperty(name="Z" ,  default = True)

    length_ratio : FloatProperty(name="骨の長さ（選択ボーンに対する割合）", default=1.0)

    def draw(self, context) :
        layout = self.layout
        layout.prop(self, "radio", expand=True)#Expandがラジオボタンにするフラグ
        layout.label(text = "複製ボーンの向き(COPY以外の場合有効)")
        layout.prop(self, "radio2", expand=True)
        layout.prop(self, "length_ratio")
        layout.prop(self, "bool_parent")

        box = layout.row().box()
        box.prop(self, "bool_const")
        box.prop(self, "const_type")
        box.prop(self, "space")
        row = box.row(align=False)
        row.prop(self, "axis_x")
        row.prop(self, "axis_y")
        row.prop(self, "axis_z")

        mode = self.radio


    def execute(self, context):

        if self.radio == 'mirror':
            self.mirrorCopy()
        else:
            self.copy()
        return{'FINISHED'}
        

    #transform.mirrorでカーソルをセンターにもってくる必要がある
    #名前をL>Rに変える
    def mirrorCopy(self): 

        # L => R　にリネーム
        #末尾が _L もしくは　中間に _L_　
        newnameArray = []
        for source in bpy.context.selected_bones:
            name = newname = source.name

            for sign in (("_L" , "_R") , ("_R" , "_L") , ("_l" , "_r") , ("_r" , "_l")):
                if name[-2:] == sign[0]:
                    newname = name[:-2] + sign[1]
                elif name.find( sign[0] + '_' ) != -1:
                    newname = name.replace(sign[0] + '_' , sign[1] + '_')

            newnameArray.append(newname)

        utils.cursorOrigin()

        bpy.ops.armature.duplicate_move()        
        utils.mirrorBoneXaxis()

        for source,newname in zip(bpy.context.selected_bones,newnameArray):
            source.name = newname


    def copy(self):
        new_name = 'ctr.Bone'
        bonearray =[]

        for bone in utils.get_selected_bones():
            bonename = bone.name
            new_name = 'ctr.bone.' + bonename
            targetname = duplicate(bonename , new_name , self.radio ,self.length_ratio , self.radio2)
            bonearray.append([bonename,targetname])


        #コンストレイン
        if self.bool_const:
            bpy.ops.object.mode_set(mode='POSE')
            for bone in bonearray:
                constraint(bone[0] , bone[1] , self.const_type , self.space ,self.axis_x , self.axis_y , self.axis_z)


    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


def register():
    bpy.utils.register_class(KIARIGTOOLS_MT_duplicator)

def unregister():
    bpy.utils.unregister_class(KIARIGTOOLS_MT_duplicator)

