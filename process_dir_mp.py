import glob
import os
import sys
import multiprocessing
import subprocess
from argparse import ArgumentParser

import psutil


def process_model(model):
    """ 处理单个 .obj 文件，并将其输出重定向到日志文件 """
    output_dir = os.path.splitext(model)[0].replace("object", "synthetic_fracture")  # 确定输出文件夹
    log_file = os.path.join(output_dir, "process.log")  # 每个模型的日志文件
    interior = model.replace("object", "interior")
    if not os.path.exists(interior):
        interior = None

    # 创建输出目录（如果不存在）
    os.makedirs(output_dir, exist_ok=True)

    # 构造 Python 命令，调用 fracture_utility 处理模型
    command = [
        sys.executable, "-c",  # 让 Python 运行一个字符串脚本
        f"""
from scripts.context import fracture_utility as fracture
fracture.generate_fractures(
    {model!r}, {interior!r}, num_modes=112, num_impacts=112,
    output_dir={output_dir!r}, verbose=True, compressed=False, cage_size=5000,
    volume_constraint=0.00)
"""
    ]

    # 运行子进程，重定向所有输出到 log_file
    with open(log_file, "w") as log:
        subprocess.run(command, stdout=log, stderr=log, text=True)

    return output_dir


def worker_process(cpus, task_queue):
    env = os.environ.copy()
    n_cpus = f"{len(cpus)}"
    env["OMP_NUM_THREADS"] = n_cpus
    env["MKL_NUM_THREADS"] = n_cpus
    env["OPENBLAS_NUM_THREADS"] = n_cpus
    env["VECLIB_MAXIMUM_THREADS"] = n_cpus
    env["NUMEXPR_NUM_THREADS"] = n_cpus

    while True:
        model = task_queue.get()
        if model is None:
            break

        print(f"Processing {model} on CPU {cpus}")
        output_dir = os.path.splitext(model)[0].replace("object", "synthetic_fracture")  # 确定输出文件夹
        log_file = os.path.join(output_dir, "process.log")  # 每个模型的日志文件
        interior = model.replace("object", "interior")
        if not os.path.exists(interior):
            interior = None

        # 创建输出目录（如果不存在）
        os.makedirs(output_dir, exist_ok=True)

        # 构造 Python 命令，调用 fracture_utility 处理模型
        command = [
            sys.executable, "-c",  # 让 Python 运行一个字符串脚本
            f"""
import psutil
psutil.Process().cpu_affinity({cpus!r})
from scripts.context import fracture_utility as fracture
fracture.generate_fractures(
    {model!r}, {interior!r}, num_modes=5, num_impacts=6,
    output_dir={output_dir!r}, verbose=True, compressed=False, cage_size=5000,
    volume_constraint=0.00)
        """
        ]

        # 运行子进程，重定向所有输出到 log_file
        with open(log_file, "w") as log:
            subprocess.run(command, env=env, stdout=log, stderr=log, text=True)

        print(f"Processed {model} on CPU {cpus}")


if __name__ == "__main__":
    # 读取输入参数
    parser = ArgumentParser()
    parser.add_argument('root_dir', type=str)
    parser.add_argument('--repeat', type=int, default=1)
    args = parser.parse_args()

    # 获取所有 .obj 文件
    models = glob.glob(f"{args.root_dir}/object/*.obj")
    task_queue = multiprocessing.Queue()

    for _ in range(args.repeat):
        for task in models:
            task_queue.put(task)

    n_cpus = psutil.cpu_count(logical=False)
    cpus = list(range(n_cpus))
    for _ in cpus:
        task_queue.put(None)

    processes = []
    for cpu in cpus:
        p = multiprocessing.Process(target=worker_process,
                                    args=((cpu, cpu + n_cpus), task_queue))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    # with multiprocessing.Pool(6) as pool, tqdm(total=len(models)) as pbar:
    #     for result in pool.imap_unordered(process_model, models):
    #         pbar.update()
    #         pbar.set_postfix_str(f"Processed {result}")
