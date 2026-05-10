import numpy as np
import matplotlib.pyplot as plt


def interactive_residual_viewer(y, y_recon, wn=None, proj_method="mean"):
    """
    Interactive residual viewer.

    Click one point on the residual map to plot original, reconstructed,
    and residual spectra. Press Enter or right-click to stop.

    In Spyder, run `%matplotlib qt` before using this function.
    """

    if y.shape != y_recon.shape:
        raise ValueError("y and y_recon must have the same dimensions.")

    if wn is None:
        wn = np.arange(1, y.shape[2] + 1)
        xlabel_txt = "Frame index"
    else:
        wn = np.asarray(wn)
        xlabel_txt = "Wavenumber"

    residual = y - y_recon

    if proj_method.lower() == "mean":
        residual_map = np.mean(np.abs(residual), axis=2)
    elif proj_method.lower() == "max":
        residual_map = np.max(np.abs(residual), axis=2)
    elif proj_method.lower() == "sum":
        residual_map = np.sum(np.abs(residual), axis=2)
    else:
        raise ValueError('proj_method must be "mean", "max", or "sum".')

    fig, ax = plt.subplots()
    im = ax.imshow(residual_map, cmap="gray", aspect="equal")
    ax.set_title("Residual map: click a point, press Enter/right-click to stop")
    ax.axis("image")
    fig.colorbar(im, ax=ax)
    plt.show(block=False)

    count = 1

    while True:
        plt.figure(fig.number)
        pts = plt.ginput(1, timeout=0)

        if len(pts) == 0:
            print("Residual viewer closed.")
            break

        x, yy = pts[0]
        x = int(round(x))
        yy = int(round(yy))

        x = max(0, min(y.shape[1] - 1, x))
        yy = max(0, min(y.shape[0] - 1, yy))

        spec_y = y[yy, x, :]
        spec_recon = y_recon[yy, x, :]
        spec_res = residual[yy, x, :]

        plt.figure()
        plt.plot(wn, spec_y, linewidth=1.5, label="Original")
        plt.plot(wn, spec_recon, linewidth=1.5, label="Reconstructed")
        plt.plot(wn, spec_res, linewidth=1.2, label="Residual")
        plt.xlabel(xlabel_txt)
        plt.ylabel("Intensity")
        plt.legend()
        plt.grid(True)
        plt.title(f"Point {count}: x={x + 1}, y={yy + 1}")
        plt.show(block=False)

        count += 1
