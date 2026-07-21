"""Optional one-time Kaggle dataset setup; never imported by the portfolio.

Requires the user's own Kaggle CLI installation and credentials. Competition
or dataset terms must be reviewed by the user before downloading. Files stay
under ignored local data directories and are not redistributed by this repo.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_TARGET = BASE_DIR / "midterm-assignment" / "data"
DATASET = "thetrumpet/teknofest-trendyol-2026-datathonn"


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the Trendyol dataset once via Kaggle CLI")
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    args = parser.parse_args()
    if shutil.which("kaggle") is None:
        raise SystemExit("Kaggle CLI bulunamadı. Kurulum: python -m pip install kaggle")
    args.target.mkdir(parents=True, exist_ok=True)
    command = ["kaggle", "datasets", "download", "-d", DATASET, "-p", str(args.target), "--unzip"]
    subprocess.run(command, check=True)
    print(f"Veri indirildi: {args.target}")
    print("Lisans/yarışma koşullarını kontrol edin; veri dosyaları git tarafından ignore edilir.")


if __name__ == "__main__":
    main()
