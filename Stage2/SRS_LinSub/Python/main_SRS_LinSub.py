# %% Step 0: Import packages

import numpy as np
import tifffile as tiff
import matplotlib.pyplot as plt


# %% Step 1: Load hyperspectral image

# Set input file type
#
# .txt --> hyperspectral text image in 2D montage
# .tif --> 3D tif image

datadir  = "Data/"
filename = "U87_CH_SRS_raw_drift_crtd_denoised"
filetype = ".txt"
Nz = 100  # Set number of frames in the hyperspectral image

input_path = datadir + filename + filetype

if input_path.lower().endswith((".tif", ".tiff")):
    y = tiff.imread(input_path)

    # tifffile often loads multi-page tif as [frames, height, width]
    # Convert to [height, width, frames] to match MATLAB
    if y.shape[0] == Nz:
        y = np.transpose(y, (1, 2, 0))

    y = y.astype(np.float64)

elif input_path.lower().endswith(".txt"):
    y_montage = np.loadtxt(input_path)

    Nx = y_montage.shape[0]
    total_columns = y_montage.shape[1]

    if total_columns % Nz != 0:
        raise ValueError(
            f"The number of columns ({total_columns}) is not divisible by Nz ({Nz})."
        )

    Ny = total_columns // Nz

    # MATLAB-style reshape:
    # y = permute(reshape(y_montage,[Nx,Ny,Nz]),[1,2,3]);
    y = np.reshape(y_montage, (Nx, Ny, Nz), order="F")

else:
    raise ValueError(f"Unsupported file type: {input_path}")

print("Loaded hyperspectral image shape:", y.shape)


# %% Step 2: Obtain background mask

# Project the image stack into 2D by spectral averaging
y_proj = np.mean(y, axis=2)

# Plot histogram of the projected image
plt.figure()
plt.hist(y_proj.ravel(), bins=100)
plt.xlabel("Mean intensity")
plt.ylabel("Pixel count")
plt.title("Histogram of spectrally averaged image")
plt.show()

# Set the threshold value using the intensity histogram
bkg_threshold = 0.29

# Generate background mask
BGmask = y_proj < bkg_threshold

# Plot the background mask
plt.figure()
plt.imshow(BGmask, cmap="gray")
plt.axis("image")
plt.axis("off")
plt.title("Background mask")
plt.show()

print("Number of background pixels:", np.sum(BGmask))


# %% Step 3: Obtain background spectrum and save

# Average all spectra in the background area
BG_spectrum = np.zeros(Nz)

for i in range(Nz):
    y_temp = y[:, :, i]
    BG_spectrum[i] = np.mean(y_temp[BGmask])

# Plot background spectrum
plt.figure()
plt.plot(np.arange(1, Nz + 1), BG_spectrum, linewidth=1.5)
plt.xlabel("Frame number")
plt.ylabel("Int (a.u.)")
plt.title("Background spectrum")
plt.show()

# Save the spectrum as the same format as Fiji/ImageJ csv file
bkg_output = np.column_stack((np.arange(1, Nz + 1), BG_spectrum))
output_path = datadir + "SRS_BKG.csv"
np.savetxt(
    output_path,
    bkg_output,
    delimiter=",",
    fmt=["%d", "%.8f"]
)

print("Background spectrum saved to: ", output_path)