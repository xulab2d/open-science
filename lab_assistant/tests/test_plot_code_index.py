from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from index_plot_code import index_file  # noqa: E402


def test_plot_code_index_captures_reusable_a5_script():
    record = index_file(ROOT / "scripts" / "quicklook_a5_dot1_raw_B_vs_nu.py")
    assert record is not None
    assert "a5" in record.tags
    assert "filling" in record.tags
    assert "imshow" in record.plot_calls
    assert "magma" in record.colormaps
    assert any(path.endswith(".png") for path in record.output_paths)


def test_plot_code_index_excludes_self():
    assert index_file(ROOT / "scripts" / "index_plot_code.py") is None
