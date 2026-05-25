# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] - 2026-05-25

### Added
- Initial release
- Config flow for adding multiple Shark IQ vacuums (one entry per vacuum)
- Vacuum entity using new `VacuumActivity` enum (HA 2025.1+)
- Battery sensor (separate, per HA's deprecation of `battery_level` on vacuum entities)
- Diagnostic sensors: Wi-Fi SSID, RSSI, IP address (disabled by default)
- REST + MQTT transport, with REST → MQTT fallback handled by `sharklocal`
- 30-second polling via `DataUpdateCoordinator`
