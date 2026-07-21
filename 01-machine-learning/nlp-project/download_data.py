"""Download UCI Sentiment Labelled Sentences once and save a local CSV.

Normal training reads only ``data/sentiment_dataset.csv`` and never calls the
network. This setup command deliberately fails rather than fabricating text.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from urllib.request import urlopen

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "sentiment_dataset.csv"
URL = "https://archive.ics.uci.edu/static/public/331/sentiment+labelled+sentences.zip"
FILES = {
    "sentiment labelled sentences/amazon_cells_labelled.txt": "amazon",
    "sentiment labelled sentences/imdb_labelled.txt": "imdb",
    "sentiment labelled sentences/yelp_labelled.txt": "yelp",
}


def main() -> None:
    """Download and combine the three official UCI labelled text files."""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DATA_PATH.exists():
        print(f"Local dataset already exists: {DATA_PATH}")
        return

    with urlopen(URL, timeout=60) as response:
        archive_bytes = response.read()

    frames: list[pd.DataFrame] = []
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        for member, source in FILES.items():
            # Split from the right so punctuation and quote characters inside
            # reviews are preserved literally instead of parsed as CSV syntax.
            records = []
            pending_text: list[str] = []
            for raw_line in archive.read(member).decode("utf-8").splitlines():
                if "\t" not in raw_line:
                    pending_text.append(raw_line.strip())
                    continue
                text, label = raw_line.rsplit("\t", maxsplit=1)
                complete_text = " ".join([*pending_text, text.strip()]).strip()
                pending_text.clear()
                records.append({"text": complete_text, "label": int(label)})
            if pending_text:
                raise ValueError(f"Unlabelled trailing text in {member}")
            frame = pd.DataFrame(records)
            frame["source"] = source
            frames.append(frame)

    dataset = pd.concat(frames, ignore_index=True)
    # UCI documents 3,000 records. Some archive revisions encode two IMDb
    # reviews across physical lines; the parser preserves them without inventing
    # labels, so 2,998 is also accepted and the resulting CSV count is reported.
    if dataset.shape[0] not in {2998, 3000} or dataset.shape[1] != 3 or set(dataset["label"]) != {0, 1}:
        raise ValueError(f"Unexpected UCI dataset shape or labels: {dataset.shape}")
    dataset.to_csv(DATA_PATH, index=False)
    print(f"Saved UCI Sentiment Labelled Sentences: {DATA_PATH} ({dataset.shape})")


if __name__ == "__main__":
    main()
