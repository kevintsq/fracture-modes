import os
from argparse import ArgumentParser

from context import fracture_utility as fracture

# Read input mesh
parser = ArgumentParser()
parser.add_argument('input', type=str, default=r"data/bunny_oded.obj")
parser.add_argument('--interior', type=str, default=None)
args = parser.parse_args()

# Choose output directory
output_dir = os.path.splitext(os.path.basename(args.input))[0]

# Call dataset generation
fracture.generate_fractures(args.input, interior_filename=args.interior, num_modes=4, num_impacts=6,
                            output_dir=output_dir, verbose=True, compressed=False, cage_size=5000,
                            volume_constraint=0.00)
