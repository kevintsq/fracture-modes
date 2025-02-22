# Include existing libraries
import os
import time

import gpytoolbox
# Libigl
import igl
import numpy as np
import tetgen
from gpytoolbox.copyleft import lazy_cage
from tqdm import tqdm

from .fracture_modes import FractureModes
from .fracture_modes_parameters import FractureModesParameters


def normalize_points(v, v_interior=None, center=None):
    """Make points fit into a side-length one cube

    Translate and scale and arbitrary point set so that it's contained tightly into a 1 by 1 # (by 1) cube, centered at zero by default. Simple yet useful to test code without worrying about scale-dependencies.

    Parameters
    ----------
    v : (n,d) numpy double array
        Matrix of point position coordinates
    center : numpy double array (optional, None by default)
        Where to center the mesh (if None, centered at zero)

    Returns
    -------
    u : numpy double array
        Normalized point position coordinates

    Examples
    --------
    ```python
    # Generate a mesh
    V, F = regular_square_mesh(3)
    # By default, this mesh is centered at zero and has side length two
    V = normalize_points(V,center=np.array([0.5,0.5]))
    # Now it's centered at (0.5,0.5) and has side length one
    ```
    """

    # Dimension:
    dim = v.shape[1]

    # First, move it to the first quadrant:
    amins = np.amin(v, axis=0)
    for dd in range(dim):
        v[:, dd] -= amins[dd]
    # Normalize for max length one
    v_max = np.max(v)
    v /= v_max
    # Center at zero
    amaxs = 0.5 * np.amax(v, axis=0)
    for dd in range(dim):
        v[:, dd] -= amaxs[dd]

    trans = 0
    if center is not None:
        trans = np.tile(center, (v.shape[0], 1))
        v += trans

    if v_interior is not None:
        assert v_interior.shape[1] == dim
        for dd in range(dim):
            v_interior[:, dd] -= amins[dd]
        v_interior /= v_max
        for dd in range(dim):
            v_interior[:, dd] -= amaxs[dd]
        if center is not None:
            v_interior += trans
        return v, v_interior

    return v, None

def generate_fractures(input_dir, interior_filename=None, num_modes=20, num_impacts=80, output_dir=None, verbose=True,
                       compressed=True, cage_size=4000, volume_constraint=(1 / 50)):
    """Randomly generate different fractures of a given object and write them to an output directory.
    
    Parameters
    ----------
    input_dir : str
        Path to a mesh file in .obj, .ply, or any other libigl-readable format
    num_modes : int (optional, default 20)
        Number of modes to consider (more modes will give more diversity to the fractures but will also be slower)
    num_impacts : int (optional, default 80)
        How many different random fractures to output
    output_dir : str (optional, default None)
        Path to the directory where all the fractures will be written
    compressed : bool (optional, default True)
        Whether to write the fractures as compressed .npy files instead of .obj. Needs to use `decompress.py` to decompress them afterwards.
    cage_size : int (optional, default 4000)
        Number of faces in the simulation mesh used
    volume_constraint : double (optional, default 0)
        Will only consider fractures with minimum piece volume larger than volume_constraint times the volume of the input. Values over 0.01 may severely delay runtime.
    """

    # directory = os.fsencode(input_dir)
    # np.random.seed(0)
    # for file in os.listdir(directory):
    filename = input_dir
    t0 = time.time()
    # try:
    t00 = time.time()
    v_fine, f_fine = igl.read_triangle_mesh(filename)
    v_interior, f_interior = None, None
    if interior_filename is not None:
        v_interior, f_interior = igl.read_triangle_mesh(interior_filename)
    # Let's normalize it so that parameter choice makes sense
    v_fine, v_interior = normalize_points(v_fine, v_interior)
    t01 = time.time()
    reading_time = t01 - t00
    if verbose:
        print(f"Read shape in {reading_time} seconds.")
    # Build cage mesh (this may actually be the bottleneck...)
    t10 = time.time()
    v, f = lazy_cage(v_fine, f_fine, num_faces=cage_size, grid_size=50)
    t11 = time.time()
    cage_time = t11 - t10
    if verbose:
        print(f"Built cage in {cage_time} seconds.")
    # Tetrahedralize cage mesh
    t20 = time.time()
    tgen = tetgen.TetGen(v, f)

    nodes, elements = tgen.tetrahedralize(minratio=1.5)
    t21 = time.time()
    tet_time = t21 - t20
    if verbose:
        print(f"Tetrahedralization in {tet_time} seconds.")

    # Initialize fracture mode class
    t30 = time.time()
    modes = FractureModes(nodes, elements, v_interior, f_interior)
    # Set parameters for call to fracture modes
    params = FractureModesParameters(num_modes=num_modes, verbose=False, d=1)
    # Compute fracture modes. This should be the bottleneck:
    modes.compute_modes(parameters=params)
    modes.impact_precomputation(v_fine=v_fine, f_fine=f_fine)

    filename_without_extension = os.path.splitext(os.path.basename(filename))[0]
    os.makedirs(output_dir, exist_ok=True)

    if compressed:
        modes.write_generic_data_compressed(output_dir)
        modes.write_segmented_modes_compressed(output_dir)
    else:
        modes.write_segmented_modes(output_dir, pieces=True)

    if num_impacts:
        t31 = time.time()
        mode_time = t31 - t30
        if verbose:
            print(f"Modes computed in {mode_time} seconds.")
        # # Generate random contact points on the surface
        B, FI = igl.random_points_on_mesh(1000 * num_impacts, v, f)
        B = np.vstack((B[:, 0], B[:, 0], B[:, 0], B[:, 1], B[:, 1], B[:, 1], B[:, 2], B[:, 2], B[:, 2])).T
        P = B[:, 0:3] * v[f[FI, 0], :] + B[:, 3:6] * v[f[FI, 1], :] + B[:, 6:9] * v[f[FI, 2], :]

        # sigmas = np.random.rand(1000 * num_impacts) * 1000

        # vols = igl.volume(modes.vertices, modes.elements)
        # total_vol = np.sum(vols)

        t40 = time.time()
        # Loop to generate many possible fractures
        # all_labels = np.zeros((modes.precomputed_num_pieces, num_impacts), dtype=int)
        running_num = 0
        with tqdm(range(P.shape[0]), desc="Generating Fractures") as pbar:
            for i in pbar:
                # t400 = time.time()
                    modes.impact_projection(contact_point=P[i, :], direction=np.array([1.0]), threshold=10)
                # min_volume = volume_constraint * total_vol / modes.n_pieces_after_impact
                # current_min_volume = total_vol
                # for i in range(modes.n_pieces_after_impact):
                #     current_min_volume = min(current_min_volume, np.sum(vols[modes.tet_labels_after_impact == i]))
                # valid_volume = (current_min_volume >= min_volume)
                # t401 = time.time()
                # # if verbose:
                # #     print("Impact simulation: ",round(t401-t400,3),"seconds.")
                # new = not (modes.piece_labels_after_impact.tolist() in all_labels.T.tolist())
                # # print(modes.piece_labels_after_impact.tolist() in all_labels.T.tolist())
                # if 1 < modes.n_pieces_after_impact < 100 and new and valid_volume:
                #     all_labels[:, running_num] = modes.piece_labels_after_impact
                    write_output_name = os.path.join(output_dir, f"fractured_{running_num}")
                    os.makedirs(write_output_name, exist_ok=True)
                    try:
                        if compressed:
                            modes.write_segmented_output_compressed(filename=write_output_name)
                        else:
                            modes.write_segmented_output(filename=write_output_name, pieces=True)
                    except ValueError:
                        continue
                    # t402 = time.time()
                    # if verbose:
                    #     print("Writing: ",round(t402-t401,3),"seconds.")
                    running_num += 1
                    pbar.set_postfix_str(f"{running_num}/{num_impacts}({running_num / num_impacts:.2%}) impacts generated")
                    if running_num >= num_impacts:
                        break
        # print(all_labels)
        t41 = time.time()
        impact_time = t41 - t40
        if verbose:
            print(f"Impacts computed in {impact_time} seconds.")
        t1 = time.time()
        total_time = t1 - t0
        if verbose:
            print(f"Generated {running_num} fractures for object {filename_without_extension} and wrote them into {output_dir} in {total_time} seconds.")
