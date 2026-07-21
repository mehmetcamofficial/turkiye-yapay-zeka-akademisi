"""Required matplotlib visualizations."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def save_visualizations(frame: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 5)); frame["toplam_tutar"].dropna().hist(bins=30); plt.title("Toplam Tutar Dağılımı"); plt.xlabel("Toplam Tutar"); plt.tight_layout(); plt.savefig(output_dir/"total_amount_histogram.png", dpi=180); plt.close()
    plt.figure(figsize=(8, 3)); plt.boxplot(frame["toplam_tutar"].dropna(), vert=False); plt.title("Toplam Tutar Kutu Grafiği"); plt.tight_layout(); plt.savefig(output_dir/"total_amount_boxplot.png", dpi=180); plt.close()
    counts = frame["odeme_turu"].value_counts(dropna=False)
    plt.figure(figsize=(8, 5)); counts.plot(kind="bar"); plt.title("Ödeme Türü Dağılımı"); plt.ylabel("Adet"); plt.tight_layout(); plt.savefig(output_dir/"payment_type_countplot.png", dpi=180); plt.close()
