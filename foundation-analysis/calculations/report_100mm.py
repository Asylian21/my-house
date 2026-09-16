"""Stable entry point: current compacted-fill-supported 100mm report.
Previous free-span-focused version is preserved in archive/.
"""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('report_ground_support.py')), run_name='__main__')
