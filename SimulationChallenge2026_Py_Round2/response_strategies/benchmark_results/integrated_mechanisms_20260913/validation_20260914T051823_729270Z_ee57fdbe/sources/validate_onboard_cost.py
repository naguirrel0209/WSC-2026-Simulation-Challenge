"""Run only static/unit checks; block Model.run and Model.warmup explicitly.

Usage from the repository root: python -B response_strategies/validate_onboard_cost.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT), str(ROOT / 'o2despy')]

# The original command now delegates to the split-manifest validator. Its
# former implementation and outputs remain preserved in benchmark_results.
from response_strategies.validate_connections import main


if __name__ == '__main__':
    sys.exit(main())
