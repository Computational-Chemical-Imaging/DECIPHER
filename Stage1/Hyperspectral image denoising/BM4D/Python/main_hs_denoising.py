# %% Section 0: Import packages

import numpy as np
import tifffile as tiff

# You may need to install bm4d first:
# pip install bm4d
from bm4d import bm4d


# %% Section 1: Load target image

datadir = "Data/"
filename = "U87_CH_SRS_raw_drift_crtd"
filetype = ".txt"
nframes = 100


########### Do not change the remaining lines in the section ###############
input_path = datadir + filename + filetype

if input_path.lower().endswith((".tif", ".tiff")):
    y = tiff.imread(input_path)

    # Convert from [frames, height, width] to [height, width, frames]
    # if needed
    if y.shape[0] == nframes:
        y = np.transpose(y, (1, 2, 0))

    y = y.astype(np.float64)

elif input_path.lower().endswith(".txt"):
    y_montage = np.loadtxt(input_path)

    r, c = y_montage.shape

    if c % nframes != 0:
        raise ValueError(
            f"The number of columns ({c}) is not divisible by nframes ({nframes})."
        )

    width = c // nframes

    # MATLAB-style reshape
    y = np.reshape(y_montage, (r, width, nframes), order="F")

else:
    raise ValueError(f"Unsupported file type: {input_path}")

print("Loaded image shape:", y.shape)


# %% Section 2: BM4D denoising

sigma = 0.05

y_denoised = bm4d(y, sigma)

print("Denoising finished.")
print("Denoised image shape:", y_denoised.shape)


# %% Section 3: Output denoised montage

height, width, frames = y_denoised.shape

y_denoised_montage = np.reshape(
    y_denoised,
    (height, width * frames),
    order="F"
)

output_path = datadir + filename + "_denoised.txt"

np.savetxt(output_path, y_denoised_montage, fmt="%.4f", delimiter="\t")

print(f"Denoised image saved to: {output_path}")