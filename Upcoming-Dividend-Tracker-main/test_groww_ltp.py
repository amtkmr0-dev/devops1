# Test script to check Groww LTP fetch


# Approach 1: Use direct access token (recommended by Groww docs)
from growwapi import GrowwAPI


# Import the access token from config
from groww_config import GROWW_API_KEY as API_AUTH_TOKEN

try:
    growwapi = GrowwAPI(API_AUTH_TOKEN)
    # Fetch LTP for RELIANCE on NSE
    result = growwapi.get_ltp(("NSE_RELIANCE",), segment="CASH")
    print("LTP result:", result)
except Exception as e:
    print(f"Error: {e}")
