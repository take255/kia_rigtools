import bpy
import imp
from bpy.props import ( StringProperty , CollectionProperty , BoolProperty)
from bpy.types import (PropertyGroup , Operator)

from . import utils
imp.reload(utils)


#---------------------------------------------------------------------------------------
#連番に対応
#連番指定していない時は選択されたものだけをリネーム
#---------------------------------------------------------------------------------------

class KIARIGTOOLS_MT_renamer(Operator):
    """リストに入力されたものを対象にする。"""
    bl_idname = "kiarigtools.renamer"
    bl_label = "renamer"
    bl_options = {'REGISTER', 'UNDO'}

    prop : StringProperty(name="part", maxlen=63)
    part : CollectionProperty(type=PropertyGroup)

    prop_role : StringProperty(name="role", maxlen=63)
    role : CollectionProperty(type=PropertyGroup)

    prop_sign : StringProperty(name="sign", maxlen=63)
    sign : CollectionProperty(type=PropertyGroup)

    prop_sub : StringProperty(name="sub", maxlen=63)
    sub : CollectionProperty(type=PropertyGroup)


    region = (
    'body',
    'arm',
    'leg',
    'hand',
    'clav',
    'spine',
    'chest',
    'foot',
    'toe',
    'base',
    'head',
    'neck',
    'hip',
    'hair',
    'Arm',
    'Thumb',
    'Index',
    'Middle',
    'Ring',
    'Pinky',

    )

    rolearray = (
    'ctr',
    'jnt',
    'attach',
    'med',#mediation(橋渡し)
    'sjnt'
    )

    signarray = (
    'l',
    'r',
    'c',
    'L',
    'R',
    'C'
    )

    subarray = (
    'switch',
    'pole',
    'base'
    )

    number : BoolProperty(name="連番付加しない" ,  default = False)
    underbar : BoolProperty(name="区切りを _ にする" ,  default = True)
    number_position : BoolProperty(name="LRの前の要素に連番" ,  default = True)
    decima_rule : BoolProperty(name="decimaの命名規則にする" ,  default = False)

    def execute(self, context):
        ui_list = context.window_manager.rig_ui_list
        if self.decima_rule == False:
            self.rename_regular(ui_list)
        else:
            self.rename_decima(ui_list)
        return {'FINISHED'}

    def rename_decima(self,ui_list):
        props = bpy.context.scene.kiarigtools_props
        amt=bpy.context.object

        utils.mode_e()
        if len(props.allbones) > 0 :
            for i,b in enumerate( props.allbones ):
                name_num = '%s_%s_%s_%01d' % ( self.prop_sign , self.prop ,self.prop_role, i )
                bone = amt.data.edit_bones[b.name]
                bone.name = name_num

            # #リストクリア
            # ui_list.clear()
            # #リスト登録
            # ui_list.add()

    def rename_regular(self,ui_list):

        #再選択用にリストを取得しておく
        allitems = lib.list_get_all()

        #区切り文字を . か　_
        sep = '.'
        if self.underbar:
            sep = '_'

        name = ''
        if self.prop_role != '':
            name += self.prop_role
        if self.prop != '':
            name += sep + self.prop
        if self.prop_sub != '':
            name += sep + self.prop_sub

        #LRの前に連番を入れる場合はこの処理をスルーし、連番を振ったあとに付加する。
        #連番を付加しない場合はそのままつけてしまう。
        #連番付加しない、ならLRの要素の前に連番のチェックあるなしにかかわらずLRを付加する

        if self.prop_sign != '' and self.number_position == False:#LRを後付けする場合(連番あり)
            name += sep + self.prop_sign

        elif self.number == True:#連番無の場合
            name += sep + self.prop_sign


        bpy.ops.object.mode_set(mode = 'EDIT')
        if len(ui_list.itemlist)>0:
            amt=bpy.context.object

            #基本連番指定する。連番指定無しで選択が一つの場合は番号を付けない。
            if not self.number:
                for i,bone in enumerate( lib.list_get_checked() ):
                    name_num = '%s%s%02d' % ( name , sep , i+1 )

                    #LRの前に連番を入れる場合はこの処理をスルーし、連番を振ったあとに付加する
                    if self.prop_sign != '' and self.number_position == True:
                        name_num += sep + self.prop_sign

                    jnt = amt.data.edit_bones[bone]
                    jnt.name = name_num
            else:
                jnt = amt.data.edit_bones[ lib.list_get_checked()[0] ]
                jnt.name = name


            # #リストクリア
            # ui_list.clear()

            #もとのリストのアイテムを再登録
            for name in allitems:
                if name in amt.data.edit_bones:
                    amt.data.edit_bones[name].select = True


            # #リスト登録
            # ui_list.add()


    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.prop_search(self, "prop_role", self, "role", icon='FONTPREVIEW')
        box.prop_search(self, "prop", self, "part", icon='FONTPREVIEW')
        box.prop_search(self, "prop_sub", self, "sub", icon='FONTPREVIEW')
        box.prop_search(self, "prop_sign", self, "sign", icon='FONTPREVIEW')
        box.prop(self, "underbar")
        box.prop(self, "number_position")
        box.prop(self, "number")
        box.prop(self, "decima_rule")

        box = layout.box()
        box.operator( 'kiarigtools.renamer_replace')
        



    #ポップアップが表示された時の処理
    def invoke(self, context, event):
        self.part.clear()
        self.role.clear()
        self.sign.clear()
        self.sub.clear()

        for p in self.rolearray:
            self.role.add().name = p

        for p in self.region:
            self.part.add().name = p

        for p in self.signarray:
            self.sign.add().name = p

        for p in self.subarray:
            self.sub.add().name = p

        return context.window_manager.invoke_props_dialog(self)


class KIARIGTOOLS_OT_renamer_replace(Operator):
    """文字列の置換"""
    bl_idname = "kiarigtools.renamer_replace"
    bl_label = ".>_"
    def execute(self, context):
        for b in utils.get_selected_bones():
            b.name = b.name.replace('.' , '_')
        return {'FINISHED'}       


classes = (
    KIARIGTOOLS_MT_renamer,
    KIARIGTOOLS_OT_renamer_replace
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
