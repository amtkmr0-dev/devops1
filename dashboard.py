from src.scanner import DividendScanner, PreDefinedScans, ScanConfiguration, ScanFilter, ScanCriteria
from src.data import YFinanceProvider, DataPipeline, get_sp500_symbols
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))


# Page configuration
st.set_page_config(
    page_title="Dividend Scanner Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'data_pipeline' not in st.session_state:
    st.session_state.data_pipeline = DataPipeline([YFinanceProvider()])
    st.session_state.scanner = DividendScanner(st.session_state.data_pipeline)


def main():
    st.title("💰 Dividend Scanner Dashboard")
    st.markdown("---")

    # Sidebar
    st.sidebar.header("Scanner Configuration")

    # Scan type selection
    scan_type = st.sidebar.selectbox(
        "Select Scan Type",
        ["High Yield Stocks", "Dividend Aristocrats",
            "Safe Dividend Stocks", "Growth Dividend Stocks", "Custom Scan"]
    )

    # Symbol input
    symbol_input_method = st.sidebar.radio(
        "Symbol Selection",
        ["S&P 500 Sample", "Custom Symbols"]
    )

    symbols = []
    if symbol_input_method == "S&P 500 Sample":
        num_symbols = st.sidebar.slider(
            "Number of stocks to scan", 10, 100, 50)
        symbols = get_sp500_symbols()[:num_symbols]
    else:
        symbol_text = st.sidebar.text_area(
            "Enter symbols (comma-separated)",
            "AAPL, MSFT, JNJ, PG, KO"
        )
        symbols = [s.strip().upper()
                   for s in symbol_text.split(',') if s.strip()]

    # Custom scan configuration
    if scan_type == "Custom Scan":
        st.sidebar.subheader("Custom Filters")

        min_yield = st.sidebar.number_input(
            "Min Dividend Yield (%)", 0.0, 20.0, 1.0) / 100
        max_payout = st.sidebar.number_input(
            "Max Payout Ratio (%)", 0.0, 200.0, 80.0) / 100
        min_market_cap = st.sidebar.number_input(
            "Min Market Cap (Billions)", 0.0, 1000.0, 1.0) * 1e9
        min_years_growth = st.sidebar.number_input(
            "Min Years Dividend Growth", 0, 50, 0)

        custom_config = ScanConfiguration(
            name="Custom Scan",
            filters=[
                ScanFilter(ScanCriteria.MIN_DIVIDEND_YIELD, min_yield, "gte"),
                ScanFilter(ScanCriteria.MAX_PAYOUT_RATIO, max_payout, "lte"),
                ScanFilter(ScanCriteria.MIN_MARKET_CAP, min_market_cap, "gte"),
                ScanFilter(ScanCriteria.MIN_YEARS_DIVIDEND_GROWTH,
                           min_years_growth, "gte")
            ],
            sort_by="dividend_health_score",
            sort_order="desc"
        )

    # Run scan button
    if st.sidebar.button("🔍 Run Scan", type="primary"):
        run_scan(scan_type, symbols, custom_config if scan_type ==
                 "Custom Scan" else None)

    # Main content area
    if 'scan_results' in st.session_state and not st.session_state.scan_results.empty:
        display_results()
    else:
        display_welcome()


def run_scan(scan_type, symbols, custom_config=None):
    """Run the dividend scan"""
    with st.spinner(f"Scanning {len(symbols)} stocks..."):
        try:
            # Get scan configuration
            if custom_config:
                config = custom_config
            elif scan_type == "High Yield Stocks":
                config = PreDefinedScans.high_yield_scanner()
            elif scan_type == "Dividend Aristocrats":
                config = PreDefinedScans.dividend_aristocrats()
            elif scan_type == "Safe Dividend Stocks":
                config = PreDefinedScans.safe_dividend_stocks()
            elif scan_type == "Growth Dividend Stocks":
                config = PreDefinedScans.growth_dividend_stocks()
            else:
                config = PreDefinedScans.high_yield_scanner()

            # Run scan
            results = st.session_state.scanner.scan_stocks(symbols, config)

            # Store results
            st.session_state.scan_results = results
            st.session_state.scan_config = config
            st.session_state.scan_timestamp = datetime.now()

            if not results.empty:
                st.success(
                    f"Scan completed! Found {len(results)} stocks matching criteria.")
            else:
                st.warning("No stocks found matching the specified criteria.")

        except Exception as e:
            st.error(f"Error running scan: {str(e)}")


def display_results():
    """Display scan results"""
    results = st.session_state.scan_results
    config = st.session_state.scan_config

    # Header
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Stocks Found", len(results))
    with col2:
        avg_yield = results['dividend_yield'].mean(
        ) * 100 if 'dividend_yield' in results.columns else 0
        st.metric("Avg Dividend Yield", f"{avg_yield:.2f}%")
    with col3:
        avg_health = results['dividend_health_score'].mean(
        ) if 'dividend_health_score' in results.columns else 0
        st.metric("Avg Health Score", f"{avg_health:.1f}")

    st.markdown("---")

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Results Table", "📈 Charts", "🎯 Top Picks", "📥 Export"])

    with tab1:
        display_results_table(results)

    with tab2:
        display_charts(results)

    with tab3:
        display_top_picks(results)

    with tab4:
        display_export_options(results)


def display_results_table(results):
    """Display results in a table"""
    st.subheader("Scan Results")

    # Format the dataframe for display
    display_df = results.copy()

    # Format numeric columns
    if 'dividend_yield' in display_df.columns:
        display_df['dividend_yield'] = display_df['dividend_yield'].apply(
            lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A")

    if 'payout_ratio' in display_df.columns:
        display_df['payout_ratio'] = display_df['payout_ratio'].apply(
            lambda x: f"{x*100:.1f}%" if pd.notna(x) else "N/A")

    if 'market_cap' in display_df.columns:
        display_df['market_cap'] = display_df['market_cap'].apply(
            lambda x: f"${x/1e9:.1f}B" if pd.notna(x) else "N/A")

    if 'current_price' in display_df.columns:
        display_df['current_price'] = display_df['current_price'].apply(
            lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")

    # Select columns to display
    columns_to_show = ['symbol', 'name', 'sector', 'current_price', 'dividend_yield',
                       'dividend_health_score', 'payout_ratio', 'market_cap']

    available_columns = [
        col for col in columns_to_show if col in display_df.columns]

    st.dataframe(
        display_df[available_columns],
        use_container_width=True,
        height=400
    )


def display_charts(results):
    """Display charts and visualizations"""
    st.subheader("Data Visualizations")

    if results.empty:
        st.info("No data available for charts")
        return

    col1, col2 = st.columns(2)

    with col1:
        # Dividend yield distribution
        if 'dividend_yield' in results.columns:
            fig = px.histogram(
                results,
                x='dividend_yield',
                title="Dividend Yield Distribution",
                nbins=20
            )
            fig.update_xaxis(title="Dividend Yield", tickformat=".1%")
            fig.update_yaxis(title="Number of Stocks")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Health score vs yield scatter
        if 'dividend_health_score' in results.columns and 'dividend_yield' in results.columns:
            fig = px.scatter(
                results,
                x='dividend_yield',
                y='dividend_health_score',
                hover_data=['symbol', 'name'],
                title="Health Score vs Dividend Yield"
            )
            fig.update_xaxis(title="Dividend Yield", tickformat=".1%")
            fig.update_yaxis(title="Health Score")
            st.plotly_chart(fig, use_container_width=True)

    # Sector analysis
    if 'sector' in results.columns:
        sector_stats = results.groupby('sector').agg({
            'dividend_yield': 'mean',
            'dividend_health_score': 'mean',
            'symbol': 'count'
        }).round(4)

        sector_stats.columns = ['Avg Yield', 'Avg Health Score', 'Count']
        sector_stats = sector_stats.sort_values('Avg Yield', ascending=False)

        fig = px.bar(
            x=sector_stats.index,
            y=sector_stats['Avg Yield'],
            title="Average Dividend Yield by Sector"
        )
        fig.update_xaxis(title="Sector")
        fig.update_yaxis(title="Average Dividend Yield", tickformat=".1%")
        st.plotly_chart(fig, use_container_width=True)


def display_top_picks(results):
    """Display top picks with detailed analysis"""
    st.subheader("🏆 Top Dividend Picks")

    if results.empty:
        st.info("No top picks available")
        return

    # Get top 5 by health score
    top_picks = results.nlargest(5, 'dividend_health_score')

    for idx, (_, stock) in enumerate(top_picks.iterrows()):
        with st.expander(f"#{idx+1} {stock['symbol']} - {stock['name']}", expanded=idx == 0):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Health Score",
                          f"{stock.get('dividend_health_score', 0):.1f}/100")
                st.metric("Dividend Yield",
                          f"{stock.get('dividend_yield', 0)*100:.2f}%")

            with col2:
                st.metric("Current Price",
                          f"${stock.get('current_price', 0):.2f}")
                st.metric("Payout Ratio",
                          f"{stock.get('payout_ratio', 0)*100:.1f}%")

            with col3:
                st.metric("Sector", stock.get('sector', 'N/A'))
                st.metric("Market Cap",
                          f"${stock.get('market_cap', 0)/1e9:.1f}B")


def display_export_options(results):
    """Display export options"""
    st.subheader("📥 Export Results")

    if results.empty:
        st.info("No data to export")
        return

    col1, col2 = st.columns(2)

    with col1:
        # CSV download
        csv = results.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name=f"dividend_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    with col2:
        # JSON download
        json_data = results.to_json(orient='records', date_format='iso')
        st.download_button(
            label="Download as JSON",
            data=json_data,
            file_name=f"dividend_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )


def display_welcome():
    """Display welcome screen"""
    st.markdown("""
    ## Welcome to Dividend Scanner! 💰
    
    This tool helps you discover and analyze dividend-paying stocks based on various criteria.
    
    ### Features:
    - 🔍 **Multiple Scan Types**: High yield, aristocrats, safe dividends, and growth stocks
    - 📊 **Health Score**: Proprietary algorithm to assess dividend sustainability
    - 📈 **Comprehensive Analysis**: Financial metrics, growth rates, and risk assessment
    - 🎯 **Custom Filters**: Create your own scanning criteria
    
    ### How to Use:
    1. Select a scan type from the sidebar
    2. Choose your symbols (S&P 500 sample or custom list)
    3. Configure filters (for custom scans)
    4. Click "Run Scan" to start analysis
    
    ### Scan Types:
    - **High Yield**: Stocks with dividend yield > 4%
    - **Dividend Aristocrats**: Companies with 25+ years of dividend increases
    - **Safe Dividends**: Conservative picks with sustainable dividends
    - **Growth Dividends**: Companies growing their dividends consistently
    
    Get started by configuring your scan in the sidebar! 👈
    """)


if __name__ == "__main__":
    main()
