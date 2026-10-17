import os
import tempfile
from typing import Any, Dict, Tuple

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import (
    GridSearchCV,
    StratifiedKFold,
    train_test_split,
)
from sklearn.preprocessing import OneHotEncoder, StandardScaler
import mlflow
import mlflow.sklearn

PROCESSED_DATA_PATH = os.path.join("data", "processed", "cleaned_heart.csv")
MODEL_OUTPUT_PATH = os.path.join("data", "processed", "model.joblib")
PLOT_DIR = "screenshots"
MLFLOW_EXPERIMENT_NAME = "Heart_Disease_Prediction"
RANDOM_STATE = 42

EXPECTED_COLUMNS = [
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
NUMERIC_FEATURES = ["age", "trestbps", "chol", "thalach", "oldpeak"]
CATEGORICAL_FEATURES = [
    "sex", "cp", "fbs", "restecg", "exang", "slope", "ca", "thal"
]
SCORING = ["accuracy", "precision", "recall", "f1", "roc_auc"]


def load_and_validate_data(
    data_path: str = PROCESSED_DATA_PATH,
) -> Tuple[pd.DataFrame, pd.Series]:
    """Load cleaned dataset and validate schema before feature splitting."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"Processed data file missing at '{data_path}'. Run eda.py first."
        )

    df = pd.read_csv(data_path)

    if list(df.columns) != EXPECTED_COLUMNS:
        raise ValueError(
            f"Schema mismatch in '{data_path}'. Expected {EXPECTED_COLUMNS}, "
            f"got {list(df.columns)}"
        )

    if df["target"].isna().any() or not df["target"].isin([0, 1]).all():
        raise ValueError(
            "Target must contain only non-missing binary labels 0 and 1")

    X = df.drop(columns=["target"])
    y = df["target"]
    return X, y


def build_pipeline(classifier: Any) -> Pipeline:
    """Build fold-local imputation, scaling, encoding, and classifier steps."""
    numeric_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        [
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline(
        [("preprocessor", preprocessor), ("classifier", classifier)]
    )


def save_model_atomically(pipeline: Pipeline, output_path: str) -> None:
    """Save model pipeline atomically to prevent partial writes."""
    output_dir = os.path.dirname(output_path) or "."
    os.makedirs(output_dir, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=output_dir, suffix=".tmp", delete=False
        ) as tmp_file:
            temp_path = tmp_file.name
            joblib.dump(pipeline, tmp_file)
        os.replace(temp_path, output_path)
        print(f"💾 Model pipeline saved atomically to '{output_path}'.")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def train_and_evaluate_model(
    model_name: str,
    pipeline: Pipeline,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    param_grid: Dict[str, Any],
) -> Tuple[Pipeline, float]:
    """Tune using stratified CV and log holdout results to MLflow."""
    os.makedirs(PLOT_DIR, exist_ok=True)

    with mlflow.start_run(run_name=model_name):
        cv = StratifiedKFold(n_splits=5, shuffle=True,
                             random_state=RANDOM_STATE)
        search = GridSearchCV(
            estimator=pipeline,
            param_grid=param_grid,
            scoring=SCORING,
            refit="roc_auc",
            cv=cv,
            n_jobs=-1,
            error_score="raise",
        )
        search.fit(X_train, y_train)
        best_pipeline = search.best_estimator_
        best_index = search.best_index_

        # The search CV selects hyperparameters; holdout metrics are reported
        # only.
        y_pred = best_pipeline.predict(X_test)
        y_proba = best_pipeline.predict_proba(X_test)[:, 1]

        metrics: Dict[str, float] = {
            **{
                f"cv_mean_{metric}": float(
                    search.cv_results_[f"mean_test_{metric}"][best_index]
                )
                for metric in SCORING
            },
            "test_accuracy": float(accuracy_score(y_test, y_pred)),
            "test_precision": float(
                precision_score(y_test, y_pred, zero_division=0)
            ),
            "test_recall": float(
                recall_score(y_test, y_pred, zero_division=0)
            ),
            "test_f1": float(f1_score(y_test, y_pred, zero_division=0)),
            "test_roc_auc": float(roc_auc_score(y_test, y_proba)),
        }

        classifier = best_pipeline.named_steps["classifier"]
        tracked_params = {
            "model_class": type(classifier).__name__,
            "cv_folds": cv.get_n_splits(),
            "cv_scoring": ",".join(SCORING),
            "selection_metric": "cv_mean_roc_auc",
            "numeric_features": ",".join(NUMERIC_FEATURES),
            "categorical_features": ",".join(CATEGORICAL_FEATURES),
            "numeric_imputation": "median",
            "categorical_imputation": "most_frequent",
            "categorical_encoding": "one_hot",
            **{
                f"classifier_{name}": value
                for name, value in classifier.get_params(deep=False).items()
            },
            **search.best_params_,
        }
        mlflow.log_params(
            {name: str(value) for name, value in tracked_params.items()}
        )
        mlflow.log_metrics(metrics)
        mlflow.set_tag("selection_metric", "cv_mean_roc_auc")
        mlflow.set_tag("dataset", "UCI Heart Disease - Cleveland, 303 records")
        mlflow.set_tag("target_mapping", "0 -> 0; 1-4 -> 1")
        mlflow.log_dict(
            {
                "random_state": RANDOM_STATE,
                "test_size": 0.2,
                "search_scoring": SCORING,
                "parameter_grid": param_grid,
                "best_parameters": search.best_params_,
            },
            "training_config.json",
        )

        search_columns = [
            column
            for column in search.cv_results_
            if column == "params"
            or column.startswith(("mean_test_", "std_test_", "rank_test_"))
        ]
        tuning_results = pd.DataFrame(search.cv_results_)[search_columns]
        with tempfile.TemporaryDirectory() as artifact_dir:
            tuning_path = os.path.join(artifact_dir, "tuning_results.csv")
            tuning_results.to_csv(tuning_path, index=False)
            mlflow.log_artifact(tuning_path, artifact_path="tuning")

        print(f"\n================ {model_name} Results ================")
        print(f"  best_params          : {search.best_params_}")
        for metric_name, score in metrics.items():
            print(f"  {metric_name:<20}: {score:.4f}")

        cm = confusion_matrix(y_test, y_pred)
        fig, ax = plt.subplots(figsize=(5, 4))
        ConfusionMatrixDisplay(
            cm, display_labels=["No Disease", "Disease"]
        ).plot(ax=ax, cmap="Blues")
        plt.title(f"Confusion Matrix - {model_name}")
        cm_path = os.path.join(
            PLOT_DIR, f"cm_{model_name.lower().replace(' ', '_')}.png"
        )
        plt.tight_layout()
        plt.savefig(cm_path, dpi=300)
        plt.close(fig)
        mlflow.log_artifact(cm_path)

        fig, ax = plt.subplots(figsize=(6, 5))
        RocCurveDisplay.from_predictions(
            y_test, y_proba, ax=ax, name=model_name)
        plt.title(f"ROC Curve - {model_name}")
        roc_path = os.path.join(
            PLOT_DIR, f"roc_{model_name.lower().replace(' ', '_')}.png"
        )
        plt.tight_layout()
        plt.savefig(roc_path, dpi=300)
        plt.close(fig)
        mlflow.log_artifact(roc_path)

        mlflow.sklearn.log_model(best_pipeline, artifact_path="model")

    return best_pipeline, metrics["cv_mean_roc_auc"]


def run_experiments() -> None:
    """Compare tuned Logistic Regression and Random Forest classifiers."""
    X, y = load_and_validate_data()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    lr_pipeline = build_pipeline(
        LogisticRegression(max_iter=1000, solver="lbfgs",
                           random_state=RANDOM_STATE)
    )
    lr_model, lr_score = train_and_evaluate_model(
        "Logistic Regression",
        lr_pipeline,
        X_train,
        X_test,
        y_train,
        y_test,
        {"classifier__C": [0.1, 1.0, 10.0]},
    )

    rf_pipeline = build_pipeline(
        RandomForestClassifier(random_state=RANDOM_STATE,
                               class_weight="balanced")
    )
    rf_model, rf_score = train_and_evaluate_model(
        "Random Forest",
        rf_pipeline,
        X_train,
        X_test,
        y_train,
        y_test,
        {
            "classifier__n_estimators": [100, 200],
            "classifier__max_depth": [3, 5, None],
            "classifier__min_samples_leaf": [1, 3],
        },
    )

    if rf_score >= lr_score:
        champion_pipeline, champion_name = rf_model, "Random Forest"
    else:
        champion_pipeline, champion_name = lr_model, "Logistic Regression"

    print(f"\nChampion Model: '{champion_name}' selected based on CV ROC-AUC.")
    save_model_atomically(champion_pipeline, MODEL_OUTPUT_PATH)


if __name__ == "__main__":
    run_experiments()
