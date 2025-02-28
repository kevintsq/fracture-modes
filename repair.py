import argparse

import pymesh
import pymeshfix
import trimesh


def pymesh2trimesh(m):
    return trimesh.Trimesh(m.vertices, m.faces)


def trimesh2pymesh(m):
    return pymesh.form_mesh(m.vertices, m.faces)


def repair_self_intersection(mt):
    if mt.is_watertight:
        return mt

    m = trimesh2pymesh(mt)
    m, _ = pymesh.remove_degenerated_triangles(m)
    mt = pymesh2trimesh(m)
    if mt.is_watertight:
        return mt

    m, _ = pymesh.remove_duplicated_vertices(m)
    mt = pymesh2trimesh(m)
    if mt.is_watertight:
        return mt

    m, _ = pymesh.remove_duplicated_faces(m)
    mt = pymesh2trimesh(m)
    if mt.is_watertight:
        return mt

    m = pymesh.resolve_self_intersection(m)
    return pymesh2trimesh(m)


def repair_watertight(mesh):
    """Attempt to repair a mesh using the default pymeshfix procedure"""
    mesh = pymeshfix.MeshFix(mesh.vertices, mesh.faces)
    mesh.repair(joincomp=True, remove_smallest_components=False)
    return trimesh.Trimesh(mesh.v, mesh.f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument(dest="input", type=str, help="Path to the input file.")
    parser.add_argument(dest="output", type=str, help="Path to the output file.")
    args = parser.parse_args()
    mesh = repair_watertight(
        trimesh.load(args.input),
    )
    mesh.export(args.output)
