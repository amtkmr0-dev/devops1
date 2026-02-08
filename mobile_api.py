#!/usr/bin/env python3
"""
Mobile API Backend for Dividend Scanner
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
import asyncio
import uvicorn
from datetime import datetime, timedelta
import jwt
import hashlib
import sqlite3
import pandas as pd
from enhanced_features import DividendAlertSystem, PortfolioTracker, AdvancedDividendAnalyzer
from src.data.free_indian_provider import FreeIndianStockProvider

# Initialize FastAPI app
app = FastAPI(
    title="Dividend Scanner Pro API",
    description="Professional API for dividend analysis and portfolio management",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
SECRET_KEY = "your-secret-key-here-change-in-production"  # Change in production

# Initialize services
provider = FreeIndianStockProvider()
alert_system = DividendAlertSystem()
portfolio_tracker = PortfolioTracker()
analyzer = AdvancedDividendAnalyzer()

# Pydantic models


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class StockScanRequest(BaseModel):
    scan_type: str = "high_yield"
    min_yield: float = 4.0
    max_pe: Optional[float] = None
    min_market_cap: Optional[float] = None
    symbols: Optional[List[str]] = None


class AlertCreate(BaseModel):
    symbol: str
    alert_type: str  # ex_dividend, high_yield, price_drop
    threshold: Optional[float] = None
    email: EmailStr


class PortfolioHolding(BaseModel):
    symbol: str
    quantity: int
    purchase_price: float
    purchase_date: Optional[str] = None


class DividendRecord(BaseModel):
    symbol: str
    dividend_per_share: float
    quantity: int
    ex_date: Optional[str] = None

# Authentication functions


def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    try:
        payload = jwt.decode(credentials.credentials,
                             SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

# Database setup


def init_user_db():
    """Initialize user database"""
    conn = sqlite3.connect("data/users.db")
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')

    conn.commit()
    conn.close()


# Initialize database
init_user_db()

# Authentication endpoints


@app.post("/api/auth/register")
async def register_user(user: UserCreate):
    """Register new user"""
    try:
        conn = sqlite3.connect("data/users.db")
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (user.email,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=400, detail="Email already registered")

        # Create user
        password_hash = hash_password(user.password)
        cursor.execute(
            "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
            (user.email, password_hash, user.name)
        )

        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Create access token
        access_token = create_access_token(data={"sub": str(user_id)})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {"id": user_id, "email": user.email, "name": user.name}
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/login")
async def login_user(user: UserLogin):
    """Login user"""
    try:
        conn = sqlite3.connect("data/users.db")
        cursor = conn.cursor()

        # Get user
        cursor.execute(
            "SELECT id, email, password_hash, name FROM users WHERE email = ?",
            (user.email,)
        )

        user_data = cursor.fetchone()
        conn.close()

        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user_id, email, stored_hash, name = user_data

        # Verify password
        if hash_password(user.password) != stored_hash:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Create access token
        access_token = create_access_token(data={"sub": str(user_id)})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {"id": user_id, "email": email, "name": name}
        }

    except Exception as e:
        if "Invalid credentials" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

# Stock scanning endpoints


@app.post("/api/scan/stocks")
async def scan_stocks(request: StockScanRequest, user_id: str = Depends(verify_token)):
    """Scan stocks based on criteria"""
    try:
        # Default symbols if none provided
        symbols = request.symbols or [
            'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ITC', 'COALINDIA',
            'NTPC', 'POWERGRID', 'ONGC', 'IOC', 'SBIN', 'HDFC'
        ]

        results = []

        for symbol in symbols:
            try:
                # Get stock data
                data = provider.get_comprehensive_stock_data(symbol)

                # Apply filters
                dividend_yield = data.get('dividend_yield', 0)
                pe_ratio = data.get('pe_ratio', 0)

                # Check criteria
                meets_criteria = True

                if dividend_yield < request.min_yield / 100:
                    meets_criteria = False

                if request.max_pe and pe_ratio and pe_ratio > request.max_pe:
                    meets_criteria = False

                if meets_criteria:
                    # Get safety score
                    safety = analyzer.dividend_safety_score(symbol)

                    results.append({
                        'symbol': symbol,
                        'current_price': data.get('current_price', 0),
                        'dividend_yield': dividend_yield * 100,
                        'pe_ratio': pe_ratio,
                        'market_cap': data.get('market_cap', 'N/A'),
                        'safety_score': safety['safety_score'],
                        'safety_rating': safety['rating'],
                        'recommendation': 'BUY' if safety['safety_score'] > 70 else 'WATCH',
                        'last_updated': datetime.now().isoformat()
                    })

            except Exception as e:
                print(f"Error scanning {symbol}: {e}")
                continue

        # Sort by safety score
        results.sort(key=lambda x: x['safety_score'], reverse=True)

        return {
            'success': True,
            'scan_type': request.scan_type,
            'total_results': len(results),
            'results': results,
            'scan_timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stock/{symbol}/analysis")
async def get_stock_analysis(symbol: str, user_id: str = Depends(verify_token)):
    """Get detailed analysis for a specific stock"""
    try:
        # Get comprehensive data
        stock_data = provider.get_comprehensive_stock_data(symbol.upper())
        safety_score = analyzer.dividend_safety_score(symbol.upper())
        prediction = analyzer.predict_next_dividend(symbol.upper())
        seasonal = analyzer.analyze_dividend_seasonality(symbol.upper())

        return {
            'success': True,
            'symbol': symbol.upper(),
            'basic_data': {
                'current_price': stock_data.get('current_price', 0),
                'dividend_yield': stock_data.get('dividend_yield', 0) * 100,
                'pe_ratio': stock_data.get('pe_ratio', 0),
                'market_cap': stock_data.get('market_cap', 'N/A'),
                'fifty_two_week_high': stock_data.get('fifty_two_week_high', 0),
                'fifty_two_week_low': stock_data.get('fifty_two_week_low', 0)
            },
            'safety_analysis': safety_score,
            'dividend_prediction': prediction,
            'seasonal_analysis': seasonal,
            'analysis_timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Portfolio management endpoints


@app.post("/api/portfolio/holdings")
async def add_portfolio_holding(holding: PortfolioHolding, user_id: str = Depends(verify_token)):
    """Add holding to portfolio"""
    try:
        portfolio_tracker.add_holding(
            user_id,
            holding.symbol.upper(),
            holding.quantity,
            holding.purchase_price
        )

        return {
            'success': True,
            'message': f'Added {holding.quantity} shares of {holding.symbol.upper()}',
            'holding': {
                'symbol': holding.symbol.upper(),
                'quantity': holding.quantity,
                'purchase_price': holding.purchase_price,
                'total_investment': holding.quantity * holding.purchase_price
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolio/summary")
async def get_portfolio_summary(user_id: str = Depends(verify_token)):
    """Get portfolio summary"""
    try:
        summary = portfolio_tracker.get_portfolio_summary(user_id)

        return {
            'success': True,
            'portfolio_summary': summary,
            'summary_timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/portfolio/dividend")
async def record_dividend(dividend: DividendRecord, user_id: str = Depends(verify_token)):
    """Record dividend received"""
    try:
        portfolio_tracker.record_dividend(
            user_id,
            dividend.symbol.upper(),
            dividend.dividend_per_share,
            dividend.quantity,
            dividend.ex_date
        )

        total_dividend = dividend.dividend_per_share * dividend.quantity

        return {
            'success': True,
            'message': f'Recorded ₹{total_dividend} dividend from {dividend.symbol.upper()}',
            'dividend_record': {
                'symbol': dividend.symbol.upper(),
                'dividend_per_share': dividend.dividend_per_share,
                'quantity': dividend.quantity,
                'total_received': total_dividend,
                'ex_date': dividend.ex_date
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Alert management endpoints


@app.post("/api/alerts")
async def create_alert(alert: AlertCreate, user_id: str = Depends(verify_token)):
    """Create new alert"""
    try:
        alert_system.add_alert(
            alert.email,
            alert.symbol.upper(),
            alert.alert_type,
            alert.threshold
        )

        return {
            'success': True,
            'message': f'Alert created for {alert.symbol.upper()}',
            'alert': {
                'symbol': alert.symbol.upper(),
                'type': alert.alert_type,
                'threshold': alert.threshold,
                'email': alert.email
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/alerts/test")
async def test_alerts(background_tasks: BackgroundTasks, user_id: str = Depends(verify_token)):
    """Test alert system"""
    try:
        # Run alert checks in background
        background_tasks.add_task(alert_system.check_ex_dividend_alerts)
        background_tasks.add_task(alert_system.check_high_yield_alerts)

        return {
            'success': True,
            'message': 'Alert checks initiated',
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Market data endpoints


@app.get("/api/market/status")
async def get_market_status():
    """Get market status"""
    try:
        now = datetime.now()

        # Simple market hours check (9:15 AM - 3:30 PM IST)
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)

        is_open = market_open <= now <= market_close and now.weekday() < 5

        return {
            'success': True,
            'market_status': 'OPEN' if is_open else 'CLOSED',
            'current_time': now.isoformat(),
            'next_open': market_open.isoformat() if not is_open else None,
            'next_close': market_close.isoformat() if is_open else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/top-dividends")
async def get_top_dividend_stocks(limit: int = 10):
    """Get top dividend-yielding stocks"""
    try:
        symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ITC', 'COALINDIA',
                   'NTPC', 'POWERGRID', 'ONGC', 'IOC', 'SBIN', 'HDFC']

        results = []

        for symbol in symbols:
            try:
                data = provider.get_comprehensive_stock_data(symbol)
                dividend_yield = data.get('dividend_yield', 0)

                if dividend_yield > 0:
                    results.append({
                        'symbol': symbol,
                        'dividend_yield': dividend_yield * 100,
                        'current_price': data.get('current_price', 0),
                        'pe_ratio': data.get('pe_ratio', 0)
                    })

            except Exception as e:
                continue

        # Sort by dividend yield
        results.sort(key=lambda x: x['dividend_yield'], reverse=True)

        return {
            'success': True,
            'top_dividends': results[:limit],
            'data_timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'Dividend Scanner Pro API',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("🚀 Starting Dividend Scanner Pro API...")
    print("📱 Mobile-ready backend with authentication")
    print("🔗 API Documentation: http://localhost:8000/api/docs")

    uvicorn.run(
        "mobile_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
