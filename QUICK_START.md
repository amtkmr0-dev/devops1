# Dividend Scanner - Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### 1. Installation
```bash
# Navigate to the project directory
cd dividend_scanner

# Create virtual environment (if not already created)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Test the Setup
```bash
# Run demo with sample data
python demo.py

# Test basic functionality
python test_setup.py
```

### 3. Configure Environment (Optional)
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys (optional for basic usage)
# Yahoo Finance works without API keys but has rate limits
```

## 🎯 Usage Examples

### Command Line Interface

#### Basic Scans
```bash
# High dividend yield scan (>4%)
python main.py --scan high_yield

# Dividend aristocrats (25+ years growth)
python main.py --scan aristocrats

# Safe dividend stocks (conservative criteria)
python main.py --scan safe

# Growth dividend stocks
python main.py --scan growth
```

#### Custom Symbol Lists
```bash
# Scan specific stocks
python main.py --symbols AAPL MSFT JNJ KO --scan safe

# Scan with larger batch
python main.py --symbols AAPL MSFT GOOGL AMZN JNJ PG KO PFE --scan high_yield
```

### Web Dashboard
```bash
# Start the interactive dashboard
streamlit run dashboard.py

# Open browser to http://localhost:8501
```

### Database Operations
```bash
# Update database with latest data
python main.py --update-db --batch-size 20

# Update specific stocks
python main.py --update-db --symbols AAPL MSFT JNJ
```

## 📊 Scan Types Explained

### 1. High Yield Scanner
**Criteria**: Dividend yield > 4%, Payout ratio < 80%, Market cap > $1B
**Best for**: Income-focused investors seeking higher yields
**Risk level**: Medium to High

### 2. Dividend Aristocrats
**Criteria**: 25+ years of consecutive dividend increases, Payout ratio < 70%
**Best for**: Long-term investors seeking stability
**Risk level**: Low to Medium

### 3. Safe Dividend Stocks
**Criteria**: 
- Yield: 2-8%
- Payout ratio: < 60%
- Coverage ratio: > 1.5x
- Debt-to-equity: < 0.5
- ROE: > 15%
**Best for**: Conservative investors
**Risk level**: Low

### 4. Growth Dividend Stocks
**Criteria**: 5+ years dividend growth, Payout ratio < 70%, ROE > 12%
**Best for**: Growth and income balance
**Risk level**: Medium

## 🎛️ Dashboard Features

### Main Interface
- **Scan Configuration**: Choose scan type and symbols
- **Results Table**: Sortable results with key metrics
- **Charts**: Visual analysis of yield distribution and health scores
- **Top Picks**: Detailed analysis of best stocks
- **Export**: Download results as CSV or JSON

### Key Metrics Displayed
- **Health Score**: Proprietary 0-100 rating
- **Dividend Yield**: Annual dividend as % of stock price
- **Payout Ratio**: Percentage of earnings paid as dividends
- **Coverage Ratio**: How well earnings cover dividend payments
- **Growth Rate**: Historical dividend growth percentage

## 🧮 Health Score Breakdown

Our dividend health score (0-100) considers:

| Component | Weight | Description |
|-----------|--------|-------------|
| Dividend Yield | 20 pts | Sweet spot: 2-6% |
| Payout Ratio | 25 pts | Optimal: 30-60% |
| Dividend Growth | 20 pts | Consistency of increases |
| Financial Health | 20 pts | P/E, debt, ROE |
| Coverage Ratio | 15 pts | Earnings coverage |

### Scoring Guidelines
- **80-100**: Excellent dividend health
- **60-79**: Good dividend potential
- **40-59**: Moderate risk
- **20-39**: Higher risk
- **0-19**: Significant concerns

## 🔧 Customization

### Creating Custom Scans
```python
from src.scanner import ScanConfiguration, ScanFilter, ScanCriteria

# Example: Tech dividend stocks
tech_scan = ScanConfiguration(
    name="Tech Dividend Stocks",
    filters=[
        ScanFilter(ScanCriteria.MIN_DIVIDEND_YIELD, 0.02, "gte"),
        ScanFilter(ScanCriteria.SECTORS, ["Technology"], "in"),
        ScanFilter(ScanCriteria.MAX_PAYOUT_RATIO, 0.5, "lte")
    ],
    sort_by="dividend_health_score",
    sort_order="desc"
)
```

### Available Filter Criteria
- `MIN_DIVIDEND_YIELD` / `MAX_DIVIDEND_YIELD`
- `MIN_MARKET_CAP` / `MAX_MARKET_CAP`
- `MIN_YEARS_DIVIDEND_GROWTH`
- `MAX_PAYOUT_RATIO`
- `MIN_DIVIDEND_COVERAGE`
- `SECTORS`
- `MIN_PE_RATIO` / `MAX_PE_RATIO`
- `MIN_ROE`
- `MAX_DEBT_TO_EQUITY`
- `EX_DIVIDEND_WITHIN_DAYS`

## 💡 Tips for Success

### 1. Start with Demo
- Run `python demo.py` to understand the features
- Experiment with different scan types
- Learn how health scores are calculated

### 2. Use Rate Limiting
- Yahoo Finance has rate limits (free tier)
- Start with small batches (10-20 stocks)
- Consider getting Alpha Vantage API key for higher limits

### 3. Combine Multiple Criteria
- Don't rely on yield alone
- Consider payout sustainability
- Check financial health metrics
- Look at dividend growth history

### 4. Regular Updates
- Update data regularly for current prices
- Monitor ex-dividend dates
- Track changes in health scores

## 🚨 Common Issues & Solutions

### Rate Limiting
**Problem**: "Too Many Requests" errors
**Solution**: 
- Wait a few minutes between runs
- Reduce batch size
- Get API keys for higher limits

### Missing Data
**Problem**: Some stocks return no data
**Solution**:
- Check symbol spelling
- Some stocks may not pay dividends
- International stocks may need different symbols

### Empty Results
**Problem**: No stocks found in scan
**Solution**:
- Relax filter criteria
- Check if symbols actually pay dividends
- Verify market is open/data is current

## 📈 Next Steps

### For Beginners
1. Run demo to understand features
2. Try predefined scans on S&P 500 sample
3. Analyze top-ranked stocks
4. Gradually learn to create custom filters

### For Advanced Users
1. Set up database for historical tracking
2. Configure API keys for better data access
3. Create sector-specific scans
4. Build automated monitoring systems

### Development
1. Add new data providers
2. Implement alert systems
3. Create portfolio tracking
4. Add backtesting capabilities

## 🔗 Resources

- **Yahoo Finance**: Primary data source (free)
- **Alpha Vantage**: Enhanced metrics (API key)
- **Streamlit Docs**: For dashboard customization
- **SQLAlchemy**: For database operations

---

**Happy Dividend Hunting! 💰**

For issues or questions, check the main README.md or create an issue in the repository.
