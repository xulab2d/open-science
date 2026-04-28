# Shuai_MT43_MRI — pyscan tooling drop

Date: 2026-03-21

## What showed up in the delta
A large code-heavy subtree under:
- tMoTe2_Measuring/Shuai_MT43_MRI/pyscan/

The delta includes many:
- Python source files (*.py)
- Compiled cache (*.pyc, __pycache__)
- A virtualenv-like path: Shuai_MT43_MRI/.venv/bin/jupyter-run
- RST docs/vendor library folders (e.g., msl-io, msl-equipment) under pyscan/drivers/

## What pyscan appears to be (high-confidence, from code structure)
A Python measurement + analysis framework for lab scans:
- Instrument driver layer: pyscan/drivers/ contains many instrument interfaces (Keithley, Zurich, Oxford, Agilent, OceanOptics, Thorlabs, etc.).
- Measurement/scan abstraction: pyscan/measurement/ exports PointByPointSweep/Average/Raster/Sparse and scan wrappers.
- GUI layer (PyQt5): pyscan/gui/* includes spectrum2Dgui and an optical_spectrum_scan GUI for loading experiments and plotting maps.
- Data model: uses `load_experiment(...)` to load runs; GUI references `.hdf5` and `.pkl` files as experiment containers.

Example evidence:
- gui/optical_spectrum_scan/spectrum2Dgui.py loads experiments via `ps.load_experiment(...)` and provides an interactive 2D spectrum map analysis UI.
- measurement/__init__.py exports scan/experiment classes.

## Operational concern
Including __pycache__/*.pyc and .venv content in Dropbox will:
- bloat cursor deltas and local cache
- inflate ingest scans/snapshots
- add noise to the scientific corpus

## Recommendation (policy question for Isaac)
Add ignore/exclusion rules for these categories under watched roots:
- **.venv/**
- **__pycache__/**
- ***.pyc**
- **.ipynb_checkpoints/**

(Still index *.py, *.md/*.rst docs, and any data outputs like *.hdf5/*.pkl/*.csv as needed.)
