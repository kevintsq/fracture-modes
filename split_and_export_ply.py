from argparse import ArgumentParser

import bpy
import os

def split_and_export_ply(input_filepath, output_folder):
    """ 在 Blender 无 GUI 模式下运行：
        - 读取 input.obj
        - 分离 mesh 的 connected parts
        - 将每个部分保存为独立的 PLY 文件
    """
    # 清除 Blender 现有的场景对象
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # 确保输出文件夹存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 导入 OBJ 文件
    bpy.ops.wm.obj_import(filepath=input_filepath)

    # 选取导入的主对象
    obj = bpy.context.selected_objects[0]  # 选取第一个对象作为主对象
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # 进入编辑模式并分离连接部分
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='LOOSE')
    bpy.ops.object.mode_set(mode='OBJECT')

    # 获取所有新分离的对象
    separated_objects = [o for o in bpy.context.selected_objects]

    # 依次导出每个分离的网格部分
    for i, part in enumerate(separated_objects):
        bpy.ops.object.select_all(action='DESELECT')
        part.select_set(True)
        bpy.context.view_layer.objects.active = part

        output_path = os.path.join(output_folder, f"piece_{i+1}.ply")
        bpy.ops.wm.ply_export(
            filepath=output_path,
            apply_modifiers=True,
            export_selected_objects=True
        )

# ------------------------------
# 处理命令行参数
if __name__ == "__main__":
    # 获取传入的参数
    args = ArgumentParser()
    args.add_argument("input", type=str, help="输入 OBJ 文件路径")
    args.add_argument("output", type=str, help="输出文件夹路径")
    args = args.parse_args()

    # 运行处理函数
    split_and_export_ply(args.input, args.output)
