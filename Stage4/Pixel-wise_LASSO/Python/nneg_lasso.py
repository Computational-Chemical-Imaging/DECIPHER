import numpy as np
from sklearn.linear_model import Lasso


def nneg_lasso(y, S, lambda_value, a=1, iter_num=5, max_iter=100000):
    """
    LASSO spectral unmixing with non-negativity constraint.

    Python version of MATLAB nneg_lasso.m.

    This function performs pixel-wise LASSO spectral unmixing on
    hyperspectral images. An L1 norm is added as a pixel-wise constraint,
    and non-negativity is imposed on the concentration maps using ADMM.

    Parameters
    ----------
    y : ndarray
        3D hyperspectral image stack with shape [Nx, Ny, Nz].
    S : ndarray
        Spectral profiles for pure components with shape [Nz, k].
    lambda_value : float
        Sparsity level for the images.
    a : float
        ADMM parameter controlling convergence speed. Default is 1.
    iter_num : int
        Number of iterations for ADMM update.
    max_iter : int
        Maximum iterations for sklearn Lasso solver.

    Returns
    -------
    C : ndarray
        Concentration maps with shape [Nx, Ny, k].
    """

    y = np.asarray(y, dtype=np.float64)
    S = np.asarray(S, dtype=np.float64)

    Nx, Ny, Nz = y.shape
    ref_Nz, k = S.shape

    if ref_Nz != Nz:
        raise ValueError(
            f"Spectral length mismatch: y has Nz={Nz}, but S has {ref_Nz} rows."
        )

    N = Nx * Ny * Nz

    C = np.zeros((Nx, Ny, k), dtype=np.float64)
    u = np.zeros((Nx, Ny, k), dtype=np.float64)
    vhat = np.zeros((Nx, Ny, k), dtype=np.float64)
    R_positive = np.zeros((Nx, Ny, k), dtype=np.float64)


    S_tilde = np.vstack((S, np.eye(k)))

    print("Iter \t residualC \t residualv \t residualu")

    for ii in range(iter_num):
        C_old = C.copy()
        vhat_old = vhat.copy()
        u_old = u.copy()

        # Update C.
        ctilde = vhat - u

        for i in range(Nx):
            for j in range(Ny):
                # MATLAB only refits all pixels on iteration 1,
                # and later refits pixels whose previous C had negatives.
                if ii == 0 or np.min(C_old[i, j, :]) < 0:
                    y_sp = y[i, j, :].reshape(-1)

                    rhs = np.concatenate(
                        (
                            y_sp,
                            np.sqrt(a) * ctilde[i, j, :].reshape(-1),
                        )
                    )

                    # MATLAB lasso solves:
                    # 1/(2N)*||rhs - S_tilde*c||^2 + lambda*||c||_1
                    # sklearn Lasso uses:
                    # 1/(2*n_samples)*||rhs - X*c||^2 + alpha*||c||_1
                    model = Lasso(
                        alpha=lambda_value,
                        fit_intercept=False,
                        positive=False,
                        max_iter=max_iter,
                        selection="cyclic",
                    )

                    model.fit(S_tilde, rhs)
                    C[i, j, :] = model.coef_

        # Update vhat.
        vhat = np.maximum(C + u, R_positive)

        # Update u.
        u = u + (C - vhat)

        # Calculate residuals.
        residualC = (1 / np.sqrt(N)) * np.sqrt(np.sum((C - C_old) ** 2))
        residualvhat = (1 / np.sqrt(N)) * np.sqrt(np.sum((vhat - vhat_old) ** 2))
        residualu = (1 / np.sqrt(N)) * np.sqrt(np.sum((u - u_old) ** 2))

        print(
            f"{ii + 1:3d} \t {residualC:3.5e} \t "
            f"{residualvhat:3.5e} \t {residualu:3.5e}"
        )

    return C
