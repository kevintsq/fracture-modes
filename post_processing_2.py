import glob
import os
from argparse import ArgumentParser

import trimesh
from tqdm import tqdm

from repair import repair_self_intersection, repair_watertight

if __name__ == '__main__':
    # Read input mesh
    parser = ArgumentParser()
    parser.add_argument('root_dir', type=str)
    args = parser.parse_args()

    # Call dataset generation
    for model in tqdm(glob.glob(f"{args.root_dir}/fixed_fracture/*/*/*.ply")):
        mesh = trimesh.load(model)
        repair_watertight(mesh)
        output_name = model.replace("fixed_fracture", "fixed3_fracture")
        os.makedirs(os.path.dirname(output_name), exist_ok=True)
        mesh.export(output_name)
        # remove_inner_faces(model)
