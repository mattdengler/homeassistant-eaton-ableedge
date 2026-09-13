# Eaton AbleEdge Home Assistant Integration

A custom Home Assistant integration for Eaton AbleEdge Breakers.

> **Status:** Planning / initial setup. This repository is not yet a working Home Assistant integration.

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
   - API Secret
   Take note of the expiration date!

Do **not** commit Eaton credentials to this repository.

## Planned Home Assistant configuration

The integration should eventually support setup through the Home Assistant UI config flow. Until that exists, expected configuration values may include:

- Eaton client ID
- Eaton client secret
- Eaton API key, if required
- Eaton account, team, or site identifier, if required by the API
- Polling interval

## Planned features

Initial feature targets:

- Authenticate with Eaton's developer APIs.
- Discover AbleEdge Breakers associated with the Eaton account/app.
- Create Home Assistant devices and entities for each breaker.
- Expose breaker state, availability, and telemetry where supported.
- Provide diagnostics without exposing secrets.

Potential future features:

- Config flow and options flow.
- Repairs for expired or revoked credentials.
- Device triggers and events.
- Energy dashboard support, if the API exposes suitable energy measurements.

## Repository layout

Expected Home Assistant custom integration layout:

```text
custom_components/
  eaton_ableedge/
    __init__.py
    manifest.json
    config_flow.py
    const.py
    coordinator.py
    sensor.py
    switch.py
    diagnostics.py
```

## Security notes

- Never commit client secrets, API keys, refresh tokens, or access tokens.
- Store credentials through Home Assistant's config entry storage.
- Redact credentials from logs and diagnostics.
- Follow Eaton's API terms of use and rate limits.

## Development notes

This integration is intended to be developed as a Home Assistant custom component first. Once stable, it can be evaluated against Home Assistant's integration quality scale and contribution requirements.

## References

- Eaton Developer Portal - Get Started: https://developer.eaton.com/get-started
- Eaton For Developers: https://www.eaton.com/us/en-us/digital/for-developer-partners.html
- Home Assistant developer documentation: https://developers.home-assistant.io/
