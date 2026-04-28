# MT43_MRI / pyscan — code drop notes

Date: 2026-03-21

## What arrived
A large code drop under:
- tMoTe2_Measuring/Shuai_MT43_MRI/pyscan/
including:
- instrument drivers (Agilent/Keithley/Ocean Optics etc.)
- GUI code for 2D optical spectrum map analysis (PyQt5 + matplotlib)
  - e.g. pyscan/gui/optical_spectrum_scan/spectrum2Dgui.py
- many compiled caches: __pycache__/ and *.pyc
- a bundled third-party library tree: pyscan/drivers/msl-equipment/ (has its own docs/README)
- a Dropbox path that looks like a local environment artifact:
  - tMoTe2_Measuring/Shuai_MT43_MRI/.venv/bin/jupyter-run

## What it seems to do (high confidence)
- `pyscan` is a Python measurement/analysis framework.
- The GUI loads “experiments” via `ps.load_experiment(...)` and expects experiment metadata in `runinfo.loop0/loop1['scan_dict']`, then provides plotting widgets for counts/band/spectrum.

## Operational concern
This content will repeatedly inflate Dropbox delta + ingest because it contains:
- __pycache__/ and *.pyc
- .ipynb_checkpoints/
- .venv/
- bundled vendor/library trees (msl-equipment)

## Recommendation (needs Isaac decision)
Consider excluding these from watch/sync scope for ingestion purposes:
- **/.venv/**
- **/__pycache__/**
- **/*.pyc**
- **/.ipynb_checkpoints/**

If the goal is to index the code itself (not just measurement outputs), we should instead treat it as a separate “code repo snapshot” with a different ingest policy.
