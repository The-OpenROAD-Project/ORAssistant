"""Unit tests for database configuration and session management."""

import pytest
import os
from unittest.mock import patch, Mock
from sqlalchemy.exc import OperationalError
from src.database import config
from src.database.config import (
    get_database_url,
    is_database_available,
    init_database,
    get_db,
)


class TestGetDatabaseUrl:
    """Test suite for database URL construction."""

    def test_get_database_url_all_vars_set(self):
        """Test database URL construction with all environment variables set."""
        with patch.dict(
            os.environ,
            {
                "POSTGRES_USER": "testuser",
                "POSTGRES_PASSWORD": "testpass",
                "POSTGRES_HOST": "localhost",
                "POSTGRES_PORT": "5432",
                "POSTGRES_DB": "testdb",
            },
        ):
            url = get_database_url()

            assert url == "postgresql://testuser:testpass@localhost:5432/testdb"

    def test_get_database_url_different_host(self):
        """Test database URL with different host."""
        with patch.dict(
            os.environ,
            {
                "POSTGRES_USER": "user",
                "POSTGRES_PASSWORD": "pass",
                "POSTGRES_HOST": "db.example.com",
                "POSTGRES_PORT": "5433",
                "POSTGRES_DB": "mydb",
            },
        ):
            url = get_database_url()

            assert url == "postgresql://user:pass@db.example.com:5433/mydb"


class TestIsDatabaseAvailable:
    """Test suite for database availability check."""

    def test_is_database_available_engine_none(self):
        """Test is_database_available returns False when engine is None."""
        with patch.object(config, "engine", None):
            result = is_database_available()

            assert result is False

    def test_is_database_available_connection_success(self):
        """Test is_database_available returns True when connection succeeds."""
        mock_engine = Mock()
        mock_conn = Mock()
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = Mock(return_value=False)

        with patch.object(config, "engine", mock_engine):
            result = is_database_available()

            assert result is True
            mock_conn.execute.assert_called_once()

    def test_is_database_available_connection_fails(self):
        """Test is_database_available returns False on OperationalError."""
        mock_engine = Mock()
        mock_engine.connect.side_effect = OperationalError("", "", "")

        with patch.object(config, "engine", mock_engine):
            result = is_database_available()

            assert result is False


class TestInitDatabase:
    """Test suite for database initialization."""

    def setUp(self):
        """Reset global state before each test."""
        config.engine = None
        config.SessionLocal = None
        config._db_initialized = False

    def test_init_database_already_initialized(self):
        """Test init_database returns True when already initialized and available."""
        self.setUp()
        mock_engine = Mock()

        with patch.object(config, "engine", mock_engine), patch.object(
            config, "SessionLocal", Mock()
        ), patch.object(config, "_db_initialized", True), patch(
            "src.database.config.is_database_available", return_value=True
        ):
            result = init_database()

            assert result is True

    def test_init_database_creates_engine(self):
        """Test init_database creates engine when None."""
        self.setUp()

        with patch.dict(
            os.environ,
            {
                "POSTGRES_USER": "user",
                "POSTGRES_PASSWORD": "pass",
                "POSTGRES_HOST": "localhost",
                "POSTGRES_PORT": "5432",
                "POSTGRES_DB": "testdb",
            },
        ), patch("src.database.config.create_engine") as mock_create_engine, patch(
            "src.database.config.is_database_available", return_value=True
        ), patch("src.database.config.inspect") as mock_inspect:
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine
            mock_inspector = Mock()
            mock_inspector.get_table_names.return_value = ["conversations", "messages"]
            mock_inspect.return_value = mock_inspector

            result = init_database()

            assert result is True
            mock_create_engine.assert_called_once()
            # Verify pool configuration
            call_kwargs = mock_create_engine.call_args[1]
            assert call_kwargs["pool_size"] == 10
            assert call_kwargs["max_overflow"] == 20
            assert call_kwargs["pool_pre_ping"] is True
            assert call_kwargs["echo"] is False
            assert call_kwargs["connect_args"]["connect_timeout"] == 5

    def test_init_database_creates_tables_when_not_exist(self):
        """Test init_database creates tables when they don't exist."""
        self.setUp()

        with patch.dict(
            os.environ,
            {
                "POSTGRES_USER": "user",
                "POSTGRES_PASSWORD": "pass",
                "POSTGRES_HOST": "localhost",
                "POSTGRES_PORT": "5432",
                "POSTGRES_DB": "testdb",
            },
        ), patch("src.database.config.create_engine") as mock_create_engine, patch(
            "src.database.config.is_database_available", return_value=True
        ), patch("src.database.config.inspect") as mock_inspect, patch(
            "src.database.config.Base"
        ) as mock_base:
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine
            mock_inspector = Mock()
            mock_inspector.get_table_names.return_value = []
            mock_inspect.return_value = mock_inspector

            result = init_database()

            assert result is True
            mock_base.metadata.create_all.assert_called_once_with(bind=mock_engine)

    def test_init_database_skips_table_creation_when_exist(self):
        """Test init_database skips table creation when they already exist."""
        self.setUp()

        with patch.dict(
            os.environ,
            {
                "POSTGRES_USER": "user",
                "POSTGRES_PASSWORD": "pass",
                "POSTGRES_HOST": "localhost",
                "POSTGRES_PORT": "5432",
                "POSTGRES_DB": "testdb",
            },
        ), patch("src.database.config.create_engine") as mock_create_engine, patch(
            "src.database.config.is_database_available", return_value=True
        ), patch("src.database.config.inspect") as mock_inspect, patch(
            "src.database.config.Base"
        ) as mock_base:
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine
            mock_inspector = Mock()
            mock_inspector.get_table_names.return_value = ["conversations", "messages"]
            mock_inspect.return_value = mock_inspector

            result = init_database()

            assert result is True
            mock_base.metadata.create_all.assert_not_called()

    def test_init_database_returns_false_when_unavailable(self):
        """Test init_database returns False when database is unavailable."""
        self.setUp()

        with patch.dict(
            os.environ,
            {
                "POSTGRES_USER": "user",
                "POSTGRES_PASSWORD": "pass",
                "POSTGRES_HOST": "localhost",
                "POSTGRES_PORT": "5432",
                "POSTGRES_DB": "testdb",
            },
        ), patch("src.database.config.create_engine") as mock_create_engine, patch(
            "src.database.config.is_database_available", return_value=False
        ):
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine

            result = init_database()

            assert result is False
            assert config._db_initialized is False

    def test_init_database_handles_operational_error(self):
        """Test init_database handles OperationalError gracefully."""
        self.setUp()

        with patch.dict(
            os.environ,
            {
                "POSTGRES_USER": "user",
                "POSTGRES_PASSWORD": "pass",
                "POSTGRES_HOST": "localhost",
                "POSTGRES_PORT": "5432",
                "POSTGRES_DB": "testdb",
            },
        ), patch(
            "src.database.config.create_engine",
            side_effect=OperationalError("", "", ""),
        ):
            result = init_database()

            assert result is False
            assert config._db_initialized is False

    def test_init_database_handles_generic_exception(self):
        """Test init_database handles generic exceptions gracefully."""
        self.setUp()

        with patch.dict(
            os.environ,
            {
                "POSTGRES_USER": "user",
                "POSTGRES_PASSWORD": "pass",
                "POSTGRES_HOST": "localhost",
                "POSTGRES_PORT": "5432",
                "POSTGRES_DB": "testdb",
            },
        ), patch(
            "src.database.config.create_engine",
            side_effect=Exception("Unexpected error"),
        ):
            result = init_database()

            assert result is False
            assert config._db_initialized is False


class TestGetDb:
    """Test suite for database session generator."""

    def setUp(self):
        """Reset global state before each test."""
        config.engine = None
        config.SessionLocal = None
        config._db_initialized = False

    def test_get_db_initializes_if_not_initialized(self):
        """Test get_db calls init_database if not initialized."""
        self.setUp()

        with patch(
            "src.database.config.init_database", return_value=True
        ) as mock_init, patch.object(
            config, "SessionLocal", Mock()
        ) as mock_session_local:
            mock_session = Mock()
            mock_session_local.return_value = mock_session

            # Use generator
            gen = get_db()
            session = next(gen)

            mock_init.assert_called_once()
            assert session == mock_session

            # Clean up generator
            try:
                next(gen)
            except StopIteration:
                pass

    def test_get_db_raises_when_session_local_none(self):
        """Test get_db raises RuntimeError when SessionLocal is None."""
        self.setUp()

        with patch(
            "src.database.config.init_database", return_value=False
        ), patch.object(config, "SessionLocal", None), patch.object(
            config, "_db_initialized", False
        ):
            with pytest.raises(
                RuntimeError, match="Database session factory not initialized"
            ):
                gen = get_db()
                next(gen)

    def test_get_db_closes_session(self):
        """Test get_db properly closes session in finally block."""
        self.setUp()

        mock_session = Mock()
        mock_session_local = Mock(return_value=mock_session)

        with patch(
            "src.database.config.init_database", return_value=True
        ), patch.object(config, "SessionLocal", mock_session_local), patch.object(
            config, "_db_initialized", True
        ):
            # Use generator
            gen = get_db()
            session = next(gen)

            assert session == mock_session

            # Trigger finally block by completing iteration
            try:
                next(gen)
            except StopIteration:
                pass

            # Verify session was closed
            mock_session.close.assert_called_once()

    def test_get_db_closes_session_on_exception(self):
        """Test get_db closes session even when exception occurs."""
        self.setUp()

        mock_session = Mock()
        mock_session_local = Mock(return_value=mock_session)

        with patch(
            "src.database.config.init_database", return_value=True
        ), patch.object(config, "SessionLocal", mock_session_local), patch.object(
            config, "_db_initialized", True
        ):
            gen = get_db()
            _session = next(gen)

            # Simulate exception in code using the session
            try:
                raise ValueError("Test exception")
            except ValueError:
                pass

            # Complete generator
            try:
                next(gen)
            except StopIteration:
                pass

            # Session should still be closed
            mock_session.close.assert_called_once()
