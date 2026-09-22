"""Test fixtures for the Eaton AbleEdge Breakers integration tests."""
from __future__ import annotations

import os
from uuid import UUID

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"

BREAKER_ID_ENV_VAR = "EATON_TEST_BREAKER_ID"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add the breaker ID test option."""
    parser.addoption(
        "--breaker-id",
        help=f"Breaker UUID used by tests (or set {BREAKER_ID_ENV_VAR})",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Validate and store the breaker ID supplied for tests."""
    breaker_id = config.getoption("breaker_id") or os.environ.get(BREAKER_ID_ENV_VAR)
    if not breaker_id:
        raise pytest.UsageError(
            f"Provide a breaker UUID with --breaker-id or {BREAKER_ID_ENV_VAR}"
        )

    try:
        config.option.breaker_id = str(UUID(breaker_id))
    except ValueError as err:
        raise pytest.UsageError(
            f"--breaker-id/{BREAKER_ID_ENV_VAR} must be a valid UUID"
        ) from err


@pytest.fixture(scope="session")
def breaker_id(pytestconfig: pytest.Config) -> str:
    """Return the validated breaker ID supplied for tests."""
    return pytestconfig.getoption("breaker_id")


@pytest.fixture
def config_data(breaker_id: str) -> dict[str, str]:
    """Return config entry data using the supplied breaker ID."""
    return {
        "api_key": "api-key",
        "api_secret": "api-secret",
        "client_id": "client-id",
        "eaton_account_username": "user@example.com",
        "eaton_account_password": "password",
        "organization_secret": "org-secret",
        "breaker_id": breaker_id,
    }


@pytest.fixture
def sample_breaker_response(breaker_id: str) -> dict:
    """Return sample API data using the supplied breaker ID."""
    return {
        "id": breaker_id,
        "status": {
            "remoteContactPosition": {"val": "Open", "ts": 1789380404},
            "mainHandlePosition": {"val": "Closed", "ts": 1788826286},
            "loadStatus": {"val": False, "ts": 1789380405},
        },
        "staticData": {
            "ratedCurrent": 60,
            "serialNumber": "0000HA2605080127",
            "partNumber": "SBR260WGF",
            "macAddress": "F0:24:F9:1A:F1:00",
        },
        "configuration": {
            "firmwareVersion": {"val": "25.11.05", "ts": 1787111141},
            "ipAddress": {"val": "192.168.7.123", "ts": 1787111141},
        },
        "telemetryData": {
            "rssi": {"val": -81, "ts": 1789386462},
            "isConnected": {"val": True, "ts": 1789386481},
        },
    }


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests in this package."""
    yield
