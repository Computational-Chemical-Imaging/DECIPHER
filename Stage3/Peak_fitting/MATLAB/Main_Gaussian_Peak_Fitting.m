%% Gaussian Peak Fitting
% Requires: Curve Fitting Toolbox

close all; clear; clc;

%% Section 1: Load and preprocess data

datadir = 'Data/';
filename = 'Raw_Spec_1600.csv';

y = load([datadir filename]);   % assumes numeric text file with >=2 cols

% Normalize the input data
y = (y - min(y)) ./ (max(y) - min(y));
x = linspace(1,size(y,1),size(y,1))';

% Plot raw spectrum to determine the number of peaks and initial positions
figure();
plot(x, y, 'LineWidth', 1.5);

%% Section 2: Define Gaussian model
% 3-Gaussian model is provided as an example. Users should change accordingly.
% lmfit GaussianModel uses:
% y = amplitude/(sigma*sqrt(2*pi)) * exp(-(x-center)^2/(2*sigma^2))
%

gauss = @(A, c, s, x) (A./(s*sqrt(2*pi))) .* exp(-((x - c).^2)./(2*s.^2));

% Specify the number of peaks, and peak amplitude, center, and width
ft = fittype(@(g1_amplitude,g1_center,g1_sigma, ...
               g2_amplitude,g2_center,g2_sigma, ...
               g3_amplitude,g3_center,g3_sigma, x) ...
    gauss(g1_amplitude,g1_center,g1_sigma,x) + ...
    gauss(g2_amplitude,g2_center,g2_sigma,x) + ...
    gauss(g3_amplitude,g3_center,g3_sigma,x), ...
    'independent', 'x', ...
    'coefficients', {'g1_amplitude','g1_center','g1_sigma', ...
                     'g2_amplitude','g2_center','g2_sigma', ...
                     'g3_amplitude','g3_center','g3_sigma'});

% Initial guess of peak intensity, position and width
startVals = [ ...
    0.1, 26, 1, ...   % g1
    0.5, 51, 1, ...   % g2
    0.6, 40, 1  ...   % g3 
];

opts = fitoptions(ft);
opts.StartPoint = startVals;

% Important: add bounds for stability. 
% Lower bound for peak intensity, position, and width 
 opts.Lower = [0, 20, 0,  ...
               0, 40,  0,  ...
               0, 30, 0  ];

% Upper bound for peak intensity, position, and width 
 opts.Upper = [Inf, 30, Inf, ...
               Inf, 60, Inf, ...
               Inf, 50, Inf];

%% Section 3: Fit the spectral data with the model
[fitObj, gof] = fit(x, y, ft, opts);

disp('=== Fit coefficients ===');
disp(fitObj);
disp('=== Goodness of fit ===');
disp(gof);

% Create fitted curve
y_fit = feval(fitObj, x);

% Evaluate individual components
c = coeffvalues(fitObj);

g1 = gauss(c(1), c(2), c(3), x);
g2 = gauss(c(4), c(5), c(6), x);
g3 = gauss(c(7), c(8), c(9), x);

%% Section 4: Evaluate the results

% Plot the input spectral data and the fitting results
figure('Position', [200 200 900 500]);
plot(x, y, 'b-', 'LineWidth', 1.5); hold on;
plot(x, y_fit, 'r-', 'LineWidth', 1.5);

plot(x, g1, '--', 'LineWidth', 1.2);
plot(x, g2, '--', 'LineWidth', 1.2);
plot(x, g3, '--', 'LineWidth', 1.2);

legend({'Observed Spectrum','Fitted Spectrum','g1_ (Gaussian)','g2_ (Gaussian)','g3_ (Gaussian)'}, ...
       'Location','best');
xlabel('Frame number');
ylabel('Intensity');
title('Gaussian Peak Fitting ');
grid on;


%% Section 5: Save components 

writematrix(g1, [datadir 'g1_.csv'], 'Delimiter', 'tab');
writematrix(g2, [datadir 'g2_.csv'], 'Delimiter', 'tab');
writematrix(g3, [datadir 'g3_.csv'], 'Delimiter', 'tab');

