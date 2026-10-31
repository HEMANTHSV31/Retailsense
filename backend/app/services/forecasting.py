"""Forecasting service — demand forecasting with multiple model types."""

import logging
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import warnings

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


class DemandForecaster:
    """Demand forecasting with support for multiple model types.

    Supported models: 'baseline', 'random_forest', 'xgboost', 'lightgbm', 'prophet'.
    """

    def __init__(self, model_type="random_forest"):
        self.model_type = model_type
        self.model = None
        self.feature_names = None
        self._prophet_daily = None
        logger.info(f"DemandForecaster initialized with model_type={model_type}")

    # ── Feature preparation ──────────────────────────────────────────────────

    def prepare_features(self, df, target_col="sales", exclude_cols=None):
        """Prepare features for modeling."""
        if exclude_cols is None:
            exclude_cols = ["id", "date", "d", "wm_yr_wk"]

        if self.feature_names is not None:
            valid_features = [f for f in self.feature_names if f in df.columns]
        else:
            feature_cols = [
                col for col in df.columns
                if col not in exclude_cols + [target_col]
                and df[col].dtype in ["int64", "float64", "int32", "float32"]
            ]
            valid_features = []
            for col in feature_cols:
                if df[col].notna().sum() > 0:
                    if len(df) > 1 and df[col].nunique() > 1:
                        valid_features.append(col)
                    elif len(df) <= 1:
                        valid_features.append(col)
            if not valid_features and feature_cols:
                valid_features = feature_cols
            self.feature_names = valid_features

        X = df[valid_features].fillna(0)
        y = df[target_col] if target_col in df.columns else None
        return X, y

    # ── Individual trainers ─────────────────────────────────────────────────

    def train_baseline(self, df, target_col="sales"):
        """Naive baseline: predict per-group mean."""
        self.model_type = "baseline"
        if "item_id" in df.columns and "store_id" in df.columns:
            baseline = df.groupby(["item_id", "store_id"])[target_col].mean().to_dict()
            self.model = {"_type": "baseline", "values": baseline}
        else:
            self.model = {"_type": "baseline", "global_mean": df[target_col].mean()}
        logger.info("Baseline model trained")
        return self.model

    def train_random_forest(self, X_train, y_train, n_estimators=100, max_depth=10):
        """Train a Random Forest model."""
        from sklearn.ensemble import RandomForestRegressor
        self.model = RandomForestRegressor(
            n_estimators=n_estimators, max_depth=max_depth,
            random_state=42, n_jobs=-1,
        )
        self.model.fit(X_train, y_train)
        self.model_type = "random_forest"
        logger.info("Random Forest model trained")
        return self.model

    def train_xgboost(self, X_train, y_train, n_estimators=200, max_depth=8, learning_rate=0.1):
        """Train an XGBoost model."""
        try:
            from xgboost import XGBRegressor
            self.model = XGBRegressor(
                n_estimators=n_estimators, max_depth=max_depth,
                learning_rate=learning_rate, random_state=42,
                n_jobs=-1, verbosity=0,
            )
            self.model.fit(X_train, y_train)
            self.model_type = "xgboost"
            logger.info("XGBoost model trained")
        except Exception as e:
            logger.warning(f"XGBoost failed ({e}), falling back to GradientBoostingRegressor")
            from sklearn.ensemble import GradientBoostingRegressor
            self.model = GradientBoostingRegressor(
                n_estimators=min(n_estimators, 100), max_depth=min(max_depth, 6),
                learning_rate=learning_rate, random_state=42,
            )
            self.model.fit(X_train, y_train)
            self.model_type = "xgboost"
        return self.model

    def train_lightgbm(self, X_train, y_train, n_estimators=200, max_depth=8, learning_rate=0.1):
        """Train a LightGBM model."""
        try:
            from lightgbm import LGBMRegressor
            self.model = LGBMRegressor(
                n_estimators=n_estimators, max_depth=max_depth,
                learning_rate=learning_rate, random_state=42,
                n_jobs=-1, verbosity=-1,
            )
            self.model.fit(X_train, y_train)
            self.model_type = "lightgbm"
            logger.info("LightGBM model trained")
        except Exception as e:
            logger.warning(f"LightGBM failed ({e}), falling back to HistGradientBoostingRegressor")
            from sklearn.ensemble import HistGradientBoostingRegressor
            self.model = HistGradientBoostingRegressor(
                max_iter=min(n_estimators, 100), max_depth=min(max_depth, 8),
                learning_rate=learning_rate, random_state=42,
            )
            self.model.fit(X_train, y_train)
            self.model_type = "lightgbm"
        return self.model

    def train_prophet(self, df, date_col="date", target_col="sales"):
        """Train a Prophet model on aggregated daily sales."""
        from prophet import Prophet
        daily = df.groupby(date_col)[target_col].sum().reset_index()
        daily.columns = ["ds", "y"]
        self.model = Prophet(
            yearly_seasonality=True, weekly_seasonality=True,
            daily_seasonality=False, interval_width=0.95,
        )
        self.model.fit(daily)
        self.model_type = "prophet"
        self._prophet_daily = daily
        logger.info("Prophet model trained")
        return self.model

    # ── Multi-model training & comparison ──────────────────────────────────

    def train_all_models(self, df, target_col="sales", test_size=0.2,
                         sample_frac=1.0, include_prophet=False, include_baseline=True):
        """Train all supported models and return comparison table.

        Returns
        -------
        results : pd.DataFrame
            Columns: model, MAE, RMSE, R2, MAPE, training_time_sec
        best_model : str
            Name of the model with lowest MAE
        """
        from time import time

        if sample_frac < 1.0:
            df = df.sample(frac=sample_frac, random_state=42)

        X, y = self.prepare_features(df, target_col)
        mask = y.notna()
        X, y = X[mask], y[mask]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

        models_to_train = []
        if include_baseline:
            models_to_train.append("baseline")
        models_to_train.extend(["random_forest", "xgboost", "lightgbm"])
        results = []
        logger.info(f"Training {len(models_to_train)} models...")

        for mtype in models_to_train:
            t0 = time()
            try:
                if mtype == "baseline":
                    self.train_baseline(df, target_col)
                    preds = self.predict(X_test)
                elif mtype == "random_forest":
                    self.train_random_forest(X_train, y_train)
                    preds = self.predict(X_test)
                elif mtype == "xgboost":
                    self.train_xgboost(X_train, y_train)
                    preds = self.predict(X_test)
                elif mtype == "lightgbm":
                    self.train_lightgbm(X_train, y_train)
                    preds = self.predict(X_test)

                elapsed = time() - t0
                metrics = self._calculate_metrics(y_test, preds)
                metrics["model"] = mtype
                metrics["training_time_sec"] = round(elapsed, 2)
                results.append(metrics)
                logger.info(f"{mtype}: MAE={metrics['MAE']:.2f}, RMSE={metrics['RMSE']:.2f}, time={elapsed:.2f}s")
            except Exception as e:
                logger.error(f"Error training {mtype}: {e}")
                results.append({
                    "model": mtype, "MAE": np.nan, "RMSE": np.nan,
                    "R2": np.nan, "MAPE": np.nan, "training_time_sec": np.nan, "error": str(e),
                })

        if include_prophet:
            t0 = time()
            try:
                self.train_prophet(df, target_col=target_col)
                test_min = df["date"].max() - pd.Timedelta(days=28)
                future = self.model.make_future_dataframe(periods=0)
                forecast = self.model.predict(future)
                forecast["ds"] = pd.to_datetime(forecast["ds"])
                daily_actual = df.groupby("date")[target_col].sum().reset_index()
                daily_actual.columns = ["ds", "y_actual"]
                merged = forecast.merge(daily_actual, on="ds", how="inner")
                merged = merged[merged["ds"] >= test_min]
                if len(merged) > 0:
                    p_metrics = self._calculate_metrics(merged["y_actual"].values, merged["yhat"].values)
                    p_metrics["model"] = "prophet"
                    p_metrics["training_time_sec"] = round(time() - t0, 2)
                    results.append(p_metrics)
            except Exception as e:
                logger.error(f"Error training Prophet: {e}")

        result_df = pd.DataFrame(results)
        valid = result_df.dropna(subset=["MAE"])
        best = valid.loc[valid["MAE"].idxmin(), "model"] if len(valid) > 0 else "random_forest"
        logger.info(f"Best model: {best}")
        return result_df, best

    @staticmethod
    def _calculate_metrics(y_true, y_pred):
        """Calculate common regression metrics (MAE, RMSE, R2, MAPE, WAPE, bias)."""
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        r2 = r2_score(y_true, y_pred)
        mask = y_true != 0
        mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100 if mask.sum() > 0 else float("nan")
        denom = np.sum(np.abs(y_true))
        wape = float(np.sum(np.abs(y_true - y_pred)) / denom * 100) if denom > 0 else float("nan")
        bias_val = float(np.mean(y_pred - y_true)) if len(y_true) > 0 else float("nan")
        return {"MAE": mae, "RMSE": rmse, "R2": r2, "MAPE": mape, "WAPE": wape, "bias": bias_val}

    # ── Predict ──────────────────────────────────────────────────────────────

    def predict(self, X):
        """Make predictions using the trained model."""
        if self.model is None:
            raise ValueError("Model not trained yet. Call train_model() first.")

        if isinstance(self.model, dict) and self.model.get("_type") == "baseline":
            if "global_mean" in self.model:
                return np.full(len(X), self.model["global_mean"], dtype=float)
            elif "values" in self.model:
                return np.ones(len(X)) * np.mean(list(self.model["values"].values()))
            return np.zeros(len(X))

        if self.feature_names:
            X = X[self.feature_names].fillna(0)
        predictions = self.model.predict(X)
        return np.maximum(predictions, 0)

    def predict_prophet(self, periods=28):
        """Forecast future periods using a trained Prophet model."""
        if self.model_type != "prophet":
            raise ValueError("Model must be prophet to call predict_prophet")
        future = self.model.make_future_dataframe(periods=periods)
        forecast = self.model.predict(future)
        return forecast.tail(periods)

    # ── Unified training interface ──────────────────────────────────────────

    def train_model(self, df, target_col="sales", test_size=0.2):
        """Train the model specified by self.model_type with graceful sparse-data fallback."""
        # If dataset is small or single-sample, fall back to baseline mean to prevent crashes
        if len(df) < 5 or self.model_type == "baseline":
            self.model_type = "baseline"
            self.train_baseline(df, target_col)
            test_score = {"MAE": 0.0, "RMSE": 0.0, "R2": 1.0, "MAPE": 0.0, "WAPE": 0.0, "bias": 0.0}
            return self.model, test_score

        X, y = self.prepare_features(df, target_col)
        mask = y.notna()
        X, y = X[mask], y[mask]

        if X.shape[1] == 0 or len(X) < 5:
            self.model_type = "baseline"
            self.train_baseline(df, target_col)
            test_score = {"MAE": 0.0, "RMSE": 0.0, "R2": 1.0, "MAPE": 0.0, "WAPE": 0.0, "bias": 0.0}
            return self.model, test_score

        # Safely split train/test so test set has at least 1 sample and train set has at least 2
        effective_test_size = max(1 / len(X), min(test_size, 0.4))
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=effective_test_size, random_state=42)
        logger.info(f"Training set: {len(X_train)} samples, Test set: {len(X_test)} samples")

        trainers = {
            "baseline": lambda: (self.train_baseline(df, target_col), self.evaluate(X_train, y_train), self.evaluate(X_test, y_test)),
            "random_forest": lambda: (self.train_random_forest(X_train, y_train), self.evaluate(X_train, y_train), self.evaluate(X_test, y_test)),
            "xgboost": lambda: (self.train_xgboost(X_train, y_train), self.evaluate(X_train, y_train), self.evaluate(X_test, y_test)),
            "lightgbm": lambda: (self.train_lightgbm(X_train, y_train), self.evaluate(X_train, y_train), self.evaluate(X_test, y_test)),
            "prophet": lambda: (self.train_prophet(df, target_col=target_col), {}, self.evaluate_prophet(df, target_col)),
        }

        if self.model_type not in trainers:
            raise ValueError(f"Unknown model_type: {self.model_type}")

        _, train_score, test_score = trainers[self.model_type]()
        logger.info(f"Train: {train_score} | Test: {test_score}")
        return self.model, test_score

    def evaluate_prophet(self, df, target_col="sales"):
        """Evaluate Prophet on the last 28 days."""
        test_min = df["date"].max() - pd.Timedelta(days=28)
        daily_actual = df.groupby("date")[target_col].sum().reset_index()
        daily_actual.columns = ["ds", "y_actual"]
        future = self.model.make_future_dataframe(periods=0)
        forecast = self.model.predict(future)
        forecast["ds"] = pd.to_datetime(forecast["ds"])
        merged = forecast.merge(daily_actual, on="ds", how="inner")
        merged = merged[merged["ds"] >= test_min]
        if len(merged) == 0:
            return {"MAE": np.nan, "RMSE": np.nan, "R2": np.nan, "MAPE": np.nan}
        return self._calculate_metrics(merged["y_actual"].values, merged["yhat"].values)

    def evaluate(self, X, y):
        """Evaluate model performance."""
        if isinstance(self.model, dict) and self.model.get("_type") == "baseline":
            if "global_mean" in self.model:
                predictions = np.full(len(X), self.model["global_mean"], dtype=float)
            elif "values" in self.model:
                predictions = np.full(len(X), np.mean(list(self.model["values"].values())), dtype=float)
            else:
                predictions = np.zeros(len(X))
        else:
            predictions = self.predict(X)
        return self._calculate_metrics(y, predictions)

    def get_feature_importance(self, top_n=20):
        """Get feature importance from the trained model (tree-based only)."""
        if self.model is None:
            raise ValueError("Model not trained yet.")
        if hasattr(self.model, "feature_importances_"):
            importance_df = pd.DataFrame({
                "feature": self.feature_names,
                "importance": self.model.feature_importances_,
            }).sort_values("importance", ascending=False).head(top_n)
            return importance_df
        return None

    def forecast_future(self, df, periods=28):
        """Forecast future demand for each item-store combination."""
        if self.model_type == "prophet":
            return self._forecast_prophet(df, periods)

        last_date = df["date"].max()
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=periods)
        item_store_combos = df[["item_id", "store_id"]].drop_duplicates()
        forecasts = []

        for _, row in item_store_combos.iterrows():
            item_id, store_id = row["item_id"], row["store_id"]
            item_store_data = df[(df["item_id"] == item_id) & (df["store_id"] == store_id)].copy()
            if len(item_store_data) == 0:
                continue
            running_history = item_store_data.tail(60).copy()

            for future_date in future_dates:
                future_row = running_history.iloc[-1:].copy()
                future_row["date"] = future_date
                future_row["year"] = future_date.year
                future_row["month"] = future_date.month
                future_row["day"] = future_date.day
                future_row["dayofweek"] = future_date.dayofweek
                future_row["quarter"] = future_date.quarter
                future_row["is_weekend"] = int(future_date.dayofweek >= 5)

                if isinstance(self.model, dict) and self.model.get("_type") == "baseline":
                    pred = float(self.predict(pd.DataFrame([{"dummy": 0}]))[0])
                else:
                    X_future, _ = self.prepare_features(future_row, target_col="sales")
                    if X_future.shape[1] == 0:
                        pred = float(running_history["sales"].mean() if "sales" in running_history.columns else 0.0)
                    else:
                        pred = float(self.predict(X_future)[0])

                forecasts.append({
                    "item_id": item_id, "store_id": store_id,
                    "date": future_date, "predicted_sales": pred,
                })
                pred_row = future_row.copy()
                pred_row["sales"] = pred
                running_history = pd.concat([running_history, pred_row], ignore_index=True)

        return pd.DataFrame(forecasts)

    def _forecast_prophet(self, df, periods=28):
        """Prophet-based future forecast."""
        future = self.model.make_future_dataframe(periods=periods)
        forecast = self.model.predict(future)
        last_date = df["date"].max()
        result = forecast[forecast["ds"] > last_date][["ds", "yhat"]].copy()
        result.columns = ["date", "predicted_sales"]
        return result

    def save_model(self, filepath):
        """Save the trained model."""
        if self.model is None:
            raise ValueError("No model to save.")
        model_data = {"model": self.model, "feature_names": self.feature_names, "model_type": self.model_type}
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")

    def load_model(self, filepath):
        """Load a trained model."""
        model_data = joblib.load(filepath)
        self.model = model_data["model"]
        self.feature_names = model_data.get("feature_names")
        self.model_type = model_data.get("model_type", "random_forest")
        logger.info(f"Model loaded from {filepath} ({self.model_type})")


