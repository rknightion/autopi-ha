---
title: Security
description: What the AutoPi integration can access, where it sends data, what it logs, and how to report a vulnerability
---

# Security

This page covers the credentials the integration needs, where they're stored, what leaves your
Home Assistant instance, what ends up in the log, and how to report a security issue.

## Credentials and their scope

The integration authenticates to the AutoPi API with a single **API token**, generated at
[app.autopi.io](https://app.autopi.io) under **Account Settings → API Tokens** and entered during
setup (or during reauth, if it's later revoked or rotated). It's sent on every request as an
`Authorization: APIToken <key>` header.

The token's actual scope is whatever permissions you grant it in the AutoPi dashboard when you
create it - the integration doesn't request or enforce a narrower scope itself. [Getting
Started](getting-started.md) and [Configuration](configuration.md) recommend granting at minimum
**Read Vehicles**, **Read Vehicle Data**, and **Read Positions**, and nothing else. Use a token
scoped to read access only; there's no functional reason to grant it more, since the integration
never writes anything back (see [Read-only operation](#read-only-operation) below).

If you monitor multiple AutoPi accounts, each config entry needs its own token - one integration
instance is scoped to one account.

## Where the token is stored

The token is stored in Home Assistant's normal config entry storage
(`.storage/core.config_entries`), the same mechanism every other integration's credentials use.
It is not handled any differently by this integration - protecting it is a matter of protecting
your Home Assistant instance and its `.storage` directory generally (file permissions, backup
encryption, who has shell/API access to the host).

## What leaves your Home Assistant instance

The integration is `cloud_polling` - it has no local mode. Every update makes HTTPS requests to
the AutoPi API, `https://api.autopi.io` by default or a custom **Base URL** if you set one during
setup. That's the only third party in the picture: the requests carry your API token and fetch
vehicle profile, position, status, trip, alert, event, diagnostic, and DTC data depending on which
sensors are active - nothing is sent to any other service.

## Read-only operation

Every request the integration makes to the AutoPi API is an HTTP `GET`. There is no code path that
issues a `POST`, `PUT`, `PATCH`, or `DELETE` against the AutoPi API, so the integration cannot
change vehicle configuration, send commands to the device, or modify anything in your AutoPi
account - it can only read data. This is a property of the client code, not just documentation
intent.

## Logging

Debug logging is opt-in (see [Troubleshooting](troubleshooting.md#reading-the-logs)) and is
verbose by design. What it contains:

- The HTTP method and the **endpoint path only** for every request - the client deliberately logs
  the path rather than the full URL so a custom Base URL isn't repeated into every log line.
- Request parameters, with `api_key` and `token` keys explicitly filtered out before logging.
- Response status codes, and on 4xx/5xx errors, the response body text.
- Auto-Zero specific logs (see [Auto-Zero Debug Logging](debug-auto-zero.md)) that include vehicle
  IDs and sensor values - for example an `Engine RPM for vehicle 123` line - and, for position
  sensors, that means **actual GPS coordinates and other vehicle telemetry appear in the log** at
  debug level while it's enabled.

The API token itself is filtered out of logged request parameters, but sensor values - including
location - are not, because the retry/debug logging exists to show what the integration is doing
with real data. Treat debug logs as containing vehicle location data: don't leave debug logging on
permanently, and redact vehicle IDs/coordinates before pasting logs into a public GitHub issue.

## Reporting a vulnerability

This repository doesn't publish a separate `SECURITY.md`. For a security issue:

- If it's not sensitive (a hardening suggestion, a non-exploitable weakness), open a normal
  [GitHub issue](https://github.com/rknightion/autopi-ha/issues) - the project's contributing
  guide states security issues get priority response.
- If it's sensitive (something exploitable against a live Home Assistant instance or AutoPi
  account), use GitHub's private vulnerability reporting from the repository's **Security** tab
  rather than a public issue, so the report isn't visible before there's a fix.
