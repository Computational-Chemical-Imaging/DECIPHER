clc;
clear;
% Add path for BM4D code and data
% Store the data under the ./Data directory
addpath(genpath('bm4d_matlab_package_4.2.5'));

%% Section 1: load target image 

% Set input file type
%
% .txt --> hyperspectral text image in 2D montage
% .tif --> 3D tif image

datadir  = 'Data/'
filename = 'U87_CH_SRS_raw_drift_crtd';
filetype = '.txt';
nframes  = 100; % Set number of frames in the hyperspectral image


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Do not change the remaining lines in this section

if endsWith([datadir filename filetype], '.tif', 'IgnoreCase', true)
    info = imfinfo([datadir filename filetype]);
    y =  zeros(info(1).Height, info(1).Width, nframes);
    for k = 1:nframes
        y(:,:,k) = imread([datadir filename filetype], k);
    end
elseif endsWith([datadir filename filetype], '.txt', 'IgnoreCase', true)
    y_montage = load([datadir filename filetype]);
    [r,c]     = size(y_montage);
    y         = permute(reshape(y_montage,[r,c/nframes,nframes]),[1,2,3]);
else
    error('Unsupported file type: %s', [filename filetype]);
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% Section 2: BM4D denoising

% Set noise standard deviation
std = 0.05;
% Run BM4D denoising
y_denoised = BM4D(y, std);

%% Section 3: Output 

% The denoised image is stored in montage text image double format
y_denoised_montage = reshape(y_denoised,[],size(y,1)*size(y,3),1);
fid = fopen([datadir filename '_denoised' '.txt'],'wt');
for ii = 1:size(y_denoised_montage,1)
    fprintf(fid,'%.4f\t',y_denoised_montage(ii,:));
    fprintf(fid,'\n');
end
fclose(fid);