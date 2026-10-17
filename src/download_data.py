import io
import os
import tempfile
import urllib.request
import zipfile

import pandas as pd

DATA_URL = "https://archive.ics.uci.edu/static/public/45/heart+disease.zip"
RAW_DATA_PATH = os.path.join("data", "raw", "heart.csv")
DATA_FILE_NAME = "processed.cleveland.data"
EXPECTED_ROWS = 303

# UCI Cleveland feature and target names, in source-file order.
COLUMN_NAMES = [
    "age",
    "sex",
    "cp",
    "trestbps",
    "chol",
    "fbs",
    "restecg",
    "thalach",
    "exang",
    "oldpeak",
    "slope",
    "ca",
    "thal",
    "target",
]


def download_dataset(
    url: str = DATA_URL,
    output_path: str = RAW_DATA_PATH,
) -> pd.DataFrame:
    """Download and validate the processed Cleveland data.

    Data is loaded from the UCI archive.
    """
    output_dir = os.path.dirname(output_path) or "."
    os.makedirs(output_dir, exist_ok=True)

    print(f"Downloading dataset archive from {url}...")
    with urllib.request.urlopen(url) as response:
        archive_data = response.read()

    with zipfile.ZipFile(io.BytesIO(archive_data)) as archive:
        data_path = next(
            (
                name
                for name in archive.namelist()
                if name.endswith(DATA_FILE_NAME)
            ),
            None,
        )
        if data_path is None:
            raise ValueError(
                f"{DATA_FILE_NAME} was not found in the UCI archive"
            )
        with archive.open(data_path) as data_file:
            df = pd.read_csv(
                data_file,
                header=None,
                names=COLUMN_NAMES,
                na_values="?",
                skipinitialspace=True,
            )

    if df.shape != (EXPECTED_ROWS, len(COLUMN_NAMES)):
        raise ValueError(
            f"Unexpected Cleveland dataset shape {df.shape}; expected "
            f"({EXPECTED_ROWS}, {len(COLUMN_NAMES)})"
        )
    if not df["target"].isin([0, 1, 2, 3, 4]).all():
        raise ValueError(
            "Dataset contains unexpected values in the target column"
        )

    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=output_dir,
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = temporary_file.name
            df.to_csv(temporary_file, index=False)
        os.replace(temporary_path, output_path)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)

    print(f"Dataset saved to '{output_path}' ({len(df)} rows).")
    return df


if __name__ == "__main__":
    download_dataset()
