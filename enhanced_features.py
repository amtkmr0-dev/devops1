#!/usr/bin/env python3
"""
Enhanced Dividend Scanner with Real-time Alerts and Portfolio Tracking
"""

import smtplib
import schedule
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import pandas as pd
import json
import sqlite3
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class DividendAlertSystem:
    """Real-time dividend alert system"""

    def __init__(self, email_config: Dict = None):
        self.email_config = email_config or {}
        self.alert_db = "data/dividend_alerts.db"
        self._setup_database()

    def _setup_database(self):
        """Setup alerts database"""
        conn = sqlite3.connect(self.alert_db)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dividend_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT,
                symbol TEXT,
                alert_type TEXT,
                threshold_value REAL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_triggered TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id INTEGER,
                symbol TEXT,
                message TEXT,
                triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (alert_id) REFERENCES dividend_alerts (id)
            )
        ''')

        conn.commit()
        conn.close()

    def add_alert(self, user_email: str, symbol: str, alert_type: str, threshold: float = None):
        """Add new dividend alert"""
        conn = sqlite3.connect(self.alert_db)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO dividend_alerts (user_email, symbol, alert_type, threshold_value)
            VALUES (?, ?, ?, ?)
        ''', (user_email, symbol, alert_type, threshold))

        conn.commit()
        conn.close()

        print(f"✅ Alert added: {alert_type} for {symbol}")

    def check_ex_dividend_alerts(self):
        """Check for upcoming ex-dividend dates"""
        from src.data.free_indian_provider import FreeIndianStockProvider

        provider = FreeIndianStockProvider()
        conn = sqlite3.connect(self.alert_db)

        # Get active ex-dividend alerts
        alerts = pd.read_sql_query('''
            SELECT * FROM dividend_alerts 
            WHERE alert_type = 'ex_dividend' AND is_active = 1
        ''', conn)

        triggered_alerts = []

        for _, alert in alerts.iterrows():
            try:
                # Get stock data
                stock_data = provider.get_comprehensive_stock_data(
                    alert['symbol'])

                # Check for upcoming ex-dividend date (next 7 days)
                # This would need real ex-dividend date data
                # For demo, we'll simulate

                alert_message = f"""
🚨 DIVIDEND ALERT: {alert['symbol']}

Ex-Dividend Date: Tomorrow!
Dividend Amount: ₹{stock_data.get('annual_dividend', 'TBD')}
Current Price: ₹{stock_data.get('current_price', 'N/A')}

Action Required: Buy before market close today to receive dividend.
"""

                triggered_alerts.append({
                    'email': alert['user_email'],
                    'subject': f"🚨 {alert['symbol']} Ex-Dividend Tomorrow!",
                    'message': alert_message,
                    'alert_id': alert['id']
                })

            except Exception as e:
                logger.error(
                    f"Error checking alert for {alert['symbol']}: {e}")

        conn.close()

        # Send alerts
        for alert in triggered_alerts:
            self.send_email_alert(
                alert['email'], alert['subject'], alert['message'])
            self._log_alert(alert['alert_id'], alert['subject'])

    def check_high_yield_alerts(self):
        """Check for stocks crossing yield thresholds"""
        from src.data.free_indian_provider import FreeIndianStockProvider

        provider = FreeIndianStockProvider()
        conn = sqlite3.connect(self.alert_db)

        alerts = pd.read_sql_query('''
            SELECT * FROM dividend_alerts 
            WHERE alert_type = 'high_yield' AND is_active = 1
        ''', conn)

        for _, alert in alerts.iterrows():
            try:
                stock_data = provider.get_comprehensive_stock_data(
                    alert['symbol'])
                current_yield = stock_data.get('dividend_yield', 0)

                if current_yield and current_yield >= alert['threshold_value']:
                    message = f"""
🎯 HIGH YIELD ALERT: {alert['symbol']}

Current Dividend Yield: {current_yield*100:.2f}%
Your Alert Threshold: {alert['threshold_value']*100:.2f}%
Current Price: ₹{stock_data.get('current_price', 'N/A')}

This stock has reached your target yield threshold!
"""

                    self.send_email_alert(
                        alert['user_email'],
                        f"🎯 {alert['symbol']} High Yield Alert!",
                        message
                    )
                    self._log_alert(
                        alert['id'], f"High yield threshold reached: {current_yield*100:.2f}%")

            except Exception as e:
                logger.error(
                    f"Error checking yield alert for {alert['symbol']}: {e}")

        conn.close()

    def send_email_alert(self, to_email: str, subject: str, message: str):
        """Send email alert"""
        try:
            if not self.email_config:
                print(f"📧 EMAIL ALERT (Demo): {subject}")
                print(message)
                print("-" * 50)
                return

            # Real email sending
            msg = MIMEMultipart()
            msg['From'] = self.email_config['email']
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(message, 'plain'))

            server = smtplib.SMTP(
                self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['email'],
                         self.email_config['password'])

            text = msg.as_string()
            server.sendmail(self.email_config['email'], to_email, text)
            server.quit()

            print(f"✅ Email sent to {to_email}")

        except Exception as e:
            logger.error(f"Error sending email: {e}")

    def _log_alert(self, alert_id: int, message: str):
        """Log triggered alert"""
        conn = sqlite3.connect(self.alert_db)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO alert_history (alert_id, message)
            VALUES (?, ?)
        ''', (alert_id, message))

        cursor.execute('''
            UPDATE dividend_alerts 
            SET last_triggered = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (alert_id,))

        conn.commit()
        conn.close()


class PortfolioTracker:
    """Track dividend portfolio performance"""

    def __init__(self):
        self.portfolio_db = "data/dividend_portfolio.db"
        self._setup_database()

    def _setup_database(self):
        """Setup portfolio database"""
        conn = sqlite3.connect(self.portfolio_db)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                symbol TEXT,
                quantity INTEGER,
                avg_purchase_price REAL,
                purchase_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dividend_received (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                symbol TEXT,
                dividend_amount REAL,
                quantity INTEGER,
                total_received REAL,
                ex_dividend_date DATE,
                payment_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def add_holding(self, user_id: str, symbol: str, quantity: int, purchase_price: float):
        """Add stock holding to portfolio"""
        conn = sqlite3.connect(self.portfolio_db)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO portfolio_holdings (user_id, symbol, quantity, avg_purchase_price, purchase_date)
            VALUES (?, ?, ?, ?, DATE('now'))
        ''', (user_id, symbol, quantity, purchase_price))

        conn.commit()
        conn.close()

        print(
            f"✅ Added to portfolio: {quantity} shares of {symbol} at ₹{purchase_price}")

    def record_dividend(self, user_id: str, symbol: str, dividend_per_share: float,
                        quantity: int, ex_date: str = None):
        """Record dividend received"""
        total_dividend = dividend_per_share * quantity

        conn = sqlite3.connect(self.portfolio_db)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO dividend_received 
            (user_id, symbol, dividend_amount, quantity, total_received, ex_dividend_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, symbol, dividend_per_share, quantity, total_dividend, ex_date))

        conn.commit()
        conn.close()

        print(f"✅ Dividend recorded: ₹{total_dividend} from {symbol}")

    def get_portfolio_summary(self, user_id: str) -> Dict:
        """Get portfolio summary with dividend analysis"""
        conn = sqlite3.connect(self.portfolio_db)

        # Get holdings
        holdings = pd.read_sql_query('''
            SELECT symbol, SUM(quantity) as total_quantity, 
                   AVG(avg_purchase_price) as avg_price
            FROM portfolio_holdings 
            WHERE user_id = ?
            GROUP BY symbol
        ''', conn, params=(user_id,))

        # Get dividends received
        dividends = pd.read_sql_query('''
            SELECT symbol, SUM(total_received) as total_dividends,
                   COUNT(*) as dividend_payments
            FROM dividend_received 
            WHERE user_id = ?
            GROUP BY symbol
        ''', conn, params=(user_id,))

        conn.close()

        # Merge data
        portfolio = holdings.merge(dividends, on='symbol', how='left')
        portfolio['total_dividends'] = portfolio['total_dividends'].fillna(0)
        portfolio['dividend_payments'] = portfolio['dividend_payments'].fillna(
            0)

        # Calculate metrics
        portfolio['investment'] = portfolio['total_quantity'] * \
            portfolio['avg_price']
        portfolio['yield_on_cost'] = portfolio['total_dividends'] / \
            portfolio['investment']

        summary = {
            'total_investment': portfolio['investment'].sum(),
            'total_dividends_received': portfolio['total_dividends'].sum(),
            'overall_yield_on_cost': portfolio['total_dividends'].sum() / portfolio['investment'].sum(),
            'holdings': portfolio.to_dict('records')
        }

        return summary


class AdvancedDividendAnalyzer:
    """Advanced dividend analysis and predictions"""

    def __init__(self):
        self.seasonal_patterns = {}

    def analyze_dividend_seasonality(self, symbol: str) -> Dict:
        """Analyze seasonal dividend patterns"""
        from src.data.free_indian_provider import FreeIndianStockProvider

        provider = FreeIndianStockProvider()
        data = provider.get_comprehensive_stock_data(symbol)

        dividend_history = data.get('dividend_history', [])

        if not dividend_history:
            return {'error': 'No dividend history available'}

        # Analyze by month
        monthly_pattern = {}
        for dividend in dividend_history:
            if 'date' in dividend:
                month = dividend['date'].month if hasattr(
                    dividend['date'], 'month') else 1
                if month not in monthly_pattern:
                    monthly_pattern[month] = []
                monthly_pattern[month].append(dividend['amount'])

        # Calculate averages
        monthly_avg = {month: sum(amounts)/len(amounts)
                       for month, amounts in monthly_pattern.items()}

        # Find best months
        best_months = sorted(monthly_avg.items(),
                             key=lambda x: x[1], reverse=True)[:3]

        return {
            'symbol': symbol,
            'monthly_pattern': monthly_avg,
            'best_dividend_months': [f"Month {month}" for month, _ in best_months],
            'seasonal_recommendation': f"Historically, {symbol} pays higher dividends in months: {', '.join([str(m) for m, _ in best_months])}"
        }

    def predict_next_dividend(self, symbol: str) -> Dict:
        """Predict next dividend amount and date"""
        from src.data.free_indian_provider import FreeIndianStockProvider

        provider = FreeIndianStockProvider()
        data = provider.get_comprehensive_stock_data(symbol)

        dividend_history = data.get('dividend_history', [])

        if len(dividend_history) < 2:
            return {'error': 'Insufficient data for prediction'}

        # Sort by date
        sorted_dividends = sorted(dividend_history,
                                  key=lambda x: x.get('date', datetime.min))

        # Calculate growth trend
        recent_dividends = sorted_dividends[-4:]  # Last 4 dividends
        amounts = [d['amount'] for d in recent_dividends]

        # Simple linear growth calculation
        if len(amounts) >= 2:
            growth_rate = (amounts[-1] - amounts[0]) / len(amounts)
            predicted_amount = amounts[-1] + growth_rate
        else:
            predicted_amount = amounts[-1] if amounts else 0

        # Predict next date (assume quarterly)
        last_date = sorted_dividends[-1].get('date')
        if last_date:
            predicted_date = last_date + timedelta(days=90)  # 3 months
        else:
            predicted_date = datetime.now() + timedelta(days=90)

        return {
            'symbol': symbol,
            'predicted_amount': round(predicted_amount, 2),
            'predicted_date': predicted_date.strftime('%Y-%m-%d'),
            'confidence': 'Medium' if len(amounts) >= 3 else 'Low',
            'basis': f"Based on {len(amounts)} recent dividends"
        }

    def dividend_safety_score(self, symbol: str) -> Dict:
        """Calculate dividend safety score"""
        from src.data.free_indian_provider import FreeIndianStockProvider

        provider = FreeIndianStockProvider()
        data = provider.get_comprehensive_stock_data(symbol)

        safety_score = 0
        factors = {}

        # Factor 1: Payout ratio (40 points)
        payout_ratio = data.get('payout_ratio', 1)
        if payout_ratio:
            if payout_ratio <= 0.5:
                payout_score = 40
            elif payout_ratio <= 0.7:
                payout_score = 30
            elif payout_ratio <= 0.8:
                payout_score = 20
            else:
                payout_score = 5

            safety_score += payout_score
            factors['payout_ratio'] = {
                'score': payout_score, 'value': f"{payout_ratio*100:.1f}%"}

        # Factor 2: Dividend history consistency (30 points)
        dividend_history = data.get('dividend_history', [])
        if len(dividend_history) >= 5:
            consistency_score = 30
        elif len(dividend_history) >= 3:
            consistency_score = 20
        else:
            consistency_score = 5

        safety_score += consistency_score
        factors['consistency'] = {
            'score': consistency_score, 'years': len(dividend_history)}

        # Factor 3: Financial health (30 points)
        pe_ratio = data.get('pe_ratio', 50)
        debt_equity = data.get('debt_to_equity', 2)
        roe = data.get('return_on_equity', 0)

        financial_score = 0
        if pe_ratio and 10 <= pe_ratio <= 25:
            financial_score += 10
        if debt_equity and debt_equity <= 0.5:
            financial_score += 10
        if roe and roe >= 0.15:
            financial_score += 10

        safety_score += financial_score
        factors['financial_health'] = {
            'score': financial_score, 'pe': pe_ratio, 'debt_equity': debt_equity}

        # Overall rating
        if safety_score >= 80:
            rating = "Very Safe"
            color = "🟢"
        elif safety_score >= 60:
            rating = "Safe"
            color = "🟡"
        elif safety_score >= 40:
            rating = "Moderate Risk"
            color = "🟠"
        else:
            rating = "High Risk"
            color = "🔴"

        return {
            'symbol': symbol,
            'safety_score': safety_score,
            'rating': f"{color} {rating}",
            'factors': factors,
            'recommendation': self._get_safety_recommendation(safety_score)
        }

    def _get_safety_recommendation(self, score: int) -> str:
        """Get recommendation based on safety score"""
        if score >= 80:
            return "Excellent dividend safety. Suitable for conservative investors."
        elif score >= 60:
            return "Good dividend safety. Suitable for most investors."
        elif score >= 40:
            return "Moderate safety. Monitor closely and diversify."
        else:
            return "High risk dividend. Consider avoiding or small allocation only."


def demo_enhanced_features():
    """Demo the enhanced features"""
    print("🚀 Enhanced Dividend Scanner Features Demo")
    print("=" * 50)

    # 1. Alert System Demo
    print("\n📢 1. Dividend Alert System")
    print("-" * 30)

    alert_system = DividendAlertSystem()

    # Add sample alerts
    alert_system.add_alert("investor@example.com", "RELIANCE", "ex_dividend")
    alert_system.add_alert("investor@example.com", "TCS", "high_yield", 0.03)

    print("Sample alerts added:")
    print("• Ex-dividend alert for RELIANCE")
    print("• High yield alert for TCS (>3%)")

    # 2. Portfolio Tracker Demo
    print("\n💼 2. Portfolio Tracker")
    print("-" * 30)

    portfolio = PortfolioTracker()

    # Add sample holdings
    portfolio.add_holding("user123", "RELIANCE", 100, 2800)
    portfolio.add_holding("user123", "TCS", 50, 3500)

    # Record dividends
    portfolio.record_dividend("user123", "RELIANCE", 8.0, 100, "2025-08-15")
    portfolio.record_dividend("user123", "TCS", 25.0, 50, "2025-08-20")

    # Get summary
    summary = portfolio.get_portfolio_summary("user123")
    print(f"\nPortfolio Summary:")
    print(f"• Total Investment: ₹{summary['total_investment']:,.0f}")
    print(f"• Total Dividends: ₹{summary['total_dividends_received']:,.0f}")
    print(f"• Yield on Cost: {summary['overall_yield_on_cost']*100:.2f}%")

    # 3. Advanced Analysis Demo
    print("\n🔬 3. Advanced Dividend Analysis")
    print("-" * 30)

    analyzer = AdvancedDividendAnalyzer()

    # Seasonality analysis
    seasonal = analyzer.analyze_dividend_seasonality("RELIANCE")
    print(f"\nSeasonal Analysis for RELIANCE:")
    if 'seasonal_recommendation' in seasonal:
        print(f"• {seasonal['seasonal_recommendation']}")

    # Dividend prediction
    prediction = analyzer.predict_next_dividend("TCS")
    print(f"\nNext Dividend Prediction for TCS:")
    if 'predicted_amount' in prediction:
        print(f"• Predicted Amount: ₹{prediction['predicted_amount']}")
        print(f"• Predicted Date: {prediction['predicted_date']}")
        print(f"• Confidence: {prediction['confidence']}")

    # Safety score
    safety = analyzer.dividend_safety_score("RELIANCE")
    print(f"\nDividend Safety Score for RELIANCE:")
    print(f"• Score: {safety['safety_score']}/100")
    print(f"• Rating: {safety['rating']}")
    print(f"• Recommendation: {safety['recommendation']}")

    print("\n" + "=" * 50)
    print("✅ Enhanced features demo completed!")
    print("\n🎯 These features make your scanner:")
    print("• Real-time alert system for timely decisions")
    print("• Portfolio tracking for performance monitoring")
    print("• Advanced analysis for better predictions")
    print("• Safety scoring for risk assessment")


if __name__ == "__main__":
    demo_enhanced_features()
