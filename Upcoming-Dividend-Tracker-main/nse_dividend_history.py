import requests
from bs4 import BeautifulSoup
from datetime import datetime


def fetch_nse_dividend_history(symbol):
    """
    Fetch historical dividend data for a given NSE symbol from the official NSE corporate actions page.
    Returns a list of dicts with keys: 'announced_date', 'ex_date', 'dividend', 'remarks'.
    """
    url = f"https://www.nseindia.com/api/corporate-announcements?symbol={symbol}&category=DIVIDEND"
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
        'Referer': f'https://www.nseindia.com/get-quotes/equity?symbol={symbol}'
    }
    session = requests.Session()
    session.headers.update(headers)
    try:
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for item in data.get('data', []):
            if 'DIVIDEND' in item.get('subject', '').upper():
                remarks = item.get('subject', '')
                ex_date = item.get('exDate', '')
                announced_date = item.get('announcementDate', '')
                dividend = None
                # Try to extract dividend amount from remarks
                import re
                m = re.search(r'([Rr][Ss]?\.?\s?)([\d.]+)', remarks)
                if m:
                    dividend = m.group(2)
                results.append({
                    'announced_date': announced_date,
                    'ex_date': ex_date,
                    'dividend': dividend,
                    'remarks': remarks
                })
        if results:
            return results
        # If no results, fall through to HTML scrape
    except Exception as e:
        print(f"[ERROR] NSE API failed for {symbol}: {e}")

    # Fallback: HTML scrape from Moneycontrol dividend history page
    try:
        mc_url = f"https://www.moneycontrol.com/stocks/company_info/dividends.php?sc_id={symbol}&durationType=Y&sel_year=all"
        mc_headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': f'https://www.moneycontrol.com/india/stockpricequote/{symbol}'
        }
        mc_resp = session.get(mc_url, headers=mc_headers, timeout=10)
        mc_resp.raise_for_status()
        soup = BeautifulSoup(mc_resp.text, 'html.parser')
        table = soup.find('table', attrs={'class': 'dividend_table'})
        results = []
        if table:
            rows = table.find_all('tr')
            for row in rows[1:]:
                cols = [td.get_text(strip=True) for td in row.find_all('td')]
                if len(cols) >= 4:
                    results.append({
                        'announced_date': cols[0],
                        'ex_date': cols[1],
                        'dividend': cols[2],
                        'remarks': cols[3]
                    })
        return results
    except Exception as e:
        print(f"[ERROR] Moneycontrol HTML scrape failed for {symbol}: {e}")
        return []
