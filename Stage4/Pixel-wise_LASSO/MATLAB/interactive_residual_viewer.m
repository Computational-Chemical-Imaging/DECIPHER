function interactive_residual_viewer(y, y_recon, wn, proj_method)
% INTERACTIVE_RESIDUAL_VIEWER
% Show residual map and interactively plot measured, reconstructed, residual spectra.
%
% Usage:
%   interactive_residual_viewer(y, y_recon)
%   interactive_residual_viewer(y, y_recon, wn)
%   interactive_residual_viewer(y, y_recon, wn, 'mean')
%
% Inputs:
%   y           - original hyperspectral image, Ny x Nx x Nw
%   y_recon     - reconstructed hyperspectral image, Ny x Nx x Nw
%   wn          - optional spectral axis
%   proj_method - 'mean', 'max', or 'sum' for residual projection

if nargin < 3 || isempty(wn)
    wn = 1:size(y, 3);
    use_wn = false;
else
    use_wn = true;
end

if nargin < 4 || isempty(proj_method)
    proj_method = 'mean';
end

assert(isequal(size(y), size(y_recon)), ...
    'y and y_recon must have the same dimensions.');

residual = y - y_recon;

switch lower(proj_method)
    case 'mean'
        residual_map = mean(abs(residual), 3);
    case 'max'
        residual_map = max(abs(residual), [], 3);
    case 'sum'
        residual_map = sum(abs(residual), 3);
    otherwise
        error('proj_method must be "mean", "max", or "sum".');
end

% Create residual map figure
mapFig = figure;
ax = axes(mapFig);
imagesc(ax, residual_map);
axis(ax, 'image');
colormap(ax, gray);
colorbar(ax);
title(ax, 'Residual map: select point or ROI; choose Done to exit');

count = 1;

while true
    mode = questdlg('Select analysis mode:', ...
        'Residual Viewer', ...
        'Point', 'ROI', 'Done', 'Point');

    if isempty(mode) || strcmp(mode, 'Done')
        break;
    end

    figure(mapFig);
    axes(ax);

    switch mode
        case 'Point'
            [x, yy] = ginput(1);
            x = round(x);
            yy = round(yy);

            x = max(1, min(size(y, 2), x));
            yy = max(1, min(size(y, 1), yy));

            spec_y = squeeze(y(yy, x, :));
            spec_recon = squeeze(y_recon(yy, x, :));
            spec_res = squeeze(residual(yy, x, :));

            plot_three_spectra(wn, spec_y, spec_recon, spec_res, ...
                sprintf('Point %d: x=%d, y=%d', count, x, yy), use_wn);

        case 'ROI'
            h = drawpolygon(ax);
            mask = createMask(h);
            delete(h); % remove overlay from residual map

            spec_y = average_spectrum(y, mask);
            spec_recon = average_spectrum(y_recon, mask);
            spec_res = average_spectrum(residual, mask);

            plot_three_spectra(wn, spec_y, spec_recon, spec_res, ...
                sprintf('ROI %d', count), use_wn);
    end

    count = count + 1;
end

end

function spectrum = average_spectrum(data, mask)
nFrames = size(data, 3);
spectrum = zeros(nFrames, 1);

for k = 1:nFrames
    frame = data(:, :, k);
    spectrum(k) = mean(frame(mask), 'omitnan');
end
end

function plot_three_spectra(wn, spec_y, spec_recon, spec_res, ttl, use_wn)
figure;

if use_wn
    xaxis = wn;
    xlabel_txt = 'Wavenumber';
else
    xaxis = 1:length(spec_y);
    xlabel_txt = 'Frame index';
end

plot(xaxis, spec_y, 'LineWidth', 1.5); hold on;
plot(xaxis, spec_recon, 'LineWidth', 1.5);
plot(xaxis, spec_res, 'LineWidth', 1.2);
hold off;

xlabel(xlabel_txt);
ylabel('Intensity');
legend('Original', 'Reconstructed', 'Residual');
title(ttl);
grid on;
end