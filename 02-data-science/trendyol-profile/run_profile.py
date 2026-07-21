"""Explicit CLI for inventory and bounded Trendyol profiling."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "midterm-assignment" / "data"
INVENTORY_PATH = BASE_DIR.parent / "midterm-assignment" / "outputs" / "dataset_inventory.json"
OUTPUT_DIR = BASE_DIR / "outputs"
sys.path.insert(0, str(BASE_DIR))

from src.inventory import build_inventory, extract_archives  # noqa: E402
from src.reporting import generate_profiles  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory-only", action="store_true")
    parser.add_argument("--max-sample-rows", type=int, default=20_000)
    args = parser.parse_args()
    extracted = extract_archives(DATA_DIR)
    if extracted:
        print(f"{len(extracted)} dosya ilk kez çıkarıldı.")
    inventory = build_inventory(DATA_DIR, INVENTORY_PATH)
    print(f"Envanter: {len(inventory)} veri dosyası")
    if not args.inventory_only:
        generate_profiles(DATA_DIR, inventory, OUTPUT_DIR, max_rows=args.max_sample_rows)
        print(f"Profil kaydedildi: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
