clc;
clear;

%% Section 1: Load MIP spectra
datadir  = 'Data/';
Spec_filename = 'Single_Spec_sample.csv';
raw_spec = readmatrix([datadir Spec_filename]);
raw_spec = raw_spec(:,2)';

Nz = length(raw_spec);

%% Section 2: Fine tune parameters using single-pixel spectra

smoothness_param = 1e3; % smoothness parameter (default, 1e3)
min_diff         = 1e-6; % break iterations if difference is less than min_diff, (default, 1e-6)

bkg_ar = arPLS_baseline_v0(raw_spec,smoothness_param,min_diff)';
peak_ar = raw_spec - bkg_ar;

figure;
plot(bkg_ar,'DisplayName','bkg');hold on
plot(peak_ar,'DisplayName','signal');
plot(raw_spec,'DisplayName','Raw Spec');
hold off;
legend();

%% Section 3: Load Hyperspectral Image

% Set input file type
%
% .txt --> hyperspectral text image in 2D montage
% .tif --> 3D tif image

filename = 'G2_MIP_DN_stab';
filetype = '.tif';

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Do not change the remaining lines in this section

if endsWith([datadir filename filetype], '.tif', 'IgnoreCase', true)
    info = imfinfo([datadir filename filetype]);
    y =  zeros(info(1).Height, info(1).Width, Nz);
    for k = 1:Nz
        y(:,:,k) = imread([datadir filename filetype], k);
    end
elseif endsWith([datadir filename filetype], '.txt', 'IgnoreCase', true)
    y_montage = load([datadir filename filetype]);
    [r,c]     = size(y_montage);
    y         = permute(reshape(y_montage,[r,c/Nz,Nz]),[1,2,3]);
else
    error('Unsupported file type: %s', [datadir filename filetype]);
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% Step 4: Apply arPLS to the whole image

% Get dimensions of the image
[xx,yy,~]=size(y);
y_arpls = zeros(size(y));

% Run KK at each pixel
parfor ii = 1:xx
    for jj = 1:yy
        pixel_spec        = squeeze(y(ii,jj,:))';
        pixel_bkg_ar      = arPLS_baseline_v0(pixel_spec,smoothness_param,min_diff)';
        pixel_peak_ar     = pixel_spec - pixel_bkg_ar;
        y_arpls(ii,jj,:)  = pixel_peak_ar;
    end
end

%% Section 5: Output 

% The output image is stored in montage text image double format
y_arpls_montage = reshape(y_arpls,[],size(y,1)*size(y,3),1);
fid = fopen([datadir filename '_arpls' '.txt'],'wt');
for ii = 1:size(y_arpls_montage,1)
    fprintf(fid,'%.4f\t',y_arpls_montage(ii,:));
    fprintf(fid,'\n');
end
fclose(fid);