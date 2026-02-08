#!/usr/bin/env python3
"""
Advanced Risk Management and Backtesting Module
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')


class DividendRiskManager:
    """Advanced risk management for dividend portfolios"""

    def __init__(self):
        self.risk_metrics = {}
        self.risk_limits = {
            'max_concentration': 0.25,  # Max 25% in single stock
            'min_diversification': 8,    # Minimum 8 stocks
            'max_sector_exposure': 0.40,  # Max 40% in single sector
            'min_sustainability_score': 60,  # Minimum sustainability score
            'max_payout_ratio': 0.80    # Maximum payout ratio
        }

    def assess_portfolio_risk(self, portfolio: List[Dict]) -> Dict:
        """Comprehensive portfolio risk assessment"""

        total_value = sum(holding['allocation_amount']
                          for holding in portfolio)

        # Concentration Risk
        concentrations = [holding['allocation_percentage']
                          for holding in portfolio]
        max_concentration = max(concentrations)
        concentration_risk = "HIGH" if max_concentration > 25 else "MEDIUM" if max_concentration > 15 else "LOW"

        # Diversification Analysis
        num_holdings = len(portfolio)
        diversification_score = min(100, (num_holdings / 15) * 100)

        # Sustainability Risk
        sustainability_scores = [holding.get(
            'sustainability', 70) for holding in portfolio]
        avg_sustainability = np.mean(sustainability_scores)
        min_sustainability = min(sustainability_scores)

        sustainability_risk = "LOW" if min_sustainability > 70 else "MEDIUM" if min_sustainability > 50 else "HIGH"

        # Yield Risk (too high might be unsustainable)
        yields = [holding.get('predicted_yield', 4) for holding in portfolio]
        avg_yield = np.mean(yields)
        max_yield = max(yields)

        yield_risk = "HIGH" if max_yield > 12 else "MEDIUM" if avg_yield > 8 else "LOW"

        # Calculate VaR (Value at Risk) simulation
        var_95 = self._calculate_var(portfolio, confidence=0.95)
        var_99 = self._calculate_var(portfolio, confidence=0.99)

        # Overall risk score
        risk_factors = {
            'concentration': 40 if concentration_risk == "HIGH" else 20 if concentration_risk == "MEDIUM" else 10,
            'diversification': max(0, 40 - diversification_score/2),
            'sustainability': 30 if sustainability_risk == "HIGH" else 15 if sustainability_risk == "MEDIUM" else 5,
            'yield': 25 if yield_risk == "HIGH" else 12 if yield_risk == "MEDIUM" else 5
        }

        overall_risk_score = sum(risk_factors.values())

        if overall_risk_score > 80:
            overall_risk = "🔴 HIGH RISK"
        elif overall_risk_score > 50:
            overall_risk = "🟡 MEDIUM RISK"
        else:
            overall_risk = "🟢 LOW RISK"

        return {
            'overall_risk': overall_risk,
            'risk_score': overall_risk_score,
            'risk_breakdown': {
                'concentration_risk': concentration_risk,
                'max_concentration': f"{max_concentration:.1f}%",
                'diversification_score': f"{diversification_score:.1f}%",
                'sustainability_risk': sustainability_risk,
                'avg_sustainability': f"{avg_sustainability:.1f}%",
                'yield_risk': yield_risk,
                'avg_yield': f"{avg_yield:.2f}%"
            },
            'var_analysis': {
                'var_95': f"₹{var_95:,.0f}",
                'var_99': f"₹{var_99:,.0f}",
                'max_1day_loss_95': f"{(var_95/total_value)*100:.2f}%",
                'max_1day_loss_99': f"{(var_99/total_value)*100:.2f}%"
            },
            'recommendations': self._generate_risk_recommendations(risk_factors, portfolio)
        }

    def _calculate_var(self, portfolio: List[Dict], confidence: float = 0.95) -> float:
        """Calculate Value at Risk using Monte Carlo simulation"""

        # Simulate price movements for each stock
        num_simulations = 10000
        portfolio_values = []

        total_investment = sum(holding['allocation_amount']
                               for holding in portfolio)

        for _ in range(num_simulations):
            daily_return = 0

            for holding in portfolio:
                # Estimate volatility based on yield and risk profile
                base_volatility = 0.02  # 2% base daily volatility

                # Adjust volatility based on yield (higher yield = higher volatility)
                yield_factor = holding.get('predicted_yield', 4) / 100
                volatility = base_volatility * (1 + yield_factor)

                # Adjust for sustainability (lower sustainability = higher volatility)
                sustainability_factor = holding.get('sustainability', 70) / 100
                volatility = volatility * (1.5 - sustainability_factor * 0.5)

                # Generate random return
                weight = holding['allocation_percentage'] / 100
                stock_return = np.random.normal(0, volatility)
                daily_return += weight * stock_return

            portfolio_value = total_investment * (1 + daily_return)
            portfolio_values.append(portfolio_value)

        # Calculate VaR
        portfolio_values.sort()
        var_index = int((1 - confidence) * num_simulations)
        var_value = total_investment - portfolio_values[var_index]

        return max(0, var_value)

    def _generate_risk_recommendations(self, risk_factors: Dict, portfolio: List[Dict]) -> List[str]:
        """Generate specific risk management recommendations"""
        recommendations = []

        if risk_factors['concentration'] > 30:
            max_holding = max(
                portfolio, key=lambda x: x['allocation_percentage'])
            recommendations.append(
                f"🚨 Reduce concentration in {max_holding['symbol']} ({max_holding['allocation_percentage']:.1f}%)"
            )

        if risk_factors['diversification'] > 20:
            recommendations.append(
                f"📈 Add more holdings - currently {len(portfolio)} stocks (target: 10-15)"
            )

        if risk_factors['sustainability'] > 20:
            low_sustainability = [
                h for h in portfolio if h.get('sustainability', 70) < 60]
            for holding in low_sustainability[:2]:  # Show top 2
                recommendations.append(
                    f"⚠️ Review {holding['symbol']} - low sustainability ({holding.get('sustainability', 0):.1f}%)"
                )

        if risk_factors['yield'] > 20:
            high_yield = [h for h in portfolio if h.get(
                'predicted_yield', 4) > 10]
            for holding in high_yield[:2]:
                recommendations.append(
                    f"🔍 Investigate {holding['symbol']} - very high yield ({holding.get('predicted_yield', 0):.1f}%)"
                )

        if not recommendations:
            recommendations.append("✅ Portfolio risk profile is well-balanced")

        return recommendations


class DividendBacktester:
    """Backtest dividend strategies"""

    def __init__(self):
        self.historical_data = None
        self.results = {}

    def generate_historical_data(self, symbols: List[str], years: int = 5) -> pd.DataFrame:
        """Generate synthetic historical dividend data"""

        # Create date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)

        date_range = pd.date_range(start=start_date, end=end_date, freq='D')

        historical_data = []

        for symbol in symbols:
            # Set base characteristics for each stock
            base_price = np.random.uniform(500, 3000)
            base_yield = np.random.uniform(0.02, 0.08)
            volatility = np.random.uniform(0.15, 0.35)

            price = base_price
            annual_dividend = base_price * base_yield

            for date in date_range:
                # Simulate price movement
                daily_return = np.random.normal(
                    0.0008, volatility/252**0.5)  # Annualized
                price *= (1 + daily_return)

                # Add market trends
                if date.month in [3, 6, 9, 12]:  # Quarterly results season
                    price *= np.random.uniform(0.98, 1.05)

                # Calculate current yield
                current_yield = annual_dividend / price

                # Simulate dividend announcements (quarterly)
                dividend_amount = 0
                if date.day == 15 and date.month in [3, 6, 9, 12]:
                    quarterly_dividend = annual_dividend / 4
                    dividend_amount = quarterly_dividend
                    # Slight growth in dividends over time
                    annual_dividend *= np.random.uniform(1.02, 1.08)

                historical_data.append({
                    'date': date,
                    'symbol': symbol,
                    'price': price,
                    'dividend_yield': current_yield,
                    'dividend_amount': dividend_amount,
                    'annual_dividend': annual_dividend
                })

        df = pd.DataFrame(historical_data)
        df['date'] = pd.to_datetime(df['date'])
        return df.sort_values(['symbol', 'date'])

    def backtest_strategy(self, strategy_config: Dict, initial_capital: float = 100000) -> Dict:
        """Backtest a dividend strategy"""

        symbols = strategy_config.get(
            'symbols', ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ITC'])
        min_yield = strategy_config.get('min_yield', 0.03)
        rebalance_frequency = strategy_config.get('rebalance_months', 6)

        # Generate historical data
        self.historical_data = self.generate_historical_data(symbols, years=3)

        # Initialize portfolio
        portfolio = {}
        cash = initial_capital
        total_dividends = 0
        transactions = []

        # Get rebalancing dates
        start_date = self.historical_data['date'].min()
        end_date = self.historical_data['date'].max()

        rebalance_dates = pd.date_range(
            start=start_date,
            end=end_date,
            freq=f'{rebalance_frequency}M'
        )

        portfolio_values = []

        for rebalance_date in rebalance_dates:

            # Get current market data
            current_data = self.historical_data[
                self.historical_data['date'] <= rebalance_date
            ].groupby('symbol').last().reset_index()

            # Filter stocks by yield criteria
            qualified_stocks = current_data[
                current_data['dividend_yield'] >= min_yield
            ].copy()

            if len(qualified_stocks) == 0:
                continue

            # Calculate total portfolio value
            portfolio_value = cash
            for symbol, shares in portfolio.items():
                if symbol in qualified_stocks['symbol'].values:
                    current_price = qualified_stocks[
                        qualified_stocks['symbol'] == symbol
                    ]['price'].iloc[0]
                    portfolio_value += shares * current_price

            # Rebalance: equal weight allocation
            target_allocation = portfolio_value / len(qualified_stocks)

            # Sell current holdings
            for symbol, shares in portfolio.items():
                if symbol in qualified_stocks['symbol'].values:
                    current_price = qualified_stocks[
                        qualified_stocks['symbol'] == symbol
                    ]['price'].iloc[0]
                    cash += shares * current_price
                    transactions.append({
                        'date': rebalance_date,
                        'symbol': symbol,
                        'action': 'SELL',
                        'shares': shares,
                        'price': current_price
                    })

            portfolio = {}

            # Buy new holdings
            for _, stock in qualified_stocks.iterrows():
                shares_to_buy = int(target_allocation / stock['price'])
                cost = shares_to_buy * stock['price']

                if cost <= cash:
                    portfolio[stock['symbol']] = shares_to_buy
                    cash -= cost

                    transactions.append({
                        'date': rebalance_date,
                        'symbol': stock['symbol'],
                        'action': 'BUY',
                        'shares': shares_to_buy,
                        'price': stock['price']
                    })

            # Record portfolio value
            current_portfolio_value = cash
            for symbol, shares in portfolio.items():
                if symbol in qualified_stocks['symbol'].values:
                    current_price = qualified_stocks[
                        qualified_stocks['symbol'] == symbol
                    ]['price'].iloc[0]
                    current_portfolio_value += shares * current_price

            portfolio_values.append({
                'date': rebalance_date,
                'portfolio_value': current_portfolio_value,
                'cash': cash,
                'invested': current_portfolio_value - cash
            })

        # Calculate dividends received
        for _, transaction in enumerate(transactions):
            if transaction['action'] == 'BUY':
                symbol = transaction['symbol']
                shares = transaction['shares']
                buy_date = transaction['date']

                # Find dividends after purchase
                dividend_data = self.historical_data[
                    (self.historical_data['symbol'] == symbol) &
                    (self.historical_data['date'] > buy_date) &
                    (self.historical_data['dividend_amount'] > 0)
                ]

                for _, dividend_row in dividend_data.iterrows():
                    total_dividends += shares * dividend_row['dividend_amount']

        # Calculate performance metrics
        if portfolio_values:
            final_value = portfolio_values[-1]['portfolio_value']
            total_return = (final_value + total_dividends -
                            initial_capital) / initial_capital
            annualized_return = (1 + total_return) ** (1/3) - 1  # 3 years

            # Calculate Sharpe ratio (simplified)
            portfolio_df = pd.DataFrame(portfolio_values)
            portfolio_df['returns'] = portfolio_df['portfolio_value'].pct_change()
            sharpe_ratio = portfolio_df['returns'].mean(
            ) / portfolio_df['returns'].std() * np.sqrt(252)

            # Max drawdown
            running_max = portfolio_df['portfolio_value'].cummax()
            drawdown = (portfolio_df['portfolio_value'] -
                        running_max) / running_max
            max_drawdown = drawdown.min()

            return {
                'success': True,
                'initial_capital': initial_capital,
                'final_portfolio_value': final_value,
                'total_dividends_received': total_dividends,
                'total_return_amount': final_value + total_dividends - initial_capital,
                'total_return_percentage': total_return * 100,
                'annualized_return': annualized_return * 100,
                'dividend_yield_on_investment': (total_dividends / initial_capital) * 100,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown * 100,
                'number_of_transactions': len(transactions),
                'rebalancing_frequency': f"Every {rebalance_frequency} months",
                'strategy_config': strategy_config,
                'portfolio_evolution': portfolio_values,
                'transactions': transactions[-10:],  # Last 10 transactions
                'backtest_period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            }

        else:
            return {'success': False, 'error': 'No valid rebalancing periods found'}


def demo_risk_management():
    """Demo risk management and backtesting features"""
    print("⚠️ Advanced Risk Management & Backtesting")
    print("=" * 50)

    # Sample portfolio for risk analysis
    sample_portfolio = [
        {'symbol': 'RELIANCE', 'allocation_amount': 150000, 'allocation_percentage': 30,
         'predicted_yield': 5.2, 'sustainability': 75},
        {'symbol': 'TCS', 'allocation_amount': 100000, 'allocation_percentage': 20,
         'predicted_yield': 3.8, 'sustainability': 85},
        {'symbol': 'HDFCBANK', 'allocation_amount': 80000, 'allocation_percentage': 16,
         'predicted_yield': 2.1, 'sustainability': 80},
        {'symbol': 'ITC', 'allocation_amount': 70000, 'allocation_percentage': 14,
         'predicted_yield': 6.8, 'sustainability': 65},
        {'symbol': 'COALINDIA', 'allocation_amount': 60000, 'allocation_percentage': 12,
         'predicted_yield': 8.5, 'sustainability': 55},
        {'symbol': 'INFY', 'allocation_amount': 40000, 'allocation_percentage': 8,
         'predicted_yield': 4.2, 'sustainability': 90}
    ]

    # Risk Assessment
    print("\n⚠️ Portfolio Risk Assessment")
    print("-" * 30)

    risk_manager = DividendRiskManager()
    risk_analysis = risk_manager.assess_portfolio_risk(sample_portfolio)

    print(f"Overall Risk Level: {risk_analysis['overall_risk']}")
    print(f"Risk Score: {risk_analysis['risk_score']}/100")

    print("\n📊 Risk Breakdown:")
    breakdown = risk_analysis['risk_breakdown']
    for risk_type, value in breakdown.items():
        print(f"• {risk_type.replace('_', ' ').title()}: {value}")

    print("\n💰 Value at Risk Analysis:")
    var = risk_analysis['var_analysis']
    for metric, value in var.items():
        print(f"• {metric.replace('_', ' ').title()}: {value}")

    print(f"\n💡 Risk Management Recommendations:")
    for rec in risk_analysis['recommendations']:
        print(f"  {rec}")

    # Backtesting
    print("\n📈 Strategy Backtesting")
    print("-" * 30)

    backtester = DividendBacktester()

    # Test high-yield strategy
    strategy_config = {
        'name': 'High Yield Strategy',
        'symbols': ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ITC', 'COALINDIA'],
        'min_yield': 0.04,  # 4% minimum yield
        'rebalance_months': 6  # Rebalance every 6 months
    }

    print(f"Testing Strategy: {strategy_config['name']}")
    print("Configuration:")
    print(f"• Minimum Yield: {strategy_config['min_yield']*100}%")
    print(f"• Rebalancing: Every {strategy_config['rebalance_months']} months")
    print(f"• Universe: {len(strategy_config['symbols'])} stocks")

    backtest_results = backtester.backtest_strategy(
        strategy_config, initial_capital=500000)

    if backtest_results['success']:
        print(f"\n📊 Backtest Results ({backtest_results['backtest_period']}):")
        print(f"• Initial Capital: ₹{backtest_results['initial_capital']:,}")
        print(
            f"• Final Portfolio Value: ₹{backtest_results['final_portfolio_value']:,.0f}")
        print(
            f"• Total Dividends: ₹{backtest_results['total_dividends_received']:,.0f}")
        print(
            f"• Total Return: {backtest_results['total_return_percentage']:.2f}%")
        print(
            f"• Annualized Return: {backtest_results['annualized_return']:.2f}%")
        print(
            f"• Dividend Yield on Investment: {backtest_results['dividend_yield_on_investment']:.2f}%")
        print(f"• Sharpe Ratio: {backtest_results['sharpe_ratio']:.2f}")
        print(f"• Max Drawdown: {backtest_results['max_drawdown']:.2f}%")
        print(
            f"• Number of Transactions: {backtest_results['number_of_transactions']}")

        # Show recent transactions
        print(f"\n🔄 Recent Transactions:")
        for transaction in backtest_results['transactions'][-5:]:
            print(f"• {transaction['date'].strftime('%Y-%m-%d')}: {transaction['action']} "
                  f"{transaction['shares']} shares of {transaction['symbol']} at ₹{transaction['price']:.0f}")

    else:
        print(f"❌ Backtest failed: {backtest_results['error']}")

    print("\n" + "=" * 50)
    print("✅ Risk management and backtesting demo completed!")
    print("\n🎯 Advanced Features Added:")
    print("• Comprehensive portfolio risk assessment")
    print("• Value at Risk (VaR) calculations")
    print("• Monte Carlo risk simulations")
    print("• Strategy backtesting with rebalancing")
    print("• Performance metrics (Sharpe, drawdown)")
    print("• Risk-adjusted recommendations")


if __name__ == "__main__":
    demo_risk_management()
