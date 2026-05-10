clc;
clear;

%% Step 1: Load hyperspectral image

% Set input file type
%
% .txt --> hyperspectral text image in 2D montage
% .tif --> 3D tif image

datadir  = 'Data/';
filename = 'U87_CH_SRS_raw_drift_crtd_denoised';
filetype = '.txt';
Nz  = 100; % Set number of frames in the hyperspectral image

% Do not change the remaining lines in this section
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if endsWith([datadir filename filetype], '.tif', 'IgnoreCase', true)
    info = imfinfo([datadir filename filetype]);
    Nx = info(1).Height;
    Ny = info(1).Width;
    y =  zeros(info(1).Height, info(1).Width, Nz);
    for Nk = 1:Nz
        y(:,:,Nk) = imread([datadir filename filetype], Nk);
    end
elseif endsWith([datadir filename filetype], '.txt', 'IgnoreCase', true)
    y_montage = load([datadir filename filetype]);
    Nx        = size(y_montage,1);
    Ny        = size(y_montage,2)/Nz;
    y         = permute(reshape(y_montage,[Nx,Ny,Nz]),[1,2,3]);
else
    error('Unsupported file type: %s', [datadir filename filetype]);
end
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% Step 2: Obtain background spectrum

% Project the image stack into 2D by spectral averaging 
y_proj = squeeze(mean(y,3));
% Plot a histogram of the projected image
figure; histogram(y_proj);

% Set the threshold value using the intensity histogram
bkg_threshold = 0.29;

% Plot the bkg mask defined by the threshold value
BGmask = zeros(size(y_proj));
BG = find(y_proj < bkg_threshold);
BGmask(BG) = 1;
figure; imagesc(BGmask); axis image off

%% Step 3: Obtain the background spectrum and save

% Average all the spectra in the background area
BG_spectrum = zeros(1,Nz);
for i = 1:Nz
    y_temp = y(:,:,i);
    BG_spectrum(i) = mean(y_temp(BGmask == 1));
end

% Plot background spectrum
figure; plot(BG_spectrum, 'Linewidth', 1.5);
xlabel('Frame number'); ylabel('Int (a.u.)')
set(gca,'FontSize',18,'LineWidth',2)

% Save the spectrum as the same format as in Fiji/ImageJ csv file
bkg_output = [(1:Nz)',BG_spectrum'];
writematrix(bkg_output, [datadir 'SRS_BKG.csv']); 

