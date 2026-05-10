clc;
close all
clear;
%% Section 1: Load CARS and NRB spectra

% Calibrate spectral window
% Find positions of two peaks (r1, r2) and frame number (f1, f2)
% Use standard chemicals for calibration. DMSO is used as example below
% Users should change accordingly

r1 = 2850;  
r2 = 2930;
f1 = 44;
f2 = 80;
Nz  = 150; % Set number of frames in the hyperspectral image
rpf =(r2-r1)/(f2-f1); % Use two signature peaks to define spectral spacing per frame
Wn = linspace(2850-43*rpf, 2930+70*rpf,Nz); % Define the spectral window in wavenumber

% Read NRB spectrum

datadir = 'Data/';

NRB_filename = 'CARS_BKG.csv';
I_NRB = readmatrix([datadir NRB_filename]);
I_NRB = I_NRB(:,end); % Keep only the second column, namely intensity values of the plot

% Read raw CARS spectrum
CARS_filename = 'CARS_protein.csv';
I_CARS = readmatrix([datadir CARS_filename]);
I_CARS = I_CARS(:,end); % Keep only the second column, namely intensity values of the plot

%% Section 2: Test Phase Retrieval on Example Spectra

[KK_ideal_imag, KK_ideal_real] = KKHilbert(I_NRB, I_CARS);
KK_ideal = KK_ideal_real + 1j*KK_ideal_imag;
phase_ideal = angle(KK_ideal);

% Plot input spectra
figure
plot(Wn,I_CARS, 'LineWidth', 2);
hold all
plot(Wn,I_NRB,'LineWidth',2);
legend('CARS','NRB');
xlabel('Wavenumber (cm^{-1})');
ylabel('Signal Int (au)');
title('CARS and NRB Signal (Spectra)');

% Plot Raman-like spectra
figure;
%plot(KK_ideal_imag,'LineWidth',2);
plot(Wn, KK_ideal_imag,'LineWidth',2);
hold all
legend('Retrieved');
xlabel('Wavenumber (cm^{-1})');
ylabel('Raman-Like Int. (no units)');
title('Raman-Like Spectra (Retrieved)');

%% Section 3: Load Hyperspectral Image

% Set input file type
%
% .txt --> hyperspectral text image in 2D montage
% .tif --> 3D tif image

filename = 'OVCAR5_CH_CARS_raw_shading_crtd_SPEND';
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

%% Section 4: Apply KK to the whole image

% Get dimensions of the image
[xx,yy,~]=size(y);
y_kk = zeros(size(y));
tic
% Run KK at each pixel
for ii = 1:xx
    for jj = 1:yy
        I_CARS = squeeze(y(ii,jj,:));
        [KK_spec_imag, KK_spec_real] = KKHilbert(I_NRB, I_CARS);
        y_kk(ii,jj,:) = KK_spec_imag;
    end
end
toc

%% Section 5: Output 

% The output image is stored in montage text image double format
y_kk_montage = reshape(y_kk,[],size(y,1)*size(y,3),1);
fid = fopen([filename '_kk' '.txt'],'wt');
for ii = 1:size(y_kk_montage,1)
    fprintf(fid,'%.4f\t',y_kk_montage(ii,:));
    fprintf(fid,'\n');
end
fclose(fid);