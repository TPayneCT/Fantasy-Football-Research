"""Refresh the current season and rebuild dashboard data. Run weekly (see .github/workflows/update.yml)."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for script in ("points_allowed.py", "build_dashboard_data.py"):
    subprocess.run([sys.executable, str(HERE / script)], check=True)
