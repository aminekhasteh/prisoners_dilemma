"""Combine the four tournament datasets into one parquet file.

Port of section 1 of EDA.ipynb. Columns missing from a dataset are filled
the same way as before: noise -> 0, everything else -> null. Adds a
`dataset` label and the has_noise / has_probend flags.

Output: Data/combined_dataset.parquet
"""
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "Data" / "10246247"
OUT = ROOT / "Data" / "combined_dataset.parquet"

DATASETS = {
    "standard": "standard_processed.csv",
    "noise": "noise_processed.csv",
    "probend": "probend_processed.csv",
    "probend_noise": "probend_noise_processed.csv",
}

COLUMNS = [
    "Rank", "Name", "Median_score", "Cooperation_rating", "Wins", "Initial_C_rate",
    "CC_rate", "CD_rate", "DC_rate", "DD_rate",
    "CC_to_C_rate", "CD_to_C_rate", "DC_to_C_rate", "DD_to_C_rate",
    "turns", "repetitions", "size", "seed", "Normalized_Rank", "SSE",
    "Stochastic", "Memory_depth", "Makes_use_of_game", "Makes_use_of_length",
    "Cooperation_rating_max", "Cooperation_rating_min",
    "Cooperation_rating_median", "Cooperation_rating_mean",
    "Cooperation_rating_comp_to_max", "Cooperation_rating_comp_to_min",
    "Cooperation_rating_comp_to_median", "Cooperation_rating_comp_to_mean",
    "memory_usage", "noise", "probend",
]


def load(name, filename):
    df = pl.read_csv(RAW_DIR / filename, infer_schema_length=100_000)
    for col in COLUMNS:
        if col not in df.columns:
            fill = 0.0 if col == "noise" else None
            df = df.with_columns(pl.lit(fill).cast(pl.Float64).alias(col))
    return df.select(COLUMNS).with_columns(
        pl.lit(name).alias("dataset"),
        # Cast so the four frames concatenate cleanly
        pl.col(["turns", "memory_usage", "noise", "probend"]).cast(pl.Float64),
    )


def main():
    frames = [load(name, f) for name, f in DATASETS.items()]
    df = pl.concat(frames, how="vertical_relaxed").with_columns(
        (pl.col("noise") != 0).cast(pl.Int32).alias("has_noise"),
        pl.col("probend").is_not_null().cast(pl.Int32).alias("has_probend"),
    )
    df.write_parquet(OUT)
    print(f"wrote {OUT} {df.shape}")
    print(df.group_by("dataset").agg(
        pl.len().alias("rows"),
        pl.col("seed").n_unique().alias("seeds"),
    ).sort("dataset"))


if __name__ == "__main__":
    main()
