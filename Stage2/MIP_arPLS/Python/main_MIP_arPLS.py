# %% Section 0: Import packages

import numpy as np
import tifffile as tiff
import matplotlib.pyplot as plt
import time
import os

from arPLS_baseline_v0 import arpls_baseline_v0
#import crikit.utils.als_methods as als


# %% Section 1: Load MIP spectra

datadir = "Data/"
spec_filename = "Single_Spec_sample.csv"

spec_path = os.path.join(datadir, spec_filename)

def read_fiji_csv_intensity(csv_path):
    data = np.genfromtxt(csv_path, delimiter=",", names=True)
    return data[data.dtype.names[-1]]

raw_spec = read_fiji_csv_intensity(spec_path)

Nz = len(raw_spec)

print("Loaded raw spectrum length:", Nz)


# %% Section 2: Fine tune parameters using single-pixel spectra

smoothness_param = 1e3  # smoothness parameter, default 1e3
min_diff = 1e-6         # break iterations if difference is less than min_diff


bkg_ar = arpls_baseline_v0(raw_spec, smoothness_param, min_diff)
#[bkg_ar, als_method] = als.als_baseline(np.angle(raw_spec), smoothness_param, min_diff

peak_ar = raw_spec - bkg_ar

plt.figure()
plt.plot(bkg_ar, label="bkg")
plt.plot(peak_ar, label="signal")
plt.plot(raw_spec, label="Raw Spec")
plt.legend()
plt.xlabel("Frame number")
plt.ylabel("Intensity")
plt.title("arPLS baseline removal on example spectrum")
plt.show()


# %% Section 3: Load Hyperspectral Image

# Set input file type
#
# .txt --> hyperspectral text image in 2D montage
# .tif --> 3D tif image

filename = "G2_MIP_DN_stab"
filetype = ".tif"

#
# Do not change the remaining lines in this section

input_path = datadir + filename + filetype

if input_path.lower().endswith((".tif", ".tiff")):
    y = tiff.imread(input_path)

    # tifffile often loads multi-page tif as [frames, height, width].
    # Convert to [height, width, frames] to match MATLAB.
    if y.shape[0] == Nz:
        y = np.transpose(y, (1, 2, 0))

    y = y.astype(np.float64)

elif input_path.lower().endswith(".txt"):
    y_montage = np.loadtxt(input_path)

    r, c = y_montage.shape

    if c % Nz != 0:
        raise ValueError(
            f"The number of columns ({c}) is not divisible by Nz ({Nz})."
        )

    y = np.reshape(y_montage, (r, c // Nz, Nz), order="F")

else:
    raise ValueError(f"Unsupported file type: {input_path}")

#

print("Loaded hyperspectral image shape:", y.shape)


# %% Section 4: Apply arPLS to the whole image

# Get dimensions of the image
xx, yy, _ = y.shape

y_arpls = np.zeros_like(y, dtype=np.float64)

start_time = time.time()

# Run arPLS at each pixel
for ii in range(xx):
    for jj in range(yy):
        pixel_spec = y[ii, jj, :]

        pixel_bkg_ar = arpls_baseline_v0(
            pixel_spec,
            smoothness_param,
            min_diff
        )

        pixel_peak_ar = pixel_spec - pixel_bkg_ar

        y_arpls[ii, jj, :] = pixel_peak_ar

elapsed_time = time.time() - start_time

print(f"arPLS correction finished in {elapsed_time:.2f} seconds.")


# %% Section 5: Output

# The output image is stored in montage text image double format

y_arpls_montage = np.reshape(
    y_arpls,
    (y.shape[0], y.shape[1] * y.shape[2]),
    order="F"
)

output_path = filename + "_arpls.txt"

np.savetxt(
    output_path,
    y_arpls_montage,
    fmt="%.4f",
    delimiter="\t"
)

print(f"arPLS-corrected image saved to: {output_path}")
