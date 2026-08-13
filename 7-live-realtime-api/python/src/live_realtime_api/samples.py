"""
Loading the sample index for the Live API example.

The bundled isiZulu sample clips live in the repo-root `data/` folder. The file
`vulavula-isizulu-samples - 5_sample_metadata.csv` is the index: one row per WAV,
with the ground-truth transcript (isiZulu), translation (English), and speaker /
topic metadata. This module parses that index so the example can stream a clip and
show the expected result alongside the live output.
"""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List, Union

METADATA_FILENAME = "vulavula-isizulu-samples - 5_sample_metadata.csv"


@dataclass(frozen=True)
class Sample:
    """One row of the sample index."""

    filename: str
    transcript: str  # ground-truth source transcript (isiZulu)
    translation: str  # ground-truth translation (English)
    domain: str
    topic: str
    scenario: str
    duration: float
    gender: str
    age_range: str
    path: Path  # absolute-ish path to the WAV file


def load_samples(data_dir: Union[str, Path]) -> List[Sample]:
    """
    Parse the metadata CSV into a list of Sample objects, in CSV row order.

    Args:
        data_dir (Union[str, Path]): Folder containing the metadata CSV and WAVs.

    Returns:
        List[Sample]: One Sample per row of the index.
    """
    data_dir = Path(data_dir)
    samples = []
    with (data_dir / METADATA_FILENAME).open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            samples.append(
                Sample(
                    filename=row["filename"],
                    transcript=row["transcript"],
                    translation=row["translation"],
                    domain=row["domain"],
                    topic=row["topic"],
                    scenario=row["scenario"],
                    duration=float(row["duration"]),
                    gender=row["gender"],
                    age_range=row["age_range"],
                    path=data_dir / row["filename"],
                )
            )
    return samples
