function [C_out, S] = ALS_lasso_aug( y, S_init, lambda, augnum, iter)
%MCR-ALS spectral unmixing with data augmentation
%   This function performs ALS spectral unmixing on hyperspectral
%   images, additional lines of S_init are added as data augmentation to
%   stablize the spectral profiles during ALS update, L1 norm is added to
%   the update of C to enforce pixel wise sparsity
%   %   Input:
%           y       --> 3D hyperspectral image stack
%           S_init  --> Spectral profiles initial guess of pure components
%           lambda  --> Sparsity level hyperparameter
%           augnum  --> Number of pure spectra datapoints for augmentation
%           iter    --> number of iterations for ALS update
%   Output:
%           C       --> Concentration maps
%           S       --> Spectral profiles
%% Initialize parameters
y           = double(y);
[Nx,Ny,Nz]  = size(y);           % 3 dimensions from the input data
[~,k]       = size (S_init);     % k is number of pure components

%% Add data augmentation for spectral profiles
S       = S_init;
D       = reshape(y,[Nx*Ny, Nz]); % Reshape y into D, each row is a spectrum
D_aug   = [D; repmat(S_init,1,augnum)']; % Add additional datapoints to raw
N       = size (D_aug,1); % Total number of data points
C_2D    = zeros(N,k);    % main variable C, reshaped as 2D matrix

%% Begin iteration
fprintf('Iter \t residualC \t residualS \t residualFit \n');
for ii = 1:iter

    % Allocate results from the previous iteration
    C_2D_old = C_2D;
    S_old    = S;

    % Update C
    parfor i = 1:N
        y_sp = D_aug(i,:)'; % Single pixel raw spectrum
        c_single_pixel = lasso(S,y_sp,'lambda',lambda,...
            'MaxIter',1e5, 'Alpha', 1);
        c_single_pixel = max(c_single_pixel,0);
        C_2D(i,:) = reshape(c_single_pixel,[1,k]);
    end

    % Update S
    parfor i = 1:Nz
        y_sf_aug = D_aug(:,i);
        s_single_frame = C_2D\y_sf_aug;
        S(i,:) = s_single_frame';
    end

    %calculate residual
    residualC = norm(C_2D(:) - C_2D_old(:)) / sqrt(Nx*Ny*k);
    residualS = norm(S(:) - S_old(:)) / sqrt(Nz*k);
    D_fit = C_2D(1:Nx*Ny,:) * S';
    D_raw = D;
    fit_error = norm(D_raw(:) - D_fit(:)) / norm(D_raw(:));

    fprintf('%3g \t %3.5e \t %3.5e \t %3.5e \n', ii, residualC, residualS, fit_error);

end

C_2D_out = C_2D(1:Nx*Ny, :);
C_out = reshape(C_2D_out,Nx, Ny, k);

end