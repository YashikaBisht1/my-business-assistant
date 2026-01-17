import pandas as pd
from typing import Dict


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean raw DataFrame:
    - Remove empty rows/columns
    - Normalize column names
    - Handle missing values

    Args:
        df (pd.DataFrame): Raw uploaded data

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    if df.empty:
        return df

    # Normalize column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # Drop completely empty rows/columns
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")

    # Fill missing values safely
    for column in df.columns:
        if df[column].dtype in ["int64", "float64"]:
            df[column] = df[column].fillna(0)
        else:
            df[column] = df[column].fillna("unknown")

    return df


def dataframe_summary(df: pd.DataFrame) -> Dict[str, str]:
    """
    Generate a high-level summary of the DataFrame.
    This is useful for LLM context.

    Args:
        df (pd.DataFrame)

    Returns:
        dict: Summary information
    """
    return {
        "rows": str(df.shape[0]),
        "columns": str(df.shape[1]),
        "column_names": ", ".join(df.columns),
    }
