#!/usr/bin/env python3
"""
Machine Learning Enhanced Dividend Predictor
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import sqlite3

warnings.filterwarnings('ignore')


class MLDividendPredictor:
    """Machine Learning-based dividend prediction system"""

    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_columns = [
            'pe_ratio', 'debt_to_equity', 'return_on_equity', 'dividend_yield',
            'payout_ratio', 'revenue_growth', 'earnings_growth', 'free_cash_flow',
            'current_ratio', 'quick_ratio', 'asset_turnover', 'market_cap_log'
        ]
        self.models_trained = False

    def generate_synthetic_data(self, n_samples: int = 1000) -> pd.DataFrame:
        """Generate synthetic financial data for training"""
        np.random.seed(42)

        data = []

        for _ in range(n_samples):
            # Generate realistic financial metrics
            pe_ratio = np.random.normal(20, 8)
            debt_to_equity = np.random.exponential(0.5)
            roe = np.random.normal(0.15, 0.08)
            payout_ratio = np.random.beta(2, 3)  # Skewed towards lower values
            revenue_growth = np.random.normal(0.08, 0.15)
            earnings_growth = np.random.normal(0.10, 0.20)
            free_cash_flow = np.random.normal(1000, 500)
            current_ratio = np.random.normal(1.5, 0.5)
            quick_ratio = np.random.normal(1.2, 0.4)
            asset_turnover = np.random.normal(0.8, 0.3)
            market_cap = np.random.lognormal(
                15, 2)  # Log-normal for market cap

            # Calculate derived features
            dividend_yield = payout_ratio * roe * \
                (1 + np.random.normal(0, 0.1))
            market_cap_log = np.log(market_cap)

            # Calculate target variables (future dividend metrics)
            # Dividend growth based on earnings growth and financial health
            financial_health_score = (
                (1 / max(pe_ratio, 1)) * 0.2 +
                (1 / max(debt_to_equity + 1, 1)) * 0.2 +
                max(roe, 0) * 0.3 +
                (1 - min(payout_ratio, 1)) * 0.2 +
                max(earnings_growth, -0.5) * 0.1
            )

            dividend_growth = earnings_growth * \
                financial_health_score + np.random.normal(0, 0.05)
            next_dividend_yield = dividend_yield * (1 + dividend_growth)
            dividend_sustainability = min(
                1.0, financial_health_score + np.random.normal(0, 0.1))

            data.append({
                'pe_ratio': max(pe_ratio, 1),
                'debt_to_equity': max(debt_to_equity, 0),
                'return_on_equity': roe,
                'dividend_yield': max(dividend_yield, 0),
                'payout_ratio': np.clip(payout_ratio, 0, 1),
                'revenue_growth': revenue_growth,
                'earnings_growth': earnings_growth,
                'free_cash_flow': free_cash_flow,
                'current_ratio': max(current_ratio, 0.1),
                'quick_ratio': max(quick_ratio, 0.1),
                'asset_turnover': max(asset_turnover, 0.1),
                'market_cap_log': market_cap_log,

                # Targets
                'next_dividend_yield': max(next_dividend_yield, 0),
                'dividend_growth': dividend_growth,
                'dividend_sustainability': np.clip(dividend_sustainability, 0, 1)
            })

        return pd.DataFrame(data)

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and engineer features"""
        df = df.copy()

        # Handle missing values
        df = df.fillna(df.median())

        # Engineer additional features
        df['debt_to_equity_safe'] = np.log1p(df['debt_to_equity'])
        df['pe_ratio_inverse'] = 1 / np.maximum(df['pe_ratio'], 1)
        df['roe_positive'] = np.maximum(df['return_on_equity'], 0)
        df['growth_stability'] = df['earnings_growth'] / \
            (df['earnings_growth'].std() + 1e-8)
        df['liquidity_score'] = (df['current_ratio'] + df['quick_ratio']) / 2
        df['efficiency_score'] = df['asset_turnover'] * df['roe_positive']

        # Financial health composite score
        df['financial_health'] = (
            df['pe_ratio_inverse'] * 0.15 +
            (1 / (df['debt_to_equity_safe'] + 1)) * 0.15 +
            df['roe_positive'] * 0.25 +
            (1 - df['payout_ratio']) * 0.15 +
            np.maximum(df['earnings_growth'], 0) * 0.15 +
            df['liquidity_score'] * 0.10 +
            df['efficiency_score'] * 0.05
        )

        return df

    def train_models(self) -> Dict[str, float]:
        """Train ML models for dividend prediction"""
        print("🤖 Training ML models for dividend prediction...")

        # Generate training data
        df = self.generate_synthetic_data(2000)
        df = self.prepare_features(df)

        # Prepare features
        X = df[self.feature_columns + ['financial_health']].fillna(0)

        # Train models for different targets
        targets = ['next_dividend_yield',
                   'dividend_growth', 'dividend_sustainability']
        results = {}

        for target in targets:
            print(f"Training model for: {target}")

            y = df[target]

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # Train ensemble model
            rf_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )

            gb_model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )

            # Train models
            rf_model.fit(X_train_scaled, y_train)
            gb_model.fit(X_train_scaled, y_train)

            # Evaluate
            rf_pred = rf_model.predict(X_test_scaled)
            gb_pred = gb_model.predict(X_test_scaled)

            # Ensemble prediction
            ensemble_pred = (rf_pred + gb_pred) / 2

            # Calculate metrics
            mae = mean_absolute_error(y_test, ensemble_pred)
            r2 = r2_score(y_test, ensemble_pred)

            results[target] = {'MAE': mae, 'R2': r2}

            # Store models
            self.models[target] = {
                'rf': rf_model,
                'gb': gb_model
            }
            self.scalers[target] = scaler

            print(f"✅ {target}: MAE={mae:.4f}, R²={r2:.4f}")

        self.models_trained = True

        # Save models
        self.save_models()

        return results

    def predict_dividend_metrics(self, stock_data: Dict) -> Dict:
        """Predict dividend metrics for a stock"""
        if not self.models_trained:
            print("🔄 Models not trained, training now...")
            self.train_models()

        try:
            # Prepare input features
            features = {
                'pe_ratio': stock_data.get('pe_ratio', 20),
                'debt_to_equity': stock_data.get('debt_to_equity', 0.5),
                'return_on_equity': stock_data.get('return_on_equity', 0.15),
                'dividend_yield': stock_data.get('dividend_yield', 0.03),
                'payout_ratio': stock_data.get('payout_ratio', 0.4),
                'revenue_growth': stock_data.get('revenue_growth', 0.08),
                'earnings_growth': stock_data.get('earnings_growth', 0.10),
                'free_cash_flow': stock_data.get('free_cash_flow', 1000),
                'current_ratio': stock_data.get('current_ratio', 1.5),
                'quick_ratio': stock_data.get('quick_ratio', 1.2),
                'asset_turnover': stock_data.get('asset_turnover', 0.8),
                'market_cap_log': np.log(stock_data.get('market_cap', 1e9))
            }

            # Create DataFrame
            df = pd.DataFrame([features])
            df = self.prepare_features(df)

            # Extract features
            X = df[self.feature_columns + ['financial_health']].fillna(0)

            predictions = {}

            for target in ['next_dividend_yield', 'dividend_growth', 'dividend_sustainability']:
                # Scale features
                X_scaled = self.scalers[target].transform(X)

                # Make predictions
                rf_pred = self.models[target]['rf'].predict(X_scaled)[0]
                gb_pred = self.models[target]['gb'].predict(X_scaled)[0]

                # Ensemble prediction
                ensemble_pred = (rf_pred + gb_pred) / 2

                predictions[target] = float(ensemble_pred)

            # Calculate additional insights
            current_yield = features['dividend_yield']
            predicted_yield = predictions['next_dividend_yield']

            yield_change = predicted_yield - current_yield
            yield_change_pct = (yield_change / current_yield) * \
                100 if current_yield > 0 else 0

            # Risk assessment
            sustainability = predictions['dividend_sustainability']

            if sustainability > 0.8:
                risk_level = "Low"
                risk_color = "🟢"
            elif sustainability > 0.6:
                risk_level = "Medium"
                risk_color = "🟡"
            else:
                risk_level = "High"
                risk_color = "🔴"

            return {
                'symbol': stock_data.get('symbol', 'UNKNOWN'),
                'current_dividend_yield': current_yield * 100,
                'predicted_dividend_yield': predicted_yield * 100,
                'yield_change': yield_change * 100,
                'yield_change_percentage': yield_change_pct,
                'dividend_growth_rate': predictions['dividend_growth'] * 100,
                'sustainability_score': sustainability * 100,
                'risk_level': f"{risk_color} {risk_level}",
                # Cap at 95%
                'prediction_confidence': min(sustainability * 100, 95),
                'recommendation': self._get_ml_recommendation(predictions),
                'analysis_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': f"Prediction failed: {str(e)}",
                'symbol': stock_data.get('symbol', 'UNKNOWN')
            }

    def _get_ml_recommendation(self, predictions: Dict) -> str:
        """Get ML-based recommendation"""
        growth = predictions['dividend_growth']
        sustainability = predictions['dividend_sustainability']

        if growth > 0.05 and sustainability > 0.8:
            return "🚀 STRONG BUY - High growth, excellent sustainability"
        elif growth > 0.02 and sustainability > 0.7:
            return "📈 BUY - Moderate growth, good sustainability"
        elif growth > 0 and sustainability > 0.6:
            return "👀 HOLD - Positive outlook with some risk"
        elif sustainability > 0.7:
            return "🛡️ INCOME - Stable dividend, low growth"
        else:
            return "⚠️ AVOID - High risk of dividend cut"

    def batch_predict(self, stocks_data: List[Dict]) -> List[Dict]:
        """Predict for multiple stocks"""
        results = []

        for stock_data in stocks_data:
            prediction = self.predict_dividend_metrics(stock_data)
            results.append(prediction)

        return results

    def save_models(self):
        """Save trained models"""
        try:
            import os
            os.makedirs('models', exist_ok=True)

            for target in self.models:
                joblib.dump(self.models[target],
                            f'models/{target}_models.joblib')
                joblib.dump(self.scalers[target],
                            f'models/{target}_scaler.joblib')

            print("✅ Models saved successfully")

        except Exception as e:
            print(f"❌ Error saving models: {e}")

    def load_models(self):
        """Load pre-trained models"""
        try:
            targets = ['next_dividend_yield',
                       'dividend_growth', 'dividend_sustainability']

            for target in targets:
                self.models[target] = joblib.load(
                    f'models/{target}_models.joblib')
                self.scalers[target] = joblib.load(
                    f'models/{target}_scaler.joblib')

            self.models_trained = True
            print("✅ Models loaded successfully")

        except Exception as e:
            print(f"⚠️ Could not load models: {e}")
            print("🔄 Will train new models when needed")


class DividendPortfolioOptimizer:
    """Optimize dividend portfolio using ML predictions"""

    def __init__(self, ml_predictor: MLDividendPredictor):
        self.ml_predictor = ml_predictor

    def optimize_portfolio(self, candidate_stocks: List[Dict],
                           investment_amount: float = 100000,
                           risk_tolerance: str = 'medium') -> Dict:
        """Optimize dividend portfolio allocation"""

        # Get ML predictions for all stocks
        predictions = self.ml_predictor.batch_predict(candidate_stocks)

        # Filter based on risk tolerance
        risk_thresholds = {
            'low': 70,      # Only high sustainability scores
            'medium': 50,   # Moderate risk acceptable
            'high': 30      # Higher risk acceptable
        }

        threshold = risk_thresholds.get(risk_tolerance, 50)
        qualified_stocks = [
            p for p in predictions
            if p.get('sustainability_score', 0) >= threshold and 'error' not in p
        ]

        if not qualified_stocks:
            return {
                'error': 'No stocks meet the risk criteria',
                'risk_tolerance': risk_tolerance
            }

        # Score each stock (combine yield, growth, and sustainability)
        for stock in qualified_stocks:
            yield_score = min(
                stock.get('predicted_dividend_yield', 0) * 2, 20)  # Cap at 10%
            growth_score = max(0, stock.get('dividend_growth_rate', 0)) * 2
            sustainability_score = stock.get('sustainability_score', 0) * 0.5

            stock['composite_score'] = yield_score + \
                growth_score + sustainability_score

        # Sort by composite score
        qualified_stocks.sort(key=lambda x: x['composite_score'], reverse=True)

        # Select top stocks (max 8 for diversification)
        selected_stocks = qualified_stocks[:8]

        # Allocate weights (higher scores get more allocation)
        total_score = sum(stock['composite_score']
                          for stock in selected_stocks)

        portfolio = []
        remaining_amount = investment_amount

        for i, stock in enumerate(selected_stocks):
            if i == len(selected_stocks) - 1:
                # Last stock gets remaining amount
                allocation = remaining_amount
            else:
                weight = stock['composite_score'] / total_score
                allocation = investment_amount * weight
                remaining_amount -= allocation

            allocation_pct = (allocation / investment_amount) * 100

            portfolio.append({
                'symbol': stock['symbol'],
                'allocation_amount': round(allocation, 2),
                'allocation_percentage': round(allocation_pct, 2),
                'predicted_yield': stock.get('predicted_dividend_yield', 0),
                'growth_rate': stock.get('dividend_growth_rate', 0),
                'sustainability': stock.get('sustainability_score', 0),
                'risk_level': stock.get('risk_level', 'Unknown'),
                'composite_score': round(stock['composite_score'], 2)
            })

        # Calculate portfolio metrics
        portfolio_yield = sum(
            (item['allocation_percentage'] / 100) * item['predicted_yield']
            for item in portfolio
        )

        portfolio_growth = sum(
            (item['allocation_percentage'] / 100) * item['growth_rate']
            for item in portfolio
        )

        avg_sustainability = sum(item['sustainability']
                                 for item in portfolio) / len(portfolio)

        return {
            'success': True,
            'total_investment': investment_amount,
            'risk_tolerance': risk_tolerance,
            'portfolio_composition': portfolio,
            'portfolio_metrics': {
                'expected_yield': round(portfolio_yield, 2),
                'expected_growth': round(portfolio_growth, 2),
                'avg_sustainability': round(avg_sustainability, 2),
                'diversification': len(portfolio),
                'annual_dividend_income': round(investment_amount * portfolio_yield / 100, 2)
            },
            'optimization_timestamp': datetime.now().isoformat()
        }


def demo_ml_features():
    """Demo ML enhanced features"""
    print("🤖 Machine Learning Enhanced Dividend Scanner")
    print("=" * 50)

    # Initialize ML predictor
    ml_predictor = MLDividendPredictor()

    # Train models
    print("\n📚 Training ML Models...")
    training_results = ml_predictor.train_models()

    print("\n🎯 Model Performance:")
    for target, metrics in training_results.items():
        print(f"• {target}: MAE={metrics['MAE']:.4f}, R²={metrics['R2']:.4f}")

    # Demo predictions
    print("\n🔮 ML Dividend Predictions")
    print("-" * 30)

    # Sample stock data
    sample_stocks = [
        {
            'symbol': 'RELIANCE',
            'pe_ratio': 25,
            'debt_to_equity': 0.3,
            'return_on_equity': 0.18,
            'dividend_yield': 0.005,
            'payout_ratio': 0.12,
            'market_cap': 1.5e12
        },
        {
            'symbol': 'TCS',
            'pe_ratio': 30,
            'debt_to_equity': 0.1,
            'return_on_equity': 0.42,
            'dividend_yield': 0.025,
            'payout_ratio': 0.35,
            'market_cap': 1.2e12
        }
    ]

    for stock_data in sample_stocks:
        prediction = ml_predictor.predict_dividend_metrics(stock_data)

        print(f"\n📊 {prediction['symbol']} ML Analysis:")
        print(f"• Current Yield: {prediction['current_dividend_yield']:.2f}%")
        print(
            f"• Predicted Yield: {prediction['predicted_dividend_yield']:.2f}%")
        print(f"• Growth Rate: {prediction['dividend_growth_rate']:.2f}%")
        print(f"• Sustainability: {prediction['sustainability_score']:.1f}%")
        print(f"• Risk Level: {prediction['risk_level']}")
        print(f"• Recommendation: {prediction['recommendation']}")

    # Demo portfolio optimization
    print("\n💼 ML Portfolio Optimization")
    print("-" * 30)

    optimizer = DividendPortfolioOptimizer(ml_predictor)

    # Add more stocks for optimization
    all_stocks = sample_stocks + [
        {'symbol': 'HDFCBANK', 'pe_ratio': 20, 'debt_to_equity': 0.8, 'return_on_equity': 0.17,
         'dividend_yield': 0.012, 'payout_ratio': 0.25, 'market_cap': 8e11},
        {'symbol': 'ITC', 'pe_ratio': 15, 'debt_to_equity': 0.1, 'return_on_equity': 0.25,
         'dividend_yield': 0.055, 'payout_ratio': 0.85, 'market_cap': 5e11},
        {'symbol': 'COALINDIA', 'pe_ratio': 12, 'debt_to_equity': 0.2, 'return_on_equity': 0.15,
         'dividend_yield': 0.065, 'payout_ratio': 0.75, 'market_cap': 1e11}
    ]

    portfolio = optimizer.optimize_portfolio(
        candidate_stocks=all_stocks,
        investment_amount=500000,
        risk_tolerance='medium'
    )

    if portfolio.get('success'):
        print(f"\n🎯 Optimized Portfolio (₹{portfolio['total_investment']:,}):")

        for holding in portfolio['portfolio_composition']:
            print(f"• {holding['symbol']}: {holding['allocation_percentage']:.1f}% "
                  f"(₹{holding['allocation_amount']:,.0f}) - {holding['risk_level']}")

        metrics = portfolio['portfolio_metrics']
        print(f"\n📈 Portfolio Metrics:")
        print(f"• Expected Yield: {metrics['expected_yield']:.2f}%")
        print(f"• Expected Growth: {metrics['expected_growth']:.2f}%")
        print(
            f"• Annual Dividend Income: ₹{metrics['annual_dividend_income']:,.0f}")
        print(f"• Avg Sustainability: {metrics['avg_sustainability']:.1f}%")
        print(f"• Diversification: {metrics['diversification']} stocks")

    print("\n" + "=" * 50)
    print("✅ ML enhanced features demo completed!")
    print("\n🎯 ML Features Added:")
    print("• Intelligent dividend yield prediction")
    print("• Growth rate forecasting")
    print("• Sustainability risk assessment")
    print("• Automated portfolio optimization")
    print("• Ensemble model predictions")


if __name__ == "__main__":
    demo_ml_features()
