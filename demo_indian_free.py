#!/usr/bin/env python3
"""
Free Indian Dividend Scanner Demo
No API keys required - uses web scraping and free data sources
"""

from src.data.dividend_news_scanner import IndianDividendNewsScanner, create_dividend_news_report
from src.data.free_indian_provider import (
    FreeIndianStockProvider,
    get_popular_indian_dividend_stocks,
    get_high_dividend_yield_stocks,
    get_dividend_aristocrats_india
)
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))


def demo_indian_dividend_stocks():
    """Demo Indian dividend stock scanning"""
    print("🇮🇳 Free Indian Dividend Scanner Demo")
    print("=" * 50)
    print("Scanning Indian stocks without any API keys!")
    print("Using: Yahoo Finance + Web Scraping\n")

    provider = FreeIndianStockProvider()

    # Get sample of popular dividend stocks
    symbols = get_high_dividend_yield_stocks()[:5]  # Limit for demo

    print(f"📊 Scanning High Dividend Yield Stocks: {', '.join(symbols)}")
    print("This may take a few minutes...\n")

    results = provider.batch_get_stocks(symbols, delay=1.0)

    # Display results
    print("Results:")
    print("-" * 70)

    dividend_stocks = []

    for symbol, data in results.items():
        if 'error' in data:
            print(f"❌ {symbol}: {data['error']}")
            continue

        if not data or 'symbol' not in data:
            print(f"⚠️  {symbol}: No data available")
            continue

        print(f"✅ {symbol} - {data.get('name', 'N/A')}")
        print(f"   💰 Current Price: ₹{data.get('current_price', 'N/A')}")
        print(f"   📈 Dividend Yield: {data.get('dividend_yield', 0)*100:.2f}%" if data.get(
            'dividend_yield') else "   📈 Dividend Yield: N/A")
        print(
            f"   🏆 Health Score: {data.get('estimated_health_score', 0):.1f}/100")
        print(f"   🏭 Sector: {data.get('sector', 'N/A')}")
        print(f"   💼 Market Cap: ₹{data.get('market_cap', 0)/1e9:.1f}B" if data.get(
            'market_cap') else "   💼 Market Cap: N/A")

        # Dividend history
        dividend_history = data.get('dividend_history', [])
        if dividend_history:
            recent_dividend = dividend_history[-1] if isinstance(
                dividend_history, list) else None
            if recent_dividend:
                print(
                    f"   📅 Last Dividend: ₹{recent_dividend.get('amount', 'N/A')}")

        print()

        dividend_stocks.append(data)

    return dividend_stocks


def demo_dividend_news_scanner():
    """Demo dividend news and announcements scanning"""
    print("\n📰 Dividend News & Announcements Scanner")
    print("=" * 50)
    print("Scanning for recent dividend announcements and upcoming dates...")
    print("⚠️  Note: This is a demo - actual web scraping may be limited\n")

    # Create sample data for demonstration
    sample_announcements = [
        {
            'symbol': 'RELIANCE',
            'company_name': 'Reliance Industries Limited',
            'dividend_amount': 8.0,
            'announcement_date': datetime.now() - timedelta(days=5),
            'ex_dividend_date': datetime.now() + timedelta(days=10),
            'source': 'BSE',
            'status': 'upcoming'
        },
        {
            'symbol': 'TCS',
            'company_name': 'Tata Consultancy Services',
            'dividend_amount': 25.0,
            'announcement_date': datetime.now() - timedelta(days=3),
            'ex_dividend_date': datetime.now() + timedelta(days=15),
            'source': 'NSE',
            'status': 'upcoming'
        },
        {
            'symbol': 'HDFCBANK',
            'company_name': 'HDFC Bank Limited',
            'dividend_amount': 18.5,
            'announcement_date': datetime.now() - timedelta(days=7),
            'ex_dividend_date': datetime.now() + timedelta(days=5),
            'source': 'MoneyControl',
            'status': 'upcoming'
        },
        {
            'symbol': 'ITC',
            'company_name': 'ITC Limited',
            'dividend_amount': 12.0,
            'announcement_date': datetime.now() - timedelta(days=2),
            'ex_dividend_date': datetime.now() + timedelta(days=20),
            'source': 'Economic Times',
            'status': 'upcoming'
        }
    ]

    print("🔍 Recent Dividend Announcements:")
    print("-" * 40)

    for announcement in sample_announcements:
        days_to_ex = (announcement['ex_dividend_date'] - datetime.now()).days

        print(f"📢 {announcement['symbol']} - {announcement['company_name']}")
        print(f"   💰 Dividend: ₹{announcement['dividend_amount']}")
        print(
            f"   📅 Ex-Date: {announcement['ex_dividend_date'].strftime('%d %b %Y')} ({days_to_ex} days)")
        print(f"   📰 Source: {announcement['source']}")
        print(f"   📊 Status: {announcement['status'].title()}")
        print()

    # Upcoming dividend calendar
    print("📅 Upcoming Dividend Calendar (Next 30 Days):")
    print("-" * 45)

    upcoming_sorted = sorted(sample_announcements,
                             key=lambda x: x['ex_dividend_date'])

    for dividend in upcoming_sorted:
        ex_date = dividend['ex_dividend_date']
        days_away = (ex_date - datetime.now()).days

        if days_away >= 0:
            urgency = "🔴" if days_away <= 3 else "🟡" if days_away <= 7 else "🟢"
            print(
                f"{urgency} {ex_date.strftime('%d %b')} - {dividend['symbol']} (₹{dividend['dividend_amount']})")

    print()


def demo_comparative_analysis():
    """Demo comparative analysis of dividend stocks"""
    print("📊 Comparative Dividend Analysis")
    print("=" * 40)

    # Sample comparison data
    comparison_data = [
        {
            'symbol': 'COALINDIA',
            'name': 'Coal India Limited',
            'dividend_yield': 0.086,  # 8.6%
            'health_score': 75.0,
            'payout_ratio': 0.65,
            'sector': 'Mining'
        },
        {
            'symbol': 'NTPC',
            'name': 'NTPC Limited',
            'dividend_yield': 0.054,  # 5.4%
            'health_score': 82.0,
            'payout_ratio': 0.45,
            'sector': 'Power'
        },
        {
            'symbol': 'POWERGRID',
            'name': 'Power Grid Corporation',
            'dividend_yield': 0.042,  # 4.2%
            'health_score': 88.0,
            'payout_ratio': 0.38,
            'sector': 'Power'
        },
        {
            'symbol': 'ITC',
            'name': 'ITC Limited',
            'dividend_yield': 0.035,  # 3.5%
            'health_score': 92.0,
            'payout_ratio': 0.55,
            'sector': 'FMCG'
        }
    ]

    print("Top Dividend Stocks Comparison:")
    print(f"{'Symbol':<12} {'Yield':<8} {'Health':<8} {'Payout':<8} {'Sector':<12}")
    print("-" * 55)

    for stock in sorted(comparison_data, key=lambda x: x['health_score'], reverse=True):
        yield_str = f"{stock['dividend_yield']*100:.1f}%"
        health_str = f"{stock['health_score']:.0f}/100"
        payout_str = f"{stock['payout_ratio']*100:.0f}%"

        print(
            f"{stock['symbol']:<12} {yield_str:<8} {health_str:<8} {payout_str:<8} {stock['sector']:<12}")

    print("\n🎯 Investment Insights:")
    print("• COALINDIA: Highest yield but mining sector risks")
    print("• NTPC: Good balance of yield and stability")
    print("• POWERGRID: Lower yield but excellent health score")
    print("• ITC: Defensive FMCG with consistent dividends")


def demo_dividend_strategies():
    """Demo different dividend investment strategies"""
    print("\n💡 Dividend Investment Strategies")
    print("=" * 40)

    strategies = {
        "🎯 High Yield Strategy": {
            "description": "Focus on stocks with dividend yield > 5%",
            "stocks": ["COALINDIA", "NTPC", "ONGC", "IOC", "BPCL"],
            "pros": ["High current income", "Good for retirees"],
            "cons": ["Higher risk", "Potential dividend cuts"],
            "suitability": "Income-focused investors"
        },

        "🛡️ Dividend Aristocrats": {
            "description": "Companies with consistent dividend growth",
            "stocks": ["RELIANCE", "TCS", "HDFCBANK", "HINDUNILVR", "ITC"],
            "pros": ["Stable income", "Dividend growth", "Lower risk"],
            "cons": ["Lower initial yield", "Higher prices"],
            "suitability": "Long-term investors"
        },

        "⚖️ Balanced Approach": {
            "description": "Mix of yield and growth potential",
            "stocks": ["POWERGRID", "NTPC", "SBIN", "BHARTIARTL", "GAIL"],
            "pros": ["Balanced risk-return", "Diversification"],
            "cons": ["Moderate returns", "Requires research"],
            "suitability": "Most retail investors"
        },

        "🚀 Growth + Dividend": {
            "description": "Growing companies that also pay dividends",
            "stocks": ["TCS", "INFY", "HDFCBANK", "ASIANPAINT", "NESTLEIND"],
            "pros": ["Capital appreciation", "Growing dividends"],
            "cons": ["Higher valuations", "Lower current yield"],
            "suitability": "Growth-oriented investors"
        }
    }

    for strategy_name, details in strategies.items():
        print(f"\n{strategy_name}")
        print(f"📋 {details['description']}")
        print(f"📈 Sample Stocks: {', '.join(details['stocks'])}")
        print(f"✅ Pros: {', '.join(details['pros'])}")
        print(f"❌ Cons: {', '.join(details['cons'])}")
        print(f"👥 Best for: {details['suitability']}")


def demo_practical_tips():
    """Demo practical tips for dividend investing"""
    print("\n💡 Practical Dividend Investing Tips")
    print("=" * 40)

    tips = [
        {
            "title": "📅 Track Ex-Dividend Dates",
            "description": "Buy before ex-date to receive dividend",
            "example": "If ex-date is Oct 15, buy by Oct 14"
        },
        {
            "title": "🔍 Check Dividend History",
            "description": "Look for consistent payment track record",
            "example": "ITC has paid dividends for 20+ years"
        },
        {
            "title": "⚖️ Monitor Payout Ratio",
            "description": "Sustainable payout ratio is 30-60%",
            "example": "80%+ payout ratio indicates high risk"
        },
        {
            "title": "🏭 Diversify Across Sectors",
            "description": "Don't concentrate in one industry",
            "example": "Mix PSU, FMCG, Banking, and IT stocks"
        },
        {
            "title": "📊 Consider Tax Implications",
            "description": "Dividend income is taxable in India",
            "example": "Factor in tax while calculating returns"
        },
        {
            "title": "🎯 Reinvest Dividends",
            "description": "Use dividends to buy more shares",
            "example": "Compound growth through reinvestment"
        }
    ]

    for tip in tips:
        print(f"\n{tip['title']}")
        print(f"   💡 {tip['description']}")
        print(f"   📝 Example: {tip['example']}")


def main():
    """Run all Indian dividend scanner demos"""
    print("🇮🇳 FREE INDIAN DIVIDEND SCANNER")
    print("=" * 50)
    print("Complete dividend analysis without any API costs!")
    print("Perfect for Indian stock market dividend investing\n")

    try:
        # Main demos
        demo_indian_dividend_stocks()
        demo_dividend_news_scanner()
        demo_comparative_analysis()
        demo_dividend_strategies()
        demo_practical_tips()

        print("\n" + "=" * 50)
        print("✅ Demo completed successfully!")
        print("\n🚀 Next Steps:")
        print("1. Run real scans: python main.py --scan high_yield")
        print("2. Use Indian symbols: RELIANCE, TCS, HDFCBANK, etc.")
        print("3. Monitor dividend announcements daily")
        print("4. Create your dividend portfolio strategy")
        print("\n💡 Pro Tips:")
        print("• Check ex-dividend dates before buying")
        print("• Diversify across sectors and market caps")
        print("• Monitor payout ratios for sustainability")
        print("• Consider tax implications of dividend income")

    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
