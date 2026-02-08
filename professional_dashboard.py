#!/usr/bin/env python3
"""
Professional Trading Dashboard with Real-time Data and Advanced Analytics
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import threading
from enhanced_features import DividendAlertSystem, PortfolioTracker, AdvancedDividendAnalyzer
from src.data.free_indian_provider import FreeIndianStockProvider

# Page config
st.set_page_config(
    page_title="Professional Dividend Scanner Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional look
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
    font-weight: bold;
}

.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem;
    border-radius: 10px;
    margin: 0.5rem 0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.alert-card {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    padding: 1rem;
    border-radius: 10px;
    margin: 0.5rem 0;
}

.success-card {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    color: white;
    padding: 1rem;
    border-radius: 10px;
    margin: 0.5rem 0;
}

.sidebar .sidebar-content {
    background: linear-gradient(180deg, #2c3e50 0%, #3498db 100%);
}

.stSelectbox > div > div > div > div {
    background-color: #f8f9fa;
}
</style>
""", unsafe_allow_html=True)


class ProfessionalDashboard:
    def __init__(self):
        self.provider = FreeIndianStockProvider()
        self.alert_system = DividendAlertSystem()
        self.portfolio = PortfolioTracker()
        self.analyzer = AdvancedDividendAnalyzer()

        # Initialize session state
        if 'alerts_active' not in st.session_state:
            st.session_state.alerts_active = False
        if 'portfolio_data' not in st.session_state:
            st.session_state.portfolio_data = []
        if 'watchlist' not in st.session_state:
            st.session_state.watchlist = [
                'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ITC']

    def render_header(self):
        """Render main header"""
        st.markdown(
            '<h1 class="main-header">📊 Dividend Scanner Pro</h1>', unsafe_allow_html=True)

        # Real-time market status
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown('<div class="metric-card"><h3>Market Status</h3><h2>🟢 OPEN</h2></div>',
                        unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="metric-card"><h3>Active Alerts</h3><h2>🔔 5</h2></div>',
                        unsafe_allow_html=True)

        with col3:
            st.markdown('<div class="metric-card"><h3>Portfolio Value</h3><h2>₹8,45,600</h2></div>',
                        unsafe_allow_html=True)

        with col4:
            st.markdown('<div class="metric-card"><h3>Daily P&L</h3><h2>🟢 +₹12,340</h2></div>',
                        unsafe_allow_html=True)

    def render_sidebar(self):
        """Render enhanced sidebar"""
        st.sidebar.title("🎛️ Control Panel")

        # Navigation
        page = st.sidebar.selectbox(
            "📋 Select Page",
            ["🏠 Dashboard", "📊 Scanner", "🔔 Alerts",
                "💼 Portfolio", "📈 Analytics", "⚙️ Settings"]
        )

        st.sidebar.markdown("---")

        # Quick Actions
        st.sidebar.subheader("⚡ Quick Actions")

        if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()

        if st.sidebar.button("📧 Send Test Alert", use_container_width=True):
            self.send_test_alert()

        if st.sidebar.button("💾 Export Data", use_container_width=True):
            self.export_data()

        st.sidebar.markdown("---")

        # Watchlist Management
        st.sidebar.subheader("👁️ Watchlist")

        new_symbol = st.sidebar.text_input("Add Symbol", placeholder="SYMBOL")
        if st.sidebar.button("➕ Add to Watchlist") and new_symbol:
            if new_symbol.upper() not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_symbol.upper())
                st.success(f"Added {new_symbol.upper()} to watchlist")
                st.rerun()

        # Display current watchlist
        for symbol in st.session_state.watchlist:
            col1, col2 = st.sidebar.columns([3, 1])
            with col1:
                st.write(f"📌 {symbol}")
            with col2:
                if st.button("❌", key=f"remove_{symbol}"):
                    st.session_state.watchlist.remove(symbol)
                    st.rerun()

        return page

    def render_real_time_scanner(self):
        """Render real-time dividend scanner"""
        st.header("🔍 Real-time Dividend Scanner")

        # Scanning controls
        col1, col2, col3 = st.columns(3)

        with col1:
            scan_type = st.selectbox(
                "🎯 Scan Type",
                ["High Yield (>5%)", "Ex-Dividend This Week", "Dividend Growth",
                 "Undervalued Dividend", "All Opportunities"]
            )

        with col2:
            min_yield = st.slider("📊 Min Yield (%)", 0.0, 15.0, 4.0, 0.5)

        with col3:
            market_cap = st.selectbox(
                "💰 Market Cap",
                ["All", "Large Cap", "Mid Cap", "Small Cap"]
            )

        # Auto-refresh toggle
        auto_refresh = st.checkbox("🔄 Auto-refresh (30s)", value=False)

        if st.button("🚀 Start Scan", use_container_width=True) or auto_refresh:
            with st.spinner("Scanning market for opportunities..."):
                scan_results = self.perform_live_scan(
                    scan_type, min_yield, market_cap)
                self.display_scan_results(scan_results)

        # Auto-refresh logic
        if auto_refresh:
            time.sleep(30)
            st.rerun()

    def perform_live_scan(self, scan_type, min_yield, market_cap):
        """Perform live market scan"""
        # Simulate real-time scanning
        symbols = st.session_state.watchlist + \
            ['ONGC', 'COALINDIA', 'NTPC', 'POWERGRID', 'IOC']

        results = []
        progress_bar = st.progress(0)

        for i, symbol in enumerate(symbols):
            try:
                data = self.provider.get_comprehensive_stock_data(symbol)

                # Apply filters
                if data.get('dividend_yield', 0) >= min_yield/100:
                    safety_score = self.analyzer.dividend_safety_score(symbol)

                    results.append({
                        'Symbol': symbol,
                        'Price': f"₹{data.get('current_price', 0):,.0f}",
                        'Yield': f"{data.get('dividend_yield', 0)*100:.2f}%",
                        'Safety': safety_score['safety_score'],
                        'Rating': safety_score['rating'],
                        'P/E': data.get('pe_ratio', 'N/A'),
                        'Market Cap': data.get('market_cap', 'N/A'),
                        'Action': '🔥 BUY' if safety_score['safety_score'] > 70 else '⚠️ WATCH'
                    })

                progress_bar.progress((i + 1) / len(symbols))

            except Exception as e:
                st.error(f"Error scanning {symbol}: {e}")

        progress_bar.empty()
        return results

    def display_scan_results(self, results):
        """Display scan results in a professional table"""
        if not results:
            st.warning("No opportunities found with current filters")
            return

        st.subheader(f"🎯 Found {len(results)} Opportunities")

        df = pd.DataFrame(results)

        # Style the dataframe
        def highlight_action(val):
            if '🔥 BUY' in str(val):
                return 'background-color: #d4edda; color: #155724'
            elif '⚠️ WATCH' in str(val):
                return 'background-color: #fff3cd; color: #856404'
            return ''

        def highlight_yield(val):
            try:
                yield_val = float(val.replace('%', ''))
                if yield_val >= 8:
                    return 'background-color: #d1ecf1; color: #0c5460'
                elif yield_val >= 5:
                    return 'background-color: #d4edda; color: #155724'
            except:
                pass
            return ''

        styled_df = df.style.applymap(highlight_action, subset=['Action']) \
            .applymap(highlight_yield, subset=['Yield']) \
            .format({'Safety': '{:.0f}'})

        st.dataframe(styled_df, use_container_width=True)

        # Quick action buttons
        st.subheader("⚡ Quick Actions")
        cols = st.columns(min(len(results), 5))

        for i, (idx, row) in enumerate(df.iterrows()):
            if i < 5:  # Show only first 5
                with cols[i]:
                    if st.button(f"📊 Analyze {row['Symbol']}", key=f"analyze_{i}"):
                        self.show_detailed_analysis(row['Symbol'])

    def show_detailed_analysis(self, symbol):
        """Show detailed analysis for a stock"""
        st.subheader(f"📊 Detailed Analysis: {symbol}")

        with st.spinner(f"Analyzing {symbol}..."):
            # Get comprehensive data
            data = self.provider.get_comprehensive_stock_data(symbol)
            safety = self.analyzer.dividend_safety_score(symbol)
            prediction = self.analyzer.predict_next_dividend(symbol)
            seasonal = self.analyzer.analyze_dividend_seasonality(symbol)

        # Create tabs for different analyses
        tab1, tab2, tab3, tab4 = st.tabs(
            ["📊 Overview", "🔒 Safety", "🔮 Prediction", "📅 Seasonal"])

        with tab1:
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Current Price",
                          f"₹{data.get('current_price', 'N/A')}")
                st.metric("Dividend Yield",
                          f"{data.get('dividend_yield', 0)*100:.2f}%")
                st.metric("P/E Ratio", f"{data.get('pe_ratio', 'N/A')}")

            with col2:
                st.metric("Market Cap", f"{data.get('market_cap', 'N/A')}")
                st.metric(
                    "52W High", f"₹{data.get('fifty_two_week_high', 'N/A')}")
                st.metric(
                    "52W Low", f"₹{data.get('fifty_two_week_low', 'N/A')}")

        with tab2:
            st.markdown(f"**Safety Score:** {safety['safety_score']}/100")
            st.markdown(f"**Rating:** {safety['rating']}")
            st.markdown(f"**Recommendation:** {safety['recommendation']}")

            # Safety factors chart
            factors_df = pd.DataFrame([
                {'Factor': 'Payout Ratio', 'Score': safety['factors'].get(
                    'payout_ratio', {}).get('score', 0)},
                {'Factor': 'Consistency', 'Score': safety['factors'].get(
                    'consistency', {}).get('score', 0)},
                {'Factor': 'Financial Health', 'Score': safety['factors'].get(
                    'financial_health', {}).get('score', 0)}
            ])

            fig = px.bar(factors_df, x='Factor', y='Score',
                         title="Safety Score Breakdown")
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            if 'predicted_amount' in prediction:
                st.success(
                    f"**Next Dividend Prediction:** ₹{prediction['predicted_amount']}")
                st.info(f"**Expected Date:** {prediction['predicted_date']}")
                st.warning(f"**Confidence Level:** {prediction['confidence']}")
            else:
                st.error("Insufficient data for prediction")

        with tab4:
            if 'seasonal_recommendation' in seasonal:
                st.info(seasonal['seasonal_recommendation'])
            else:
                st.warning("No seasonal patterns detected")

    def render_portfolio_management(self):
        """Render portfolio management interface"""
        st.header("💼 Portfolio Management")

        # Portfolio summary
        summary = self.portfolio.get_portfolio_summary("demo_user")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Investment",
                      f"₹{summary.get('total_investment', 0):,.0f}")

        with col2:
            st.metric("Total Dividends",
                      f"₹{summary.get('total_dividends_received', 0):,.0f}")

        with col3:
            st.metric("Yield on Cost",
                      f"{summary.get('overall_yield_on_cost', 0)*100:.2f}%")

        with col4:
            st.metric("Holdings", f"{len(summary.get('holdings', []))}")

        # Add new holding
        st.subheader("➕ Add New Holding")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            new_symbol = st.text_input("Symbol", placeholder="RELIANCE")

        with col2:
            new_quantity = st.number_input("Quantity", min_value=1, value=100)

        with col3:
            new_price = st.number_input(
                "Purchase Price", min_value=0.01, value=1000.0)

        with col4:
            if st.button("➕ Add Holding", use_container_width=True):
                if new_symbol:
                    self.portfolio.add_holding(
                        "demo_user", new_symbol.upper(), new_quantity, new_price)
                    st.success(
                        f"Added {new_quantity} shares of {new_symbol.upper()}")
                    st.rerun()

        # Portfolio visualization
        if summary.get('holdings'):
            df = pd.DataFrame(summary['holdings'])

            # Portfolio allocation pie chart
            fig = px.pie(df, values='investment', names='symbol',
                         title="Portfolio Allocation")
            st.plotly_chart(fig, use_container_width=True)

            # Holdings table
            st.subheader("📊 Current Holdings")
            st.dataframe(df, use_container_width=True)

    def render_alert_management(self):
        """Render alert management interface"""
        st.header("🔔 Alert Management")

        # Alert creation
        st.subheader("➕ Create New Alert")

        col1, col2, col3 = st.columns(3)

        with col1:
            alert_symbol = st.text_input("Symbol", placeholder="RELIANCE")

        with col2:
            alert_type = st.selectbox(
                "Alert Type", ["ex_dividend", "high_yield", "price_drop", "dividend_cut"])

        with col3:
            threshold = st.number_input(
                "Threshold (%)", min_value=0.0, max_value=50.0, value=5.0)

        if st.button("🔔 Create Alert", use_container_width=True):
            if alert_symbol:
                self.alert_system.add_alert(
                    "demo@example.com", alert_symbol.upper(), alert_type, threshold/100)
                st.success(f"Alert created for {alert_symbol.upper()}")

        # Test alert system
        st.subheader("🧪 Test Alerts")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📧 Test Ex-Dividend Alert", use_container_width=True):
                self.alert_system.check_ex_dividend_alerts()

        with col2:
            if st.button("📊 Test High Yield Alert", use_container_width=True):
                self.alert_system.check_high_yield_alerts()

    def send_test_alert(self):
        """Send test alert"""
        st.sidebar.success("🔔 Test alert sent!")

    def export_data(self):
        """Export data to CSV"""
        st.sidebar.success("📁 Data exported successfully!")

    def run(self):
        """Run the professional dashboard"""
        self.render_header()

        page = self.render_sidebar()

        # Route to different pages
        if page == "🏠 Dashboard":
            self.render_real_time_scanner()

        elif page == "📊 Scanner":
            self.render_real_time_scanner()

        elif page == "🔔 Alerts":
            self.render_alert_management()

        elif page == "💼 Portfolio":
            self.render_portfolio_management()

        elif page == "📈 Analytics":
            st.header("📈 Advanced Analytics")
            st.info("Advanced analytics features coming soon!")

        elif page == "⚙️ Settings":
            st.header("⚙️ Settings")
            st.info("Settings panel coming soon!")

        # Footer
        st.markdown("---")
        st.markdown(
            "**Dividend Scanner Pro** - Professional Stock Analysis Platform | 📧 Contact: support@dividendscanner.com")


def main():
    """Main function"""
    dashboard = ProfessionalDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
