# Download NSE equity symbol list and build a mapping for robust company name to symbol resolution
import requests
import csv
import os
from difflib import get_close_matches

NSE_SYMBOLS_CSV = 'nse_equity_list.csv'
NSE_SYMBOLS_URL = 'https://archives.nseindia.com/content/equities/EQUITY_L.csv'

# Download the CSV if not present
if not os.path.exists(NSE_SYMBOLS_CSV):
    print('Downloading NSE equity symbol list...')
    r = requests.get(NSE_SYMBOLS_URL)
    with open(NSE_SYMBOLS_CSV, 'wb') as f:
        f.write(r.content)

# Build mapping: company name (upper) -> symbol
company_to_symbol = {}
with open(NSE_SYMBOLS_CSV, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        name = row['NAME OF COMPANY'].strip().upper()
        symbol = row['SYMBOL'].strip().upper()
        company_to_symbol[name] = symbol


def resolve_nse_symbol(company_name):
    # Try exact match
    name = company_name.strip().upper()
    if name in company_to_symbol:
        return company_to_symbol[name]
    # Fuzzy match (top 1, cutoff 0.85)
    matches = get_close_matches(
        name, company_to_symbol.keys(), n=1, cutoff=0.85)
    if matches:
        return company_to_symbol[matches[0]]
    return None


if __name__ == '__main__':
    # Test
    for test_name in [
        'Akzo Nobel India Limited',
        'Starteck Finance Limited',
        'Sun TV Network Limited',
        'Tainwala Chemical and Plastic (I) Limited',
        'Reliance Industries Limited',
    ]:
        print(f"{test_name} -> {resolve_nse_symbol(test_name)}")
