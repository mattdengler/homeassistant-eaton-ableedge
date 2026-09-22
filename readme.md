> [!CAUTION]
> This project is under initial development and is not yet fully working and tested.

# Eaton AbleEdge Home Assistant Integration

A custom Home Assistant integration for Eaton AbleEdge Breakers.

> **Status:** Initial working integration skeleton. The `custom_components/eaton_ableedge/` integration implements the API flow, config flow, coordinator, and basic entities described below, but has not yet been exercised against the live Eaton API with real credentials. See "Manual testing with real Eaton credentials" below.

## Goal

This project will provide a Home Assistant integration for monitoring and controlling Eaton AbleEdge Breakers through Eaton's developer APIs, where supported by Eaton and by the user's Eaton account/API access.

## Eaton developer setup

Start with Eaton's developer resources:

- Eaton Developer Portal: https://developer.eaton.com/get-started
- Eaton For Developers page: https://www.eaton.com/us/en-us/digital/for-developer-partners.html

### 1. Create or sign in to an Eaton developer account

Use the Eaton Developer Portal to sign in with an existing Eaton account or register a new developer account.

After signing in, review the available API catalog and any terms of use for APIs related to AbleEdge Breakers.

### 2. Create a team

Eaton uses teams to group users who share access to applications and credentials.

From the Eaton developer resources:

1. Navigate to **Manage your teams** / **Teams**.
2. Create a new team.
3. Provide a clear team name and optional description.
4. Add team members as needed.
5. Assign appropriate roles:
   - **Owner**: full team control, including member management.
   - **App admin**: can request API access and manage app credentials.
   - **Viewer**: can view the app and credentials.

For a personal Home Assistant setup, a team with only yourself as the initial member should be sufficient to start.

### 3. Create an app

After creating a team:

1. Navigate to **Manage your apps** / **My Apps**.
2. Create a new app for this Home Assistant integration.
3. Associate the app with the team.
4. Request access to the relevant Eaton API product(s) for AbleEdge Breakers. Specifically, request access to:
   - AbleEdge Authorize API
   - AbleEdge API
5. Wait for any required Eaton API product-owner approval.
6. Once enabled, collect the app credentials needed by the integration, such as:
   - App ID
   - API Key
   - API Secret (taking note of the expiration date!)

### 4. Create an AbleEdge organization

After the Eaton developer app has the required API access:

1. Go to the AbleEdge Portal: https://ableedge-portal.eaton.com
2. Log in with your Eaton account.
3. Create a new Organization.
4. Collect the organization details needed by the integration:
   - Organization ID
   - Client ID
   - Generate a secret (taking note of the expiration date!)

Do **not** commit Eaton credentials to this repository.

## Planned Home Assistant configuration

The integration should support setup through the Home Assistant UI config flow.

The user will need to provide the following values:

- `API_KEY`
- `API_SECRET`
- `CLIENT_ID`
- `EATON_ACCOUNT_USERNAME`
- `EATON_ACCOUNT_PASSWORD`
- `ORGANIZATION_SECRET`
- `BREAKER_ID`

The `API_SECRET` and `ORGANIZATION_SECRET` are only valid for one year. They are generated from Eaton's secure apps page:

- Eaton secure apps: https://www.eaton.com/us/en-us/digital/secure/apps.html

The integration should use Home Assistant's config entry storage for these values, mark secret fields as passwords in the config flow, and redact all credential values from logs, diagnostics, and error messages.

## Planned API flow

The curl examples below describe the tested Eaton API behavior. The actual Home Assistant integration should implement this flow in Python using Home Assistant's async HTTP client rather than shelling out to `curl` or `base64`.

### Runtime credential names

- `API_KEY`: Eaton app API key.
- `API_SECRET`: Eaton app API secret.
- `CLIENT_ID`: AbleEdge organization client ID.
- `EATON_ACCOUNT_USERNAME`: Eaton account email/username.
- `EATON_ACCOUNT_PASSWORD`: Eaton account password.
- `ORGANIZATION_SECRET`: AbleEdge organization secret.
- `BREAKER_ID`: AbleEdge breaker UUID.
- `BASE64_ENCODED_API_KEY_AND_SECRET`: Base64 encoded `<API_KEY>:<API_SECRET>` value.
- `OAUTH_TOKEN`: Eaton OAuth access token.
- `SESSION_ACCESS_TOKEN`: AbleEdge user session access token returned from user login.
- `ORGANIZATION_TOKEN`: AbleEdge organization token used for breaker management requests.

### Step 1: Build the Basic authorization value

When the `API_KEY` is entered or changed, build the Basic authorization value from the API key and secret:

```shell
echo -n "<API_KEY>:<API_SECRET>" | base64
```

The output is `BASE64_ENCODED_API_KEY_AND_SECRET`.

In the Home Assistant integration, do this directly in Python instead of executing a shell command:

```python
import base64

base64_encoded_api_key_and_secret = base64.b64encode(
    f"{api_key}:{api_secret}".encode("utf-8")
).decode("ascii")
```

This value can be recalculated when needed; it does not need to be stored separately if `API_KEY` and `API_SECRET` are already stored securely in the config entry.

### Step 2: Generate the Eaton OAuth token

Generate an Eaton OAuth token with the client credentials grant:

```shell
curl -X POST "https://api.eaton.com/oauth/accesstoken?grant_type=client_credentials" \
  -d "" \
  -H "Authorization: Basic <BASE64_ENCODED_API_KEY_AND_SECRET>" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

The response is JSON. Store the `access_token` value as `OAUTH_TOKEN` and use the `expires_in` value to determine when the token must be refreshed.

This token should be refreshed before it expires. The observed flow requires generating it approximately once per day, but the integration should rely on the `expires_in` value and refresh with a safety margin.

### Step 3: Authorize the Eaton user

Authorize the Eaton account user with the OAuth token:

```shell
curl --compressed -X POST "https://api.eaton.com/ableedge/authorization/v1/users/login" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <OAUTH_TOKEN>" \
  --data '{"email":"<EATON_ACCOUNT_USERNAME>","password":"<EATON_ACCOUNT_PASSWORD>"}'
```

The response is JSON containing the user's authorization information. Store the `accessToken` value as `SESSION_ACCESS_TOKEN` for AbleEdge requests that require the user session token.

### Step 4: Get the organization token

Get a JWT for the AbleEdge organization service account:

```shell
curl --compressed -X POST "https://api.eaton.com/ableedge/authorization/v1/organizations/token" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <OAUTH_TOKEN>" \
  --data '{"clientId":"<CLIENT_ID>","secret":"<ORGANIZATION_SECRET>"}'
```

The response is JSON containing the organization `token`. Store this value as `ORGANIZATION_TOKEN` and use it for breaker management API requests.

### Step 5: Get breaker data

Fetch breaker details with the organization token:

```shell
curl --compressed -X GET "https://api.eaton.com/ableedge/breakermanagement/v1/breakers/<BREAKER_ID>" \
  -H "accept: application/json" \
  -H "api-key: <API_KEY>" \
  -H "authorization: Bearer <ORGANIZATION_TOKEN>"
```

The response contains breaker metadata, status, static data, configuration, and telemetry data.

Example response:

```json
{
  "id": "00000000-0000-0000-0000-000000000000",
  "metadata": {
    "loadcenterId": "00000000-0000-0000-0000-000000000000",
    "siteId": "00000000-0000-0000-0000-000000000000"
  },
  "status": {
    "remoteContactPosition": {
      "val": "Open",
      "ts": 1789380404
    },
    "mainHandlePosition": {
      "val": "Closed",
      "ts": 1788826286
    },
    "loadStatus": {
      "val": false,
      "ts": 1789380405
    }
  },
  "staticData": {
    "ratedCurrent": 60,
    "serialNumber": "0000AA0000000000",
    "partNumber": "SBR260WGF",
    "macAddress": "00:00:00:00:00:00"
  },
  "configuration": {
    "autoLoadShedEnabled": {
      "val": true,
      "ts": 1783792542
    },
    "firmwareVersion": {
      "val": "25.11.05",
      "ts": 1787111141
    },
    "networkSSID": {
      "val": "Brain",
      "ts": 1787111141
    },
    "ipAddress": {
      "val": "192.168.0.20",
      "ts": 1787111141
    }
  },
  "telemetryData": {
    "rssi": {
      "val": -81,
      "ts": 1789386462
    },
    "meter": {
      "current": {},
      "voltage": {},
      "powerFactor": {},
      "activePower": {},
      "reactivePower": {},
      "apparentPower": {},
      "activeEnergy": {},
      "reactiveEnergy": {},
      "apparentEnergy": {},
      "reverseActiveEnergy": {},
      "reverseApparentEnergy": {},
      "frequency": {}
    },
    "lastUpdate": 1789386462,
    "isConnected": {
      "val": true,
      "ts": 1789386481
    }
  }
}
```

## Planned implementation approach

The integration should implement the API flow using Home Assistant best practices:

- Use a config flow for setup and reauthentication.
- Use Home Assistant's shared async HTTP client instead of blocking HTTP calls.
- Avoid shell commands; generate Base64 values in Python.
- Cache tokens in memory and track their expiration timestamps.
- Refresh `OAUTH_TOKEN` before `expires_in` elapses, with a safety margin.
- Refresh `SESSION_ACCESS_TOKEN` and `ORGANIZATION_TOKEN` when needed or when the API returns an authorization failure.
- Use a `DataUpdateCoordinator` to poll breaker state and share updates across entities.
- Keep secrets out of entity state, logs, diagnostics, issue reports, and exceptions.
- Use Home Assistant repairs or config-entry reauth when one-year Eaton secrets expire.

## Planned features

Initial feature targets:

- Authenticate with Eaton's developer APIs.
- Discover or configure AbleEdge Breakers associated with the Eaton account/app.
- Create Home Assistant devices and entities for each breaker.
- Expose breaker state, availability, and telemetry where supported.
- Provide diagnostics without exposing secrets.

Potential future features:

- Config flow and options flow.
- Repairs for expired or revoked credentials.
- Device triggers and events.
- Energy dashboard support, if the API exposes suitable energy measurements.

## Repository layout

Implemented Home Assistant custom integration layout:

```text
custom_components/
  eaton_ableedge/
    __init__.py
    manifest.json
    config_flow.py
    const.py
    coordinator.py
    api.py
    entity.py
    sensor.py
    binary_sensor.py
    diagnostics.py
    strings.json
    translations/
      en.json
tests/
  conftest.py
  test_api.py
  test_config_flow.py
  test_integration.py
```

> Note: a `switch.py` platform (e.g. for remote breaker control) is not yet
> implemented. The Eaton breaker management API used here is currently
> treated as read-only; add a `switch` platform if/when a supported write
> endpoint is confirmed.

## Manual testing with real Eaton credentials

1. Copy `custom_components/eaton_ableedge/` into your Home Assistant
   `config/custom_components/` directory (or symlink it) and restart Home
   Assistant.
2. In the Home Assistant UI, go to **Settings → Devices & Services → Add
   Integration** and search for "Eaton AbleEdge Breakers".
3. Enter the values collected during the Eaton developer/AbleEdge portal
   setup above: `API_KEY`, `API_SECRET`, `CLIENT_ID`,
   `EATON_ACCOUNT_USERNAME`, `EATON_ACCOUNT_PASSWORD`, `ORGANIZATION_SECRET`,
   and `BREAKER_ID`.
4. On submit, the config flow performs the full API flow (OAuth token, user
   login, organization token, and an initial breaker fetch) to validate the
   credentials before creating the entry.
5. Once set up, a device for the breaker should appear with sensors for
   remote contact position, main handle position, signal strength, rated
   current, firmware version, and IP address, plus binary sensors for
   connectivity and load status. Data refreshes every 40 seconds by default
   (see "API rate limits" below).
6. Use **Settings → Devices & Services → (entry) → Download diagnostics** to
   confirm all secrets and tokens are redacted.

## API rate limits

The Eaton developer free tier allows only **100 API requests per hour**. The
integration only calls the breaker management endpoint on each poll (the
OAuth, user login, and organization tokens are cached in memory and reused
until they expire), so the `DataUpdateCoordinator`'s polling interval
directly controls the request rate.

- `MAX_API_REQUESTS_PER_HOUR` (100) and `MANUAL_TESTING_REQUEST_HEADROOM`
  (10) in `const.py` define the budget: automated polling is capped at 90
  requests/hour, reserving 10 requests/hour of headroom for manual testing
  (e.g. curl or the Eaton developer portal) without risking a 429.
- `DEFAULT_SCAN_INTERVAL` is derived from that budget (currently 40 seconds)
  rather than hard-coded, so adjusting the constants in `const.py` keeps the
  polling interval and the stated budget in sync.
- If you need more manual testing headroom, increase
  `MANUAL_TESTING_REQUEST_HEADROOM` (reserving more requests) or otherwise
  adjust `DEFAULT_SCAN_INTERVAL` directly; just keep the total under
  100/hour.

## Security notes

- Never commit client secrets, API keys, passwords, organization secrets, refresh tokens, access tokens, or organization tokens.
- Store user-provided credentials through Home Assistant's config entry storage.
- Prefer short-lived in-memory storage for generated tokens.
- Redact credentials and tokens from logs and diagnostics.
- Follow Eaton's API terms of use and rate limits.

## Development notes

This integration is intended to be developed as a Home Assistant custom component first. Once stable, it can be evaluated against Home Assistant's integration quality scale and contribution requirements.

Install the test dependencies and supply a valid breaker UUID at test runtime:

```shell
python -m pip install -r requirements-test.txt
EATON_TEST_BREAKER_ID="<BREAKER_ID>" pytest
```

The test suite uses this value only in mocked URLs, config entries, and response
data; it does not make requests to the Eaton API. You can alternatively pass
`pytest --breaker-id "<BREAKER_ID>"`. Pytest exits with an explanatory error if
the value is missing or is not a valid UUID.

## References

- Eaton Developer Portal - Get Started: https://developer.eaton.com/get-started
- Eaton For Developers: https://www.eaton.com/us/en-us/digital/for-developer-partners.html
- AbleEdge Portal: https://ableedge-portal.eaton.com
- Eaton secure apps: https://www.eaton.com/us/en-us/digital/secure/apps.html
- Home Assistant developer documentation: https://developers.home-assistant.io/
