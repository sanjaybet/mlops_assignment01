import pandas as pd
import pytest

from src.download_data import COLUMN_NAMES
from src.eda import clean_data
from src.predict import load_model


def test_raw_dataset_has_expected_shape():
    df = pd.read_csv("data/raw/heart.csv")
    assert df.shape == (303, 14)
    assert list(df.columns) == [
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


def test_processed_dataset_has_binary_target():
    df = pd.read_csv("data/processed/cleaned_heart.csv")
    assert set(df["target"].unique()) == {0, 1}
    assert df.shape[0] == 303
    assert df["target"].isna().sum() == 0


def test_trained_model_predicts_probabilities():
    model = load_model()
    sample = (
        pd.read_csv("data/processed/cleaned_heart.csv")
        .drop(columns="target")
        .head(2)
    )
    predictions = model.predict(sample)
    probabilities = model.predict_proba(sample)

    assert predictions.shape[0] == 2
    assert probabilities.shape == (2, 2)
    assert probabilities.sum(axis=1).round(6).tolist() == [1.0, 1.0]


def test_clean_data_maps_target_and_removes_duplicates():
    rows = [[58, 1, 1, 120, 200, 0, 0, 160, 0, 1.0, 2, 0, 3, target]
            for target in range(5)]
    source = pd.DataFrame(rows + [rows[0]], columns=COLUMN_NAMES)

    cleaned = clean_data(source)

    assert len(cleaned) == 5
    assert cleaned["target"].tolist() == [0, 1, 1, 1, 1]


@pytest.mark.parametrize("invalid_target", [None, 5, -1, "invalid"])
def test_clean_data_rejects_invalid_targets(invalid_target):
    row = [58, 1, 1, 120, 200, 0, 0, 160, 0, 1.0, 2, 0, 3, invalid_target]
    source = pd.DataFrame([row], columns=COLUMN_NAMES)

    with pytest.raises(ValueError, match="Target"):
        clean_data(source)


def test_clean_data_rejects_wrong_schema():
    source = pd.DataFrame({"age": [58], "target": [0]})

    with pytest.raises(ValueError, match="columns"):
        clean_data(source)
