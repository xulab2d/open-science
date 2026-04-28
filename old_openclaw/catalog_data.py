#!/usr/bin/env python3
"""Catalog all files in /data into /out/records.jsonl"""

import json
import os
import re
import hashlib
from pathlib import Path

try:
    import scipy.io as sio
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

DATA_DIR = Path("/Users/isaacvanorman/.openclaw/workspace/data")
OUT_FILE = Path("/Users/isaacvanorman/.openclaw/workspace/out/records.jsonl")

def parse_filename(relpath):
    """Extract metadata from filename and path."""
    p = Path(relpath)
    name = p.stem
    ext = p.suffix.lstrip('.')
    parts = list(p.parts)
    
    record = {
        "path": relpath,
        "file_type": ext,
        "role": classify_role(ext, name),
    }
    
    # Modality from top-level folder
    top = parts[0] if parts else ""
    if top.startswith("PL"):
        record["modality"] = "PL"
        if "_run" in top:
            record["run"] = top.split("_")[-1]  # e.g. "run2"
        else:
            record["run"] = "run1"
    elif top.startswith("Reflectance"):
        record["modality"] = "Reflectance"
        if "_run" in top:
            record["run"] = top.split("_")[-1]
        else:
            record["run"] = "run1"
    elif top == "RMCD":
        record["modality"] = "RMCD"
        record["run"] = "run1"
    
    # Spot identification
    spot = extract_spot(parts)
    if spot:
        record["spot"] = spot
    
    # Parameters from filename
    params = extract_params(name, parts)
    if params:
        record["parameters"] = params
    
    # Experiment type
    exp_type = classify_experiment(name, parts)
    if exp_type:
        record["experiment_type"] = exp_type
    
    # Series identification
    series = extract_series(name, relpath)
    if series:
        record["series_id"] = series
    
    record["confidence"] = "high" if ext == "mat" else "medium"
    
    return record

def classify_role(ext, name):
    if ext == "m":
        return "script"
    elif ext == "asv":
        return "autosave"
    elif ext in ("c", "h", "html", "txt"):
        return "support"
    elif ext in ("jpg", "png"):
        return "image"
    elif ext == "mat":
        # Background files
        lower = name.lower()
        if "bkg" in lower or "background" in lower:
            return "background"
        if re.match(r'^\d+g_\d+nm_\d+s', name):
            return "background"
        return "raw_data"
    return "unknown"

def extract_spot(parts):
    for p in parts:
        if p.startswith("Spot") or p.startswith("Dot"):
            return p
    return None

def extract_params(name, parts):
    params = {}
    
    # Power: e.g. 100nW, 50nW, 20nW
    m = re.search(r'(\d+)nW', name)
    if m:
        params["power_nW"] = int(m.group(1))
    
    # Exposure: e.g. 5s, 2s, 10s
    m = re.search(r'_(\d+)s_', name)
    if m:
        params["exposure_s"] = int(m.group(1))
    
    # Grating: e.g. 300g
    m = re.search(r'(\d+)g_', name)
    if m:
        params["grating"] = int(m.group(1))
    
    # Center wavelength: e.g. 1160nmc, 1120nmc, 1160nm
    m = re.search(r'(\d{4})nmc?', name)
    if m:
        params["center_wavelength_nm"] = int(m.group(1))
    
    # Displacement field from filename: D_0, D_n0p34, D_0p32
    m = re.search(r'_D_?(n?)(\d+p?\d*)', name)
    if m:
        val = m.group(2).replace('p', '.')
        val = float(val)
        if m.group(1) == 'n':
            val = -val
        params["D_field"] = val
    
    # D field from folder name
    for p in parts:
        dm = re.match(r'[BD][\s=]*\s*([-n]?\d+\.?\d*)', p.replace('p','.'))
        if dm:
            pass  # folder-level D captured in experiment type
        dm2 = re.search(r'D\s*=\s*([-]?\d+\.?\d*)', p)
        if dm2:
            if "D_field" not in params:
                params["D_field_folder"] = float(dm2.group(1))
    
    # Filling factor: v_n1, v_n43
    m = re.search(r'_v_(n?)(\d+)', name)
    if m:
        val = int(m.group(2))
        if m.group(1) == 'n':
            val = -val
        params["filling_v"] = val
    
    # B-field set index: Bset1, Bset41
    m = re.search(r'Bset(\d+)', name)
    if m:
        params["B_set_index"] = int(m.group(1))
    
    # Voltage set index: Vset1
    m = re.search(r'Vset(\d+)', name)
    if m:
        params["V_set_index"] = int(m.group(1))
    
    # Temperature set index: Tset1
    m = re.search(r'Tset(\d+)', name)
    if m:
        params["T_set_index"] = int(m.group(1))
    
    # Polarization: _L or _R at end
    m = re.search(r'_(L|R)$', name)
    if m:
        params["polarization"] = m.group(1)
    
    # B-field from folder: e.g. "0.5T", "8T", "4T"
    for p in parts:
        bm = re.match(r'^(\d+\.?\d*)T$', p)
        if bm:
            params["B_field_T"] = float(bm.group(1))
    
    # Temperature from folder: e.g. "T = 1.65K"
    for p in parts:
        tm = re.match(r'T\s*=\s*(\d+\.?\d*)K', p)
        if tm:
            params["temperature_K"] = float(tm.group(1))
    
    return params if params else None

def classify_experiment(name, parts):
    lower = name.lower()
    path_str = "/".join(parts).lower()
    
    if "curie" in path_str or "curie" in lower:
        return "Curie_Weiss"
    if "hysteresis" in lower or "hysteresis" in path_str:
        return "hysteresis"
    if "tdep" in lower or "tdep" in path_str:
        return "T_dep"
    if "bdispersion" in path_str or "bsweep" in lower or "bfield" in path_str:
        return "B_dispersion"
    if "dualgate" in lower or "dualgatesweep" in lower:
        return "dual_gate_sweep"
    if "dopingdep" in lower or "doping" in lower:
        return "doping_dep"
    if "ddep" in lower or "dsweep" in lower or "dfield" in path_str.lower():
        return "Dfield_dep"
    if "spatial" in lower:
        return "spatial_scan"
    if "polariz" in lower or "polariz" in path_str:
        return "polarization"
    if "finedualgate" in lower or "veryfinedualgate" in lower:
        return "dual_gate_sweep"
    if "wavelength" in lower:
        return "wavelength_dep"
    if "optimization" in path_str:
        return "Dfield_optimization"
    if re.match(r'^\d+g_\d+nm_', name):
        return "background"
    return None

def extract_series(name, relpath):
    """Group files that differ only by sweep index."""
    # Remove Bset/Vset/Tset index to get series base
    base = re.sub(r'_?[BVT]set\d+', '', name)
    if base != name:
        parent = str(Path(relpath).parent)
        return f"{parent}/{base}"
    return None

def inspect_mat(filepath):
    """Get variable names and shapes from .mat file."""
    if not HAS_SCIPY:
        return None, None
    try:
        d = sio.loadmat(str(filepath), variable_names=None)
        keys = [k for k in d.keys() if not k.startswith('__')]
        shapes = {}
        for k in keys:
            v = d[k]
            if hasattr(v, 'shape'):
                shapes[k] = list(v.shape)
            else:
                shapes[k] = str(type(v).__name__)
        return keys, shapes
    except Exception as e:
        return None, {"error": str(e)}

def main():
    records = []
    all_files = sorted(DATA_DIR.rglob("*"))
    all_files = [f for f in all_files if f.is_file() and not f.name.startswith('.')]
    
    print(f"Found {len(all_files)} files to catalog")
    
    # For .mat files, sample every Nth for variable inspection to save time
    # Inspect all non-indexed files and first file of each series
    seen_series = set()
    
    for i, filepath in enumerate(all_files):
        relpath = str(filepath.relative_to(DATA_DIR))
        record = parse_filename(relpath)
        
        # Inspect .mat files selectively
        if filepath.suffix == '.mat' and HAS_SCIPY:
            series = record.get("series_id")
            should_inspect = (
                series is None or  # standalone file
                series not in seen_series  # first of series
            )
            if series:
                seen_series.add(series)
            
            if should_inspect:
                keys, shapes = inspect_mat(filepath)
                if keys:
                    record["mat_variables"] = keys
                if shapes:
                    record["data_shape"] = shapes
        
        records.append(record)
        
        if (i + 1) % 500 == 0:
            print(f"  Processed {i+1}/{len(all_files)}")
    
    # Write records
    with open(OUT_FILE, 'w') as f:
        for r in records:
            f.write(json.dumps(r) + '\n')
    
    print(f"\nWrote {len(records)} records to {OUT_FILE}")
    
    # Print summary stats
    from collections import Counter
    modalities = Counter(r.get("modality") for r in records)
    exp_types = Counter(r.get("experiment_type") for r in records)
    roles = Counter(r.get("role") for r in records)
    
    print(f"\nBy modality: {dict(modalities)}")
    print(f"By experiment type: {dict(exp_types)}")
    print(f"By role: {dict(roles)}")
    
    # Count series
    series_ids = [r["series_id"] for r in records if "series_id" in r]
    print(f"\nIdentified {len(set(series_ids))} sweep series covering {len(series_ids)} files")

if __name__ == "__main__":
    main()
