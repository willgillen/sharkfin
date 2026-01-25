import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.account import Account
from app.core.security import get_password_hash

# Use PostgreSQL for testing to match production environment
# This allows us to use PostgreSQL-specific features like JSONB
# Build test database URL from the main DATABASE_URL
def get_test_database_url():
    """Get test database URL, deriving credentials from DATABASE_URL."""
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        # Replace the database name with shark_fin_test
        test_url = db_url.rsplit("/", 1)[0] + "/shark_fin_test"
    else:
        # Fallback for local development
        test_url = "postgresql://sharkfin:sharkfin@localhost:5433/shark_fin_test"
    return test_url

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", get_test_database_url())

engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_test_database_if_not_exists():
    """Create the test database if it doesn't exist."""
    from sqlalchemy import create_engine as create_temp_engine, text
    from sqlalchemy.exc import ProgrammingError

    # Get the database URL and extract connection info
    db_url = TEST_DATABASE_URL
    # Connect to postgres database to create the test database
    admin_url = db_url.rsplit("/", 1)[0] + "/postgres"

    admin_engine = create_temp_engine(admin_url, isolation_level="AUTOCOMMIT")

    try:
        with admin_engine.connect() as conn:
            # Extract database name from URL
            db_name = db_url.split("/")[-1]

            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                {"dbname": db_name}
            )
            exists = result.fetchone() is not None

            if not exists:
                # Create the test database
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                print(f"\nCreated test database '{db_name}'")
    except ProgrammingError:
        # Database might already exist or we don't have permissions
        # This is okay, the test will fail later if there's a real issue
        pass
    finally:
        admin_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create test database and all tables before running tests, drop after."""
    # Create the test database if it doesn't exist
    create_test_database_if_not_exists()

    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield

    # Clean up: drop all tables (but keep the database for next run)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a new database session for a test with transaction rollback."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_account(db_session, test_user):
    """Create a test account."""
    from app.models.account import AccountType
    account = Account(
        user_id=test_user.id,
        name="Test Checking",
        type=AccountType.CHECKING,
        current_balance=1000.00
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "testpassword123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
