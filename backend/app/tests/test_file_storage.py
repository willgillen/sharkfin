"""
Test file storage for import history.

Tests that original import files are:
1. Compressed and stored in the database
2. Can be downloaded later
3. Are decompressed correctly on download
"""
import pytest
import gzip
from io import BytesIO
from fastapi.testclient import TestClient
from app.models.user import User
from app.models.account import Account, AccountType
from app.models.import_history import ImportHistory
from sqlalchemy.orm import Session


@pytest.fixture
def test_account(db_session: Session, test_user: User):
    """Create a test account"""
    account = Account(
        user_id=test_user.id,
        name="Test Checking",
        type=AccountType.CHECKING,
        opening_balance=1000.00
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


class TestFileStorage:
    """Test file storage and download functionality"""

    def test_csv_file_stored_and_compressed(self, db_session: Session, test_user: User, test_account: Account):
        """Test that CSV files are compressed and stored"""
        # Create test CSV content
        csv_content = b"""Date,Description,Amount
2026-01-01,Test Transaction 1,100.00
2026-01-02,Test Transaction 2,200.00
2026-01-03,Test Transaction 3,300.00"""

        # Create import record with file data
        from app.services.import_service import ImportService
        service = ImportService(db_session)

        import_record = service.create_import_record(
            user_id=test_user.id,
            account_id=test_account.id,
            filename="test.csv",
            import_type="csv",
            total_rows=3,
            file_size=len(csv_content),
            file_data=csv_content
        )

        # Verify record was created
        assert import_record.id is not None
        assert import_record.original_file_data is not None
        assert import_record.is_compressed is True
        assert import_record.original_file_name == "test.csv"
        assert import_record.original_file_size == len(csv_content)

        # Verify file is compressed (should be smaller or equal)
        assert len(import_record.original_file_data) <= len(csv_content)

        # Verify can be decompressed
        decompressed = gzip.decompress(import_record.original_file_data)
        assert decompressed == csv_content

    def test_ofx_file_stored_and_compressed(self, db_session: Session, test_user: User, test_account: Account):
        """Test that OFX files are compressed and stored"""
        # Create test OFX content
        ofx_content = b"""OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
<SIGNONMSGSRSV1>
<SONRS>
<STATUS>
<CODE>0
<SEVERITY>INFO
</STATUS>
<DTSERVER>20260101120000
<LANGUAGE>ENG
</SONRS>
</SIGNONMSGSRSV1>
</OFX>"""

        from app.services.import_service import ImportService
        service = ImportService(db_session)

        import_record = service.create_import_record(
            user_id=test_user.id,
            account_id=test_account.id,
            filename="test.ofx",
            import_type="ofx",
            total_rows=0,
            file_size=len(ofx_content),
            file_data=ofx_content
        )

        assert import_record.original_file_data is not None
        assert import_record.is_compressed is True

        # Verify decompression works
        decompressed = gzip.decompress(import_record.original_file_data)
        assert decompressed == ofx_content

    def test_import_without_file_data(self, db_session: Session, test_user: User, test_account: Account):
        """Test that imports can be created without storing file data"""
        from app.services.import_service import ImportService
        service = ImportService(db_session)

        import_record = service.create_import_record(
            user_id=test_user.id,
            account_id=test_account.id,
            filename="test.csv",
            import_type="csv",
            total_rows=5,
            file_size=1000,
            file_data=None  # No file data
        )

        assert import_record.id is not None
        assert import_record.original_file_data is None
        assert import_record.is_compressed is False
        assert import_record.original_file_size is None

    def test_file_download_endpoint(self, client: TestClient, db_session: Session, test_user: User, test_account: Account, auth_headers):
        """Test downloading the original import file"""
        # Create import with file data
        csv_content = b"""Date,Description,Amount
2026-01-01,Test,100.00"""

        from app.services.import_service import ImportService
        service = ImportService(db_session)

        import_record = service.create_import_record(
            user_id=test_user.id,
            account_id=test_account.id,
            filename="test_download.csv",
            import_type="csv",
            total_rows=1,
            file_size=len(csv_content),
            file_data=csv_content
        )

        # Download the file
        response = client.get(
            f"/api/v1/imports/{import_record.id}/download",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.content == csv_content
        assert 'attachment' in response.headers['content-disposition']
        assert 'test_download.csv' in response.headers['content-disposition']

    def test_download_nonexistent_import(self, client: TestClient, test_user: User, auth_headers):
        """Test downloading a non-existent import returns 404"""
        response = client.get(
            "/api/v1/imports/99999/download",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "Import not found" in response.json()["detail"]

    def test_download_import_without_file_data(self, client: TestClient, db_session: Session, test_user: User, test_account: Account, auth_headers):
        """Test downloading an import without stored file data returns 404"""
        from app.services.import_service import ImportService
        service = ImportService(db_session)

        import_record = service.create_import_record(
            user_id=test_user.id,
            account_id=test_account.id,
            filename="no_file.csv",
            import_type="csv",
            total_rows=0,
            file_size=0,
            file_data=None  # No file stored
        )

        response = client.get(
            f"/api/v1/imports/{import_record.id}/download",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "Original file not available" in response.json()["detail"]

    def test_download_other_user_import(self, client: TestClient, db_session: Session, test_user: User, test_account: Account, auth_headers):
        """Test that users cannot download other users' import files"""
        # Create another user
        from app.core.security import get_password_hash
        other_user = User(
            email="other@test.com",
            hashed_password=get_password_hash("otherpassword123"),
            full_name="Other User"
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        # Create import for test_user
        csv_content = b"Date,Amount\n2026-01-01,100.00"

        from app.services.import_service import ImportService
        service = ImportService(db_session)

        import_record = service.create_import_record(
            user_id=test_user.id,
            account_id=test_account.id,
            filename="private.csv",
            import_type="csv",
            total_rows=1,
            file_size=len(csv_content),
            file_data=csv_content
        )

        # Get auth headers for other_user
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": other_user.email, "password": "otherpassword123"}
        )
        other_token = login_response.json()["access_token"]
        other_auth_headers = {"Authorization": f"Bearer {other_token}"}

        # Try to download as other_user
        response = client.get(
            f"/api/v1/imports/{import_record.id}/download",
            headers=other_auth_headers
        )

        assert response.status_code == 404
        assert "Import not found" in response.json()["detail"]

    def test_compression_reduces_file_size(self, db_session: Session, test_user: User, test_account: Account):
        """Test that compression actually reduces file size for larger files"""
        # Create large CSV with repetitive data (compresses well)
        csv_lines = ["Date,Description,Amount\n"]
        for i in range(1000):
            csv_lines.append(f"2026-01-01,Test Transaction {i % 10},100.00\n")

        csv_content = "".join(csv_lines).encode('utf-8')

        from app.services.import_service import ImportService
        service = ImportService(db_session)

        import_record = service.create_import_record(
            user_id=test_user.id,
            account_id=test_account.id,
            filename="large.csv",
            import_type="csv",
            total_rows=1000,
            file_size=len(csv_content),
            file_data=csv_content
        )

        # Compressed size should be significantly smaller (at least 50% reduction for repetitive data)
        compression_ratio = len(import_record.original_file_data) / len(csv_content)
        assert compression_ratio < 0.5  # At least 50% compression

    def test_file_media_types(self, client: TestClient, db_session: Session, test_user: User, test_account: Account, auth_headers):
        """Test that different file types return appropriate media types"""
        from app.services.import_service import ImportService
        service = ImportService(db_session)

        test_cases = [
            ("test.csv", "csv", b"Date,Amount\n2026-01-01,100", "text/csv"),
            ("test.ofx", "ofx", b"<OFX>test</OFX>", "application/x-ofx"),
            ("test.qfx", "qfx", b"<OFX>test</OFX>", "application/x-ofx"),
        ]

        for filename, import_type, content, expected_media_type in test_cases:
            import_record = service.create_import_record(
                user_id=test_user.id,
                account_id=test_account.id,
                filename=filename,
                import_type=import_type,
                total_rows=1,
                file_size=len(content),
                file_data=content
            )

            response = client.get(
                f"/api/v1/imports/{import_record.id}/download",
                headers=auth_headers
            )

            assert response.status_code == 200
            assert expected_media_type in response.headers['content-type']
