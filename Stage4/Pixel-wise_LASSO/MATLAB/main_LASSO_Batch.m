close all
clear
clc

%% Section 1: Load basis spectra

% Calibrate spectral window
% Find positions of two peaks (r1, r2) and frame number (f1, f2)
% Use standard chemicals for calibration.
% Users should change accordingly.

r1 = 1655;
r2 = 1745;
f1 = 20;
f2 = 58;
Nz = 80; % Set number of frames in the hyperspectral image

rpf =(r2-r1)/(f2-f1);
Wn = linspace(r1-f1*rpf, r2+(Nz-f2+1)*rpf, Nz);

% Specify data directory for basis spectra and image.
datadir = 'data/';

% Define names of the spectra basis.
% Names should be consistent with csv file names
components = {'BSA','TAG','CHL'};

bgfilename = 'SRS_BKG';

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

%% Stage 2: Set image batch directory and load file names

% Set input file type
%
% .txt --> hyperspectral text image in 2D montage
% .tif --> 3D tif image

imgdir   = 'imagedata/';
filetype = '.tif';
Filelist = dir([imgdir '*' filetype]); % Set file pattern

cells    = struct2cell(Filelist);
sortvals = cells(6,:);
mat      = cell2mat(sortvals);
[~,ix]   = sort(mat);

Filelist = Filelist(ix);

file_num = size(Filelist,1);
clear ix cells sortvals mat

%% Stage 3: Begin the loop of spectral unmixing for all images
for jj = 1:file_num

    %%%%%%%%%%% Loop Step 1: Load image %%%%%%%%%
    
    %%%%%%%%%%%%%%%% Do not change the lines in between %%%%%%%%%%%%%%%%%
    close all
    % Load specific image
    filename = Filelist(jj).name;

    if endsWith([filename], '.tif', 'IgnoreCase', true)
        info = imfinfo([imgdir filename]);
        Nx = info(1).Height;
        Ny = info(1).Width;
        y =  zeros(info(1).Height, info(1).Width, Nz);
        for Nk = 1:Nz
            y(:,:,Nk) = imread([imgdir filename], Nk);
        end
    elseif endsWith([filename], '.txt', 'IgnoreCase', true)
        y_montage = load([imgdir filename]);
        Nx        = size(y_montage,1);
        Ny        = size(y_montage,2)/Nz;
        y         = permute(reshape(y_montage,[Nx,Ny,Nz]),[1,2,3]);
    else
        error('Unsupported file type: %s', [filename]);
    end
    %%%%%%%%%%%%%%%% Do not change the lines in between %%%%%%%%%%%%%%%%%


    %%%%%%%%%%% Loop Step 2: Subtract background %%%%%%%%

    %%%%%%%%%%%%%%%% Do not change the lines in between %%%%%%%%%%%%%%%%%
    BG_spectrum = readmatrix([datadir bgfilename ext]);
    BG_spectrum = BG_spectrum(:,end);

    figure; plot(Wn, BG_spectrum, 'Linewidth', 1.5);
    xlabel('Raman shift (cm^{-1})'); ylabel('Int (a.u.)')
    xlim([2820, 3030])
    set(gca,'FontSize',18,'LineWidth',2);
    title ('Background spectrum')

    y_sub = zeros(size(y), 'like', y);
    for i = 1:Nz
        y_sub(:,:,i) = y(:,:,i) - BG_spectrum(i);
    end
    %%%%%%%%%%%%%%%% Do not change the lines in between %%%%%%%%%%%%%%%%%


    %%%%%%%%%%% Loop Step 3: Run pixel-wise LASSO %%%%%%%%%

    % Set the sparsity level for all channels, same for all by default, change
    % if the initial outcome is unsatisfatory
    l = 5e-2;

    % These two parameters do not need to change in most cases
    a    = 1;            % Controls convergence speed of ADMM
    iter = 5;            % Number of iterations for ADMM

    %%%%%%%%%%%%%%%% Do not change the lines in between %%%%%%%%%%%%%%%%%
    C = nneg_lasso(y_sub, ref, L, a, iter);

    % Calculate the residual of unmixing
    C_2D = reshape(C, [],k);
    y_recon_2D = C_2D * ref.';
    y_recon = reshape(y_recon_2D, Nx, Ny, Nz);

    y_res = y_sub - y_recon;

    % Display concentration maps and examine image quality

    % Use the first channel (C(:,:,1)) to set up the display threshold.
    % Can use other channels if necessary
    disp_min = prctile(reshape(C(:,:,1), [Nx*Ny,1]), 0.3);
    disp_max = prctile(reshape(C(:,:,1), [Nx*Ny,1]), 99.7);

    figure(5);
    clims = [disp_min disp_max];

    for ii = 1:k
        subplot(2,3,ii); % Change subplot size if needed
        imagesc(C(:,:,ii), clims);
        colormap bone; axis off; axis square
    end
    drawnow
    pause(4);
    %%%%%%%%%%%%%%%% Do not change the lines in between %%%%%%%%%%%%%%%%%

    %%%%%%%%%%% Loop Step 4: Output concentration and residual %%%%%%%%%

    % Set output filepath
    opt_filepath = 'Output_maps/';
    if ~exist(opt_filepath, 'dir')
        mkdir(opt_filepath);
    end

    %%%%%%%%%%%%%%%% Do not change the lines in between %%%%%%%%%%%%%%%%%
    % Output concentration maps
    outExt = '.txt';
    for ii = 1:k
        cname = components{ii};
        outFile = fullfile(opt_filepath, [filename, '_', cname, outExt]);
        writematrix(C(:,:,ii), outFile, 'Delimiter', '\t');
    end
    % Output residual map in montage
    y_res_montage = reshape(y_res,size(y_res,1)*size(y_res,3),1);
    fid = fopen([datadir filename '_residual' '.txt'],'wt');
    for ii = 1:size(y_res_montage,1)
        fprintf(fid,'%.4f\t',y_res_montage(ii,:));
        fprintf(fid,'\n');
    end
    fclose(fid);
    %%%%%%%%%%%%%%%% Do not change the lines in between %%%%%%%%%%%%%%%%%
end