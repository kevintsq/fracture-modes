import glob
import os
from argparse import ArgumentParser

from tqdm import tqdm

# Read input mesh
parser = ArgumentParser()
parser.add_argument('input', type=str)
args = parser.parse_args()

# Call dataset generation
for model in tqdm(glob.glob(f"{args.input}/*.obj")):
    # Choose output directory
    output_dir = os.path.splitext(model)[0]

    from scripts.context import fracture_utility as fracture

    fracture.generate_fractures(model, num_modes=10, num_impacts=0,
                                output_dir=output_dir, verbose=True, compressed=False, cage_size=2000,
                                volume_constraint=0.00)

    del fracture
