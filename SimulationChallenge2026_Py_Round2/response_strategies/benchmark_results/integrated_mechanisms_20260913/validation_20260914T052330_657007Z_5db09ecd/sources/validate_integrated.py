"""Run the integrated-candidate contract checks with all model advance blocked.

Usage: python -B response_strategies/validate_integrated.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT), str(ROOT / 'o2despy')]

from response_strategies.validate_connections import main


if __name__ == '__main__':
    sys.exit(main(
        extra_tests=['response_strategies/test_integrated_strategy.py'],
        extra_sources=['integrated_strategy.py', 'test_integrated_strategy.py',
                       'validate_integrated.py', 'INTEGRATED_MECHANISMS.md'],
        experiment_name='integrated_mechanisms_20260913',
    ))
