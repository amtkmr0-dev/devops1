# User profile page
import os
import sys
from src.api.fyers_adapter import get_quotes, save_token
from src.api.fyers_adapter import get_authorize_url, exchange_auth_code
from src.database import models
from nse_symbol_resolver import resolve_nse_symbol
import re
import requests
import time
import xml.etree.ElementTree as ET
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from datetime import datetime, timedelta


# User profile page
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


# ...existing code...

# User profile page (moved below app initialization)


# Import robust NSE symbol resolver
# Ensure project root and script dir are in sys.path for module imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))


# Explicitly allow all hosts for ngrok access
app = Flask(__name__)
app.config['SERVER_NAME'] = None
app.config['DEBUG'] = False

# Ensure db_manager is initialized before any route
db_path = os.path.abspath(os.path.join(os.path.dirname(
    __file__), '..', 'data', 'dividend_portfolio.db'))
print(f"[DEBUG] Using database at: {db_path}")
db_url = f'sqlite:///{db_path}'
models.init_database(db_url)


@app.route('/watchlist/add', methods=['POST'])
def add_to_watchlist():
    symbol = request.get_json().get('symbol')
    if not symbol:
        return jsonify({'success': False, 'error': 'No symbol provided'}), 400
    # For demo, skip user_id and just add to a generic watchlist or log
    print(f"[INFO] Adding symbol to watchlist: {symbol}")
    return jsonify({'success': True})


# User registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            email = request.form.get('email')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            phone = request.form.get('phone')
            address = request.form.get('address')
        except Exception as e:
            error = f"Form error: {str(e)}"
            return render_template('register.html', error=error)
        if not all([username, password, email, first_name, last_name, phone, address]):
            error = "All fields are required."
            return render_template('register.html', error=error)
        db_sess = models.db_manager.get_session()
        user = db_sess.query(models.User).filter_by(username=username).first()
        if user:
            error = 'Username already exists.'
            db_sess.close()
            return render_template('register.html', error=error)
        email_exists = db_sess.query(
            models.User).filter_by(email=email).first()
        if email_exists:
            error = 'Email already exists.'
            db_sess.close()
            return render_template('register.html', error=error)
        try:
            user = models.User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                address=address
            )
            user.set_password(password)
            db_sess.add(user)
            db_sess.commit()
            db_sess.close()
            flash('Registration successful. Please log in.')
            return redirect(url_for('modern_dashboard'))
        except Exception as e:
            db_sess.rollback()
            db_sess.close()
            error = f"Database error: {str(e)}"
            return render_template('register.html', error=error)
    return render_template('register.html', error=error)

# User login route


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db_sess = models.db_manager.get_session()
        user = db_sess.query(models.User).filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            db_sess.close()
            flash('Logged in successfully.')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('modern_dashboard'))
        else:
            error = 'Invalid username or password.'
        db_sess.close()
    return render_template('login.html', error=error)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))


app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    db_sess = models.db_manager.get_session()
    user = db_sess.query(models.User).get(int(user_id))
    db_sess.close()
    return user


# UserMixin for User model
models.User.__bases__ = (UserMixin,) + models.User.__bases__


# Profile route (ensure it's defined after app and login setup)
@app.route('/profile')
@login_required
def profile():
    # Use Flask-Login's current_user to pass user info to template
    db_sess = models.db_manager.get_session()
    user = db_sess.query(models.User).get(int(current_user.get_id()))
    if user is None:
        db_sess.close()
        flash('User not found.')
        return redirect(url_for('modern_dashboard'))
    db_sess.close()
    return render_template('profile.html', user=user)


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    db_sess = models.db_manager.get_session()
    user = db_sess.query(models.User).get(int(current_user.get_id()))
    if user is None:
        db_sess.close()
        flash('User not found.')
        return redirect(url_for('modern_dashboard'))
    if request.method == 'POST':
        # Accept simple fields and persist
        full = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        theme = request.form.get('theme', 'light')
        # Split full into first/last
        if full:
            parts = full.split(None, 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ''
        if email:
            user.email = email
        if phone:
            user.phone = phone
        # store theme in a misc column if available, otherwise session
        try:
            user.theme = theme
        except Exception:
            session['theme'] = theme
        try:
            db_sess.add(user)
            db_sess.commit()
            flash('Settings saved.')
        except Exception as e:
            db_sess.rollback()
            flash('Could not save settings: ' + str(e))
        db_sess.close()
        return redirect(url_for('settings'))
    db_sess.close()
    return render_template('settings.html', user=user)


@app.route('/modern')
@app.route('/index1')
def modern_dashboard():
    filter_type = request.args.get('filter', 'upcoming')
    data = get_dividend_data()
    if filter_type == 'thisweek':
        filtered = filter_by_week(data, 0)
    elif filter_type == 'nextweek':
        filtered = filter_by_week(data, 1)
    else:
        filtered = data
    search = request.args.get('search', '').lower()
    if search:
        filtered = [d for d in filtered if search in d['company'].lower()]
    return render_template('modern.html', feed_items=filtered, filter_type=filter_type, search=search)


@app.route('/admin/fyers/token', methods=['POST'])
def admin_save_fyers_token():
    # Simple admin endpoint to store FYERS access token to data/fyers_token.json
    data_in = request.get_json() or {}
    token = data_in.get('access_token') or data_in.get('token')
    if not token:
        return jsonify({'success': False, 'error': 'No token provided'}), 400
    try:
        save_token(token)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/fyers/diagnostics', methods=['GET'])
def admin_fyers_diagnostics():
    # Accept 'symbol' as query param (company name or NSE_xxx)
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({'error': 'symbol query param required'}), 400
    # If user supplied a company name, try to resolve
    if not symbol.upper().startswith('NSE_'):
        n = resolve_nse_symbol(symbol)
        if n:
            query_sym = f"NSE_{n}"
        else:
            query_sym = symbol
    else:
        query_sym = symbol
    try:
        # diagnostics=True returns (quote_map, raw)
        qmap, raw = get_quotes([query_sym], diagnostics=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'query': query_sym, 'quotes': qmap, 'raw': raw})


@app.route('/auth/fyers/start')
def fyers_auth_start():
    # Redirect user to FYERS auth URL
    state = request.args.get('state', 'divscanner')
    try:
        url = get_authorize_url(state=state)
    except Exception as e:
        return f"Error building authorize URL: {e}", 500
    return redirect(url)


@app.route('/auth/fyers/callback')
def fyers_auth_callback():
    # FYERS will redirect with ?auth_code=... or ?code=... depending on setup
    auth_code = request.args.get('auth_code') or request.args.get(
        'code') or request.args.get('authcode')
    if not auth_code:
        return 'Missing auth code in callback', 400
    try:
        info = exchange_auth_code(auth_code)
    except Exception as e:
        return f'Auth exchange failed: {e}', 500
    # Store minimal info and show success
    return render_template('auth_success.html', info=info)


# Set the RSS feed URL
url = 'https://archives.nseindia.com/content/RSS/Corporate_action.xml'
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}


# Helper to parse dividend info from description


def parse_dividend_info(title, description, pub_date=None):
    # Example description: "Castrol India Ltd has informed BSE that the Company has fixed Record Date as 11-Aug-2025 for the purpose of Dividend. The dividend, if approved, will be paid on or after 17-Aug-2025."
    # Try to extract ex-date and dividend amount
    ex_date = None
    announcement_date = None
    dividend = None
    record_date = None
    book_closure_start = None
    book_closure_end = None
    purpose = None

    # Announcement date: prefer pub_date if provided
    if pub_date:
        try:
            announcement_date = datetime.strptime(
                pub_date.split()[0], '%d-%b-%Y').date()
        except Exception:
            announcement_date = pub_date.split()[0]
    else:
        ann_date_match = re.search(
            r'ANNOUNCEMENT DATE[:\s]*([\d-]+)', description, re.IGNORECASE)
        if ann_date_match:
            try:
                announcement_date = datetime.strptime(
                    ann_date_match.group(1), '%d-%m-%Y').date()
            except Exception:
                announcement_date = ann_date_match.group(1)
        else:
            ann_date_title = re.search(r'(\d{2}-[A-Za-z]{3}-\d{4})', title)
            if ann_date_title:
                try:
                    announcement_date = datetime.strptime(
                        ann_date_title.group(1), '%d-%b-%Y').date()
                except Exception:
                    announcement_date = ann_date_title.group(1)

    # Ex-date (prefer EX-DATE, fallback to RECORD DATE, then announcement date)
    ex_date_match = re.search(
        r'EX-DATE:?\s*([0-9]{2}-[A-Za-z]{3}-[0-9]{4})', description, re.IGNORECASE)
    if not ex_date_match:
        ex_date_match = re.search(
            r'EX-DATE:?\s*([0-9]{2}-[A-Za-z]{3}-[0-9]{4})', title, re.IGNORECASE)
    if ex_date_match:
        try:
            ex_date = datetime.strptime(
                ex_date_match.group(1), '%d-%b-%Y').date()
        except Exception:
            ex_date = ex_date_match.group(1)
    record_date_match = re.search(
        r'RECORD DATE:([\d-]+)', description, re.IGNORECASE)
    if record_date_match:
        try:
            record_date = datetime.strptime(
                record_date_match.group(1), '%d-%m-%Y').date()
        except Exception:
            record_date = record_date_match.group(1)
        # If ex_date is not found, use record_date as ex_date
        if not ex_date:
            ex_date = record_date
    # If ex_date is still missing but announcement_date is present, use announcement_date
    if not ex_date and announcement_date:
        ex_date = announcement_date

    # Book closure
    bc_start = re.search(
        r'BOOK CLOSURE START DATE:([\d-]+)', description, re.IGNORECASE)
    if bc_start:
        book_closure_start = bc_start.group(1)
    bc_end = re.search(
        r'BOOK CLOSURE END DATE:([\d-]+)', description, re.IGNORECASE)
    if bc_end:
        book_closure_end = bc_end.group(1)

    # Purpose
    purpose_match = re.search(r'PURPOSE:([^|]+)', description, re.IGNORECASE)
    if purpose_match:
        purpose = purpose_match.group(1).strip()

    # Dividend amount (try to extract from purpose or description, match RS or RE, with or without 'PER SHARE')
    dividend = None
    # Try description first, robust regex for RS/RE, with/without space, with/without PER SHARE
    div_match = re.search(
        r'(?:DIVIDEND|INTERIM DIVIDEND|SPECIAL DIVIDEND)[\s-]*(RS|RE)[\s.:/-]*([\d,.]+)', description.upper())
    if not div_match and purpose:
        div_match = re.search(
            r'(?:DIVIDEND|INTERIM DIVIDEND|SPECIAL DIVIDEND)[\s-]*(RS|RE)[\s.:/-]*([\d,.]+)', purpose.upper())
    if div_match:
        dividend = div_match.group(2)
    # (Announcement date extraction already handled above)

    # Company name
    company = title.split(' - ')[0].strip()
    # Format ex_date and announcement_date as strings (YYYY-MM-DD) if they are date objects
    if isinstance(ex_date, datetime):
        ex_date = ex_date.date()
    if isinstance(ex_date, (datetime, type(datetime.now().date()))):
        ex_date = ex_date.strftime('%Y-%m-%d')
    if isinstance(announcement_date, datetime):
        announcement_date = announcement_date.date()
    if isinstance(announcement_date, (datetime, type(datetime.now().date()))):
        announcement_date = announcement_date.strftime('%Y-%m-%d')
    if isinstance(record_date, datetime):
        record_date = record_date.date()
    if isinstance(record_date, (datetime, type(datetime.now().date()))):
        record_date = record_date.strftime('%Y-%m-%d')
    return {
        'company': company,
        'title': title,
        'description': description,
        'ex_date': ex_date,
        'record_date': record_date,
        'book_closure_start': book_closure_start,
        'book_closure_end': book_closure_end,
        'purpose': purpose,
        'announcement_date': announcement_date,
        'dividend': dividend,
        'ltp': None,  # Placeholder for current price
        'ltp_change': None  # Placeholder for price change
    }


def get_dividend_data():
    response = requests.get(url, headers=headers)
    time.sleep(2)
    xml_content = response.content
    root = ET.fromstring(xml_content)
    items = root.findall('.//item')
    keyword = 'DIVIDEND'
    data = []
    # First pass: collect items and resolve their NSE symbols
    for item in items:
        description = item.find('description').text
        pub_date = item.find('pubDate').text if item.find(
            'pubDate') is not None else None
        if keyword in description:
            title = item.find('title').text
            info = parse_dividend_info(
                title.replace('\n', ''), description, pub_date)
            company = info['company']
            nse_symbol = resolve_nse_symbol(company)
            if not nse_symbol:
                print(
                    f"[WARN] NSE symbol mapping failed for company: {company}")
            info['_nse_symbol'] = nse_symbol
            info['ltp'] = None
            info['ltp_change'] = None
            data.append(info)

    # Batch fetch LTPs for all resolved symbols using FYERS adapter
    symbols_to_query = []
    for entry in data:
        s = entry.get('_nse_symbol')
        if s:
            symbols_to_query.append(f"NSE_{s}")
    # de-duplicate while preserving order
    seen = set()
    unique_symbols = []
    for s in symbols_to_query:
        if s not in seen:
            unique_symbols.append(s)
            seen.add(s)

    quote_map = {}
    if unique_symbols:
        try:
            quote_map = get_quotes(unique_symbols)
        except Exception as e:
            print(f"[ERROR] FYERS get_quotes failed: {e}")

    # Attach LTPs back to entries
    for entry in data:
        s = entry.get('_nse_symbol')
        if s:
            entry['ltp'] = quote_map.get(f"NSE_{s}")
            if entry['ltp'] is None:
                print(f"[WARN] LTP not found for symbol: NSE_{s}")
        else:
            entry['ltp'] = None

    # cleanup helper keys
    for entry in data:
        if '_nse_symbol' in entry:
            del entry['_nse_symbol']

    return data

# Helper to map company name to Yahoo Finance symbol (basic, for demo)


def get_yahoo_symbol(company_name):
    # For Indian stocks, Yahoo uses NSE: TATAMOTORS.NS, RELIANCE.NS, etc.
    # Try to generate symbol from company name
    mapping = {
        'Brigade Enterprises Limited': 'BRIGADE.NS',
        'Castrol': 'CASTROLIND.NS',
        'Jio Financial': 'JIOFIN.NS',
        'Akzo Nobel': 'AKZOINDIA.NS',
        # Add more exceptions as needed
    }
    # If in mapping, return mapped symbol
    if company_name in mapping:
        return mapping[company_name]
    # Try to extract the main part of the company name (before Limited, Ltd, etc.)
    import re
    base = re.split(r' Limited| Ltd| Pvt| PLC|\(|-',
                    company_name, flags=re.IGNORECASE)[0].strip()
    # Remove non-alphanumeric characters and spaces
    base = re.sub(r'[^A-Za-z0-9]', '', base)
    if not base:
        return None
    symbol = base.upper() + '.NS'
    return symbol


def filter_by_week(data, week_offset=0):
    # week_offset=0: this week, 1: next week
    today = datetime.today().date()
    start = today + timedelta(days=-today.weekday(), weeks=week_offset)
    end = start + timedelta(days=6)
    # Convert start and end to string for comparison with ex_date
    start_str = start.strftime('%Y-%m-%d')
    end_str = end.strftime('%Y-%m-%d')
    return [d for d in data if d['ex_date'] and start_str <= d['ex_date'] <= end_str]


@app.route('/')
@app.route('/index')
def index():
    filter_type = request.args.get('filter', 'upcoming')
    data = get_dividend_data()
    if filter_type == 'thisweek':
        filtered = filter_by_week(data, 0)
    elif filter_type == 'nextweek':
        filtered = filter_by_week(data, 1)
    else:
        filtered = data
    # For search
    search = request.args.get('search', '').lower()
    if search:
        filtered = [d for d in filtered if search in d['company'].lower()]
    return render_template('index.html', feed_items=filtered, filter_type=filter_type, search=search)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=False)
