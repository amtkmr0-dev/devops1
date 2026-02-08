
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, nullable=False, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    address = Column(String(255))
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    watchlist = relationship("Watchlist", back_populates="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stock_symbol = Column(String(20), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="watchlist")


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    sector = Column(String(100))
    market_cap = Column(Float)
    current_price = Column(Float)
    currency = Column(String(3), default="USD")
    exchange = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    dividends = relationship("Dividend", back_populates="stock")
    financial_metrics = relationship("FinancialMetric", back_populates="stock")


class Dividend(Base):
    __tablename__ = "dividends"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)

    # Dividend Information
    dividend_amount = Column(Float, nullable=False)
    dividend_yield = Column(Float)
    ex_dividend_date = Column(DateTime)
    payment_date = Column(DateTime)
    record_date = Column(DateTime)
    declaration_date = Column(DateTime)

    # Dividend Type
    # regular, special, stock
    dividend_type = Column(String(20), default="regular")
    frequency = Column(String(20))  # annual, semi-annual, quarterly, monthly

    # Metrics
    payout_ratio = Column(Float)
    dividend_growth_rate = Column(Float)  # YoY growth rate

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    stock = relationship("Stock", back_populates="dividends")


class FinancialMetric(Base):
    __tablename__ = "financial_metrics"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)

    # Financial Ratios
    pe_ratio = Column(Float)
    debt_to_equity = Column(Float)
    return_on_equity = Column(Float)
    revenue_growth = Column(Float)
    profit_margin = Column(Float)

    # Dividend Specific Metrics
    dividend_coverage_ratio = Column(Float)
    free_cash_flow = Column(Float)
    earnings_per_share = Column(Float)

    # Health Score (Custom calculated)
    dividend_health_score = Column(Float)

    # Period Information
    reporting_period = Column(String(10))  # Q1, Q2, Q3, Q4, Annual
    fiscal_year = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    stock = relationship("Stock", back_populates="financial_metrics")


class ScanResult(Base):
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, index=True)
    scan_name = Column(String(100), nullable=False)
    scan_criteria = Column(Text)  # JSON string of criteria used

    # Results
    total_stocks_scanned = Column(Integer)
    stocks_found = Column(Integer)
    result_data = Column(Text)  # JSON string of results

    # Metadata
    scan_date = Column(DateTime, default=datetime.utcnow)
    execution_time_seconds = Column(Float)


class UserAlert(Base):
    __tablename__ = "user_alerts"

    id = Column(Integer, primary_key=True, index=True)
    stock_symbol = Column(String(10), nullable=False)
    # yield_threshold, ex_dividend, new_dividend
    alert_type = Column(String(50), nullable=False)
    threshold_value = Column(Float)

    # Alert Settings
    is_active = Column(Boolean, default=True)
    email_notification = Column(Boolean, default=True)
    sms_notification = Column(Boolean, default=False)

    # Contact Info
    email = Column(String(255))
    phone = Column(String(20))

    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered = Column(DateTime)

# Database connection and session management


class DatabaseManager:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        """Create all tables"""
        print("[DEBUG] Creating all tables in database...")
        Base.metadata.create_all(bind=self.engine)
        print("[DEBUG] Table creation complete.")

    def get_session(self):
        """Get database session"""
        session = self.SessionLocal()
        try:
            return session
        except Exception:
            session.close()
            raise

    def close_session(self, session):
        """Close database session"""
        session.close()


# Global database manager (will be initialized in main app)
db_manager = None


def init_database(database_url: str):
    """Initialize database"""
    global db_manager
    db_manager = DatabaseManager(database_url)
    db_manager.create_tables()
    return db_manager
