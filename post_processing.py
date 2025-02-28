import glob
import os
from argparse import ArgumentParser

import bpy
from tqdm import tqdm


def remove_inner_faces(ply_file):
    bpy.ops.wm.ply_import(filepath=ply_file)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_non_manifold()
    bpy.ops.mesh.delete(type='FACE')
    bpy.ops.mesh.select_interior_faces()
    bpy.ops.mesh.delete(type='FACE')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.edge_face_add()
    # bpy.ops.mesh.select_loose()
    # bpy.ops.mesh.delete(type='VERT')
    bpy.ops.object.mode_set(mode='OBJECT')
    output_name = ply_file.replace("synthetic_fracture", "fixed_fracture")
    os.makedirs(os.path.dirname(output_name), exist_ok=True)
    bpy.ops.wm.ply_export(
        filepath=output_name,
        export_selected_objects=True,
        ascii_format=True,
    )


if __name__ == '__main__':
    # Read input mesh
    parser = ArgumentParser()
    parser.add_argument('root_dir', type=str)
    args = parser.parse_args()

    # Call dataset generation
    for model in tqdm(glob.glob(f"{args.root_dir}/synthetic_fracture/*/*/*.ply")):
        remove_inner_faces(model)
