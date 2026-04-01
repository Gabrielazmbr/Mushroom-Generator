import numpy as np
import pyvista as pv


def plot(curve):
    # Convert to PyVista Line and Display
    plotter = pv.Plotter()
    line = pv.Spline(curve, n_points=len(curve))
    plotter.add_mesh(line, color="green", line_width=3)

    # Display grid
    plotter.add_axes()
    plotter.show_grid()
    plotter.show()


def plot_mesh(verts, faces, color="white", smooth=True, show_points=False):
    verts = np.asarray(verts)
    faces = np.asarray(faces, dtype=int)

    if faces.size == 0:
        pl = pv.Plotter()
        line = (
            pv.Spline(verts, n_points=len(verts))
            if verts.shape[0] > 1
            else pv.PolyData(verts)
        )
        pl.add_mesh(line, color="green", line_width=3)
        pl.add_axes()
        pl.show_grid()
        pl.show()
        return

    faces_vtk = np.hstack([np.full((faces.shape[0], 1), 3, dtype=int), faces]).astype(
        np.int64
    )
    faces_vtk = faces_vtk.reshape((-1,))

    mesh = pv.PolyData(verts, faces_vtk)
    mesh.compute_normals(cell_normals=False, inplace=True)
    plotter = pv.Plotter()
    plotter.add_mesh(mesh, color=color, smooth_shading=smooth, show_edges=False)

    if show_points:
        plotter.add_mesh(
            pv.PolyData(np.asarray(verts).reshape(-1, 3)),
            color="red",
            point_size=6,
            render_points_as_spheres=True,
        )

    plotter.add_axes()
    plotter.show_grid()
    plotter.show()


def visualize_pyvista(X, Y, Z, color="red", show_edges=True):
    grid = pv.StructuredGrid(X, Y, Z)
    # Create a plotter and add the mesh
    plotter = pv.Plotter()
    plotter.add_mesh(grid, color=color, show_edges=show_edges)
    # Display grid
    plotter.add_axes()
    plotter.show_grid()
    plotter.show()


def plot_lines(gill_array, lengths, color="red", line_width=2):
    plotter = pv.Plotter()
    gills_count = gill_array.shape[0]
    for i in range(gills_count):
        n = int(lengths[i])
        if n < 2:
            continue
        pts = gill_array[i, :n, :]
        # Use a Spline or direct PolyData line; Spline smooths the line.
        line = pv.Spline(pts, n_points=max(n, 2))
        plotter.add_mesh(line, color=color, line_width=line_width)
    plotter.add_axes()
    plotter.show_grid()
    plotter.show()
