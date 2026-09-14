"""Constants for the Eaton AbleEdge Breakers integration."""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "eaton_ableedge"
MANUFACTURER = "Eaton"

# Config entry / options data keys.
# These intentionally mirror the README's runtime credential names while
# following Home Assistant's lower_snake_case convention for storage keys.
CONF_API_KEY = "api_key"
CONF_API_SECRET = "api_secret"
CONF_CLIENT_ID = "client_id"
CONF_EATON_ACCOUNT_USERNAME = "eaton_account_username"
CONF_EATON_ACCOUNT_PASSWORD = "eaton_account_password"
CONF_ORGANIZATION_SECRET = "organization_secret"
CONF_BREAKER_ID = "breaker_id"

# Eaton API endpoints.
OAUTH_TOKEN_URL = "https://api.eaton.com/oauth/accesstoken"
USER_LOGIN_URL = "https://api.eaton.com/ableedge/authorization/v1/users/login"
ORGANIZATION_TOKEN_URL = (
    "https://api.eaton.com/ableedge/authorization/v1/organizations/token"
)
BREAKER_URL_TEMPLATE = (
    "https://api.eaton.com/ableedge/breakermanagement/v1/breakers/{breaker_id}"
)

# Refresh the OAuth token this many seconds before it actually expires.
TOKEN_REFRESH_SAFETY_MARGIN_SECONDS = 300
# Fallback lifetime to assume if the API does not return `expires_in`.
DEFAULT_TOKEN_LIFETIME_SECONDS = 86400

DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)

# Keys that must always be redacted from diagnostics output.
REDACT_KEYS = {
    CONF_API_KEY,
    CONF_API_SECRET,
    CONF_CLIENT_ID,
    CONF_EATON_ACCOUNT_USERNAME,
    CONF_EATON_ACCOUNT_PASSWORD,
    CONF_ORGANIZATION_SECRET,
    "oauth_token",
    "access_token",
    "session_access_token",
    "organization_token",
    "authorization",
    "password",
    "token",
    "secret",
}
