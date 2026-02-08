import os
import json
import stat
import time
import hashlib
from typing import List, Dict, Optional, Tuple, Any
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from src.config import settings

logger = logging.getLogger(__name__)
if not logger.handlers:
    # basic configuration if app hasn't configured logging
    logging.basicConfig(level=logging.INFO)


TOKEN_FILE = os.path.abspath(os.path.join(os.path.dirname(
    __file__), '..', '..', 'data', 'fyers_token.json'))


def _read_token_file() -> Dict[str, Any]:
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        return {}
    return {}


def _write_token_file(obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
        json.dump(obj, f)
    try:
        os.chmod(TOKEN_FILE, stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass


def save_token(access_token: str) -> None:
    # backward-compatible small helper (stores only access_token)
    obj = _read_token_file() or {}
    obj.update({'access_token': access_token,
               'expires_at': None, 'refresh_token': None})
    _write_token_file(obj)


def save_token_full(access_token: str, refresh_token: Optional[str], expires_in: Optional[int]) -> None:
    obj = {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_at': int(time.time()) + int(expires_in) if expires_in else None
    }
    _write_token_file(obj)


def _get_stored_tokens() -> Tuple[Optional[str], Optional[str], Optional[int]]:
    obj = _read_token_file()
    return obj.get('access_token'), obj.get('refresh_token'), obj.get('expires_at')


def _to_fyers_symbols(nse_symbols: List[str]) -> List[str]:
    out: List[str] = []
    for s in nse_symbols:
        name = s
        if name.startswith('NSE_'):
            name = name.split('NSE_', 1)[1]
        if ':' in name:
            name = name.split(':')[-1]
        name = name.replace('_', '').upper()
        fy_sym = f"NSE:{name}-EQ"
        out.append(fy_sym)
    return out


def _app_hash() -> str:
    # Fyers requires sha256 of client_id:secret
    # prefer environment variables (they may be updated at runtime) then settings
    client = os.getenv('FYERS_CLIENT_ID') or settings.fyers_client_id
    secret = os.getenv('FYERS_SECRET_KEY') or settings.fyers_secret_key
    if not client or not secret:
        raise RuntimeError(
            'FYERS client id/secret are not configured in environment or settings')
    return hashlib.sha256(f"{client}:{secret}".encode()).hexdigest()


def get_authorize_url(state: str = 'state', env: str = 't1') -> str:
    # env 't1' for testing; production may use 'api' host
    # prefer environment variables first so changes to .env are picked up immediately
    client = os.getenv('FYERS_CLIENT_ID') or settings.fyers_client_id
    redirect = os.getenv('FYERS_REDIRECT_URI') or settings.fyers_redirect_uri
    if not client:
        raise RuntimeError('FYERS_CLIENT_ID not set')
    host = 'https://api-t1.fyers.in' if env == 't1' else 'https://api.fyers.in'
    return f"{host}/api/v3/generate-authcode?client_id={client}&redirect_uri={redirect}&response_type=code&state={state}"


def exchange_auth_code(auth_code: str) -> Dict[str, Any]:
    url = 'https://api-t1.fyers.in/api/v3/validate-authcode'
    payload = {
        'grant_type': 'authorization_code',
        'appIdHash': _app_hash(),
        'code': auth_code
    }
    headers = {'Content-Type': 'application/json'}
    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    try:
        data = resp.json()
    except Exception as exc:
        raise RuntimeError(
            'Non-JSON response from FYERS token exchange') from exc

    # FYERS sometimes nests in 'data' key
    if isinstance(data, dict) and 'data' in data and isinstance(data['data'], dict):
        data = data['data']

    access = data.get('access_token') or data.get('accessToken')
    refresh = data.get('refresh_token') or data.get('refreshToken')
    expires_in = data.get('expires_in') or data.get('expires')
    if not access:
        raise RuntimeError('Token exchange failed: ' + str(data))
    save_token_full(access, refresh, expires_in)
    return data


def refresh_with_refresh_token(refresh_token: str) -> Dict[str, Any]:
    url = 'https://api-t1.fyers.in/api/v3/validate-authcode'
    payload = {
        'grant_type': 'refresh_token',
        'appIdHash': _app_hash(),
        'refresh_token': refresh_token
    }
    headers = {'Content-Type': 'application/json'}
    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    try:
        data = resp.json()
    except Exception as exc:
        raise RuntimeError('Non-JSON response from FYERS refresh') from exc
    if isinstance(data, dict) and 'data' in data and isinstance(data['data'], dict):
        data = data['data']
    access = data.get('access_token') or data.get('accessToken')
    refresh = data.get('refresh_token') or data.get('refreshToken')
    expires_in = data.get('expires_in') or data.get('expires')
    if not access:
        raise RuntimeError('Refresh failed: ' + str(data))
    save_token_full(access, refresh, expires_in)
    logger.info('FYERS token refreshed; expires_in=%s', expires_in)
    return data


def _get_valid_access_token() -> str:
    access, refresh, expires_at = _get_stored_tokens()
    now = int(time.time())
    if access and expires_at and isinstance(expires_at, (int, float)):
        if expires_at - 30 > now:
            return access
    # if no expiry set but access exists, optimistically return it
    if access and not expires_at:
        return access
    # Attempt refresh
    if refresh:
        try:
            info = refresh_with_refresh_token(refresh)
            return info.get('access_token') or info.get('accessToken')
        except Exception as e:
            logger.exception('Failed to refresh token')
            raise RuntimeError(f'Failed to refresh FYERS token: {e}')
    raise RuntimeError(
        'No valid FYERS access token available; please authenticate')


def get_quotes(nse_symbols: List[str], diagnostics: bool = False):
    """Fetch LTPs for the given NSE-style symbols using Fyers REST API.

    Returns a mapping from the original symbol string to a float LTP or None.
    When diagnostics=True, returns (mapping, raw_response)
    """
    # Try a single batch request to FYERS first. If FYERS responds but some symbols
    # are missing or returns a validation error, fall back to a public quote
    # provider (Yahoo Finance) for the missing symbols so the dashboard keeps working.
    results: Dict[str, Optional[float]] = {s: None for s in nse_symbols}
    raw_map: Dict[str, Any] = {}
    fy_symbols = _to_fyers_symbols(nse_symbols)

    try:
        token = _get_valid_access_token()
    except Exception as e:
        logger.info('FYERS access token unavailable: %s', e)
        token = None

    if token:
        session = requests.Session()
        host = 'https://api.fyers.in'
        url = f"{host}/api/v2/quotes?symbols={','.join(fy_symbols)}"
        try:
            resp = session.get(
                url, headers={'Authorization': f'Bearer {token}'}, timeout=8)
            try:
                data = resp.json()
            except Exception:
                data = None
            raw_map['fyers'] = {'status_code': resp.status_code, 'data': data}
            if resp.status_code == 200 and isinstance(data, dict):
                # parse whatever we can
                for i, orig in enumerate(nse_symbols):
                    fy = fy_symbols[i]
                    ltp = None
                    if fy in data and isinstance(data[fy], dict):
                        node = data[fy]
                        ltp = node.get('ltp') or node.get(
                            'last_price') or node.get('lp')
                    elif 'data' in data and isinstance(data['data'], dict) and fy in data['data']:
                        node = data['data'][fy]
                        if isinstance(node, dict):
                            ltp = node.get('ltp') or node.get(
                                'last_price') or node.get('lp')
                    results[orig] = float(ltp) if ltp is not None else None
            else:
                logger.info(
                    'FYERS batch quotes failed or returned non-200: %s', raw_map['fyers'])
        except requests.RequestException as e:
            logger.info('FYERS request exception: %s', e)
            raw_map['fyers'] = {'error': str(e)}

    # Identify missing symbols and attempt fallbacks (BSE then Yahoo)
    missing = [s for s, v in results.items() if v is None]
    bse_results = {}
    if missing:
        # Try BSE fallback first (best-effort)
        try:
            bse_results = _attempt_bse_fallback(missing)
            raw_map['bse_fallback'] = bse_results
            for s, v in bse_results.items():
                if v is not None:
                    results[s] = v
        except Exception as e:
            logger.info('BSE fallback failed: %s', e)

    # Final fallback: Yahoo Finance public endpoint for NSE (.NS)
    missing = [s for s, v in results.items() if v is None]
    yahoo_map: Dict[str, Optional[float]] = {}
    if missing:
        try:
            yahoo_map = _yahoo_fallback(missing)
            raw_map['yahoo_fallback'] = yahoo_map
            for s, v in yahoo_map.items():
                if v is not None:
                    results[s] = v
        except Exception as e:
            logger.info('Yahoo fallback failed: %s', e)

    if diagnostics:
        return results, raw_map
    return results

    result: Dict[str, Optional[float]] = {}
    raw = data
    # parse known shapes
    if isinstance(data, dict) and 'd' in data and isinstance(data['d'], list):
        for entry, orig in zip(data['d'], nse_symbols):
            ltp = None
            if isinstance(entry, dict):
                if 'v' in entry and isinstance(entry['v'], dict):
                    v = entry['v']
                    ltp = v.get('lp') or v.get('last_price') or v.get('ltp')
                ltp = ltp or entry.get('last_price') or entry.get('price')
            result[orig] = float(ltp) if ltp is not None else None
        if diagnostics:
            return result, raw
        return result

    if isinstance(data, dict):
        for i, orig in enumerate(nse_symbols):
            fy = fy_symbols[i]
            ltp = None
            if fy in data:
                node = data[fy]
                if isinstance(node, dict):
                    ltp = node.get('ltp') or node.get(
                        'last_price') or node.get('lp')
            if ltp is None and 'data' in data and isinstance(data['data'], dict):
                node = data['data'].get(fy) or (list(data['data'].values())[
                    i] if data['data'] else None)
                if isinstance(node, dict):
                    ltp = node.get('ltp') or node.get('last_price')
            result[orig] = float(ltp) if ltp is not None else None
        if diagnostics:
            return result, raw
        return result

    for orig in nse_symbols:
        result[orig] = None
    if diagnostics:
        return result, raw
    return result


def _attempt_bse_fallback(missing_symbols: List[str]) -> Dict[str, Optional[float]]:
    # Try converting NSE_<SYM> -> BSE:<SYM> and query the quotes endpoint again
    # This is a lightweight best-effort fallback; not all symbols exist on BSE.
    bse_inputs = []
    for s in missing_symbols:
        name = s
        if name.startswith('NSE_'):
            name = name.split('NSE_', 1)[1]
        name = name.replace('_', '').upper()
        bse_inputs.append(f"BSE:{name}-EQ")
    if not bse_inputs:
        return {s: None for s in missing_symbols}
    # build a temporary request using whatever token we have
    try:
        token = _get_valid_access_token()
    except Exception:
        return {s: None for s in missing_symbols}
    headers = {'Authorization': f'Bearer {token}'}
    q = ','.join(bse_inputs)
    url = f'https://api.fyers.in/api/v2/quotes?symbols={q}'
    try:
        resp = requests.get(url, headers=headers, timeout=6)
        data = resp.json()
    except Exception:
        return {s: None for s in missing_symbols}
    out: Dict[str, Optional[float]] = {}
    if isinstance(data, dict):
        for i, orig in enumerate(missing_symbols):
            bfy = bse_inputs[i]
            ltp = None
            if bfy in data:
                node = data[bfy]
                if isinstance(node, dict):
                    ltp = node.get('ltp') or node.get('last_price')
            out[orig] = float(ltp) if ltp is not None else None
    else:
        for s in missing_symbols:
            out[s] = None
    return out


def _yahoo_fallback(missing_symbols: List[str]) -> Dict[str, Optional[float]]:
    """Fetch prices from Yahoo Finance public quote endpoint (best-effort).

    Maps symbols like 'NSE_RELIANCE' or 'RELIANCE' -> 'RELIANCE.NS'.
    Returns a dict mapping original symbol -> float price or None.
    """
    if not missing_symbols:
        return {}
    tickers = []
    for s in missing_symbols:
        name = s
        if name.startswith('NSE_'):
            name = name.split('NSE_', 1)[1]
        if ':' in name:
            name = name.split(':')[-1]
        name = name.replace('_', '').upper()
        tickers.append(f"{name}.NS")
    q = ','.join(tickers)
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={q}"
    try:
        resp = requests.get(url, timeout=6)
        data = resp.json()
    except Exception:
        return {s: None for s in missing_symbols}
    out: Dict[str, Optional[float]] = {}
    if isinstance(data, dict) and 'quoteResponse' in data and isinstance(data['quoteResponse'], dict):
        results = data['quoteResponse'].get('result') or []
        # Build map from returned symbol (e.g. 'RELIANCE.NS') -> price
        sym_price: Dict[str, Optional[float]] = {}
        for entry in results:
            try:
                sym = entry.get('symbol')
                price = entry.get('regularMarketPrice')
                if sym:
                    sym_price[sym.upper()] = float(
                        price) if price is not None else None
            except Exception:
                continue
        # Map back to original missing_symbols
        for orig in missing_symbols:
            name = orig
            if name.startswith('NSE_'):
                name = name.split('NSE_', 1)[1]
            if ':' in name:
                name = name.split(':')[-1]
            name = name.replace('_', '').upper()
            key = f"{name}.NS"
            out[orig] = sym_price.get(key)
    else:
        for s in missing_symbols:
            out[s] = None
    return out
