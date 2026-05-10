close all
clear
clc

%% Section 1: Load basis spectra

% Calibrate the spectral window
% Find positions of two peaks (r1, r2) and frame number (f1, f2).
% Use standard chemicals for calibration. DMSO is used as example below.
% Users should change accordingly

r1 = 2913;   r2 = 2994;
f1 = 40;     f2 = 76;
Nz  = 100; % Set number of frames in the hyperspectral image

rpf =(r2-r1)/(f2-f1);
Wn = linspace(r1-f1*rpf, r2+(Nz-f2+1)*rpf, Nz); % Wavenumber range

% Load spectral references

% Specify data directory for basis spectra and image. 
% Default: data/
datadir = 'data/';

% Define names of the spectra basis. 
% Names should be consistent with csv file names
components = {'BSA','TAG','CHL','RNA','GLU'};

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Do not change the remaining lines in this section

% Build normalized reference matrix ref (Nz x k)
k = numel(components);
ref = zeros(numel(Wn), k);
for ii = 1:k
    cname = components{ii};
    ext   = '.csv';
    spec_temp = readmatrix([datadir cname ext]);
    spec_temp = spec_temp(:,end); % take the last column
    ref(:,ii) = (spec_temp - min(spec_temp)) ./ (max(spec_temp) - min(spec_temp));
end

clear ii spec_temp;

% Plot normalized references with offsets
figure;
for ii = 1:k
    plot(Wn, ref(:,ii) + (ii-1), 'LineWidth', 1); hold on
end
hold off
set(gca,'XMinorTick','on','YMinorTick','on');
xlabel('Raman shift (cm^{-1})'); ylabel('Int (a.u.)')
legend(components);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% Section 2: Load hyperspectral image

% Set input file type
%
% .txt --> hyperspectral text image in 2D montage
% .tif --> 3D tif image

filename = 'U87_CH_SRS_raw_drift_crtd_denoised';
filetype = '.txt';

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Do not change the remaining lines in this section
fileid = [datadir filename filetype];
if endsWith(fileid, '.tif', 'IgnoreCase', true)
    info = imfinfo(fileid);
    Nx = info(1).Height;
    Ny = info(1).Width;
    y =  zeros(info(1).Height, info(1).Width, Nz);
    for Nk = 1:Nz
        y(:,:,Nk) = imread(fileid, Nk);
    end
elseif endsWith(fileid, '.txt', 'IgnoreCase', true)
    y_montage = load(fileid);
    Nx        = size(y_montage,1);
    Ny        = size(y_montage,2)/Nz;
    y         = permute(reshape(y_montage,[Nx,Ny,Nz]),[1,2,3]);
else
    error('Unsupported file type: %s', fileid);
end

C    = zeros(Nx,Ny,k);  % Allocate empty concentration maps
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% Section 3: Subtract background
% Set the threshold value using the intensity histogram
bgfilename = 'SRS_BKG';


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Do not change the remaining lines in this section
BG_spectrum = readmatrix([datadir bgfilename ext]);
BG_spectrum = BG_spectrum(:,end);

figure; plot(Wn, BG_spectrum, 'Linewidth', 1.5);
xlabel('Raman shift (cm^{-1})'); ylabel('Int (a.u.)')
set(gca,'FontSize',18,'LineWidth',2);
title ('Background spectrum')

y_sub = zeros(size(y), 'like', y);
for i = 1:Nz
    y_sub(:,:,i) = y(:,:,i) - BG_spectrum(i);
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% Step 4: Run pixel-wise LASSO unmixing and plot results

% Set the sparsity level for all channels
l = 1e-2;

% Set control parameters for ADMM optimization
% These two parameters do not need to change in most cases
a    = 1;            % Controls convergence speed of ADMM
iter = 10;            % Number of iterations for ADMM

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Do not change the remaining lines in this section

C = nneg_lasso(y_sub, ref, l, a, iter);

% Calculate the residual of unmixing
C_2D = reshape(C, [],k);
y_recon_2D = C_2D * ref.';
y_recon = reshape(y_recon_2D, Nx, Ny, Nz);

y_res = y_sub - y_recon;

% Use the first channel (C(:,:,1)) to set up the display threshold.
% Can use other channels if necessary
disp_min = prctile(reshape(C(:,:,1), [Nx*Ny,1]), 0.3);
disp_max = prctile(reshape(C(:,:,1), [Nx*Ny,1]), 99.7);

figure;
clims = [disp_min disp_max];

for ii = 1:k
    subplot(2,3,ii); % Change subplot size if needed
    imagesc(C(:,:,ii), clims);
    colormap bone; axis off; axis square
end
drawnow
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% Step 5: Residual Analysis

interactive_residual_viewer(y_sub, y_recon, Wn, 'mean');


%% Step 6: Output as txt files

% Set output filepath
opt_filepath = 'chemical_maps_CH/';
if ~exist(opt_filepath, 'dir')
    mkdir(opt_filepath);
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Do not change the remaining lines in this section
outExt = '.txt';
for ii = 1:k
    cname = components{ii};
    outFile = fullfile(opt_filepath, [filename, '_', cname, outExt]);
    writematrix(C(:,:,ii), outFile, 'Delimiter', '\t');
end
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%