#!/usr/bin/env python3
"""
Demo script for dividend scanner with sample data
"""

from src.scanner import DividendScanner, PreDefinedScans, ScanConfiguration, ScanFilter, ScanCriteria
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))


class MockDataProvider:
    """Mock data provider for demo purposes"""

    def __init__(self):
        # Sample data for demonstration
        self.stock_data = {
            'AAPL': {
                'symbol': 'AAPL',
                'name': 'Apple Inc.',
                'sector': 'Technology',
                'market_cap': 3000000000000,  # 3T
                'current_price': 185.0,
                'dividend_yield': 0.0043,  # 0.43%
                'payout_ratio': 0.15,
                'pe_ratio': 28.5,
                'debt_to_equity': 0.31,
                'return_on_equity': 0.56,
                'profit_margin': 0.25,
                'earnings_per_share': 6.50
            },
            'JNJ': {
                'symbol': 'JNJ',
                'name': 'Johnson & Johnson',
                'sector': 'Healthcare',
                'market_cap': 450000000000,  # 450B
                'current_price': 175.0,
                'dividend_yield': 0.0290,  # 2.9%
                'payout_ratio': 0.47,
                'pe_ratio': 15.8,
                'debt_to_equity': 0.47,
                'return_on_equity': 0.25,
                'profit_margin': 0.20,
                'earnings_per_share': 11.05
            },
            'KO': {
                'symbol': 'KO',
                'name': 'The Coca-Cola Company',
                'sector': 'Consumer Staples',
                'market_cap': 260000000000,  # 260B
                'current_price': 60.5,
                'dividend_yield': 0.0315,  # 3.15%
                'payout_ratio': 0.75,
                'pe_ratio': 24.2,
                'debt_to_equity': 1.45,
                'return_on_equity': 0.42,
                'profit_margin': 0.23,
                'earnings_per_share': 2.48
            },
            'T': {
                'symbol': 'T',
                'name': 'AT&T Inc.',
                'sector': 'Telecommunications',
                'market_cap': 130000000000,  # 130B
                'current_price': 18.0,
                'dividend_yield': 0.0611,  # 6.11%
                'payout_ratio': 0.85,
                'pe_ratio': 12.1,
                'debt_to_equity': 1.18,
                'return_on_equity': 0.12,
                'profit_margin': 0.08,
                'earnings_per_share': 1.49
            },
            'REALTY': {
                'symbol': 'REALTY',
                'name': 'Realty Income Corporation',
                'sector': 'Real Estate',
                'market_cap': 45000000000,  # 45B
                'current_price': 55.0,
                'dividend_yield': 0.0520,  # 5.20%
                'payout_ratio': 0.83,
                'pe_ratio': 55.0,
                'debt_to_equity': 0.35,
                'return_on_equity': 0.04,
                'profit_margin': 0.25,
                'earnings_per_share': 1.00
            }
        }

    def get_stock_data(self, symbol, use_cache=True):
        return self.stock_data.get(symbol, {})

    def get_dividend_history(self, symbol, use_cache=True):
        # Generate sample dividend history
        if symbol not in self.stock_data:
            return pd.DataFrame()

        stock = self.stock_data[symbol]
        current_yield = stock['dividend_yield']
        current_price = stock['current_price']
        annual_dividend = current_price * current_yield
        quarterly_dividend = annual_dividend / 4

        # Generate 3 years of quarterly dividends
        dates = []
        amounts = []
        base_date = datetime.now() - timedelta(days=3*365)

        for i in range(12):  # 12 quarters
            ex_date = base_date + timedelta(days=i*90)
            # Add some growth
            growth_factor = 1 + (i * 0.02)  # 2% growth per quarter
            amount = quarterly_dividend * growth_factor

            dates.append(ex_date)
            amounts.append(amount)

        df = pd.DataFrame({
            'symbol': symbol,
            'ex_dividend_date': dates,
            'dividend_amount': amounts,
            'dividend_type': 'regular'
        })

        # Calculate growth rates
        df = df.sort_values('ex_dividend_date')
        df['dividend_growth_rate'] = df['dividend_amount'].pct_change() * 100

        return df

    def get_financial_metrics(self, symbol, use_cache=True):
        stock_data = self.stock_data.get(symbol, {})
        return {
            'pe_ratio': stock_data.get('pe_ratio'),
            'debt_to_equity': stock_data.get('debt_to_equity'),
            'return_on_equity': stock_data.get('return_on_equity'),
            'profit_margin': stock_data.get('profit_margin'),
            'earnings_per_share': stock_data.get('earnings_per_share'),
            'dividend_coverage_ratio': 1 / stock_data.get('payout_ratio', 1) if stock_data.get('payout_ratio') else None
        }


def demo_basic_scan():
    """Demo basic dividend scanning"""
    print("=== Basic Dividend Scan Demo ===\n")

    # Create mock data pipeline
    mock_provider = MockDataProvider()
    scanner = DividendScanner(mock_provider)

    # Sample symbols
    symbols = ['AAPL', 'JNJ', 'KO', 'T', 'REALTY']

    print(f"Scanning symbols: {', '.join(symbols)}")
    print()

    # Run high yield scan
    config = PreDefinedScans.high_yield_scanner()
    results = scanner.scan_stocks(symbols, config)

    print("High Yield Scan Results:")
    print("=" * 50)

    if not results.empty:
        # Format and display results
        display_cols = ['symbol', 'name', 'sector',
                        'dividend_yield', 'dividend_health_score', 'payout_ratio']
        available_cols = [
            col for col in display_cols if col in results.columns]

        formatted_results = results[available_cols].copy()

        # Format percentages
        if 'dividend_yield' in formatted_results.columns:
            formatted_results['dividend_yield'] = formatted_results['dividend_yield'].apply(
                lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A")

        if 'payout_ratio' in formatted_results.columns:
            formatted_results['payout_ratio'] = formatted_results['payout_ratio'].apply(
                lambda x: f"{x*100:.1f}%" if pd.notna(x) else "N/A")

        if 'dividend_health_score' in formatted_results.columns:
            formatted_results['dividend_health_score'] = formatted_results['dividend_health_score'].apply(
                lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")

        print(formatted_results.to_string(index=False))
        print(f"\nFound {len(results)} stocks matching high yield criteria")
    else:
        print("No stocks found matching the criteria")


def demo_custom_scan():
    """Demo custom scanning criteria"""
    print("\n\n=== Custom Scan Demo ===\n")

    # Create mock data pipeline
    mock_provider = MockDataProvider()
    scanner = DividendScanner(mock_provider)

    # Custom scan: Conservative dividend stocks
    custom_config = ScanConfiguration(
        name="Conservative Dividend Stocks",
        filters=[
            ScanFilter(ScanCriteria.MIN_DIVIDEND_YIELD, 0.02, "gte"),  # >= 2%
            ScanFilter(ScanCriteria.MAX_DIVIDEND_YIELD, 0.05, "lte"),  # <= 5%
            ScanFilter(ScanCriteria.MAX_PAYOUT_RATIO, 0.8, "lte"),     # <= 80%
            ScanFilter(ScanCriteria.MIN_DIVIDEND_COVERAGE,
                       1.25, "gte")  # >= 1.25x coverage
        ],
        sort_by="dividend_health_score",
        sort_order="desc"
    )

    symbols = ['AAPL', 'JNJ', 'KO', 'T', 'REALTY']
    print(f"Running custom scan on: {', '.join(symbols)}")
    print(f"Criteria: Yield 2-5%, Payout ≤80%, Coverage ≥1.25x")
    print()

    results = scanner.scan_stocks(symbols, custom_config)

    if not results.empty:
        print("Custom Scan Results:")
        print("=" * 50)

        for _, stock in results.iterrows():
            print(f"📊 {stock['symbol']} - {stock['name']}")
            print(f"   Sector: {stock.get('sector', 'N/A')}")
            print(
                f"   Dividend Yield: {stock.get('dividend_yield', 0)*100:.2f}%")
            print(
                f"   Health Score: {stock.get('dividend_health_score', 0):.1f}/100")
            print(f"   Payout Ratio: {stock.get('payout_ratio', 0)*100:.1f}%")
            print()
    else:
        print("No stocks found matching custom criteria")


def demo_health_scores():
    """Demo health score analysis"""
    print("\n=== Dividend Health Score Analysis ===\n")

    mock_provider = MockDataProvider()
    scanner = DividendScanner(mock_provider)

    # Simple scan to get all stocks with health scores
    config = ScanConfiguration(
        name="All Stocks Analysis",
        filters=[
            ScanFilter(ScanCriteria.MIN_DIVIDEND_YIELD,
                       0.001, "gte")  # Very low threshold
        ],
        sort_by="dividend_health_score",
        sort_order="desc"
    )

    symbols = ['AAPL', 'JNJ', 'KO', 'T', 'REALTY']
    results = scanner.scan_stocks(symbols, config)

    if not results.empty:
        print("Health Score Breakdown:")
        print("=" * 50)
        print("Score Components: Yield(20) + Payout(25) + Growth(20) + Financial(20) + Coverage(15)")
        print()

        for _, stock in results.iterrows():
            symbol = stock['symbol']
            score = stock.get('dividend_health_score', 0)

            print(f"🏆 {symbol} - Health Score: {score:.1f}/100")

            # Get individual data points
            stock_data = mock_provider.get_stock_data(symbol)
            financial_data = mock_provider.get_financial_metrics(symbol)

            yield_val = stock_data.get('dividend_yield', 0) * 100
            payout = stock_data.get('payout_ratio', 0) * 100
            coverage = financial_data.get('dividend_coverage_ratio', 0)

            print(f"   • Dividend Yield: {yield_val:.2f}%")
            print(f"   • Payout Ratio: {payout:.1f}%")
            print(f"   • Coverage Ratio: {coverage:.2f}x")
            print(f"   • P/E Ratio: {financial_data.get('pe_ratio', 'N/A')}")
            print(
                f"   • ROE: {financial_data.get('return_on_equity', 0)*100:.1f}%")
            print()


def demo_predefined_scans():
    """Demo all predefined scan types"""
    print("\n=== Predefined Scan Types Demo ===\n")

    mock_provider = MockDataProvider()
    scanner = DividendScanner(mock_provider)
    symbols = ['AAPL', 'JNJ', 'KO', 'T', 'REALTY']

    scan_configs = [
        ("High Yield", PreDefinedScans.high_yield_scanner()),
        ("Safe Dividends", PreDefinedScans.safe_dividend_stocks()),
        ("Growth Dividends", PreDefinedScans.growth_dividend_stocks())
    ]

    for scan_name, config in scan_configs:
        print(f"🔍 {scan_name} Scan")
        print("-" * 30)

        results = scanner.scan_stocks(symbols, config)

        if not results.empty:
            print(f"Found {len(results)} stocks:")
            for _, stock in results.iterrows():
                health_score = stock.get('dividend_health_score', 0)
                yield_pct = stock.get('dividend_yield', 0) * 100
                print(
                    f"  • {stock['symbol']}: {health_score:.1f} score, {yield_pct:.2f}% yield")
        else:
            print("  No stocks found matching criteria")
        print()


def main():
    """Run all demos"""
    print("🎯 Dividend Scanner - Demo Mode")
    print("=" * 50)
    print("This demo uses sample data to showcase scanner functionality")
    print("In production, real market data would be fetched from APIs")
    print()

    try:
        demo_basic_scan()
        demo_custom_scan()
        demo_health_scores()
        demo_predefined_scans()

        print("\n" + "=" * 50)
        print("✅ Demo completed successfully!")
        print("\nNext Steps:")
        print("1. Configure real API keys in .env file")
        print("2. Run with real data: python main.py --scan high_yield")
        print("3. Start web dashboard: streamlit run dashboard.py")
        print("4. Create custom scans for your investment strategy")

    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
