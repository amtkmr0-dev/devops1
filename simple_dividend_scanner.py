
import streamlit as st
import pandas as pd

from src.data.dividend_news_scanner import IndianDividendNewsScanner
from src.data.moneycontrol_dividend_scraper import fetch_dividends_moneycontrol, FILTERS


def main():
    st.set_page_config(page_title="Dividend Screen - India", layout="wide")
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {padding-top: 2rem;}
        .stApp {background-color: #f7f9fb;}
        .div-header {
            font-size: 2.2rem;
            font-weight: 700;
            color: #222;
            margin-bottom: 0.5rem;
            margin-top: 0.5rem;
            text-align: left;
        }
        .div-sub {
            font-size: 1.1rem;
            color: #666;
            margin-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="div-header">Dividend Screen</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="div-sub">Find upcoming and recently announced dividend-paying stocks. Search by stock name or filter for opportunities.</div>', unsafe_allow_html=True)

    # --- Controls ---
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        data_source = st.selectbox(
            "Data Source", ["Moneycontrol (CSV)", "Screener/Other"], index=0)
    with col2:
        search = st.text_input("Search by Stock Name", "", key="search")
    with col3:
        if data_source == "Moneycontrol (CSV)":
            csv_filter = st.selectbox(
                "Show", ["Upcoming", "This Week", "Next Week"], index=0, key="csv_filter")
        else:
            filter_type = st.selectbox(
                "Show", ["Upcoming", "Recently Announced", "All"], index=0, key="other_filter")

    # --- Data ---
    if data_source == "Moneycontrol (CSV)":
        # Load the selected CSV file
        csv_map = {
            "Upcoming": "Upcoming.csv",
            "This Week": "ThisWeek.csv",
            "Next Week": "NextWeek.csv"
        }
        csv_file = csv_map[csv_filter]
        try:
            df = pd.read_csv(csv_file)
            if search:
                df = df[df['Stock Name'].str.contains(
                    search, case=False, na=False)]
            st.markdown("---")
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to load {csv_file}: {e}")
    else:
        scanner = IndianDividendNewsScanner()
        data = scanner.scan_all()
        df = pd.DataFrame(data)
        if search:
            df = df[df['company'].str.contains(
                search, case=False, na=False) | df['symbol'].str.contains(search, case=False, na=False)]
        if filter_type == "Upcoming":
            df = df[df['announcement_date'] >=
                    pd.Timestamp.today().strftime('%Y-%m-%d')]
        elif filter_type == "Recently Announced":
            df = df[(pd.to_datetime(df['announcement_date'], errors='coerce') >= (
                pd.Timestamp.today() - pd.Timedelta(days=30)))]
        st.markdown("---")
        if not df.empty:
            st.dataframe(df[['symbol', 'company', 'title', 'announcement_date', 'ex_date', 'link']].sort_values(
                'announcement_date', ascending=False), use_container_width=True)
        else:
            st.info("No dividend announcements found for your filters.")


if __name__ == "__main__":
    main()
