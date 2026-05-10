# %% Section 0: Import packages

import numpy as np
import tifffile as tiff
import matplotlib.pyplot as plt
import time
import os
import crikit.pre as crikit
import crikit.utils.als_methods as als


# %% Section 1: Load CARS and NRB spectra

# Calibrate spectral window
# Find positions of two peaks (r1, r2) and frame number (f1, f2)
# Use standard chemicals for calibration. DMSO is used as example below
# Users should change accordingly

r1 = 2850
r2 = 2930
f1 = 44
f2 = 80
Nz = 150  # Set number of frames in the hyperspectral image

rpf = (r2 - r1) / (f2 - f1)  # spectral spacing per frame

# Define the spectral window in wavenumber
Wn = np.linspace(2850 - 43 * rpf, 2930 + 70 * rpf, Nz)

# Data directory
datadir = "Data/"

# Read NRB spectrum
NRB_filename = "CARS_BKG.csv"
NRB_path = os.path.join(datadir, NRB_filename)

# Read raw CARS spectrum
CARS_filename = "CARS_protein.csv"
CARS_path = os.path.join(datadir, CARS_filename)

def read_fiji_csv_intensity(csv_path):
    data = np.genfromtxt(csv_path, delimiter=",", names=True)
    return data[data.dtype.names[-1]]

I_NRB = read_fiji_csv_intensity(NRB_path)
I_CARS = read_fiji_csv_intensity(CARS_path)

print("Loaded NRB spectrum shape:", I_NRB.shape)
print("Loaded CARS spectrum shape:", I_CARS.shape)


# %% Section 2: Test Phase Retrieval on Example Spectra

PHASE_OFFSET = 0 # DC phase-offset (default = 0)
NORM_BY_NRB = 1 # Normalize retrieved spectrum by NRB/REF-- Removes the optical system response (default = 1)

KK_ideal = crikit.kkrelation(I_NRB,I_CARS,PHASE_OFFSET,NORM_BY_NRB) # Complex spectrum
KK_ideal_imag = KK_ideal.imag # "Raman-like# (imag{complex spectrum})

# Plot input spectra
plt.figure()
plt.plot(Wn, I_CARS, linewidth=2, label="CARS")
plt.plot(Wn, I_NRB, linewidth=2, label="NRB")
plt.legend()
plt.xlabel("Wavenumber (cm$^{-1}$)")
plt.ylabel("Signal Int (a.u.)")
plt.title("CARS and NRB Signal (Spectra)")
plt.show()

# Plot Raman-like spectra
plt.figure()
plt.plot(Wn, KK_ideal_imag, linewidth=2, label="Retrieved")
plt.legend()
plt.xlabel("Wavenumber (cm$^{-1}$)")
plt.ylabel("Raman-Like Int. (no units)")
plt.title("Raman-Like Spectra (Retrieved)")
plt.show()


# %% Section 3: Load Hyperspectral Image

# Set input file type
#
# .txt --> hyperspectral text image in 2D montage
# .tif --> 3D tif image

filename = "OVCAR5_CH_CARS_raw_shading_crtd_SPEND"
filetype = ".tif"

# Do not change the remaining lines in this section

input_path = os.path.join(datadir, filename + filetype)

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


# %% Section 4: Apply KK to the whole image

# Get dimensions of the image
xx, yy, _ = y.shape

y_kk = np.zeros_like(y, dtype=np.float64)

start_time = time.time()

# Run KK at each pixel
for ii in range(xx):
    for jj in range(yy):
        I_CARS = y[ii, jj, :]
        KK_ideal = crikit.kkrelation(I_NRB,I_CARS,PHASE_OFFSET,NORM_BY_NRB) # Complex spectrum
        KK_ideal_imag = KK_ideal.imag # "Raman-like# (imag{complex spectrum})        
        y_kk[ii, jj, :] = KK_ideal_imag

elapsed_time = time.time() - start_time

print(f"KK retrieval finished in {elapsed_time:.2f} seconds.")


# %% Section 5: Output

# The output image is stored in montage text image double format

y_kk_montage = np.reshape(
    y_kk,
    (y.shape[0], y.shape[1] * y.shape[2]),
    order="F"
)

output_path = datadir + filename + "_kk.txt"

np.savetxt(
    output_path,
    y_kk_montage,
    fmt="%.4f",
    delimiter="\t"
)

print(f"KK-retrieved image saved to: {output_path}")
