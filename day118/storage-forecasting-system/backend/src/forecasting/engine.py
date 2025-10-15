import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.exponential_smoothing.ets import ETSModel
import warnings
warnings.filterwarnings('ignore')

class ForecastingEngine:
    def __init__(self):
        self.models = {
            'linear': LinearRegression(),
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
        }
        self.model_scores = {}
        
    def prepare_features(self, df: pd.DataFrame) -> tuple:
        """Prepare time series features for forecasting"""
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp').sort_index()
        
        # Create time-based features
        df['hour'] = df.index.hour
        df['day_of_week'] = df.index.dayofweek
        df['day_of_month'] = df.index.day
        df['month'] = df.index.month
        df['quarter'] = df.index.quarter
        
        # Create lag features
        df['usage_lag_1'] = df['used_bytes'].shift(1)
        df['usage_lag_7'] = df['used_bytes'].shift(7)
        df['usage_lag_30'] = df['used_bytes'].shift(30)
        
        # Rolling statistics
        df['usage_ma_7'] = df['used_bytes'].rolling(window=7).mean()
        df['usage_ma_30'] = df['used_bytes'].rolling(window=30).mean()
        df['usage_std_7'] = df['used_bytes'].rolling(window=7).std()
        
        # Remove NaN values
        df = df.dropna()
        
        feature_columns = ['hour', 'day_of_week', 'day_of_month', 'month', 'quarter',
                          'usage_lag_1', 'usage_lag_7', 'usage_lag_30', 
                          'usage_ma_7', 'usage_ma_30', 'usage_std_7']
        
        X = df[feature_columns]
        y = df['used_bytes']
        
        return X, y, df.index
    
    def train_models(self, X, y):
        """Train multiple forecasting models"""
        # Split for validation
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        for name, model in self.models.items():
            try:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_val)
                mae = mean_absolute_error(y_val, y_pred)
                self.model_scores[name] = mae
                print(f"✅ {name} model trained - MAE: {mae:.2f}")
            except Exception as e:
                print(f"❌ Failed to train {name}: {e}")
                self.model_scores[name] = float('inf')
    
    def forecast_arima(self, series: pd.Series, periods: int) -> dict:
        """ARIMA forecasting"""
        try:
            model = ARIMA(series, order=(1, 1, 1))
            fitted_model = model.fit()
            forecast = fitted_model.forecast(steps=periods)
            conf_int = fitted_model.get_forecast(periods).conf_int()
            
            return {
                'forecast': forecast.tolist(),
                'lower_bound': conf_int.iloc[:, 0].tolist(),
                'upper_bound': conf_int.iloc[:, 1].tolist(),
                'model_name': 'ARIMA'
            }
        except:
            return None
    
    def forecast_exponential_smoothing(self, series: pd.Series, periods: int) -> dict:
        """Exponential smoothing forecasting"""
        try:
            model = ETSModel(series, trend='add', seasonal='add', seasonal_periods=7)
            fitted_model = model.fit()
            forecast = fitted_model.forecast(periods)
            
            return {
                'forecast': forecast.tolist(),
                'lower_bound': (forecast * 0.9).tolist(),
                'upper_bound': (forecast * 1.1).tolist(),
                'model_name': 'ExponentialSmoothing'
            }
        except:
            return None
    
    def generate_ensemble_forecast(self, df: pd.DataFrame, horizon_days: int) -> dict:
        """Generate ensemble forecast combining multiple models"""
        X, y, timestamps = self.prepare_features(df)
        
        if len(X) < 30:  # Need minimum data
            raise ValueError("Insufficient data for forecasting")
        
        # Train models
        self.train_models(X, y)
        
        # Get best performing model
        best_model_name = min(self.model_scores, key=self.model_scores.get)
        best_model = self.models[best_model_name]
        
        # Generate future features
        last_timestamp = timestamps[-1]
        future_dates = pd.date_range(
            start=last_timestamp + timedelta(days=1),
            periods=horizon_days,
            freq='D'
        )
        
        # Create future features (simplified)
        future_features = []
        for date in future_dates:
            features = [
                date.hour if hasattr(date, 'hour') else 12,  # default hour
                date.dayofweek,
                date.day,
                date.month,
                date.quarter,
                y.iloc[-1],  # last usage as lag_1
                y.iloc[-7:].mean(),  # last 7 days avg as lag_7
                y.iloc[-30:].mean(),  # last 30 days avg as lag_30
                y.iloc[-7:].mean(),  # ma_7
                y.iloc[-30:].mean(),  # ma_30
                y.iloc[-7:].std()  # std_7
            ]
            future_features.append(features)
        
        future_X = pd.DataFrame(future_features, columns=X.columns)
        
        # Generate predictions
        predictions = best_model.predict(future_X)
        
        # Calculate confidence intervals (simplified)
        historical_std = y.std()
        lower_bound = predictions - 1.96 * historical_std
        upper_bound = predictions + 1.96 * historical_std
        
        # Try ARIMA and Exponential Smoothing
        arima_result = self.forecast_arima(y, horizon_days)
        exp_smooth_result = self.forecast_exponential_smoothing(y, horizon_days)
        
        # Ensemble: average of available predictions
        ensemble_predictions = [predictions]
        if arima_result:
            ensemble_predictions.append(np.array(arima_result['forecast']))
        if exp_smooth_result:
            ensemble_predictions.append(np.array(exp_smooth_result['forecast']))
        
        final_forecast = np.mean(ensemble_predictions, axis=0)
        
        return {
            'forecast': final_forecast.tolist(),
            'lower_bound': lower_bound.tolist(),
            'upper_bound': upper_bound.tolist(),
            'model_accuracy': 1.0 - (self.model_scores[best_model_name] / y.mean()),
            'best_model': best_model_name,
            'dates': future_dates.strftime('%Y-%m-%d').tolist()
        }
