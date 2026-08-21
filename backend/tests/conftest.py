import os
import sys
from datetime import date, datetime
import pytest

# Ensure backend root is on Python sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database.session import Base, get_db
from app.models.company import Company
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.category import Category
from app.models.vendor import Vendor
from app.models.transaction import Transaction, TransactionType
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.budget import Budget

# In-memory SQLite with StaticPool for fast, isolated thread-safe tests
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        # Seed minimum test company & records
        comp = Company(name="Test Corp", industry="Tech", currency="USD")
        db.add(comp)
        db.commit()
        db.refresh(comp)

        dept = Department(company_id=comp.id, name="Engineering")
        cat = Category(company_id=comp.id, name="Cloud Infrastructure", color_code="#6366F1")
        vend = Vendor(company_id=comp.id, name="Amazon Web Services", reliability_score=95, quality_score=90, average_delivery_days=2)
        db.add_all([dept, cat, vend])
        db.commit()

        # Add sample expenses & subscriptions
        for i in range(10):
            tx = Transaction(
                company_id=comp.id,
                department_id=dept.id,
                category_id=cat.id,
                vendor_id=vend.id,
                transaction_date=date(2026, 8, 1 + (i % 25)),
                description=f"Cloud Compute Node {i}",
                amount=1200.0 + (i * 100),
                transaction_type=TransactionType.EXPENSE,
                payment_method="Credit Card",
                reference_number=f"TX-TEST-{i}"
            )
            db.add(tx)

        sub = Subscription(
            company_id=comp.id,
            department_id=dept.id,
            vendor_id=vend.id,
            vendor="Amazon Web Services",
            service_name="Cloud Monitoring Pro",
            monthly_cost=5000.0,
            total_licenses=20,
            active_licenses=10,
            renewal_date=date(2026, 9, 30),
            status=SubscriptionStatus.ACTIVE
        )
        bg = Budget(
            company_id=comp.id,
            department_id=dept.id,
            year=2026,
            allocated_amount=50000.0,
            spent_amount=15000.0
        )
        db.add_all([sub, bg])
        db.commit()

        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def test_company(db_session):
    return db_session.query(Company).first()


@pytest.fixture(scope="function")
def test_user(db_session, test_company):
    from app.auth.hashing import hash_password
    user = User(
        name="Admin Test",
        email="admin_test@moneyanalysis.ai",
        password_hash=hash_password("Password123!"),
        role=UserRole.ADMIN,
        company_id=test_company.id
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

