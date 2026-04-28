project_root = '/Volumes/Xu Lab/tMoTe2_Measuring/Zengde_Weijie_A5_AAtA_dot_oldattodry';
data_dir = fullfile(project_root, 'data', '02PL', 'dot1dispersion');
out_dir = fullfile(pwd, 'out', 'plots');

if ~exist(out_dir, 'dir')
    mkdir(out_dir);
end

files = dir(fullfile(data_dir, '*Bset*.mat'));
if isempty(files)
    error('No Bset files found in %s', data_dir);
end

bg = load(fullfile(data_dir, '1140c_20s.mat'));
bcg = bg.dat';
energy = 1240 ./ bg.w;

e_min = 1.080;
e_max = 1.084;
energy_mask = energy >= e_min & energy <= e_max;

dt = 34;
db = 27.4;
eps0 = 8.85e-12;
cbg = 3.0 * eps0 / (db * 1e-9);
ctg = 3.0 * eps0 / (dt * 1e-9);

v13 = -1.3344;
v23 = -2.34762;
n1 = -(v13 - v23) * 3;

Bvals = nan(numel(files), 1);
raw_band_sum = [];
filling_matrix = [];

for idx = 1:numel(files)
    s = load(fullfile(files(idx).folder, files(idx).name));
    dat = s.dat;
    num_pts = size(dat, 3);

    if isempty(raw_band_sum)
        raw_band_sum = nan(numel(files), num_pts);
        filling_matrix = nan(numel(files), num_pts);
    end

    for j = 1:num_pts
        spec = squeeze(dat(:, 1, j)) - bcg;
        spec = spec - mean(spec(990:1000));
        raw_band_sum(idx, j) = sum(spec(energy_mask));
    end

    nn = ((ctg * s.Vt + cbg * s.Vb) / 1.6e-19 / 1e4) * 1e-12;
    filling_matrix(idx, :) = -(nn - v23) ./ n1 - 2/3;
    Bvals(idx) = s.currentBfield;
end

[Bsorted, order] = sort(Bvals, 'ascend');
raw_band_sum = raw_band_sum(order, :);
filling_matrix = filling_matrix(order, :);
filling_axis = filling_matrix(1, :);

fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 1450 650]);
ax = axes(fig);
imagesc(ax, filling_axis, Bsorted, raw_band_sum);
set(ax, 'YDir', 'normal', 'Layer', 'top', 'FontSize', 16, 'LineWidth', 1);
xlabel('\nu');
ylabel('B (T)');
title(sprintf('A5 dot1 raw band sum, %.3f-%.3f eV', e_min, e_max));
ylim([0 7]);

clim = prctile(raw_band_sum(:), [3 99]);
clim(1) = min(clim(1), clim(2) - eps);
clim(clim <= 0) = max(min(raw_band_sum(raw_band_sum > 0)), 1);
caxis(ax, clim);
colormap(ax, turbo);
cb = colorbar(ax, 'eastoutside');
ylabel(cb, 'Band-summed PL (a.u.)');

png_path = fullfile(out_dir, 'a5_dot1_raw_band_sum_B_vs_nu.png');
exportgraphics(fig, png_path, 'Resolution', 250);
fprintf('Wrote %s\n', png_path);
