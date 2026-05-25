# Shark IQ (Local) — Home Assistant Integration

[![hassfest](https://github.com/charger68/sharkiq_local/actions/workflows/hassfest.yml/badge.svg)](https://github.com/charger68/sharkiq_local/actions/workflows/hassfest.yml)
[![HACS](https://github.com/charger68/sharkiq_local/actions/workflows/hacs.yml/badge.svg)](https://github.com/charger68/sharkiq_local/actions/workflows/hacs.yml)

A Home Assistant custom integration for **Shark IQ robot vacuums**, powered by the [`sharklocal`](https://github.com/sharkiqlibs/sharklocal) library. Talks to your vacuums entirely over your LAN — no cloud account or internet round-trip.

Supports **multiple vacuums** — add each one through the UI and they appear as separate devices.

## Features

- **Vacuum entity per device** with start / stop / pause / return-to-base controls
- **Battery sensor** (separate, the proper HA way)
- **Diagnostic sensors**: Wi-Fi SSID, signal strength (RSSI), IP address (disabled by default)
- Uses both REST and MQTT transports for the best feature coverage
- Polls every 30 seconds; falls back from REST to MQTT automatically if needed

## Requirements

- Home Assistant 2025.1 or newer (uses the new `VacuumActivity` API)
- Python 3.11+ (HA already meets this)
- Each Shark IQ on your network with a known IP — give them static DHCP reservations

## Installation

### Option A: HACS (recommended)

1. In HACS, go to **Integrations**
2. Click the three-dot menu (top right) → **Custom repositories**
3. Add `https://github.com/charger68/sharkiq_local` with category **Integration**
4. Find **Shark IQ (Local)** in the integrations list and install
5. Restart Home Assistant

### Option B: Manual

1. Download the latest release zip from the [Releases page](https://github.com/charger68/sharkiq_local/releases)
2. Extract and copy `custom_components/sharkiq_local/` into your HA `config/custom_components/` directory
3. Restart Home Assistant

## Setup

1. Find each vacuum's IP address (router DHCP list, or run `nmap -sn 192.168.1.0/24`)
2. Give each one a static DHCP reservation in your router so the IP doesn't change
3. In HA: **Settings → Devices & Services → Add Integration → Shark IQ (Local)**
4. Enter the IP and a friendly name (e.g. `Downstairs Shark`)
5. Submit. Repeat for your second vacuum.

Each vacuum becomes its own device with its own entities:

```
vacuum.downstairs_shark
sensor.downstairs_shark_battery
vacuum.upstairs_shark
sensor.upstairs_shark_battery
```

## Configuration options

When adding a vacuum:

| Field | Default | Notes |
|---|---|---|
| IP address | — | e.g. `192.168.1.100` |
| Name | — | shown in HA |
| Mapping | `sharkiq_v1` | the only built-in mapping today |
| Also enable MQTT | on | gives real-time mode updates between polls |

### Adjusting the polling interval

After setup, click **Configure** on the integration card (Settings → Devices & Services → Shark IQ (Local) → your vacuum) to change how often the integration polls each vacuum for status.

- **Default 30 seconds** — sensible balance of freshness and network traffic
- **15 seconds** — snappier dashboard feel, fine for daily use
- **10 seconds** — works, but you won't really notice the improvement
- **Under 5 seconds** — not allowed; no benefit and risks racing requests
- **60+ seconds** — fine if you mostly drive automations off MQTT mode-change events (which push instantly regardless of poll rate); battery numbers will just be staler

Range: 5 to 600 seconds. Changes apply immediately, no restart needed.

## Example automation

Run both vacuums at 10am on weekdays:

```yaml
automation:
  - alias: "Vacuum on weekdays"
    triggers:
      - trigger: time
        at: "10:00:00"
    conditions:
      - condition: time
        weekday: [mon, tue, wed, thu, fri]
    actions:
      - action: vacuum.start
        target:
          entity_id:
            - vacuum.downstairs_shark
            - vacuum.upstairs_shark
```

Notify when battery is low:

```yaml
automation:
  - alias: "Shark battery low"
    triggers:
      - trigger: numeric_state
        entity_id:
          - sensor.downstairs_shark_battery
          - sensor.upstairs_shark_battery
        below: 20
    actions:
      - action: notify.mobile_app_phone
        data:
          message: "{{ trigger.to_state.attributes.friendly_name }} is at {{ trigger.to_state.state }}%."
```

## Troubleshooting

**"Cannot connect" when adding** — Confirm the IP responds to a ping and that you typed it correctly. The Shark needs to be on the same VLAN as Home Assistant.

**Entity goes unavailable** — Check HA logs for `sharkiq_local`. The vacuum may be asleep on the dock; it should wake on the next poll.

**Mode shows as `idle` instead of `docked`** — The Shark REST API conflates these. The library uses the `charging` field to tell them apart; if `charging` is reading as `unconnected` but the vacuum is on the dock, the dock plate may not be making contact.

## Credits

- [`sharklocal`](https://github.com/sharkiqlibs/sharklocal) — the underlying Python library doing all the protocol work
- The Shark IQ reverse-engineering community
