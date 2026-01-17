import pandas as pd
import numpy as np
from typing import Dict, List


def analyze_dataframe(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Perform basic analysis on a DataFrame and generate insights.

    Args:
        df (pd.DataFrame): Cleaned DataFrame

    Returns:
        dict: Human-readable insights
    """
    insights: Dict[str, List[str]] = {
        "general": [],
        "statistics": [],
        "anomalies": []
    }

    if df.empty:
        insights["general"].append("The uploaded dataset is empty.")
        return insights

    insights["general"].append(
        f"The dataset contains {df.shape[0]} rows and {df.shape[1]} columns."
    )

    # Numeric analysis
    numeric_columns = df.select_dtypes(include=np.number).columns

    for column in numeric_columns:
        mean_value = df[column].mean()
        max_value = df[column].max()
        min_value = df[column].min()

        insights["statistics"].append(
            f"Column '{column}' has an average value of {mean_value:.2f}, "
            f"with a minimum of {min_value} and a maximum of {max_value}."
        )

        # Simple anomaly detection
        threshold = mean_value + 2 * df[column].std()
        anomalies = df[df[column] > threshold]

        if not anomalies.empty:
            insights["anomalies"].append(
                f"Column '{column}' has {len(anomalies)} values significantly "
                f"higher than average."
            )

    return insights
