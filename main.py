#!/usr/bin/env python3
"""
Dividend Scanner - Main Application
A comprehensive tool for scanning and analyzing dividend-paying stocks
"""

from src.utils.logger import setup_logging
from src.scanner import DividendScanner, PreDefinedScans
from src.data import YFinanceProvider, AlphaVantageProvider, DataPipeline, get_sp500_symbols, get_dividend_aristocrats
from src.database import init_database, DatabaseManager, Stock, Dividend, FinancialMetric
from src.config import settings
import sys
import os
import asyncio
import logging
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))


# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


class DividendScannerApp:
    """Main application class"""

    def __init__(self):
        self.db_manager = None
        self.data_pipeline = None
        self.scanner = None
        self._initialize()

    def _initialize(self):
        """Initialize all components"""
        try:
            # Initialize database
            self.db_manager = init_database(settings.database_url)
            logger.info("Database initialized successfully")

            # Initialize data providers
            providers = [YFinanceProvider()]

            if settings.alpha_vantage_api_key:
                providers.append(AlphaVantageProvider(
                    settings.alpha_vantage_api_key))

            # Initialize data pipeline
            self.data_pipeline = DataPipeline(providers)
            logger.info(
                f"Data pipeline initialized with {len(providers)} providers")

            # Initialize scanner
            self.scanner = DividendScanner(self.data_pipeline)
            logger.info("Dividend scanner initialized")

        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            raise

    def run_quick_scan(self, scan_type: str = "high_yield", symbols: list = None):
        """Run a quick dividend scan"""
        try:
            # Get symbols to scan
            if symbols is None:
                if scan_type == "aristocrats":
                    symbols = get_dividend_aristocrats()[:20]  # Limit for demo
                else:
                    symbols = get_sp500_symbols()[:50]  # Limit for demo

            logger.info(f"Running {scan_type} scan on {len(symbols)} symbols")

            # Get scan configuration
            if scan_type == "high_yield":
                config = PreDefinedScans.high_yield_scanner()
            elif scan_type == "aristocrats":
                config = PreDefinedScans.dividend_aristocrats()
            elif scan_type == "safe":
                config = PreDefinedScans.safe_dividend_stocks()
            elif scan_type == "growth":
                config = PreDefinedScans.growth_dividend_stocks()
            else:
                config = PreDefinedScans.high_yield_scanner()

            # Run scan
            results = self.scanner.scan_stocks(symbols, config)

            if not results.empty:
                print(f"\n=== {config.name} Results ===")
                print(f"Found {len(results)} stocks matching criteria:")
                print("\nTop 10 Results:")
                print(results[['symbol', 'name', 'dividend_yield', 'dividend_health_score', 'payout_ratio']].head(
                    10).to_string(index=False))

                # Save results
                output_file = f"data/{scan_type}_scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                results.to_csv(output_file, index=False)
                print(f"\nFull results saved to: {output_file}")
            else:
                print("No stocks found matching the criteria")

        except Exception as e:
            logger.error(f"Error running scan: {e}")
            raise

    def update_database(self, symbols: list = None, batch_size: int = 10):
        """Update database with latest stock data"""
        try:
            if symbols is None:
                symbols = get_sp500_symbols()[:100]  # Limit for demo

            logger.info(f"Updating database with {len(symbols)} symbols")

            session = self.db_manager.get_session()

            try:
                # Process in batches
                for i in range(0, len(symbols), batch_size):
                    batch = symbols[i:i + batch_size]
                    logger.info(
                        f"Processing batch {i//batch_size + 1}: {batch}")

                    # Get data for batch
                    batch_data = self.data_pipeline.batch_update_stocks(
                        batch, delay=0.2)

                    # Save to database
                    for symbol, data in batch_data.items():
                        if 'error' in data:
                            logger.warning(
                                f"Skipping {symbol} due to error: {data['error']}")
                            continue

                        self._save_stock_data(session, symbol, data)

                    session.commit()
                    logger.info(f"Batch {i//batch_size + 1} completed")

                logger.info("Database update completed successfully")

            finally:
                self.db_manager.close_session(session)

        except Exception as e:
            logger.error(f"Error updating database: {e}")
            raise

    def _save_stock_data(self, session, symbol: str, data: dict):
        """Save stock data to database"""
        try:
            stock_info = data.get('stock_info', {})
            financial_metrics = data.get('financial_metrics', {})
            dividend_history = data.get('dividend_history')

            # Create or update stock record
            stock = session.query(Stock).filter(Stock.symbol == symbol).first()

            if not stock:
                stock = Stock(
                    symbol=symbol,
                    name=stock_info.get('name', ''),
                    sector=stock_info.get('sector', ''),
                    market_cap=stock_info.get('market_cap'),
                    current_price=stock_info.get('current_price'),
                    currency=stock_info.get('currency', 'USD'),
                    exchange=stock_info.get('exchange', '')
                )
                session.add(stock)
                session.flush()  # Get the ID
            else:
                # Update existing record
                stock.name = stock_info.get('name', stock.name)
                stock.sector = stock_info.get('sector', stock.sector)
                stock.market_cap = stock_info.get(
                    'market_cap', stock.market_cap)
                stock.current_price = stock_info.get(
                    'current_price', stock.current_price)
                stock.updated_at = datetime.now()

            # Save financial metrics
            financial_metric = FinancialMetric(
                stock_id=stock.id,
                pe_ratio=financial_metrics.get('pe_ratio'),
                debt_to_equity=financial_metrics.get('debt_to_equity'),
                return_on_equity=financial_metrics.get('return_on_equity'),
                revenue_growth=financial_metrics.get('revenue_growth'),
                profit_margin=financial_metrics.get('profit_margin'),
                earnings_per_share=financial_metrics.get('earnings_per_share'),
                free_cash_flow=financial_metrics.get('free_cash_flow'),
                dividend_coverage_ratio=financial_metrics.get(
                    'dividend_coverage_ratio'),
                reporting_period="current",
                fiscal_year=datetime.now().year
            )
            session.add(financial_metric)

            # Save dividend history
            if dividend_history is not None and not dividend_history.empty:
                for _, row in dividend_history.iterrows():
                    dividend = Dividend(
                        stock_id=stock.id,
                        dividend_amount=row.get('dividend_amount'),
                        ex_dividend_date=row.get('ex_dividend_date'),
                        dividend_type=row.get('dividend_type', 'regular'),
                        dividend_growth_rate=row.get('dividend_growth_rate')
                    )
                    session.add(dividend)

        except Exception as e:
            logger.error(f"Error saving data for {symbol}: {e}")


def main():
    """Main entry point"""
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(
        description="Dividend Scanner Application")
    parser.add_argument('--scan', choices=['high_yield', 'aristocrats', 'safe', 'growth'],
                        default='high_yield', help='Type of scan to run')
    parser.add_argument('--symbols', nargs='+',
                        help='Specific symbols to scan')
    parser.add_argument('--update-db', action='store_true',
                        help='Update database with latest data')
    parser.add_argument('--batch-size', type=int, default=10,
                        help='Batch size for database updates')

    args = parser.parse_args()

    try:
        # Initialize application
        app = DividendScannerApp()

        if args.update_db:
            app.update_database(symbols=args.symbols,
                                batch_size=args.batch_size)
        else:
            app.run_quick_scan(scan_type=args.scan, symbols=args.symbols)

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
