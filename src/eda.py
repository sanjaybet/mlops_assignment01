import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

if __package__:
    from .download_data import COLUMN_NAMES, RAW_DATA_PATH
else:
    from download_data import COLUMN_NAMES, RAW_DATA_PATH

PROCESSED_DATA_PATH = os.path.join("data", "processed", "cleaned_heart.csv")
PLOT_DIR = "screenshots"
CONTINUOUS_COLUMNS = ["age", "trestbps", "chol", "thalach", "oldpeak"]


def load_raw_data(data_path: str = RAW_DATA_PATH) -> pd.DataFrame:
    """Load the downloaded CSV and validate its columns and numeric values."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"Raw data file not found at '{data_path}'. "
            "Run download_data.py first."
        )

    df = pd.read_csv(data_path, na_values="?")
    if list(df.columns) != COLUMN_NAMES:
        raise ValueError(
            f"Schema mismatch in '{data_path}'. Expected {COLUMN_NAMES}, "
            f"got {list(df.columns)}"
        )

    for column in COLUMN_NAMES:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Deduplicate records and map original target values to a binary label."""
    if list(df.columns) != COLUMN_NAMES:
        raise ValueError(
            f"Input data must have columns in this order: {COLUMN_NAMES}"
        )
    if df["target"].isna().any():
        raise ValueError("Target contains missing or non-numeric values")
    if not df["target"].isin([0, 1, 2, 3, 4]).all():
        raise ValueError(
            "Target contains values outside the documented range 0-4")

    cleaned = df.drop_duplicates().copy()
    cleaned["target"] = (cleaned["target"] > 0).astype(int)
    return cleaned


def save_visualizations(
    raw_df: pd.DataFrame, cleaned_df: pd.DataFrame
) -> None:
    """Create histograms, a correlation heatmap, and a class-balance plot."""
    os.makedirs(PLOT_DIR, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")

    fig, axes = plt.subplots(2, 3, figsize=(13, 8))
    for axis, column in zip(axes.flat, CONTINUOUS_COLUMNS):
        sns.histplot(
            data=raw_df,
            x=column,
            bins=20,
            kde=True,
            ax=axis,
            color="#287C8E",
        )
        axis.set_title(column.replace("_", " ").title())
        axis.set_xlabel("")
    axes.flat[-1].set_visible(False)
    fig.suptitle("Cleveland Heart Disease: Feature Distributions", fontsize=15)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOT_DIR, "feature_histograms.png"), dpi=180)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(12, 9))
    sns.heatmap(
        cleaned_df.corr(numeric_only=True),
        annot=True,
        fmt=".2f",
        cmap="vlag",
        center=0,
        linewidths=0.4,
        cbar_kws={"shrink": 0.75},
        ax=axis,
    )
    axis.set_title("Feature Correlation Heatmap")
    fig.tight_layout()
    fig.savefig(os.path.join(PLOT_DIR, "correlation_heatmap.png"), dpi=180)
    plt.close(fig)

    class_counts = cleaned_df["target"].value_counts().sort_index()
    labels = ["No disease (0)", "Disease present (1)"]
    counts = [int(class_counts.get(0, 0)), int(class_counts.get(1, 0))]
    fig, axis = plt.subplots(figsize=(7, 5))
    bars = axis.bar(
        labels, counts, color=["#4C956C", "#D1495B"], width=0.62
    )
    axis.set_title("Binary Target Class Balance")
    axis.set_ylabel("Number of records")
    axis.bar_label(bars, padding=4)
    axis.set_ylim(0, max(counts) * 1.15)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOT_DIR, "class_balance.png"), dpi=180)
    plt.close(fig)


def run_eda() -> pd.DataFrame:
    """Prepare the modeling dataset and save reproducible EDA artifacts."""
    raw_df = load_raw_data()
    cleaned_df = clean_data(raw_df)
    os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok=True)
    cleaned_df.to_csv(PROCESSED_DATA_PATH, index=False)
    save_visualizations(raw_df, cleaned_df)

    print(f"Raw data shape: {raw_df.shape}")
    print(f"Duplicate rows removed: {len(raw_df) - len(cleaned_df)}")
    print("Missing values by column:")
    print(raw_df.isna().sum().to_string())
    print("Binary target counts:")
    print(cleaned_df["target"].value_counts().sort_index().to_string())
    print(f"Cleaned dataset saved to '{PROCESSED_DATA_PATH}'.")
    print(f"EDA visualizations saved to '{PLOT_DIR}'.")
    print(
        "Missing feature values are preserved for imputation inside the training "
        "pipeline, preventing statistics from leaking across cross-validation folds."
    )
    return cleaned_df


if __name__ == "__main__":
    run_eda()
