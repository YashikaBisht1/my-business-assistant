"""Enhanced data analyzer with comprehensive business insights."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd

from business_assistant.data.excel_loader import load_data
from business_assistant.utils.logging import get_logger

logger = get_logger(__name__)


class DataAnalyzer:
    """
    Handles loading and analyzing uploaded datasets (Excel, CSV).
    Provides comprehensive business insights and validation.
    """

    def __init__(self, file_path: Path, sheet_name: Optional[str] = None) -> None:
        """
        Initialize analyzer with a data file.
        
        Args:
            file_path: Path to data file
            sheet_name: Optional sheet name for Excel files
        """
        self.file_path = Path(file_path)
        self.sheet_name = sheet_name
        self.dataframe = self._load_file()

    def _load_file(self) -> pd.DataFrame:
        """
        Load Excel or CSV file into a pandas DataFrame.
        """
        return load_data(self.file_path, self.sheet_name)

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

    def detect_outliers(self, method: str = "iqr") -> Dict[str, List[int]]:
        """
        Detect outliers in numeric columns.
        
        Args:
            method: 'iqr' (Interquartile Range) or 'zscore'
        
        Returns:
            Dictionary mapping column names to list of outlier indices
        """
        outliers = {}
        numeric_cols = self.dataframe.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            series = self.dataframe[col].dropna()
            if len(series) == 0:
                continue
            
            if method == "iqr":
                Q1 = series.quantile(0.25)
                Q3 = series.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outlier_indices = series[(series < lower_bound) | (series > upper_bound)].index.tolist()
            else:  # zscore
                z_scores = np.abs((series - series.mean()) / series.std())
                outlier_indices = series[z_scores > 2.5].index.tolist()
            
            if outlier_indices:
                outliers[col] = outlier_indices
        
        return outliers

    def correlation_analysis(self) -> Dict[str, Any]:
        """
        Analyze correlations between numeric columns.
        
        Returns:
            Dictionary with correlation matrix and top correlations
        """
        numeric_df = self.dataframe.select_dtypes(include=[np.number])
        
        if numeric_df.shape[1] < 2:
            return {"message": "Need at least 2 numeric columns for correlation analysis"}
        
        corr_matrix = numeric_df.corr()
        
        # Find top correlations (excluding self-correlations)
        top_correlations = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                col1 = corr_matrix.columns[i]
                col2 = corr_matrix.columns[j]
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) > 0.5:  # Significant correlation
                    top_correlations.append({
                        "column1": col1,
                        "column2": col2,
                        "correlation": float(corr_value)
                    })
        
        top_correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        
        return {
            "correlation_matrix": corr_matrix.to_dict(),
            "top_correlations": top_correlations[:10]  # Top 10
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
        text += f"- Column Names: {', '.join(summary['column_names'])}\n\n"

        if numeric["mean"]:
            text += "Numeric Insights:\n"
            for col, mean_val in numeric["mean"].items():
                text += f"- {col}: mean={mean_val:.2f}, min={numeric['min'][col]:.2f}, max={numeric['max'][col]:.2f}\n"
            text += "\n"
        
        # Add outlier information
        outliers = self.detect_outliers()
        if outliers:
            text += "Outliers Detected:\n"
            for col, indices in outliers.items():
                text += f"- {col}: {len(indices)} outlier(s)\n"
            text += "\n"

        return text
