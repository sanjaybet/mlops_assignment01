import pandas as pd

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
    sample = pd.read_csv("data/processed/cleaned_heart.csv").drop(columns="target").head(2)
    predictions = model.predict(sample)
    probabilities = model.predict_proba(sample)

    assert predictions.shape[0] == 2
    assert probabilities.shape == (2, 2)
    assert probabilities.sum(axis=1).round(6).tolist() == [1.0, 1.0]
