"""
Top-level dispatch: given a FileArrivedEvent, load and analyze the file,
return a FileAnalysisResult.
"""

from __future__ import annotations

from pathlib import Path

from ..schemas import FileAnalysisResult, FileArrivedEvent
from .generic import check_generic
from .loader import load_mat
from .pl import analyze_pl
from .reflectance import analyze_reflectance
from .rmcd import analyze_rmcd

# Flags that indicate a genuine data problem (score += 0.5 each)
# Zero coercive field is intentionally absent — it is expected physics.
_ERROR_FLAGS = {
    "load_failed",
    "all_nan",
    "all_zeros",
    "missing_reflectance_data",
    "missing_intensity_array",
    "all_nan_spectra",
    "near_zero_dRR",
    "all_nan_gate_map",
    "all_nan_after_normalization",
    "all_nan_after_bg_sub",
    "insufficient_finite_hysteresis_points",
    "unrecognized_rmcd_format",
    "zero_dimension",
    "all_nan_spatial",
}

# Flags that suggest something worth noting (score += 0.2 each)
_WARN_FLAGS = {
    "low_snr",
    "tiny_file",
    "no_saturation_contrast",
    "vanishing_loop_area_at_high_field",
    "no_spatial_variation",
    "no_gate_dependent_contrast",
    "very_low_intensity",
    "weak_resonance_feature",
    "mostly_nan_gate_points",
    "mostly_nan_gate_map",
    "peak_outside_typical_window",
    "insufficient_data_in_energy_window",
    # corpus_outlier_feature, corpus_globally_unusual, corpus_plot_unusual are
    # intentionally excluded — their score is carried by the numeric corpus_sim /
    # corpus_zscore / corpus_plot_sim flags to avoid double-counting.
}


def _score_flags(flags: list[str]) -> float:
    """
    Convert quality flags into a 0–1 anomaly score.

    Scoring tiers:
      ≥ 0.5  error   — hard data failures (load error, all NaN, etc.)
      0–0.49 warn    — physics anomalies, corpus divergence, soft issues

    Corpus signals (corpus_sim, corpus_zscore, corpus_plot_sim) are capped
    collectively at 0.45 so that cross-sample divergence never alone triggers
    the error threshold — only genuine instrument/DAQ failures do that.
    """
    hard_score = 0.0
    corpus_score = 0.0
    soft_score = 0.0

    for f in flags:
        base = f.split(":")[0]
        detail = f.split(":", 1)[1] if ":" in f else ""

        if any(base == ef or base.startswith(ef) for ef in _ERROR_FLAGS):
            hard_score += 0.5
        elif base in ("corpus_sim", "corpus_zscore", "corpus_plot_sim"):
            try:
                corpus_score += float(detail)
            except ValueError:
                pass
        elif any(base == wf or base.startswith(wf) for wf in _WARN_FLAGS):
            soft_score += 0.2
        elif "analysis_error" in base:
            soft_score += 0.3

    score = hard_score + min(corpus_score, 0.45) + soft_score
    return min(score, 1.0)


def _describe_flags(flags: list[str]) -> list[str]:
    """Convert flags to concise human-readable anomaly reasons."""
    desc = []
    for f in flags:
        parts = f.split(":", 1)
        key = parts[0]
        detail = parts[1] if len(parts) > 1 else ""

        if key == "load_failed":
            desc.append(f"File could not be loaded — {detail or 'unknown format'}")
        elif key == "all_nan":
            desc.append(f"Primary data variable '{detail}' is all NaN — possible DAQ dropout or partial write")
        elif key == "all_zeros":
            desc.append(f"Primary data variable '{detail}' is all zeros — possible DAQ or detector failure")
        elif key == "tiny_file":
            desc.append(f"File is very small ({detail}) — may be a partial or failed write")
        elif key == "zero_dimension":
            desc.append(f"Array '{detail}' has a zero-length axis — acquisition may have stopped early")
        elif key == "low_snr":
            desc.append(f"PL signal-to-noise ratio is low (SNR={detail}) — check laser power or optical alignment")
        elif key == "very_low_intensity":
            desc.append("PL intensity extremely low — check laser, detector, and collection optics")
        elif key == "peak_outside_typical_window":
            desc.append(f"PL peak at {detail} is outside the typical tMoTe2 window (0.95–1.20 eV) — possible wavelength calibration issue")
        elif key == "all_nan_after_bg_sub":
            desc.append("All PL data became NaN after background subtraction — background may exceed signal")
        elif key == "mostly_nan_gate_points":
            desc.append(f"Most gate sweep points are NaN ({detail}) — sweep may not have completed")
        elif key == "missing_intensity_array":
            desc.append("No intensity array found in PL file — unexpected variable naming?")
        elif key == "missing_reflectance_data":
            desc.append("No reflectance data array found — check variable naming convention")
        elif key == "near_zero_dRR":
            desc.append("dR/R is near zero across all gate points — possible beam or reference issue")
        elif key == "all_nan_after_normalization":
            desc.append("Reflectance normalization produced all NaN — reference spectrum may be zero")
        elif key == "weak_resonance_feature":
            desc.append("d(dR/R)/dE resonance dip is very weak — possible temperature drift or alignment issue")
        elif key == "insufficient_data_in_energy_window":
            desc.append("Insufficient spectral data in 1.08–1.15 eV window — check wavelength calibration")
        elif key == "no_saturation_contrast":
            desc.append("RMCD shows no contrast between high positive and negative field — sample may be paramagnetic at this condition")
        elif key == "vanishing_loop_area_at_high_field":
            desc.append("RMCD hysteresis loop area is near zero at high field — unexpectedly weak hysteresis")
        elif key == "no_gate_dependent_contrast":
            desc.append("RMCD gate map shows no variation across gate voltages — sweep may not have run or contacts issue")
        elif key == "no_spatial_variation":
            desc.append("RMCD spatial map is uniform — possible dead detector or no contrast at this condition")
        elif key == "all_nan_gate_map":
            desc.append("RMCD gate map is entirely NaN — data acquisition failed")
        elif key == "mostly_nan_gate_map":
            desc.append(f"RMCD gate map is mostly NaN ({detail}) — sweep partially completed")
        elif key == "insufficient_finite_hysteresis_points":
            desc.append("RMCD hysteresis sweep has too few finite data points — acquisition may have failed")
        elif key == "unrecognized_rmcd_format":
            desc.append("RMCD file format not recognized — unexpected variable structure")
        elif key == "corpus_outlier_feature":
            desc.append(f"Physics outlier: {detail} is >3σ from corpus mean — possibly interesting or anomalous")
        elif key == "corpus_globally_unusual":
            desc.append(f"Globally unusual data shape ({detail}) — no close match in corpus")
        elif key == "corpus_plot_unusual":
            desc.append(f"Plot looks visually unusual vs corpus ({detail}) — structural change or instrument issue")
        elif key == "analysis_error":
            desc.append(f"Analysis error: {detail}")
        # Intentionally not describing benign flags like missing_wavelength_axis in
        # ways that inflate anomaly score — those get handled by modality analyzers.
    return desc


def analyze_file(
    event: FileArrivedEvent,
    corpus_dir: "Path | None" = None,
    corpus_sample: str | None = None,
    add_to_corpus: bool = False,
    add_plot_to_corpus: bool = False,
) -> FileAnalysisResult:
    """
    Load and analyze a single data file.
    Never raises — returns an error-flagged result on any failure.

    corpus_dir:    If provided, query the corpus for nearest neighbors and
                   flag if the file is a physics outlier.
    corpus_sample: Optional — restrict corpus search to files from this sample.
    add_to_corpus: If True AND the file has no errors, add its metrics to the corpus.
                   Only call with True when ingesting known-good reference data.
    """
    path = Path(event.local_path)
    modality = event.inferred_modality

    mat_data, load_error = load_mat(path)

    generic_flags, generic_metrics = check_generic(path, mat_data, load_error, modality)

    variables_found = list(mat_data.keys()) if mat_data else []
    all_metrics: dict = dict(generic_metrics)
    all_flags: list[str] = list(generic_flags)

    if mat_data is not None:
        try:
            if modality == "PL":
                mod_metrics = analyze_pl(mat_data, event.filename)
                all_flags.extend(mod_metrics.pop("pl_flags", []))
                all_metrics.update(mod_metrics)
            elif modality == "RMCD":
                mod_metrics = analyze_rmcd(mat_data, event.filename)
                all_flags.extend(mod_metrics.pop("rmcd_flags", []))
                all_metrics.update(mod_metrics)
            elif modality == "Reflectance":
                mod_metrics = analyze_reflectance(mat_data, event.filename)
                all_flags.extend(mod_metrics.pop("refl_flags", []))
                all_metrics.update(mod_metrics)
        except Exception as e:
            all_flags.append(f"analysis_error:{str(e)[:80]}")

    anomaly_score = _score_flags(all_flags)
    anomaly_reasons = _describe_flags(all_flags)

    # Drop raw variable list — too verbose for LLM
    all_metrics.pop("variables", None)

    # --- Corpus comparison ---
    corpus_result = None
    has_errors = any(
        any(base == ef or base.startswith(ef) for ef in _ERROR_FLAGS)
        for base in (f.split(":")[0] for f in all_flags)
    )

    if corpus_dir is not None and all_metrics:
        # --- Metric corpus ---
        try:
            from ..corpus import query_similar
            corpus_result = query_similar(
                all_metrics, modality, corpus_dir,
                sample_filter=corpus_sample,
            )
            if corpus_result is not None:
                sim = corpus_result.get("nearest_sim", 1.0)
                z_scores = corpus_result.get("z_scores", {})
                outlier_feats = corpus_result.get("outlier_features", [])

                # Continuous similarity contribution: (1-sim)*0.4, capped at 0.4
                sim_contrib = round(min((1.0 - sim) * 0.4, 0.4), 4)
                if sim_contrib > 0.005:
                    all_flags.append(f"corpus_sim:{sim_contrib}")

                # Continuous z-score contribution: scales with worst feature
                if z_scores:
                    max_z = max(abs(z) for z in z_scores.values())
                    z_contrib = round(min(max_z / 10.0, 0.4), 4)
                    if z_contrib > 0.005:
                        all_flags.append(f"corpus_zscore:{z_contrib}")

                # Keep human-readable outlier flags for descriptions
                if outlier_feats:
                    all_flags.append(f"corpus_outlier_feature:{','.join(outlier_feats)}")
                elif sim < 0.85:
                    all_flags.append(f"corpus_globally_unusual:sim={sim:.3f}")
        except Exception:
            pass

        # --- Plot corpus (DINOv2) — only if plot vectors exist ---
        _plot_vec_exists = any(
            (corpus_dir / f"{c}_plot_vectors.npy").exists()
            for c in ("PL", "RMCD_hysteresis", "RMCD_gate_map", "Reflectance")
        )
        if mat_data is not None and _plot_vec_exists:
            try:
                from ..plot_embed import query_plot_similar
                plot_result = query_plot_similar(
                    mat_data, all_metrics, modality, corpus_dir,
                    sample_filter=corpus_sample,
                )
                if corpus_result is not None:
                    corpus_result["plot_result"] = plot_result
                else:
                    corpus_result = {"plot_result": plot_result}
                if plot_result is not None:
                    plot_sim = plot_result.get("nearest_sim", 1.0)
                    # Continuous plot similarity contribution: (1-sim)*0.2
                    plot_contrib = round(min((1.0 - plot_sim) * 0.2, 0.2), 4)
                    if plot_contrib > 0.005:
                        all_flags.append(f"corpus_plot_sim:{plot_contrib}")
                    if plot_result.get("is_plot_outlier"):
                        all_flags.append(f"corpus_plot_unusual:sim={plot_sim:.3f}")
            except Exception:
                pass

    if add_to_corpus and corpus_dir is not None and not has_errors and all_metrics:
        # Add to metric corpus
        try:
            from ..corpus import add_entry
            add_entry(
                metrics=all_metrics,
                filename=event.filename,
                sample=corpus_sample or "",
                modality=modality,
                path=event.local_path,
                corpus_dir=corpus_dir,
            )
        except Exception:
            pass
        # Add to plot corpus (only if mat_data available and explicitly requested)
        if add_plot_to_corpus and mat_data is not None:
            try:
                from ..plot_embed import add_plot_entry
                add_plot_entry(
                    mat_data=mat_data,
                    metrics=all_metrics,
                    filename=event.filename,
                    sample=corpus_sample or "",
                    modality=modality,
                    path=event.local_path,
                    corpus_dir=corpus_dir,
                )
            except Exception:
                pass

    # Re-score after potential corpus flags
    anomaly_score = _score_flags(all_flags)
    anomaly_reasons = _describe_flags(all_flags)

    return FileAnalysisResult(
        event_id=event.event_id,
        filename=event.filename,
        local_path=event.local_path,
        modality=modality,
        loadable=mat_data is not None,
        variables_found=variables_found,
        quality_flags=all_flags,
        metrics=all_metrics,
        anomaly_score=round(anomaly_score, 3),
        anomaly_reasons=anomaly_reasons,
        corpus_result=corpus_result,
    )
