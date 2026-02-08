# Dividend Scanner

A comprehensive tool for scanning and analyzing dividend-paying stocks based on various financial criteria.

## Features

- 🔍 **Multiple Scan Types**: High yield, dividend aristocrats, safe dividends, and growth stocks
- 📊 **Health Score**: Proprietary algorithm to assess dividend sustainability
- 📈 **Comprehensive Analysis**: Financial metrics, growth rates, and risk assessment
- 🎯 **Custom Filters**: Create your own scanning criteria
- 💾 **Database Storage**: SQLite/PostgreSQL support for historical data
- 🖥️ **Web Dashboard**: Interactive Streamlit dashboard
- 📱 **CLI Interface**: Command-line interface for automated scanning

## Project Structure

```
dividend_scanner/
├── main.py                 # Main CLI application
├── dashboard.py            # Streamlit web dashboard
├── requirements.txt        # Python dependencies
├── .env                   # Environment configuration
├── src/
│   ├── config.py          # Application configuration
│   ├── database/          # Database models and management
│   │   ├── __init__.py
│   │   └── models.py
│   ├── data/              # Data providers and pipeline
│   │   ├── __init__.py
│   │   └── providers.py
│   ├── scanner/           # Scanning engine
│   │   ├── __init__.py
│   │   └── engine.py
│   ├── utils/             # Utilities
│   │   ├── __init__.py
│   │   └── logger.py
├── data/                  # Data storage
├── logs/                  # Application logs
└── tests/                 # Test files
```

## Installation

1. **Clone or create the project directory**:
   ```bash
   cd dividend_scanner
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

## Quick Start

### Command Line Interface

1. **Run a quick high-yield dividend scan**:
   ```bash
   python main.py --scan high_yield
   ```

2. **Scan dividend aristocrats**:
   ```bash
   python main.py --scan aristocrats
   ```

3. **Scan specific stocks**:
   ```bash
   python main.py --symbols AAPL MSFT JNJ KO --scan safe
   ```

4. **Update database with latest data**:
   ```bash
   python main.py --update-db --batch-size 20
   ```

### Web Dashboard

1. **Start the Streamlit dashboard**:
   ```bash
   streamlit run dashboard.py
   ```

2. **Open your browser** to `http://localhost:8501`

3. **Configure your scan** in the sidebar and click "Run Scan"

## Scan Types

### Predefined Scans

1. **High Yield Scanner** (`high_yield`)
   - Dividend yield > 4%
   - Payout ratio < 80%
   - Market cap > $1B

2. **Dividend Aristocrats** (`aristocrats`)
   - 25+ years of consecutive dividend increases
   - Payout ratio < 70%

3. **Safe Dividend Stocks** (`safe`)
   - Yield between 2-8%
   - Payout ratio < 60%
   - Dividend coverage ratio > 1.5
   - Debt-to-equity < 0.5
   - ROE > 15%

4. **Growth Dividend Stocks** (`growth`)
   - 5+ years of dividend growth
   - Payout ratio < 70%
   - ROE > 12%

### Custom Scans

Create custom scans by defining your own filters:

```python
from src.scanner import ScanConfiguration, ScanFilter, ScanCriteria

custom_config = ScanConfiguration(
    name="My Custom Scan",
    filters=[
        ScanFilter(ScanCriteria.MIN_DIVIDEND_YIELD, 0.03, "gte"),
        ScanFilter(ScanCriteria.MAX_PAYOUT_RATIO, 0.6, "lte"),
        ScanFilter(ScanCriteria.SECTORS, ["Technology", "Healthcare"], "in")
    ],
    sort_by="dividend_health_score",
    sort_order="desc"
)
```

## Dividend Health Score

Our proprietary health score (0-100) evaluates dividend sustainability based on:

- **Dividend Yield** (20 points): Sweet spot 2-6%
- **Payout Ratio** (25 points): Optimal 30-60%
- **Dividend Growth** (20 points): Consistency of increases
- **Financial Health** (20 points): P/E ratio, debt levels, ROE
- **Coverage Ratio** (15 points): Earnings coverage of dividends

## Data Sources

- **Yahoo Finance**: Primary data source (free)
- **Alpha Vantage**: Enhanced financial metrics (API key required)
- **Fyers**: Indian market data (API credentials required)

## Configuration

### Environment Variables

Create a `.env` file with:

```bash
# Database
DATABASE_URL=sqlite:///./data/dividend_scanner.db

# API Keys
ALPHA_VANTAGE_API_KEY=your_key_here
FYERS_CLIENT_ID=your_client_id
FYERS_SECRET_KEY=your_secret_key

# Email Notifications
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Application Settings
DEBUG=True
LOG_LEVEL=INFO
```

## API Integration

### Yahoo Finance (Default)
- No API key required
- Rate limited
- Good for basic stock and dividend data

### Alpha Vantage (Optional)
- Free tier: 5 API calls per minute, 500 per day
- Enhanced financial metrics
- Get API key from: https://www.alphavantage.co/support/#api-key

### Fyers (Optional)
- Indian stock market data
- Requires broker account
- Real-time data access

## Database Schema

The application uses SQLAlchemy with support for SQLite and PostgreSQL:

- **stocks**: Basic stock information
- **dividends**: Dividend history and payments
- **financial_metrics**: Financial ratios and metrics
- **scan_results**: Historical scan results
- **user_alerts**: Alert configurations

## Examples

### Example 1: Find High-Yield Technology Stocks

```python
from src.scanner import ScanConfiguration, ScanFilter, ScanCriteria

tech_high_yield = ScanConfiguration(
    name="Tech High Yield",
    filters=[
        ScanFilter(ScanCriteria.MIN_DIVIDEND_YIELD, 0.025, "gte"),
        ScanFilter(ScanCriteria.SECTORS, ["Technology"], "in"),
        ScanFilter(ScanCriteria.MAX_PAYOUT_RATIO, 0.7, "lte")
    ]
)
```

### Example 2: Conservative Dividend Portfolio

```python
conservative_scan = ScanConfiguration(
    name="Conservative Dividends",
    filters=[
        ScanFilter(ScanCriteria.MIN_DIVIDEND_YIELD, 0.02, "gte"),
        ScanFilter(ScanCriteria.MAX_DIVIDEND_YIELD, 0.06, "lte"),
        ScanFilter(ScanCriteria.MIN_YEARS_DIVIDEND_GROWTH, 10, "gte"),
        ScanFilter(ScanCriteria.MAX_DEBT_TO_EQUITY, 0.3, "lte"),
        ScanFilter(ScanCriteria.MIN_DIVIDEND_COVERAGE, 2.0, "gte")
    ]
)
```

## Development

### Running Tests

```bash
pytest tests/
```

### Adding New Data Providers

1. Inherit from `DataProvider` class
2. Implement required methods
3. Add to data pipeline

### Adding New Scan Criteria

1. Add to `ScanCriteria` enum
2. Implement filter logic in `DividendScanner`
3. Update health score calculation if needed

## Deployment

### Local Development
```bash
streamlit run dashboard.py
```

### Production Deployment
- Use PostgreSQL for database
- Set up proper environment variables
- Consider using Docker
- Set up monitoring and logging

## Troubleshooting

### Common Issues

1. **API Rate Limits**: Reduce batch size or add delays
2. **Missing Data**: Some stocks may not have dividend history
3. **Database Errors**: Check database URL and permissions

### Logging

Logs are stored in `logs/dividend_scanner.log` with rotation.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is for educational and personal use. Please respect data provider terms of service.

## Roadmap

- [ ] Real-time alerts and notifications
- [ ] Portfolio tracking integration
- [ ] Additional international markets
- [ ] Machine learning predictions
- [ ] Mobile app interface
- [ ] API for third-party integrations
