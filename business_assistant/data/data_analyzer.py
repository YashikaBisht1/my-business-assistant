from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd


class DataAnalyzer:
    """
    Handles loading and analyzing uploaded datasets (Excel, CSV).
    """

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.dataframe = self._load_file()

    def _load_file(self) -> pd.DataFrame:
        """
        Load Excel or CSV file into a pandas DataFrame.
        """
        if self.file_path.suffix == ".xlsx":
            return pd.read_excel(self.file_path)

        if self.file_path.suffix == ".csv":
            return pd.read_csv(self.file_path)

        raise ValueError("Unsupported file format")

    def basic_summary(self) -> Dict[str, Any]:
        """
        Generate a basic statistical summary of the dataset.
        """
        return {
            "rows": self.dataframe.shape[0],
            "columns": self.dataframe.shape[1],
            "column_names": list(self.dataframe.columns),
            "missing_values": self.dataframe.isna().sum().to_dict(),
        }

    def numeric_insights(self) -> Dict[str, Any]:
        """
        Analyze numeric columns for business insights.
        """
        numeric_df = self.dataframe.select_dtypes(include=np.number)

        return {
            "mean": numeric_df.mean().to_dict(),
            "median": numeric_df.median().to_dict(),
            "min": numeric_df.min().to_dict(),
            "max": numeric_df.max().to_dict(),
        }

    def to_text_summary(self) -> str:
        """
        Convert insights into plain text for LLM context.
        """
        summary = self.basic_summary()
        numeric = self.numeric_insights()

        text = "Dataset Overview:\n"
        text += f"- Rows: {summary['rows']}\n"
        text += f"- Columns: {summary['columns']}\n"
        text += f"- Column Names: {summary['column_names']}\n\n"

        text += "Numeric Insights:\n"
        for col, mean in numeric["mean"].items():
            text += f"- {col}: mean={mean}, min={numeric['min'][col]}, max={numeric['max'][col]}\n"

        return text
