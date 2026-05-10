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

% Generate noisy image corrupted by additive spatially correlated noise
% with noise power spectrum PSD
z = y + noise;

% Call BM4D With the default settings, using 3-D blocks
y_est = BM4D(z, PSD);

% Use 8x8x1 blocks
%y_est = BM4D(z, PSD, '8x8');

% To include refiltering:
%y_est = BM4D(z, PSD, 'refilter');

% For other settings, use BM4DProfile.
% profile = BM4DProfile(); % equivalent to profile = BM4DProfile('np');
% profile.gamma = 6;  % redefine value of gamma parameter
% y_est = BM4D(z, PSD, profile);

% Note: For white noise, you may instead of the PSD 
% also pass a standard deviation 
% y_est = BM4D(z, sqrt(noise_var));

psnr = getPSNR(y, y_est);
i = 5;
figure,
subplot(1, 3, 1);
imshow(y(:, :, i) / max(y(:)));
title(['y (frame', num2str(i), ')']);
subplot(1, 3, 2);
imshow(z(:, :, i) / max(y(:)));
title('z');
subplot(1, 3, 3);
imshow(y_est(:, :, i) / max(y(:)));
title('y_{est}');

