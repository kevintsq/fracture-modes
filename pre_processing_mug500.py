import glob
import os
from multiprocessing import Pool

import pyvista as pv
from fast_simplification import simplify_mesh
from psutil import cpu_count
from tqdm import tqdm

# 路径配置
zip_folder = "/mnt/NAS/data/MUG500"
output_folder = os.path.join(zip_folder, "objects")


def process_single_zip(file_path) -> str:
    try:
        mesh = pv.read(file_path)
        mesh = simplify_mesh(mesh, 0.9)
        out_path = os.path.join(output_folder, os.path.basename(file_path).replace("_clear.stl", ".ply"))
        os.makedirs(output_folder, exist_ok=True)
        mesh.save(out_path)
        return f"[Done] {file_path}"
    except Exception as e:
        return f"[Error] {file_path}: {str(e)}"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--rank", type=int, default=0)
    args = parser.parse_args()
    rank = args.rank

    # 机器设置
    cpus = [16, 16, 12, 12, 10, 32]

    items = list(sorted(glob.glob(os.path.join(zip_folder, "*/*_clear.stl"))))

    # === 按 rank 分配任务 ===
    total = sum(cpus)
    sizes = [round(len(items) * c / total) for c in cpus]

    # 调整最后一块，确保总和正确
    sizes[-1] = len(items) - sum(sizes[:-1])

    # 得到每段的起止 index
    start_idx = sum(sizes[:rank])
    end_idx = start_idx + sizes[rank]
    items = items[start_idx:end_idx]

    with Pool(processes=cpu_count(logical=False)) as pool:
        for result in tqdm(pool.imap_unordered(process_single_zip, items), total=len(items), desc=f"Rank {rank} Processing"):
            print(result)
