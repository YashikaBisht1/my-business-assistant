"""Data loading utilities with validation and error handling."""
from __future__ import annotations

import pandas as pd
from pathlib import Path
from typing import Union, Optional
import os

from business_assistant.core.config import settings
from business_assistant.utils.logging import get_logger

logger = get_logger(__name__)


def validate_file(file_path: Path) -> tuple[bool, Optional[str]]:
    """Validate file before loading.
    
    Returns:
        (is_valid, error_message)
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"
    
    # Check file size
    file_size = file_path.stat().st_size
    if file_size > settings.MAX_UPLOAD_SIZE:
        max_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
        return False, f"File too large: {file_size / (1024*1024):.1f}MB (max: {max_mb}MB)"
    
    if file_size == 0:
        return False, "File is empty"
    
    # Check extension
    ext = file_path.suffix.lower().lstrip(".")
    if ext not in settings.allowed_extensions_list:
        return False, f"File type not allowed: {ext} (allowed: {', '.join(settings.allowed_extensions_list)})"
    
    return True, None


def load_data(file_path: Union[str, Path], sheet_name: Optional[str] = None) -> pd.DataFrame:
    """
    Load data from Excel, CSV, JSON, or simple text file into a pandas DataFrame.
    
    Args:
        file_path: Path to the uploaded file
        sheet_name: Optional sheet name for Excel files (defaults to first sheet)
    
    Returns:
        pd.DataFrame: Processed data ready for analysis.
    
    Raises:
        ValueError: If file is invalid or cannot be loaded
        FileNotFoundError: If file doesn't exist
    """
    file_path = Path(file_path)
    
    # Validate file
    is_valid, error_msg = validate_file(file_path)
    if not is_valid:
        raise ValueError(error_msg)
    
    ext = file_path.suffix.lower()
    
    try:
        logger.info(f"Loading file: {file_path.name} ({ext})")
        
        if ext in [".xlsx", ".xls"]:
            # Excel file
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                # Try first sheet
                excel_file = pd.ExcelFile(file_path)
                df = pd.read_excel(excel_file, sheet_name=excel_file.sheet_names[0])
                logger.info(f"Loaded sheet: {excel_file.sheet_names[0]}")
        elif ext == ".csv":
            # CSV file - try different encodings
            encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]
            df = None
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    logger.info(f"Loaded CSV with encoding: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise ValueError("Could not decode CSV file with any standard encoding")
        elif ext == ".json":
            # JSON file
            df = pd.read_json(file_path)
        elif ext == ".txt":
            # Simple text file: try tab-separated first, then comma
            try:
                df = pd.read_csv(file_path, sep="\t")
            except Exception:
                df = pd.read_csv(file_path, sep=",")
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        # Validate DataFrame
        if df.empty:
            raise ValueError("File loaded but contains no data")
        
        # Basic cleaning: drop fully empty rows and columns
        original_shape = df.shape
        df = df.dropna(how="all")
        df = df.dropna(axis=1, how="all")
        df = df.reset_index(drop=True)
        
        if df.empty:
            raise ValueError("After cleaning, file contains no data")
        
        logger.info(f"Loaded {df.shape[0]} rows, {df.shape[1]} columns (from {original_shape})")
        
        return df

    except pd.errors.EmptyDataError:
        raise ValueError("File appears to be empty or corrupted")
    except Exception as e:
        logger.error(f"Error loading file {file_path}: {e}", exc_info=True)
        if isinstance(e, (ValueError, FileNotFoundError)):
            raise
        raise ValueError(f"Failed to load file: {str(e)}")
