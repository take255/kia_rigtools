import bpy
import imp
from bpy.props import ( FloatProperty , EnumProperty ,BoolProperty )
#from bpy.types import PropertyGroup


#def constraint(source_name , target_name_array , const_type , space ,axis_x , axis_y , axis_z):
#コンストレインを返す
def constraint(source_name , target_name , const_type , space ,axis_array , invert_array ):
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
        if axis_array[0]:
            c.use_x = True
        else:
            c.use_x = False

        if axis_array[1]:
            c.use_y = True
        else:
            c.use_y = False

        if axis_array[2]:
            c.use_z = True
        else:
            c.use_z = False   

        c.invert_x = invert_array[0]
        c.invert_y = invert_array[1]
        c.invert_z = invert_array[2]
    
    return c

#this function can expand argument nimber.
#const_type , source_name , target_name , space ,axis_array , invert_array , ratio
#const_type == COPY_LOCATION , source_name , target_name , space ,axis_array , invert_array , ratio
#const_type == COPY_ROTATION , source_name , target_name , space ,axis_array , invert_array , influence
#const_type == COPY_TRANSFORMS , source_name , target_name , space

def do_const(*args):
    amt = bpy.context.object
    bpy.ops.object.mode_set(mode='POSE')

    const_type = args[0]
    source = amt.pose.bones[args[1]]
    target = args[2]
    space  = args[3]

    
    c =source.constraints.new(const_type)
    c.target = amt
    c.subtarget = target
    c.target_space = space
    c.owner_space = space

    if const_type == 'COPY_LOCATION':
        c.head_tail = args[6]

    if const_type == 'COPY_ROTATION':
        if len(args) > 6:
            c.influence = args[6]


    if const_type != 'COPY_TRANSFORMS':
        axis_array = args[4]
        invert_array = args[5]

        if axis_array[0]:
            c.use_x = True
        else:
            c.use_x = False

        if axis_array[1]:
            c.use_y = True
        else:
            c.use_y = False

        if axis_array[2]:
            c.use_z = True
        else:
            c.use_z = False   

        c.invert_x = invert_array[0]
        c.invert_y = invert_array[1]
        c.invert_z = invert_array[2]
    
    return c

#コンストレインを返す
#map_form , map_to = lOCATION or ROTATION or SCALE
#
def constraint_transformation(source_name , target_name , const_type , space , map_from , map_to ,transform ):
    bpy.ops.object.mode_set(mode='POSE')
    amt = bpy.context.object
    source = amt.pose.bones[source_name]
    target = target_name

    c =source.constraints.new(const_type)
    c.target = amt
    c.subtarget = target
    c.target_space = space
    c.owner_space = space

 
    c.map_from = map_from
    c.map_to = map_to

    c.from_min_y_rot = -3.14159
    c.from_max_y_rot = 3.14159
    c.from_min_x_rot = -3.14159
    c.from_max_x_rot = 3.14159
    c.from_min_z_rot = -3.14159
    c.from_max_z_rot = 3.14159


    if transform[0] != 'Mute':
        c.to_min_x_rot = -3.14159
        c.to_max_x_rot = 3.14159

        c.map_to_x_from = transform[0]


    if transform[1] != 'Mute':
        c.to_min_y_rot = -3.14159
        c.to_max_y_rot = 3.14159

        c.map_to_y_from = transform[1]


    if transform[2] != 'Mute':
        c.to_min_z_rot = -3.14159
        c.to_max_z_rot = 3.14159

        c.map_to_y_from = transform[2]
    return c

# class ConstraintTools(bpy.types.Operator):
#     bl_idname = "rigtool.constrainttools"
#     bl_label = "コンストレインツール"

#     def execute(self, context):
#         return {'FINISHED'}

#     def invoke(self, context, event):
#         return context.window_manager.invoke_props_dialog(self)

#     def draw(self, context):
#         scn = context.scene
#         layout = self.layout

#         layout.operator("rigtool.setup_constraint")


#         row = layout.row()
#         row.alignment = 'EXPAND'

#         row.operator("rigtool.constraint_cleanup")
#         row.operator("rigtool.constraint_empty_cleanup")
#         # row.prop(scn, "const_disp_hide", icon='BLENDER', toggle=True)

        # layout.prop(scn, "const_influence", icon='BLENDER', toggle=True)


#Muteでコンストレイン無効にする
TRANSFORM_ITEM = (('X','X',''),('Y','Y',''),('Z','Z',''),('Mute','Mute',''))
TRANSFORM_TYPE = (('LOCATION','LOCATION',''),('ROTATION','ROTATION',''),('SCALE','SCALE',''))

#複数ボーンのコンストレイン適用ツール
#リストに複数のボーンを登録し、同時にコンストレインする。
#選択をコンストレイン元を指定、チェックされたものをコンストレインのターゲット
class KIARIGTOOLS_MT_constrainttools(bpy.types.Operator):
    """複数ボーンをコンストレインする\nリストに対象のボーンを登録して実行する\nボタンを押すとUIが起動する\n選択されたものをコンストレイン元とし、チェックされたものを対象とする。"""
    bl_idname = "kiarigtools.constrainttools"
    bl_label = "constraint tools"

    const_type : bpy.props.EnumProperty(items = (
    ('COPY_TRANSFORMS','TRANSFORM',''),
    ('COPY_ROTATION','ROTATION',''),
    ('COPY_LOCATION','LOCATION',''),
    ('TRANSFORM','TRANSFORMATION','')
    ),name = 'const_type')

    space : bpy.props.EnumProperty(items = (
    ('WORLD','WORLD',''),
    ('LOCAL','LOCAL',''),
    ),name = 'space')

    transform_x : bpy.props.EnumProperty(default ='X'  , items = TRANSFORM_ITEM , name = 'X')
    transform_y : bpy.props.EnumProperty(default ='Y'  ,items = TRANSFORM_ITEM , name = 'Y')
    transform_z : bpy.props.EnumProperty(default ='Z'  ,items = TRANSFORM_ITEM , name = 'Z')

    map_from : bpy.props.EnumProperty(default ='LOCATION'  ,items = TRANSFORM_TYPE , name = 'source')
    map_to : bpy.props.EnumProperty(default ='LOCATION'  ,items = TRANSFORM_TYPE , name = 'destination')


    use_x : BoolProperty(name="X" ,  default = True)
    use_y : BoolProperty(name="Y" ,  default = True)
    use_z : BoolProperty(name="Z" ,  default = True)

    invert_x : BoolProperty(name="X" ,  default = False)
    invert_y : BoolProperty(name="Y" ,  default = False)
    invert_z : BoolProperty(name="Z" ,  default = False)


    def draw(self, context) :
        layout = self.layout
        layout.prop(self, "const_type")
        layout.prop(self, "space")

        box = layout.row().box()
        row = box.row(align=False)
        row.prop(self, "use_x")
        row.prop(self, "use_y")
        row.prop(self, "use_z")

        box = layout.row().box()
        box.label(text = "Invert")
        row = box.row(align=False)
        row.prop(self, "invert_x")
        row.prop(self, "invert_y")
        row.prop(self, "invert_z")

        box = layout.row().box()
        box.label(text = "Transformation")
        #row = box.row(align=False)

        box.prop(self, "map_from")
        box.prop(self, "map_to")
        
        row = box.row(align=False)
        row.prop(self, "transform_x")
        row.label(text = '>>X')

        row = box.row(align=False)
        row.prop(self, "transform_y")
        row.label(text = '>>Y')

        row = box.row(align=False)
        row.prop(self, "transform_z")
        row.label(text = '>>Z')


    #チェックされたものを対象とする。
    #コンストレインの元は選択されたもの
    def execute(self, context):
       #ポーズモードにする
        bpy.ops.object.mode_set(mode = 'POSE')

        if lib.list_exists():
            amt = bpy.context.object
            first = lib.list_get_selected()
            allbone = lib.list_get_checked()

            allbone.remove(first)
            #source = amt.pose.bones[first]

            for tgt in allbone:

                if self.const_type == 'TRANSFORM':
                    constraint_transformation( tgt , first  ,self.const_type , self.space ,
                    self.map_from,self.map_to,
                    (self.transform_x , self.transform_y , self.transform_z) )
                else:
                    constraint(tgt , first  ,self.const_type , self.space ,
                    (self.use_x,self.use_y,self.use_z) ,
                    (self.invert_x , self.invert_y , self.invert_z)
                    )
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)



def register():
    bpy.utils.register_class(KIARIGTOOLS_MT_constrainttools)

def unregister():
    bpy.utils.unregister_class(KIARIGTOOLS_MT_constrainttools)
