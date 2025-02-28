import glob
import os
from argparse import ArgumentParser

from tqdm import tqdm

# Read input mesh
parser = ArgumentParser()
parser.add_argument('root_dir', type=str)
args = parser.parse_args()

# Call dataset generation
for model in tqdm(glob.glob(f"{args.root_dir}/object/*.obj")):
    # Choose output directory
    output_dir = os.path.splitext(model)[0].replace("object", "synthetic_fracture")  # 确定输出文件夹
    os.makedirs(output_dir, exist_ok=True)

    from scripts.context import fracture_utility as fracture

    interior = model.replace("object", "interior")

    fracture.generate_fractures(model, interior, num_modes=5, num_impacts=5,
                                output_dir=output_dir, verbose=True, compressed=False, cage_size=2000,
                                volume_constraint=0.00)

    del fracture
