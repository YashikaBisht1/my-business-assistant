"""Simple analysis engine to convert uploaded Excel/CSV into computed insights
and small visualizations.

This module is intentionally lightweight: it reads a tabular file with
pandas, cleans the DataFrame (using dataframe_utils), computes basic
statistics, detects simple anomalies, and writes 1-3 PNG visualizations
into the logs directory. It returns a JSON-serializable dict of insights
and a list of generated image paths.
"""
from __future__ import annotations

import io
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError as e:
    pd = None  # type: ignore
    HAS_PANDAS = False
    IMPORT_ERROR = str(e)

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend (required for headless environments)
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError as e:
    plt = None  # type: ignore
    HAS_MATPLOTLIB = False
    if 'IMPORT_ERROR' not in globals():
        IMPORT_ERROR = str(e)

from business_assistant.analysis.dataframe_utils import clean_dataframe
from business_assistant.core.config import settings


def _ensure_visuals_dir() -> Path:
    visuals = Path(settings.LOGS_DIR) / "visuals"
    visuals.mkdir(parents=True, exist_ok=True)
    return visuals


def _numeric_columns(df: Any) -> List[str]:
    if pd is None:
        return []
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]


def _detect_anomalies(df: Any, numeric_cols: List[str]) -> List[str]:
    anomalies: List[str] = []
    for col in numeric_cols:
        series = df[col]
        if series.empty:
            continue
        mean = series.mean()
        std = series.std()
        if std == 0 or (pd is not None and pd.isna(std)):
            continue
        # detect values with z-score > 2.5
        z = (series - mean).abs() / std
        outliers = series.index[z > 2.5].tolist()
        if outliers:
            anomalies.append(f"Column '{col}' has {len(outliers)} outlier(s) (z>2.5)")
    return anomalies


def _make_plots(df: Any, visuals_dir: Path, max_plots: int = 3) -> List[str]:
    images: List[str] = []
    if not HAS_MATPLOTLIB or plt is None:
        return images

    numeric = _numeric_columns(df)
    plotted = 0
    for col in numeric:
        if plotted >= max_plots:
            break
        try:
            fig, ax = plt.subplots(figsize=(6, 3))
            df[col].plot(kind="line", ax=ax, title=f"{col}")
            ax.set_xlabel("")
            fname = visuals_dir / f"plot_{col}_{int(datetime.utcnow().timestamp())}.png"
            fig.tight_layout()
            fig.savefig(str(fname))
            plt.close(fig)
            images.append(str(fname))
            plotted += 1
        except Exception:
            # skip plotting errors
            continue

    # If no numeric columns, generate a simple table snapshot image
    if not images and plt is not None:
        try:
            fig, ax = plt.subplots(figsize=(6, 2))
            ax.axis("off")
            sample = df.head(10).to_string()
            ax.text(0, 1, sample, fontsize=8, family="monospace", va="top")
            fname = visuals_dir / f"table_sample_{int(datetime.utcnow().timestamp())}.png"
            fig.savefig(str(fname), bbox_inches="tight")
            plt.close(fig)
            images.append(str(fname))
        except Exception:
            pass

    return images


def process_tabular(file_path: str) -> Dict[str, object]:
    """Read a CSV or Excel file and produce computed insights + visuals.

    Args:
        file_path: path to the uploaded file (temporary path from Gradio)

    Returns:
        dict containing 'insights' (dict) and 'visuals' (list of image paths)
    """
    if not HAS_PANDAS:
        error_msg = "pandas is not available in this environment"
        if 'IMPORT_ERROR' in globals():
            error_msg += f": {IMPORT_ERROR}"
        error_msg += ". Please install: pip install pandas matplotlib"
        raise RuntimeError(error_msg)
    
    if not HAS_MATPLOTLIB:
        # Continue without matplotlib - visuals won't be generated
        import warnings
        warnings.warn("matplotlib not available - visualizations will be skipped")

    visuals_dir = _ensure_visuals_dir()

    # Read file
    try:
        ext = Path(file_path).suffix.lower()
        if ext in {".csv"}:
            df = pd.read_csv(file_path)
        else:
            # try excel for xls/xlsx, fallback to CSV reader
            df = pd.read_excel(file_path)
    except Exception as exc:
        # fallback: try reading via pandas read_csv from bytes
        with open(file_path, "rb") as fh:
            data = fh.read()
        try:
            df = pd.read_csv(io.BytesIO(data))
        except Exception as exc2:
            raise RuntimeError(f"Failed to read uploaded file: {exc} / {exc2}")

    # Clean
    df = clean_dataframe(df)

    # Basic stats
    numeric_cols = _numeric_columns(df)
    stats: Dict[str, object] = {}
    for col in numeric_cols:
        s = df[col]
        stats[col] = {
            "count": int(s.count()),
            "mean": float(s.mean()) if not pd.isna(s.mean()) else None,
            "std": float(s.std()) if not pd.isna(s.std()) else None,
            "min": float(s.min()) if not pd.isna(s.min()) else None,
            "max": float(s.max()) if not pd.isna(s.max()) else None,
        }

    # Simple trend/opinion: compare last vs first period if time-like index available
    trends: List[str] = []
    if "date" in df.columns:
        try:
            df["date"] = pd.to_datetime(df["date"])
            # pick a numeric column to trend if available
            if numeric_cols:
                col = numeric_cols[0]
                first = df.sort_values("date").iloc[0][col]
                last = df.sort_values("date").iloc[-1][col]
                if pd.notna(first) and pd.notna(last):
                    pct = ((last - first) / (abs(first) if first else 1)) * 100
                    trends.append(f"{col} changed {pct:.1f}% from first to last date in dataset")
        except Exception:
            pass

    # Anomalies
    anomalies = _detect_anomalies(df, numeric_cols)

    # Comparisons: if 'region' present, give high-level grouping
    comparisons: Dict[str, object] = {}
    if "region" in df.columns and numeric_cols:
        try:
            grp = df.groupby("region")[numeric_cols].mean().to_dict(orient="index")
            comparisons = {"region_means": grp}
        except Exception:
            comparisons = {}

    insights = {
        "trends": "; ".join(trends) if trends else "",
        "averages": stats,
        "anomalies": anomalies,
        "comparisons": comparisons,
    }

    visuals = _make_plots(df, visuals_dir)

    return {"insights": insights, "visuals": visuals}
