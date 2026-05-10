# %% Section 0: Import packages

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import os


# %% Section 1: Load and preprocess data

datadir = "Data"
filename = "Raw_Spec_1600.csv"

input_path = os.path.join(datadir, filename)

# Load data
# If the file is comma-separated, use delimiter=","
# If it is tab- or space-separated, remove delimiter=","
try:
    y = np.loadtxt(input_path, delimiter=",")
except ValueError:
    y = np.loadtxt(input_path)

# If the input has multiple columns, keep the last column as intensity
if y.ndim == 2:
    y = y[:, -1]

# Normalize the input data
y = (y - np.min(y)) / (np.max(y) - np.min(y))

# MATLAB:
# x = linspace(1,size(y,1),size(y,1))';
x = np.linspace(1, len(y), len(y))

# Plot raw spectrum to determine number of peaks and initial positions
plt.figure()
plt.plot(x, y, linewidth=1.5)
plt.xlabel("Frame number")
plt.ylabel("Normalized intensity")
plt.title("Raw spectrum")
plt.show()


# %% Section 2: Define Gaussian model

# MATLAB/lmfit-style Gaussian:
# y = amplitude/(sigma*sqrt(2*pi)) * exp(-(x-center)^2/(2*sigma^2))

def gauss(x, amplitude, center, sigma):
    return (
        amplitude / (sigma * np.sqrt(2 * np.pi))
        * np.exp(-((x - center) ** 2) / (2 * sigma**2))
    )


def three_gaussian_model(
    x,
    g1_amplitude, g1_center, g1_sigma,
    g2_amplitude, g2_center, g2_sigma,
    g3_amplitude, g3_center, g3_sigma
):
    return (
        gauss(x, g1_amplitude, g1_center, g1_sigma)
        + gauss(x, g2_amplitude, g2_center, g2_sigma)
        + gauss(x, g3_amplitude, g3_center, g3_sigma)
    )


# Initial guess of peak amplitude, position, and width
startVals = [
    0.1, 26, 1,   # g1
    0.5, 51, 1,   # g2
    0.6, 40, 1    # g3
]

# Lower bound for peak amplitude, position, and width
lower_bounds = [
    0, 20, 0,
    0, 40, 0,
    0, 30, 0
]

# Upper bound for peak amplitude, position, and width
upper_bounds = [
    np.inf, 30, np.inf,
    np.inf, 60, np.inf,
    np.inf, 50, np.inf
]


# %% Section 3: Fit the spectral data with the model

popt, pcov = curve_fit(
    three_gaussian_model,
    x,
    y,
    p0=startVals,
    bounds=(lower_bounds, upper_bounds),
    maxfev=10000
)

# Create fitted curve
y_fit = three_gaussian_model(x, *popt)

# Evaluate individual components
g1 = gauss(x, popt[0], popt[1], popt[2])
g2 = gauss(x, popt[3], popt[4], popt[5])
g3 = gauss(x, popt[6], popt[7], popt[8])

# Goodness of fit
residuals = y - y_fit
ss_res = np.sum(residuals**2)
ss_tot = np.sum((y - np.mean(y))**2)
r_squared = 1 - ss_res / ss_tot

print("=== Fit coefficients ===")
print(f"g1_amplitude = {popt[0]:.6f}")
print(f"g1_center    = {popt[1]:.6f}")
print(f"g1_sigma     = {popt[2]:.6f}")
print(f"g2_amplitude = {popt[3]:.6f}")
print(f"g2_center    = {popt[4]:.6f}")
print(f"g2_sigma     = {popt[5]:.6f}")
print(f"g3_amplitude = {popt[6]:.6f}")
print(f"g3_center    = {popt[7]:.6f}")
print(f"g3_sigma     = {popt[8]:.6f}")

print("\n=== Goodness of fit ===")
print(f"R-squared = {r_squared:.6f}")
print(f"Residual sum of squares = {ss_res:.6e}")


# %% Section 4: Evaluate the results

plt.figure(figsize=(9, 5))

plt.plot(x, y, linewidth=1.5, label="Observed Spectrum")
plt.plot(x, y_fit, linewidth=1.5, label="Fitted Spectrum")

plt.plot(x, g1, "--", linewidth=1.2, label="g1_ (Gaussian)")
plt.plot(x, g2, "--", linewidth=1.2, label="g2_ (Gaussian)")
plt.plot(x, g3, "--", linewidth=1.2, label="g3_ (Gaussian)")

plt.legend(loc="best")
plt.xlabel("Frame number")
plt.ylabel("Intensity")
plt.title("Gaussian Peak Fitting")
plt.grid(True)
plt.show()


# %% Section 5: Save components

np.savetxt(
    os.path.join(datadir, "g1_.csv"),
    g1,
    delimiter="\t",
    fmt="%.8f"
)

np.savetxt(
    os.path.join(datadir, "g2_.csv"),
    g2,
    delimiter="\t",
    fmt="%.8f"
)

np.savetxt(
    os.path.join(datadir, "g3_.csv"),
    g3,
    delimiter="\t",
    fmt="%.8f"
)

print("Gaussian components saved.")