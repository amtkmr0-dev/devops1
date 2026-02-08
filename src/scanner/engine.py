import pandas as pd
from typing import List, Dict, Optional, Tuple, Callable
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ScanCriteria(Enum):
    """Enumeration of available scan criteria"""
    MIN_DIVIDEND_YIELD = "min_dividend_yield"
    MAX_DIVIDEND_YIELD = "max_dividend_yield"
    MIN_MARKET_CAP = "min_market_cap"
    MAX_MARKET_CAP = "max_market_cap"
    MIN_YEARS_DIVIDEND_GROWTH = "min_years_dividend_growth"
    MAX_PAYOUT_RATIO = "max_payout_ratio"
    MIN_DIVIDEND_COVERAGE = "min_dividend_coverage"
    SECTORS = "sectors"
    MIN_PE_RATIO = "min_pe_ratio"
    MAX_PE_RATIO = "max_pe_ratio"
    MIN_ROE = "min_roe"
    MAX_DEBT_TO_EQUITY = "max_debt_to_equity"
    EX_DIVIDEND_WITHIN_DAYS = "ex_dividend_within_days"


@dataclass
class ScanFilter:
    """Single scan filter"""
    criteria: ScanCriteria
    value: any
    operator: str = "gte"  # gte, lte, eq, in, not_in


@dataclass
class ScanConfiguration:
    """Complete scan configuration"""
    name: str
    filters: List[ScanFilter]
    sort_by: str = "dividend_yield"
    sort_order: str = "desc"  # asc, desc
    limit: Optional[int] = None


class DividendHealthCalculator:
    """Calculate dividend health scores"""

    @staticmethod
    def calculate_health_score(stock_data: Dict, financial_metrics: Dict, dividend_data: pd.DataFrame) -> float:
        """
        Calculate a proprietary dividend health score (0-100)
        Higher score = healthier dividend
        """
        score = 0.0
        max_score = 100.0

        # 1. Dividend Yield Score (0-20 points)
        # Sweet spot: 2-6% yield
        dividend_yield = stock_data.get('dividend_yield', 0) or 0
        if isinstance(dividend_yield, str):
            dividend_yield = float(dividend_yield.replace('%', '')) / 100

        if 0.02 <= dividend_yield <= 0.06:
            score += 20
        elif 0.01 <= dividend_yield < 0.02:
            score += 15
        elif 0.06 < dividend_yield <= 0.08:
            score += 15
        elif dividend_yield > 0.08:
            score += 5  # Too high might be risky

        # 2. Payout Ratio Score (0-25 points)
        payout_ratio = stock_data.get(
            'payout_ratio') or financial_metrics.get('payout_ratio')
        if payout_ratio:
            if isinstance(payout_ratio, str):
                payout_ratio = float(payout_ratio.replace('%', '')) / 100

            if 0.3 <= payout_ratio <= 0.6:
                score += 25
            elif 0.2 <= payout_ratio < 0.3:
                score += 20
            elif 0.6 < payout_ratio <= 0.8:
                score += 15
            elif payout_ratio > 0.8:
                score += 5  # High risk

        # 3. Dividend Growth Score (0-20 points)
        if not dividend_data.empty:
            # Check for consistent dividend growth
            growth_rates = dividend_data['dividend_growth_rate'].dropna()
            if len(growth_rates) >= 3:
                positive_growth_years = (growth_rates > 0).sum()
                growth_consistency = positive_growth_years / len(growth_rates)
                score += growth_consistency * 20

        # 4. Financial Health Score (0-20 points)
        pe_ratio = financial_metrics.get('pe_ratio')
        debt_to_equity = financial_metrics.get('debt_to_equity')
        roe = financial_metrics.get('return_on_equity')

        financial_health = 0
        if pe_ratio and 10 <= pe_ratio <= 25:
            financial_health += 7
        if debt_to_equity and debt_to_equity <= 0.5:
            financial_health += 7
        if roe and roe >= 0.15:
            financial_health += 6

        score += financial_health

        # 5. Coverage Ratio Score (0-15 points)
        coverage_ratio = financial_metrics.get('dividend_coverage_ratio')
        if coverage_ratio:
            if coverage_ratio >= 2.0:
                score += 15
            elif coverage_ratio >= 1.5:
                score += 12
            elif coverage_ratio >= 1.2:
                score += 8
            else:
                score += 3

        return min(score, max_score)


class DividendScanner:
    """Main dividend scanning engine"""

    def __init__(self, data_pipeline):
        self.data_pipeline = data_pipeline
        self.health_calculator = DividendHealthCalculator()

    def scan_stocks(self, symbols: List[str], config: ScanConfiguration) -> pd.DataFrame:
        """
        Scan stocks based on configuration
        """
        logger.info(f"Starting scan '{config.name}' on {len(symbols)} stocks")

        results = []

        for symbol in symbols:
            try:
                # Get all data for the stock
                stock_data = self.data_pipeline.get_stock_data(symbol)
                financial_metrics = self.data_pipeline.get_financial_metrics(
                    symbol)
                dividend_data = self.data_pipeline.get_dividend_history(symbol)

                if not stock_data:
                    continue

                # Apply filters
                if self._passes_filters(stock_data, financial_metrics, dividend_data, config.filters):
                    # Calculate health score
                    health_score = self.health_calculator.calculate_health_score(
                        stock_data, financial_metrics, dividend_data
                    )

                    # Compile result
                    result = {
                        'symbol': symbol,
                        'name': stock_data.get('name', ''),
                        'sector': stock_data.get('sector', ''),
                        'current_price': stock_data.get('current_price'),
                        'market_cap': stock_data.get('market_cap'),
                        'dividend_yield': stock_data.get('dividend_yield'),
                        'payout_ratio': stock_data.get('payout_ratio'),
                        'pe_ratio': financial_metrics.get('pe_ratio'),
                        'debt_to_equity': financial_metrics.get('debt_to_equity'),
                        'return_on_equity': financial_metrics.get('return_on_equity'),
                        'dividend_coverage_ratio': financial_metrics.get('dividend_coverage_ratio'),
                        'dividend_health_score': health_score,
                        'last_dividend_amount': self._get_last_dividend_amount(dividend_data),
                        'dividend_growth_rate': self._get_avg_dividend_growth(dividend_data),
                        'years_of_growth': self._count_growth_years(dividend_data),
                        'next_ex_dividend_date': self._estimate_next_ex_dividend(dividend_data),
                        'scan_date': datetime.now()
                    }

                    results.append(result)

            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue

        # Convert to DataFrame
        df = pd.DataFrame(results)

        if df.empty:
            return df

        # Sort results
        ascending = config.sort_order == "asc"
        df = df.sort_values(by=config.sort_by, ascending=ascending)

        # Apply limit
        if config.limit:
            df = df.head(config.limit)

        logger.info(f"Scan '{config.name}' completed. Found {len(df)} stocks.")

        return df

    def _passes_filters(self, stock_data: Dict, financial_metrics: Dict,
                        dividend_data: pd.DataFrame, filters: List[ScanFilter]) -> bool:
        """Check if stock passes all filters"""

        for filter_obj in filters:
            criteria = filter_obj.criteria
            value = filter_obj.value
            operator = filter_obj.operator

            # Get the actual value to compare
            actual_value = self._get_filter_value(
                criteria, stock_data, financial_metrics, dividend_data)

            if actual_value is None:
                return False

            # Apply filter
            if not self._apply_filter(actual_value, value, operator):
                return False

        return True

    def _get_filter_value(self, criteria: ScanCriteria, stock_data: Dict,
                          financial_metrics: Dict, dividend_data: pd.DataFrame):
        """Get the actual value for a filter criteria"""

        if criteria == ScanCriteria.MIN_DIVIDEND_YIELD or criteria == ScanCriteria.MAX_DIVIDEND_YIELD:
            yield_val = stock_data.get('dividend_yield')
            if isinstance(yield_val, str):
                return float(yield_val.replace('%', '')) / 100
            return yield_val

        elif criteria == ScanCriteria.MIN_MARKET_CAP or criteria == ScanCriteria.MAX_MARKET_CAP:
            return stock_data.get('market_cap')

        elif criteria == ScanCriteria.MAX_PAYOUT_RATIO:
            payout = stock_data.get('payout_ratio')
            if isinstance(payout, str):
                return float(payout.replace('%', '')) / 100
            return payout

        elif criteria == ScanCriteria.MIN_DIVIDEND_COVERAGE:
            return financial_metrics.get('dividend_coverage_ratio')

        elif criteria == ScanCriteria.SECTORS:
            return stock_data.get('sector')

        elif criteria == ScanCriteria.MIN_PE_RATIO or criteria == ScanCriteria.MAX_PE_RATIO:
            return financial_metrics.get('pe_ratio')

        elif criteria == ScanCriteria.MIN_ROE:
            return financial_metrics.get('return_on_equity')

        elif criteria == ScanCriteria.MAX_DEBT_TO_EQUITY:
            return financial_metrics.get('debt_to_equity')

        elif criteria == ScanCriteria.MIN_YEARS_DIVIDEND_GROWTH:
            return self._count_growth_years(dividend_data)

        elif criteria == ScanCriteria.EX_DIVIDEND_WITHIN_DAYS:
            next_ex_div = self._estimate_next_ex_dividend(dividend_data)
            if next_ex_div:
                days_until = (next_ex_div - datetime.now()).days
                return days_until
            return None

        return None

    def _apply_filter(self, actual_value, filter_value, operator: str) -> bool:
        """Apply filter logic"""

        if actual_value is None:
            return False

        if operator == "gte":
            return actual_value >= filter_value
        elif operator == "lte":
            return actual_value <= filter_value
        elif operator == "eq":
            return actual_value == filter_value
        elif operator == "in":
            return actual_value in filter_value
        elif operator == "not_in":
            return actual_value not in filter_value

        return False

    def _get_last_dividend_amount(self, dividend_data: pd.DataFrame) -> Optional[float]:
        """Get the most recent dividend amount"""
        if dividend_data.empty:
            return None

        sorted_data = dividend_data.sort_values(
            'ex_dividend_date', ascending=False)
        return sorted_data.iloc[0]['dividend_amount'] if len(sorted_data) > 0 else None

    def _get_avg_dividend_growth(self, dividend_data: pd.DataFrame) -> Optional[float]:
        """Calculate average dividend growth rate"""
        if dividend_data.empty:
            return None

        growth_rates = dividend_data['dividend_growth_rate'].dropna()
        return growth_rates.mean() if len(growth_rates) > 0 else None

    def _count_growth_years(self, dividend_data: pd.DataFrame) -> int:
        """Count consecutive years of dividend growth"""
        if dividend_data.empty:
            return 0

        growth_rates = dividend_data['dividend_growth_rate'].dropna()
        consecutive_growth = 0

        for rate in reversed(growth_rates.tolist()):
            if rate > 0:
                consecutive_growth += 1
            else:
                break

        return consecutive_growth

    def _estimate_next_ex_dividend(self, dividend_data: pd.DataFrame) -> Optional[datetime]:
        """Estimate next ex-dividend date based on historical pattern"""
        if dividend_data.empty:
            return None

        # Simple estimation: assume quarterly dividends
        # In production, you'd want more sophisticated logic
        sorted_data = dividend_data.sort_values(
            'ex_dividend_date', ascending=False)
        if len(sorted_data) >= 2:
            last_date = sorted_data.iloc[0]['ex_dividend_date']
            prev_date = sorted_data.iloc[1]['ex_dividend_date']

            # Calculate typical interval
            interval = last_date - prev_date

            # Estimate next date
            estimated_next = last_date + interval

            # Only return if it's in the future
            if estimated_next > datetime.now():
                return estimated_next

        return None

# Predefined scan configurations


class PreDefinedScans:
    """Collection of predefined scan configurations"""

    @staticmethod
    def high_yield_scanner() -> ScanConfiguration:
        """High dividend yield scanner (>4%)"""
        return ScanConfiguration(
            name="High Yield Scanner",
            filters=[
                ScanFilter(ScanCriteria.MIN_DIVIDEND_YIELD, 0.04, "gte"),
                ScanFilter(ScanCriteria.MAX_PAYOUT_RATIO, 0.8, "lte"),
                ScanFilter(ScanCriteria.MIN_MARKET_CAP,
                           1e9, "gte")  # >$1B market cap
            ],
            sort_by="dividend_yield",
            sort_order="desc"
        )

    @staticmethod
    def dividend_aristocrats() -> ScanConfiguration:
        """Dividend aristocrats (25+ years of growth)"""
        return ScanConfiguration(
            name="Dividend Aristocrats",
            filters=[
                ScanFilter(ScanCriteria.MIN_YEARS_DIVIDEND_GROWTH, 25, "gte"),
                ScanFilter(ScanCriteria.MAX_PAYOUT_RATIO, 0.7, "lte")
            ],
            sort_by="years_of_growth",
            sort_order="desc"
        )

    @staticmethod
    def safe_dividend_stocks() -> ScanConfiguration:
        """Safe dividend stocks (conservative criteria)"""
        return ScanConfiguration(
            name="Safe Dividend Stocks",
            filters=[
                ScanFilter(ScanCriteria.MIN_DIVIDEND_YIELD, 0.02, "gte"),
                ScanFilter(ScanCriteria.MAX_DIVIDEND_YIELD, 0.08, "lte"),
                ScanFilter(ScanCriteria.MAX_PAYOUT_RATIO, 0.6, "lte"),
                ScanFilter(ScanCriteria.MIN_DIVIDEND_COVERAGE, 1.5, "gte"),
                ScanFilter(ScanCriteria.MAX_DEBT_TO_EQUITY, 0.5, "lte"),
                ScanFilter(ScanCriteria.MIN_ROE, 0.15, "gte")
            ],
            sort_by="dividend_health_score",
            sort_order="desc"
        )

    @staticmethod
    def growth_dividend_stocks() -> ScanConfiguration:
        """Growth dividend stocks (growing dividends)"""
        return ScanConfiguration(
            name="Growth Dividend Stocks",
            filters=[
                ScanFilter(ScanCriteria.MIN_YEARS_DIVIDEND_GROWTH, 5, "gte"),
                ScanFilter(ScanCriteria.MAX_PAYOUT_RATIO, 0.7, "lte"),
                ScanFilter(ScanCriteria.MIN_ROE, 0.12, "gte")
            ],
            sort_by="dividend_growth_rate",
            sort_order="desc"
        )

    @staticmethod
    def sector_focused_scan(sectors: List[str]) -> ScanConfiguration:
        """Sector-focused dividend scanner"""
        return ScanConfiguration(
            name=f"Sector Focused: {', '.join(sectors)}",
            filters=[
                ScanFilter(ScanCriteria.SECTORS, sectors, "in"),
                ScanFilter(ScanCriteria.MIN_DIVIDEND_YIELD, 0.01, "gte"),
                ScanFilter(ScanCriteria.MAX_PAYOUT_RATIO, 0.8, "lte")
            ],
            sort_by="dividend_yield",
            sort_order="desc"
        )
