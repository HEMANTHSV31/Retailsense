"""CSV upload validation and cleaning service."""

import logging
import os
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates and cleans uploaded CSV data files."""

    REQUIRED_COLUMNS = {"date", "sales"}
    RECOGNIZED_SALES_COLS = {"sales", "quantity", "demand", "qty", "units_sold", "volume", "sales_quantity", "units"}
    RECOGNIZED_DATE_COLS = {"date", "day", "transaction_date", "sale_date", "order_date", "timestamp", "datetime"}
    RECOGNIZED_ITEM_COLS = {"item_id", "product_id", "sku", "product", "item", "article"}
    RECOGNIZED_STORE_COLS = {"store_id", "store", "location", "warehouse", "branch"}

    @classmethod
    def validate_dataframe(cls, df: pd.DataFrame) -> dict:
        """Validate an in-memory DataFrame (works for CSV and Excel alike)."""
        result = {"valid": False, "row_count": 0, "column_count": 0, "columns": [], "warnings": [], "errors": []}
        if df is None or len(df) == 0:
            result["errors"].append("File is empty")
            return result

        result["row_count"] = len(df)
        result["column_count"] = len(df.columns)
        result["columns"] = list(df.columns)
        cols_lower = {c.lower() for c in df.columns}

        has_sales = bool(cols_lower & cls.RECOGNIZED_SALES_COLS)
        has_date = bool(cols_lower & cls.RECOGNIZED_DATE_COLS)

        if not has_sales and not has_date:
            result["errors"].append("File must have at least a date column and a sales/quantity column")
            return result
        if not has_sales:
            result["errors"].append("No sales column found. Expected one of: " + ", ".join(cls.RECOGNIZED_SALES_COLS))
            return result
        if not has_date:
            result["errors"].append("No date column found. Expected one of: " + ", ".join(cls.RECOGNIZED_DATE_COLS))
            return result

        sales_col = next(c for c in df.columns if c.lower() in cls.RECOGNIZED_SALES_COLS)
        date_col = next(c for c in df.columns if c.lower() in cls.RECOGNIZED_DATE_COLS)
        item_col = next((c for c in df.columns if c.lower() in cls.RECOGNIZED_ITEM_COLS), None)
        store_col = next((c for c in df.columns if c.lower() in cls.RECOGNIZED_STORE_COLS), None)

        if not pd.api.types.is_numeric_dtype(df[sales_col]):
            result["errors"].append(f"Sales column '{sales_col}' must be numeric")
            return result
        try:
            pd.to_datetime(df[date_col])
        except Exception:
            result["errors"].append(f"Date column '{date_col}' contains invalid dates")
            return result

        result["valid"] = True
        result["sales_col"] = sales_col
        result["date_col"] = date_col
        result["item_col"] = item_col
        result["store_col"] = store_col

        try:
            dates = pd.to_datetime(df[date_col])
            result["date_range"] = {
                "start": dates.min().strftime("%Y-%m-%d"),
                "end": dates.max().strftime("%Y-%m-%d"),
                "days": (dates.max() - dates.min()).days,
            }
        except Exception:
            pass

        sales = df[sales_col]
        result["sales_stats"] = {
            "sum": round(sales.sum(), 2),
            "mean": round(sales.mean(), 2),
            "min": round(sales.min(), 2),
            "max": round(sales.max(), 2),
            "std": round(sales.std(), 2),
        }

        missing_sales = df[sales_col].isna().sum()
        if missing_sales > 0:
            result["warnings"].append(f"Found {missing_sales} missing sales values ({missing_sales / len(df) * 100:.1f}%)")
        if df[sales_col].min() < 0:
            result["warnings"].append("Found negative sales values — these may be returns")
        if item_col is None:
            result["warnings"].append("No product/item column found. Using single-product assumption.")
        if store_col is None:
            result["warnings"].append("No store/location column found. Using single-store assumption.")

        return result

    @classmethod
    def load_dataframe(cls, filepath: str, nrows: int | None = None) -> pd.DataFrame:
        """Load DataFrame from CSV or Excel (.xlsx, .xls)."""
        ext = os.path.splitext(filepath)[1].lower()
        if ext in [".xlsx", ".xls"]:
            return pd.read_excel(filepath, nrows=nrows)
        return pd.read_csv(filepath, nrows=nrows)

    @classmethod
    def validate_file(cls, filepath: str) -> dict:
        """Validate a CSV or Excel file and return validation results."""
        try:
            df = cls.load_dataframe(filepath, nrows=10000)
        except Exception as e:
            return {
                "valid": False,
                "row_count": 0,
                "column_count": 0,
                "columns": [],
                "warnings": [],
                "errors": [f"Cannot read file: {str(e)}"],
            }
        return cls.validate_dataframe(df)

    # Alias for backward compatibility
    validate_csv = validate_file

    @classmethod
    def auto_clean(cls, df: pd.DataFrame, validation: dict) -> pd.DataFrame:
        """Auto-clean a dataframe based on validation results."""
        df = df.copy()

        # Map columns
        col_map = {}
        sales_col = validation.get("sales_col", "sales")
        date_col = validation.get("date_col", "date")
        item_col = validation.get("item_col")
        store_col = validation.get("store_col")

        if sales_col and sales_col != "sales":
            col_map[sales_col] = "sales"
        if date_col and date_col != "date":
            col_map[date_col] = "date"
        if item_col and item_col not in ("item_id", "item_id"):
            col_map[item_col] = "item_id"
        if store_col and store_col not in ("store_id", "store_id"):
            col_map[store_col] = "store_id"

        df = df.rename(columns=col_map)

        # Ensure standard columns
        if "item_id" not in df.columns:
            df["item_id"] = "PRODUCT_001"
        if "store_id" not in df.columns:
            df["store_id"] = "STORE_001"

        # Parse dates
        df["date"] = pd.to_datetime(df["date"])

        # Clean sales
        df["sales"] = pd.to_numeric(df["sales"], errors="coerce")
        df["sales"] = df["sales"].fillna(0).clip(lower=0)

        # Drop duplicates
        before = len(df)
        df = df.drop_duplicates(subset=["date", "item_id", "store_id"])
        if len(df) < before:
            logger.info(f"Removed {before - len(df)} duplicate rows")

        return df


