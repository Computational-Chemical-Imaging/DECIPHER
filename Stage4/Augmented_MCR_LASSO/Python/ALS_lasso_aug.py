import numpy as np
from sklearn.linear_model import Lasso


def ALS_lasso_aug(y, S_init, lambda_value, augnum, iter_num, max_iter=100000):
    """
    Python version of MATLAB ALS_lasso_aug.m.

    MCR-ALS spectral unmixing with data augmentation. The concentration
    update uses pixel-wise LASSO followed by non-negativity projection; the
    spectral update uses least squares.
    """

    y = np.asarray(y, dtype=np.float64)
    S_init = np.asarray(S_init, dtype=np.float64)

    Nx, Ny, Nz = y.shape
    Nz_ref, k = S_init.shape

    if Nz_ref != Nz:
        raise ValueError(
            f"Spectral length mismatch: y has Nz={Nz}, but S_init has {Nz_ref} rows."
        )

    # MATLAB: D = reshape(y,[Nx*Ny, Nz]);
    D = np.reshape(y, (Nx * Ny, Nz), order="F")

    # MATLAB: D_aug = [D; repmat(S_init,1,augnum)'];
    # This repeats the k reference spectra augnum times as augmented spectra.
    D_aug = np.vstack((D, np.tile(S_init.T, (augnum, 1))))

    N = D_aug.shape[0]
    S = S_init.copy()
    C_2D = np.zeros((N, k), dtype=np.float64)

    print("Iter \t residualC \t residualS")

    for ii in range(iter_num):
        C_2D_old = C_2D.copy()
        S_old = S.copy()

        # Update C by LASSO for each spectrum.
        for i in range(N):
            y_sp = D_aug[i, :]

            model = Lasso(
                alpha=lambda_value,
                fit_intercept=False,
                positive=False,
                max_iter=max_iter,
                selection="cyclic"
            )
            model.fit(S, y_sp)

            # MATLAB: c_single_pixel = max(c_single_pixel,0);
            C_2D[i, :] = np.maximum(model.coef_, 0)

        # Update S by least squares frame by frame.
        for i in range(Nz):
            y_sf_aug = D_aug[:, i]
            s_single_frame, _, _, _ = np.linalg.lstsq(C_2D, y_sf_aug, rcond=None)
            S[i, :] = s_single_frame

        residualC = np.sqrt(np.sum((C_2D - C_2D_old) ** 2)) / np.sqrt(Nx * Ny * k)
        residualS = np.sqrt(np.sum((S - S_old) ** 2)) / np.sqrt(Nz * k)

        print(f"{ii + 1:3d} \t {residualC:3.5e} \t {residualS:3.5e}")

    C_2D_out = C_2D[: Nx * Ny, :]
    C_out = np.reshape(C_2D_out, (Nx, Ny, k), order="F")

    return C_out, S
