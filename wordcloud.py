"""Generate a per-country skills word cloud from files/cleaned/*_final.csv."""

from __future__ import annotations

import ast
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

# This file's own directory sits first on sys.path, so a plain
# `from wordcloud import WordCloud` would import this script itself
# instead of the installed wordcloud package. Drop it before importing.
_THIS_DIR = str(Path(__file__).resolve().parent)
sys.path = [entry for entry in sys.path if entry != _THIS_DIR]
from wordcloud import WordCloud  # noqa: E402

sys.path.insert(0, _THIS_DIR)

CLEANED_DIR = Path("files/cleaned")
OUTPUT_DIR = Path("results/wordclouds")
SKILL_COLUMN = "matched_mapped_skills"

COUNTRY_NAMES = {
    "be": "Belgium",
    "cs": "Czechia",
    "de": "Germany",
    "el": "Greece",
    "es": "Spain",
    "fr": "France",
    "nl": "Netherlands",
    "sv": "Sweden",
}


def parse_skills(value: object) -> list[str]:
    if pd.isna(value):
        return []
    try:
        parsed = ast.literal_eval(str(value))
    except (SyntaxError, ValueError):
        return []
    return [str(skill) for skill in parsed] if isinstance(parsed, list) else []


def country_name(csv_file: Path) -> str:
    code = csv_file.stem.split("_")[0].lower()
    return COUNTRY_NAMES.get(code, code)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_files = sorted(CLEANED_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {CLEANED_DIR}")

    for csv_file in csv_files:
        df = pd.read_csv(csv_file, sep=";", low_memory=False)
        if SKILL_COLUMN not in df.columns:
            print(f"Skipping {csv_file.name}: no '{SKILL_COLUMN}' column")
            continue

        skills = [skill for value in df[SKILL_COLUMN] for skill in parse_skills(value)]
        if not skills:
            print(f"Skipping {csv_file.name}: no skills found")
            continue

        frequencies = Counter(skills)
        cloud = WordCloud(
            width=1600,
            height=900,
            background_color="white",
        ).generate_from_frequencies(frequencies)

        output_path = OUTPUT_DIR / f"{country_name(csv_file)}.png"
        cloud.to_file(output_path)
        print(f"{csv_file.name}: {len(skills)} skill mentions, {len(frequencies)} unique -> {output_path}")


if __name__ == "__main__":
    main()
