import pandas as pd
from pathlib import Path
from typing import Union

def load_data(file_path: Union[str, Path]) -> pd.DataFrame:
    """
    Load data from Excel, CSV, JSON, or simple text file into a pandas DataFrame.
    
    Args:
        file_path (str | Path): Path to the uploaded file.
    
    Returns:
        pd.DataFrame: Processed data ready for analysis.
    """
    file_path = Path(file_path)
    ext = file_path.suffix.lower()

    try:
        if ext in [".xlsx", ".xls"]:
            # Excel file
            df = pd.read_excel(file_path)
        elif ext == ".csv":
            # CSV file
            df = pd.read_csv(file_path)
        elif ext == ".json":
            # JSON file
            df = pd.read_json(file_path)
        elif ext == ".txt":
            # Simple text file: assume tab-separated
            df = pd.read_csv(file_path, sep="\t")
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        # Basic cleaning: drop fully empty rows and columns
        df.dropna(how="all", inplace=True)
        df.dropna(axis=1, how="all", inplace=True)
        df.reset_index(drop=True, inplace=True)

        return df

    except Exception as e:
        print(f"Error loading file {file_path}: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error
