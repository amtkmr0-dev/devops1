#!/usr/bin/env python3
"""
Simple test script to verify the dividend scanner setup
"""


def test_basic_imports():
    """Test basic imports"""
    try:
        print("Testing basic imports...")

        # Test data providers
        from src.data import YFinanceProvider, DataPipeline
        print("✓ Data providers imported successfully")

        # Test scanner
        from src.scanner import DividendScanner, PreDefinedScans
        print("✓ Scanner components imported successfully")

        # Test config
        from src.config import settings
        print("✓ Configuration imported successfully")

        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False


def test_data_pipeline():
    """Test data pipeline functionality"""
    try:
        print("\nTesting data pipeline...")

        from src.data import YFinanceProvider, DataPipeline

        # Create providers
        provider = YFinanceProvider()
        pipeline = DataPipeline([provider])

        # Test with a simple stock
        test_symbol = "AAPL"
        print(f"Testing data fetch for {test_symbol}...")

        stock_data = pipeline.get_stock_data(test_symbol)

        if stock_data:
            print(f"✓ Successfully fetched data for {test_symbol}")
            print(f"  Name: {stock_data.get('name', 'N/A')}")
            print(f"  Sector: {stock_data.get('sector', 'N/A')}")
            print(
                f"  Dividend Yield: {stock_data.get('dividend_yield', 'N/A')}")
        else:
            print(f"✗ No data returned for {test_symbol}")
            return False

        return True
    except Exception as e:
        print(f"✗ Data pipeline error: {e}")
        return False


def test_scanner():
    """Test scanner functionality"""
    try:
        print("\nTesting scanner...")

        from src.data import YFinanceProvider, DataPipeline
        from src.scanner import DividendScanner, PreDefinedScans

        # Create scanner
        provider = YFinanceProvider()
        pipeline = DataPipeline([provider])
        scanner = DividendScanner(pipeline)

        # Test with a small sample
        test_symbols = ["AAPL", "MSFT"]
        config = PreDefinedScans.high_yield_scanner()
        config.limit = 5  # Limit results for testing

        print(f"Testing scan with symbols: {test_symbols}")

        results = scanner.scan_stocks(test_symbols, config)

        print(f"✓ Scanner completed successfully")
        print(f"  Results found: {len(results)}")

        if not results.empty:
            print("  Sample result:")
            first_result = results.iloc[0]
            print(f"    Symbol: {first_result.get('symbol', 'N/A')}")
            print(
                f"    Health Score: {first_result.get('dividend_health_score', 'N/A')}")

        return True
    except Exception as e:
        print(f"✗ Scanner error: {e}")
        return False


def main():
    """Run all tests"""
    print("=== Dividend Scanner Test Suite ===\n")

    tests = [
        test_basic_imports,
        test_data_pipeline,
        test_scanner
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=== Test Results ===")
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All tests passed! The dividend scanner is ready to use.")
        print("\nNext steps:")
        print("1. Run a quick scan: python main.py --scan high_yield")
        print("2. Start the dashboard: streamlit run dashboard.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nCommon issues:")
        print("- Missing dependencies: pip install -r requirements.txt")
        print("- Network issues: Check internet connection")
        print("- API rate limits: Try again in a few minutes")


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Add src to path
    sys.path.append(str(Path(__file__).parent / "src"))

    main()
