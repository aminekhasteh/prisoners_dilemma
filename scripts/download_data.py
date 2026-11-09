"""Download the Glynatsi, Knight & Harper (2024) tournament data from Zenodo.

Record: https://zenodo.org/records/10246247 (~1.75 GB in total).
Files are saved to Data/10246247/ and skipped if already present.
"""
import urllib.request
from pathlib import Path

RECORD = "https://zenodo.org/records/10246247/files"
FILES = [
    "standard_processed.csv",
    "noise_processed.csv",
    "probend_processed.csv",
    "probend_noise_processed.csv",
]
OUT_DIR = Path(__file__).resolve().parent.parent / "Data" / "10246247"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        path = OUT_DIR / name
        if path.exists():
            print(f"skip {name} (exists)")
            continue
        print(f"downloading {name} ...")
        tmp = path.with_suffix(".part")
        urllib.request.urlretrieve(f"{RECORD}/{name}?download=1", tmp)
        tmp.rename(path)
    print("done")


if __name__ == "__main__":
    main()
