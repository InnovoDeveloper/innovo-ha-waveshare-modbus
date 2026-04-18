# Waveshare Modbus Relay — Home Assistant Custom Integration

Custom integration for Home Assistant to control [**Waveshare Modbus PoE ETH Relay (B)**](https://www.waveshare.com/modbus-poe-eth-relay-b.htm) boards and read their digital inputs. Uses Modbus RTU over TCP for reliable communication.

![Waveshare Modbus PoE ETH Relay](https://www.waveshare.com/media/catalog/product/cache/1/image/800x800/9df78eab33525d08d6e5fb8d27136e95/m/o/modbus-poe-eth-relay-b-1.jpg)

Based on [icecoldfire/HomeAssistant-Waveshare-Relay](https://github.com/icecoldfire/HomeAssistant-Waveshare-Relay), rewritten with:
- **Modbus RTU over TCP** (CRC16 framing) instead of Modbus TCP
- **Digital input binary sensors** (detect open/close on DI terminals)
- **UI-configurable feature toggles** (enable/disable switches and inputs)
- **DI toggle mode** (physical buttons toggle corresponding relays)
- Fixed compatibility with Home Assistant 2025.x+

## Features

| Feature | Entity Type | Description |
|---------|------------|-------------|
| Relay control | `switch` | Turn relays ON/OFF, reads back actual state |
| Digital inputs | `binary_sensor` | Detects triggered/open/close on DI terminals |
| DI toggle mode | Config option | Physical buttons on DI terminals toggle relays |

## Links

- [Product page](https://www.waveshare.com/modbus-poe-eth-relay-b.htm) — Waveshare Modbus PoE ETH Relay (B)
- [Wiki / Documentation](https://www.waveshare.com/wiki/Modbus_POE_ETH_Relay_(B)) — Wiring, protocol specs, software tools
- [Original integration](https://github.com/icecoldfire/HomeAssistant-Waveshare-Relay) — Upstream project this is based on

## Requirements

- Home Assistant 2025.1.0 or later
- Waveshare Modbus PoE ETH Relay board (8ch, 4ch, or 2ch)
- Device must be on the same network (or routable) from HA

## Device Configuration

Before adding the integration, configure your Waveshare relay board:

### 1. Access the Device Web Interface

Open a browser and navigate to the device IP (default: `http://192.168.1.200`). Default password: `admin`.

### 2. Network Settings

| Setting | Recommended Value |
|---------|------------------|
| Device IP | Set to your network (e.g., `192.168.10.97`) |
| Device Port | `4196` (default) |
| Work Mode | **TCP Server** |
| IP Mode | DHCP or Static |

### 3. Serial Settings (for RTU over TCP)

| Setting | Value |
|---------|-------|
| Baud Rate | 115200 |
| Data Bits | 8 |
| Parity | None |
| Stop Bits | 1 |

> **Note:** The device port (default 4196) is the Modbus RTU-over-TCP port, NOT the standard Modbus TCP port 502. This integration communicates using raw Modbus RTU frames over the TCP socket.

## Installation

### Manual Installation

1. Copy the `waveshare_relay` folder to your Home Assistant `custom_components` directory:
   ```
   custom_components/
   └── waveshare_relay/
       ├── __init__.py
       ├── binary_sensor.py
       ├── config_flow.py
       ├── const.py
       ├── manifest.json
       ├── switch.py
       ├── utils.py
       └── translations/
           └── en.json
   ```
2. Restart Home Assistant

### HACS Installation (Recommended)

1. Open HACS in Home Assistant
2. Click the **three dots** menu (top right) > **Custom repositories**
3. Add the repository URL:
   ```
   https://github.com/InnovoDeveloper/innovo-ha-waveshare-modbus
   ```
4. Set category to **Integration**
5. Click **Add**
6. Search for **"Waveshare Modbus Relay"** in the HACS store
7. Click **Download**
8. Restart Home Assistant

## Configuration (UI)

1. Go to **Settings > Devices & Services**
2. Click **+ Add Integration**
3. Search for **"Waveshare"**
4. Fill in the configuration:

| Field | Default | Description |
|-------|---------|-------------|
| IP Address | — | Device IP on your network |
| Modbus Port | 4196 | RTU-over-TCP port (check device web UI) |
| Device Name | Waveshare Relay | Friendly name for the device |
| Number of Channels | 8 | Match your board (8, 4, or 2) |
| Enable Relay Switches | ON | Creates switch entities for relay control |
| Enable Digital Inputs | ON | Creates binary_sensor entities for DI terminals |
| DI Toggle Mode | OFF | Physical buttons toggle corresponding relays |

## Entities Created

With all features enabled on an 8-channel board:

**Switches** (relay control):
- `switch.waveshare_relay_1` through `switch.waveshare_relay_8`

**Binary Sensors** (digital inputs):
- `binary_sensor.waveshare_relay_input_1` through `binary_sensor.waveshare_relay_input_8`

## Example YAML Configurations

The integration is fully UI-configured, but here are useful YAML snippets for automations and templates.

### Template Lights (wrap relays as light entities)

Add to `configuration.yaml`:

```yaml
template:
  - light:
      - name: "Light 1"
        unique_id: waveshare_light_1
        state: "{{ is_state('switch.waveshare_relay_1', 'on') }}"
        turn_on:
          - service: switch.turn_on
            target:
              entity_id: switch.waveshare_relay_1
        turn_off:
          - service: switch.turn_off
            target:
              entity_id: switch.waveshare_relay_1

      - name: "Light 2"
        unique_id: waveshare_light_2
        state: "{{ is_state('switch.waveshare_relay_2', 'on') }}"
        turn_on:
          - service: switch.turn_on
            target:
              entity_id: switch.waveshare_relay_2
        turn_off:
          - service: switch.turn_off
            target:
              entity_id: switch.waveshare_relay_2

      # Repeat for channels 3-8...
```

### Automation: DI Toggle Mode on Startup

If you prefer YAML over the config flow option:

```yaml
automation:
  - alias: "Waveshare DI Toggle Mode"
    trigger:
      - platform: homeassistant
        event: start
    action:
      - service: modbus.write_register
        data:
          hub: waveshare_1
          slave: 1
          address: 4096
          value: 2
      - service: modbus.write_register
        data:
          hub: waveshare_1
          slave: 1
          address: 4097
          value: 2
      # Repeat for addresses 4098-4103 (channels 3-8)
```

> **Note:** If you enabled "DI Toggle Mode" in the integration config flow, this automation is not needed — the integration handles it automatically on startup.

### Full Example: configuration.yaml with Waveshare

```yaml
# Main configuration
default_config:

homeassistant:
  country: US
  time_zone: America/New_York

frontend:
  themes: !include_dir_merge_named themes

automation: !include automations.yaml
script: !include scripts.yaml
scene: !include scenes.yaml

# Template lights wrapping Waveshare relays
template:
  - light:
      - name: "Living Room Light"
        unique_id: waveshare_light_1
        state: "{{ is_state('switch.waveshare_relay_1', 'on') }}"
        turn_on:
          - service: switch.turn_on
            target:
              entity_id: switch.waveshare_relay_1
        turn_off:
          - service: switch.turn_off
            target:
              entity_id: switch.waveshare_relay_1

      - name: "Kitchen Light"
        unique_id: waveshare_light_2
        state: "{{ is_state('switch.waveshare_relay_2', 'on') }}"
        turn_on:
          - service: switch.turn_on
            target:
              entity_id: switch.waveshare_relay_2
        turn_off:
          - service: switch.turn_off
            target:
              entity_id: switch.waveshare_relay_2

      - name: "Bedroom Light"
        unique_id: waveshare_light_3
        state: "{{ is_state('switch.waveshare_relay_3', 'on') }}"
        turn_on:
          - service: switch.turn_on
            target:
              entity_id: switch.waveshare_relay_3
        turn_off:
          - service: switch.turn_off
            target:
              entity_id: switch.waveshare_relay_3

      - name: "Bathroom Light"
        unique_id: waveshare_light_4
        state: "{{ is_state('switch.waveshare_relay_4', 'on') }}"
        turn_on:
          - service: switch.turn_on
            target:
              entity_id: switch.waveshare_relay_4
        turn_off:
          - service: switch.turn_off
            target:
              entity_id: switch.waveshare_relay_4

      - name: "Hallway Light"
        unique_id: waveshare_light_5
        state: "{{ is_state('switch.waveshare_relay_5', 'on') }}"
        turn_on:
          - service: switch.turn_on
            target:
              entity_id: switch.waveshare_relay_5
        turn_off:
          - service: switch.turn_off
            target:
              entity_id: switch.waveshare_relay_5

      - name: "Garage Light"
        unique_id: waveshare_light_6
        state: "{{ is_state('switch.waveshare_relay_6', 'on') }}"
        turn_on:
          - service: switch.turn_on
            target:
              entity_id: switch.waveshare_relay_6
        turn_off:
          - service: switch.turn_off
            target:
              entity_id: switch.waveshare_relay_6

      - name: "Porch Light"
        unique_id: waveshare_light_7
        state: "{{ is_state('switch.waveshare_relay_7', 'on') }}"
        turn_on:
          - service: switch.turn_on
            target:
              entity_id: switch.waveshare_relay_7
        turn_off:
          - service: switch.turn_off
            target:
              entity_id: switch.waveshare_relay_7

      - name: "Office Light"
        unique_id: waveshare_light_8
        state: "{{ is_state('switch.waveshare_relay_8', 'on') }}"
        turn_on:
          - service: switch.turn_on
            target:
              entity_id: switch.waveshare_relay_8
        turn_off:
          - service: switch.turn_off
            target:
              entity_id: switch.waveshare_relay_8
```

## Modbus Protocol Details

| Property | Value |
|----------|-------|
| Protocol | Modbus RTU over TCP |
| Default Port | 4196 |
| Device ID | 1 |
| Relay read | FC 0x01 (Read Coils), addresses 0-7 |
| Relay write | FC 0x05 (Write Single Coil) |
| Digital inputs | FC 0x02 (Read Discrete Inputs), addresses 0-7 |
| DI mode config | FC 0x06 (Write Register), addresses 0x1000-0x1007 |
| Device address | FC 0x03 (Read Register), address 0x4000 |
| Firmware version | FC 0x03 (Read Register), address 0x8000 |

### Coil Values (FC 0x05)

| Value | Action |
|-------|--------|
| 0xFF00 | Turn relay ON |
| 0x0000 | Turn relay OFF |
| 0x5500 | Toggle relay |
| 0xCC00 | Momentary pulse (close then auto-open) |

### DI Mode Values (register 0x1000+)

| Value | Mode |
|-------|------|
| 0 | Disabled |
| 1 | Momentary (press = on, release = off) |
| 2 | Toggle (each press toggles relay) |
| 3 | Latching |

## Troubleshooting

### Cannot connect to device
- Verify the device IP and port in the web interface (`http://<device-ip>`)
- Ensure "Work Mode" is set to **TCP Server**
- Check that port 4196 (or your configured port) is not blocked by firewall
- Try pinging the device: `ping 192.168.10.97`

### Relays not responding
- Confirm Device ID is 1 (check register 0x4000 via web interface)
- Check serial settings: 115200 baud, 8N1

### Digital inputs always show OFF
- Verify wiring: DI terminals need a signal (dry contact or voltage) to trigger
- Check if DI mode is configured (enable "DI Toggle Mode" in integration settings)

## License

MIT
