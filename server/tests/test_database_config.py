import pytest

from src.database.core import is_postgresql_url, validate_database_url


def test_postgresql_urls_are_accepted():
    assert is_postgresql_url("postgresql://user:pass@localhost/trustshare")
    assert is_postgresql_url("postgresql+psycopg2://user:pass@localhost/trustshare")


def test_sqlite_is_rejected_when_postgresql_is_required():
    with pytest.raises(RuntimeError, match="requires PostgreSQL"):
        validate_database_url("sqlite:///./app.db", require_postgresql=True)


def test_sqlite_remains_available_for_isolated_unit_tests():
    validate_database_url("sqlite:///./test.db", require_postgresql=False)
