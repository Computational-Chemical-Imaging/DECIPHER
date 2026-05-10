% BM4D denoising demo file, based on
% Y. Mäkinen, L. Azzari, A. Foi, 2020,
% "Collaborative Filtering of Correlated Noise: Exact Transform-Domain Variance for Improved Shrinkage and Patch Matching",
% in IEEE Transactions on Image Processing, vol. 29, pp. 8339-8354.
% M. Maggioni, V. Katkovnik, K. Egiazarian, A. Foi, 2013,
% "Nonlocal Transform-Domain Filter for Volumetric Data Denoising and Reconstruction",
% in IEEE Transactions on Image Processing, vol. 22, pp. 119-133.
% Y. Mäkinen, S. Marchesini, A. Foi, 2022,
% "Ring Artifact and Poisson Noise Attenuation via Volumetric Multiscale Nonlocal Collaborative Filtering of Spatially Correlated Noise",
% in Journal of Synchrotron Radiation, vol. 29, pp. 829-842.

% The location of the BM4D files -- this folder only contains demo data
addpath('bm4d');

% Experiment specifications   

% Load noise-free image

% The example data is acquired from: http://www.bic.mni.mcgill.ca/brainweb/
% C.A. Cocosco, V. Kollokian, R.K.-S. Kwan, A.C. Evans,
%  "BrainWeb: Online Interface to a 3D MRI Simulated Brain Database"
% NeuroImage, vol.5, no.4, part 2/4, S425, 1997
% -- Proceedings of 3rd International Conference on Functional Mapping of the Human Brain, Copenhagen, May 1997.

data_name = 'brain_slices.mat';
y = load(data_name, 'brain_slices');
y = y.brain_slices;
y = y(20:60, 20:60, 1:10);
% Possible noise types to be generated 'gw', 'g1', 'g2', 'g3', 'g4', 'g1w',
% 'g2w', 'g3w', 'g4w'.
noise_type =  'g1';
noise_var = 0.02 * max(y(:))^2; % Noise variance
seed = 0; % seed for pseudorandom noise realization
% Generate noise with given PSD
kernel = getExperimentKernel(noise_type, noise_var, size(y));
[noise, PSD, kernel] = getExperimentNoise3D(kernel, seed, size(y));
% N.B.: For the sake of simulating a more realistic acquisition scenario,
% the generated noise is *not* circulant. Therefore there is a slight
% discrepancy between PSD and the actual PSD computed from infinitely many
% realizations of this noise with different seeds.

% Weaker noise
kernel = getExperimentKernel(noise_type, noise_var / 4, size(y));
[noise2, PSD2, kernel2] = getExperimentNoise3D(kernel, seed, size(y));

% Generate noisy image corrupted by additive spatially correlated noise
% with noise power spectrum PSD
z = y + noise;
z2 = y + noise2;

% Call BM4D With the default settings
[y_est_z] = BM4D(z, PSD);
[y_est_z2] = BM4D(z2, PSD2);

% Call multi-channel BM4D for the two images, using the less noisy image as the first channel
% Now, the block-matching will be performed on this channel, yielding less
% noisy matches
[y_est2] = BM4D_multichannel(cat(4, z2, z), cat(4, PSD2, PSD));

% The PSNR of y_est_z2 and the first channel of y_est2 should be identical, as we are
% denoising the same image with the same PSD and no further inputs.

% However, PSNR of channel 2 of y_est2 is better than that of y_est_z,
% because blockmatches were done on the less noisy channel 1

psnr_z2 = getPSNR(y, y_est_z2)
psnr_z = getPSNR(y, y_est_z)

psnr_ch1 = getPSNR(y, y_est2(:, :, :, 1))
psnr_ch2 = getPSNR(y, y_est2(:, :, :, 2))

i = 5;
figure,
subplot(1, 4, 1);
imshow(y(:, :, i) / max(y(:)));
title(['y (frame', num2str(i), ')']);
subplot(1, 4, 2);
imshow(z(:, :, i) / max(y(:)));
title('z');
subplot(1, 4, 3);
imshow(y_est_z(:, :, i) / max(y(:)));
title('y_{est}');

subplot(1, 4, 4);
imshow(y_est2(:, :, i, 2) / max(y(:)));
title('y_{est} (less noise B-M)');


