# %% Section 0: Import packages

import os
import glob
import numpy as np
import tifffile as tiff
import matplotlib.pyplot as plt

from nneg_lasso import nneg_lasso


# %% Section 1: Load basis spectra

# Calibrate spectral window
# Find positions of two peaks (r1, r2) and frame number (f1, f2)
# Use standard chemicals for calibration.
# Users should change accordingly.

r1 = 1655
r2 = 1745
f1 = 20
f2 = 58
Nz = 80  # Set number of frames in the hyperspectral image

rpf = (r2 - r1) / (f2 - f1)
Wn = np.linspace(r1 - f1 * rpf, r2 + (Nz - f2 + 1) * rpf, Nz)

# Specify data directory for basis spectra and image.
datadir = "data"

# Define names of the spectra basis.
# Names should be consistent with csv file names.
components = ["BSA", "TAG", "CHL"]

bgfilename = "SRS_BKG"



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

    # Take the last column
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
plt.title("Normalized reference spectra")
plt.show()



# %% Stage 2: Set image batch directory and load file names

# Set input file type
#
# .txt --> hyperspectral text image in 2D montage
# .tif --> 3D tif image

imgdir = "imagedata"
filetype = ".tif"

# Equivalent of MATLAB:
# Filelist = dir([imgdir '*' filetype]);
filelist = glob.glob(os.path.join(imgdir, "*" + filetype))

# Sort by modification time, similar to MATLAB sorting by datenum
filelist = sorted(filelist, key=os.path.getmtime)

file_num = len(filelist)

print(f"Found {file_num} files.")

for f in filelist:
    print(os.path.basename(f))


# %% Stage 3: Begin the loop of spectral unmixing for all images

# Load background spectrum once before the loop
ext = ".csv"
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
plt.title("Background spectrum")
plt.show()


# Set LASSO parameters
lambda_value = 1e-2

# These two parameters do not need to change in most cases
a = 1
iter_num = 5

# Set output filepath
opt_filepath = "Output_maps"
os.makedirs(opt_filepath, exist_ok=True)


for jj, filepath in enumerate(filelist):

    print("\n========================================")
    print(f"Processing file {jj + 1}/{file_num}: {os.path.basename(filepath)}")
    print("========================================")

    #  Loop Step 1: Load image %%%%%%%%%

    filename = os.path.basename(filepath)

    if filename.lower().endswith((".tif", ".tiff")):
        y = tiff.imread(filepath)

        # tifffile often loads multi-page tif as [frames, height, width].
        # Convert to [height, width, frames] to match MATLAB.
        if y.shape[0] == Nz:
            y = np.transpose(y, (1, 2, 0))

        y = y.astype(np.float64)
        Nx, Ny, _ = y.shape

    elif filename.lower().endswith(".txt"):
        y_montage = np.loadtxt(filepath)

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
        raise ValueError(f"Unsupported file type: {filename}")

    print("Loaded image shape:", y.shape)


    # Loop Step 2: Subtract background %%%%%%%%%

    y_sub = np.zeros_like(y, dtype=np.float64)

    for i in range(Nz):
        y_sub[:, :, i] = y[:, :, i] - BG_spectrum[i]


    # Loop Step 3: Run pixel-wise LASSO %%%%%%%%%

    C = nneg_lasso(y_sub, ref, lambda_value, a, iter_num)

    # Calculate residual of unmixing
    C_2D = np.reshape(C, (-1, k), order="F")
    y_recon_2D = C_2D @ ref.T
    y_recon = np.reshape(y_recon_2D, (Nx, Ny, Nz), order="F")

    y_res = y_sub - y_recon


    # Display concentration maps and examine image quality

    plt.figure(figsize=(10, 5))
    
    for ii in range(k):
        img = C[:, :, ii]
    
        disp_min = np.percentile(img.reshape(-1), 0.3)
        disp_max = np.percentile(img.reshape(-1), 99.7)
    
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
    
    plt.suptitle(filename)
    plt.tight_layout()
    plt.show()
    

    # Loop Step 4: Output concentration and residual %%%%%%%%%

    # Remove file extension for cleaner output names
    filename_no_ext = os.path.splitext(filename)[0]

    # Output concentration maps
    outExt = ".txt"

    for ii, cname in enumerate(components):
        outFile = os.path.join(
            opt_filepath,
            filename_no_ext + "_" + cname + outExt
        )

        np.savetxt(
            outFile,
            C[:, :, ii],
            fmt="%.8f",
            delimiter="\t"
        )

    # Output residual map in montage format
    # Save as [Nx, Ny*Nz], consistent with previous hyperspectral montage format
    y_res_montage = np.reshape(
        y_res,
        (Nx, Ny * Nz),
        order="F"
    )

    residual_outfile = os.path.join(
        opt_filepath,
        filename_no_ext + "_residual.txt"
    )

    np.savetxt(
        residual_outfile,
        y_res_montage,
        fmt="%.4f",
        delimiter="\t"
    )

    print(f"Saved concentration maps and residual to: {opt_filepath}")

print("\nBatch processing finished.")