import numpy as np
from scipy import sparse
from scipy.linalg import cho_factor, cho_solve
from scipy.special import expit


def arpls_baseline_v0(signal, smoothness_param=1e3, min_diff=1e-6):
    """
    Python version of MATLAB arPLS_baseline_v0.m using Cholesky solving.

    Asymmetric reweighted penalized least squares baseline removal.

    Parameters
    ----------
    signal : ndarray
        1D input spectrum.
    smoothness_param : float
        Smoothness parameter. MATLAB default is 1e3.
    min_diff : float
        Stop iterations if relative weight-vector change is below this value.
        MATLAB default is 1e-6.

    Returns
    -------
    baseline : ndarray
        Estimated arPLS baseline.
    """

    ORDER = 2
    MAX_ITER = 100

    signal = np.asarray(signal, dtype=np.float64).ravel()
    signal_length = len(signal)

    if signal_length < 3:
        raise ValueError(
            "Signal length must be at least 3 for second-order difference."
        )

    difference_matrix = sparse.diags(
        diagonals=[
            np.ones(signal_length),
            -2 * np.ones(signal_length),
            np.ones(signal_length),
        ],
        offsets=[0, 1, 2],
        shape=(signal_length - ORDER, signal_length),
        format="csc",
    )

    minimization_matrix = (
        smoothness_param * difference_matrix.T @ difference_matrix
    ).toarray()

    penalty_vector = np.ones(signal_length, dtype=np.float64)
    baseline = np.zeros(signal_length, dtype=np.float64)

    for _ in range(MAX_ITER):

        penalty_matrix = np.diag(penalty_vector)
        A = penalty_matrix + minimization_matrix

        try:
            chol_factor = cho_factor(A, lower=False, check_finite=False)
        except np.linalg.LinAlgError:
            break

        baseline = cho_solve(
            chol_factor,
            penalty_vector * signal,
            check_finite=False,
        )

        d = signal - baseline

        # Negative residuals
        dn = d[d < 0]

        if dn.size == 0:
            break

        m = np.mean(dn)
        s = np.std(dn)

        if s == 0 or not np.isfinite(s):
            break

        z = 2.0 * (d - (2.0 * s - m)) / s
        penalty_vector_temp = expit(-z)

        relative_diff = (
            np.linalg.norm(penalty_vector - penalty_vector_temp)
            / np.linalg.norm(penalty_vector)
        )

        if relative_diff < min_diff:
            penalty_vector = penalty_vector_temp
            break

        penalty_vector = penalty_vector_temp

    return baseline