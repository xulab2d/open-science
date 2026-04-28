project_root = '/Volumes/Xu Lab/tMoTe2_Measuring/Zengde_Weijie_A5_AAtA_dot_oldattodry';
data_dir = [project_root filesep 'data/02PL/dot1dispersion'];
out_dir = [pwd filesep 'out/plots'];

if ~exist(out_dir, 'dir')
    mkdir(out_dir);
end

addpath(project_root);

mins = -2;
maxs = 2;
dt = 34;
db = 27.4;
n0 = 0;

epsilon = 8.85e-12;
cbg = 3.0 * epsilon / (db * 1e-9);
ctg = 3.0 * epsilon / (dt * 1e-9);

dbkg = load([data_dir filesep '1140c_20s.mat']);
bcg = dbkg.dat';
energy = 1240 ./ dbkg.w;

energyrangefull = [1.0798 1.0838];
energyrangecuthighB = [1.0828 1.0838];
energyrangecutlowB = [1.0827 1.0836];
energyrangearoundn1 = [1.0794 1.0828];
energyrangearoundn23 = [1.0815 1.0836];

files = dir([data_dir filesep '*Bset*.mat']);
if isempty(files)
    error('No Bset files found in %s', data_dir);
end

num_files = numel(files);
Bvals = NaN(num_files, 1);
summatrix1 = [];
filling_matrix = [];
nn_matrix = [];

for idx = 1:num_files
    d1 = load([files(idx).folder filesep files(idx).name]);

    if any(d1.w ~= dbkg.w)
        error('Background wavelength mismatch for %s', files(idx).name);
    end

    I1 = d1.dat;
    PLfinal1 = NaN(size(I1, 1), size(I1, 3));
    datmerged1 = NaN(size(I1, 1), size(I1, 3));

    for i = 1:size(I1, 3)
        datmerged1(:, i) = squeeze(cmerge(I1(:, 1, i), I1(:, 1, i)));
        PLfinal1(:, i) = datmerged1(:, i) - bcg;
    end

    I1 = PLfinal1 - mean(PLfinal1(1:20, :));

    nn = ((ctg * d1.Vt + cbg * d1.Vb) / 1.6e-19 / 1e4) * (1e-12) - n0;

    v13 = -1.3344;
    v23 = -2.34762;
    n1 = -(v13 - v23) * 3;
    filling = -(nn - v23) ./ n1 - 2 / 3;

    if isempty(summatrix1)
        summatrix1 = NaN(num_files, numel(nn));
        filling_matrix = NaN(num_files, numel(nn));
        nn_matrix = NaN(num_files, numel(nn));
    end

    Bvals(idx) = d1.currentBfield;
    filling_matrix(idx, :) = filling;
    nn_matrix(idx, :) = nn;

    for j = 1:numel(nn)
        currentB = d1.currentBfield;
        if nn(j) > -1.5 && currentB > 1.5 && currentB < 4
            energyrange = energyrangecutlowB;
        elseif nn(j) > -1.5 && currentB > 4
            energyrange = energyrangecuthighB;
        elseif nn(j) < -3
            energyrange = energyrangearoundn1;
        elseif nn(j) > -2.5 && nn(j) <= -1.5 && currentB > 5
            energyrange = energyrangearoundn23;
        else
            energyrange = energyrangefull;
        end

        ind1 = findPixel(energyrange(2), energy);
        ind2 = findPixel(energyrange(1), energy);
        range = min(ind1, ind2):max(ind1, ind2);

        [~, peak_idx] = max(I1(range, j), [], 1);
        sum_idx = range(peak_idx) + (mins:maxs);
        sum_idx = sum_idx(sum_idx >= 1 & sum_idx <= size(I1, 1));
        summatrix1(idx, j) = sum(I1(sum_idx, j));
    end
end

[Bsorted, order] = sort(Bvals, 'ascend');
summatrix1 = summatrix1(order, :);
filling_matrix = filling_matrix(order, :);

filling_axis = filling_matrix(1, :);

dlmwrite([out_dir filesep 'a5_dot1_Bsorted.tsv'], Bsorted, 'delimiter', '\t', 'precision', '%.10f');
dlmwrite([out_dir filesep 'a5_dot1_filling_axis.tsv'], filling_axis, 'delimiter', '\t', 'precision', '%.10f');
dlmwrite([out_dir filesep 'a5_dot1_summatrix1.tsv'], summatrix1, 'delimiter', '\t', 'precision', '%.10f');

fprintf('Wrote %s\n', [out_dir filesep 'a5_dot1_Bsorted.tsv']);
fprintf('Wrote %s\n', [out_dir filesep 'a5_dot1_filling_axis.tsv']);
fprintf('Wrote %s\n', [out_dir filesep 'a5_dot1_summatrix1.tsv']);
