"""
Per-modality data analyzers.

Each analyzer:
  - receives a loaded .mat dict (from loader.py) and the filename
  - returns a flat dict of metrics (numbers, booleans, short strings)
  - never returns raw arrays — only derived quantities
  - never raises: returns an error-flagged dict if something goes wrong

Dispatch:
  from monitor.analyze import analyze_file
"""

from .dispatch import analyze_file  # noqa: F401
