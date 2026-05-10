# %% Section 0: Import packages

import os
import numpy as np
import tifffile as tiff
import matplotlib.pyplot as plt

from ALS_lasso_aug import ALS_lasso_aug
from interactive_residual_viewer_mcr import interactive_residual_viewer


# %% Section 1: Load basis spectra

# Calibrate the spectral window
# Find positions of two peaks (r1, r2) and frame number (f1, f2).
# Use standard chemicals for calibration. DMSO is used as example below.
# Users should change accordingly.

r1 = 2913
r2 = 2994
f1 = 40
f2 = 76
Nz = 100  # Set number of frames in the hyperspectral image

rpf = (r2 - r1) / (f2 - f1)
Wn = np.linspace(r1 - f1 * rpf, r2 + (Nz - f2 + 1) * rpf, Nz)

# Load spectral references

# Specify data directory for basis spectra and image.
# Default: data/
datadir = "data"

# Define names of the spectra basis.
# Names should be consistent with csv file names.
components = ["BSA", "TAG", "CHL", "RNA", "GLU"]


# Do not change the remaining lines in this section

# Build normalized reference matrix ref, shape [Nz, k]
k = len(components)
ref = np.zeros((len(Wn), k), dtype=np.float64)

for ii, cname in enumerate(components):
    ext = ".csv"
    spec_path = os.path.join(datadir, cname + ext)

    try:
        spec_temp = np.loadtxt(spec_path, delimiter=",")
    except ValueError:
        spec_temp = np.genfromtxt(spec_path, delimiter=",", skip_header=1)

    # Take the last column.
    if spec_temp.ndim == 2:
        spec_temp = spec_temp[:, -1]

    spec_min = np.min(spec_temp)
    spec_max = np.max(spec_temp)

    if spec_max == spec_min:
        raise ValueError(f"Reference spectrum {cname} has zero dynamic range.")

    ref[:, ii] = (spec_temp - spec_min) / (spec_max - spec_min)

# Plot normalized references with offsets
plt.figure()
for ii in range(k):
    plt.plot(Wn, ref[:, ii] + ii, linewidth=1, label=components[ii])

plt.xlabel("Raman shift (cm$^{-1}$)")
plt.ylabel("Int (a.u.)")
plt.legend()
plt.minorticks_on()
plt.title("Initial normalized reference spectra")
plt.show()



# %% Section 2: Load hyperspectral image

# Set input file type
#
# .txt --> hyperspectral text image in 2D montage
# .tif --> 3D tif image

filename = "U87_CH_SRS_raw_drift_crtd_denoised"
filetype = ".txt"


# Do not change the remaining lines in this section

input_path = os.path.join(datadir, filename + filetype)

if input_path.lower().endswith((".tif", ".tiff")):
    y = tiff.imread(input_path)

    # tifffile often loads multi-page tif as [frames, height, width].
    # Convert to [height, width, frames] to match MATLAB.
    if y.shape[0] == Nz:
        y = np.transpose(y, (1, 2, 0))

    y = y.astype(np.float64)
    Nx, Ny, _ = y.shape

elif input_path.lower().endswith(".txt"):
    y_montage = np.loadtxt(input_path)

    Nx = y_montage.shape[0]
    total_cols = y_montage.shape[1]

    if total_cols % Nz != 0:
        raise ValueError(
            f"The number of columns ({total_cols}) is not divisible by Nz ({Nz})."
        )

    Ny = total_cols // Nz

    # MATLAB-style reshape:
    # y = permute(reshape(y_montage,[Nx,Ny,Nz]),[1,2,3]);
    y = np.reshape(y_montage, (Nx, Ny, Nz), order="F")

else:
    raise ValueError(f"Unsupported file type: {input_path}")

C = np.zeros((Nx, Ny, k), dtype=np.float64)

print("Loaded hyperspectral image shape:", y.shape)


# %% Section 3: Subtract background

# Set the threshold value using the intensity histogram.
bgfilename = "SRS_BKG"
ext = ".csv"


# Do not change the remaining lines in this section

bg_path = os.path.join(datadir, bgfilename + ext)

try:
    BG_spectrum = np.loadtxt(bg_path, delimiter=",")
except ValueError:
    BG_spectrum = np.genfromtxt(bg_path, delimiter=",", skip_header=1)

if BG_spectrum.ndim == 2:
    BG_spectrum = BG_spectrum[:, -1]

if len(BG_spectrum) != Nz:
    raise ValueError(
        f"Background spectrum length ({len(BG_spectrum)}) does not match Nz ({Nz})."
    )

plt.figure()
plt.plot(Wn, BG_spectrum, linewidth=1.5)
plt.xlabel("Raman shift (cm$^{-1}$)")
plt.ylabel("Int (a.u.)")
plt.xlim([2820, 3030])
plt.title("Background spectrum")
plt.show()

y_sub = np.zeros_like(y, dtype=np.float64)

for i in range(Nz):
    y_sub[:, :, i] = y[:, :, i] - BG_spectrum[i]



# %% Section 4: Run augmented MCR-LASSO unmixing and plot results

# Set the sparsity level for all channels.
l = 1e-2

# Number of datapoints for augmentation, default is 1*Nx*Ny.
augnum = 1 * Nx * Ny

# Number of iterations for ALS.
iter_num = 3

# Do not change the remaining lines in this section

C, ref_new = ALS_lasso_aug(y_sub, ref, l, augnum, iter_num)

# Calculate the residual of unmixing.
C_2D = np.reshape(C, (-1, k), order="F")
y_recon_2D = C_2D @ ref_new.T
y_recon = np.reshape(y_recon_2D, (Nx, Ny, Nz), order="F")

y_res = y_sub - y_recon


# Plot concentration maps.
# MATLAB used C(:,:,1) for all channels.
# Here each channel is scaled independently for better Python display.
plt.figure(figsize=(10, 6))
for ii in range(k):
    img = C[:, :, ii]

    disp_min = np.percentile(img.reshape(-1), 0.3)
    disp_max = np.percentile(img.reshape(-1), 99.7)

    # Avoid empty display range
    if disp_max <= disp_min:
        disp_min = np.min(img)
        disp_max = np.max(img)

    plt.subplot(2, 3, ii + 1)
    plt.imshow(
        img,
        cmap="bone",
        vmin=disp_min,
        vmax=disp_max,
        aspect="equal"
    )
    plt.axis("off")
    plt.title(components[ii])
    plt.colorbar(fraction=0.046, pad=0.04)

plt.tight_layout()
plt.show()

# Plot updated normalized references with offsets.
plt.figure()
for ii in range(k):
    plt.plot(Wn, ref_new[:, ii] + ii, linewidth=1, label=components[ii])

plt.xlabel("Raman shift (cm$^{-1}$)")
plt.ylabel("Int (a.u.)")
plt.legend()
plt.minorticks_on()
plt.title("Updated reference spectra after augmented MCR-LASSO")
plt.show()


# %% Section 5: Residual Analysis

# For Spyder, use a Qt backend before running this section:
# %matplotlib qt
interactive_residual_viewer(y_sub, y_recon, Wn, proj_method="mean")


# %% Section 6: Output concentration maps and references

# Set output filepath.
opt_filepath = "output"
os.makedirs(opt_filepath, exist_ok=True)

# Do not change the remaining lines in this section

outExt = ".txt"

for ii, cname in enumerate(components):
    # Save the concentration maps as .txt image.
    outFile = os.path.join(opt_filepath, filename + "_" + cname + outExt)

    np.savetxt(
        outFile,
        C[:, :, ii],
        fmt="%.8f",
        delimiter="\t"
    )

    # Save the spectrum as the same format as in Fiji/ImageJ csv file.
    outSpecFile = os.path.join(opt_filepath, cname + "_out.csv")
    outSpecData = np.column_stack((np.arange(1, Nz + 1), ref_new[:, ii]))

    np.savetxt(
        outSpecFile,
        outSpecData,
        delimiter=",",
        fmt=["%d", "%.8f"]
    )

print(f"Saved outputs to: {opt_filepath}")

