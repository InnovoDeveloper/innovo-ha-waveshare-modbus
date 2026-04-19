# Waveshare Modbus Relay — Home Assistant Custom Integration

Custom integration for Home Assistant to control [**Waveshare Modbus PoE ETH Relay (B)**](https://www.waveshare.com/modbus-poe-eth-relay-b.htm) boards and read their digital inputs. Uses Modbus RTU over TCP for reliable communication.

![Waveshare Modbus PoE ETH Relay](https://www.waveshare.com/media/catalog/product/cache/1/image/800x800/9df78eab33525d08d6e5fb8d27136e95/m/o/modbus-poe-eth-relay-b-1.jpg)

Based on [icecoldfire/HomeAssistant-Waveshare-Relay](https://github.com/icecoldfire/HomeAssistant-Waveshare-Relay), rewritten with:
- **Modbus RTU over TCP** (CRC16 framing) instead of Modbus TCP
- **Digital input binary sensors** (detect open/close on DI terminals)
- **UI-configurable feature toggles** (enable/disable switches and inputs)
- **Standard and Extended modes** for simple or power-user setups
- Fixed compatibility with Home Assistant 2025.x+

## Links

- [Product page](https://www.waveshare.com/modbus-poe-eth-relay-b.htm) — Waveshare Modbus PoE ETH Relay (B)
- [Wiki / Documentation](https://www.waveshare.com/wiki/Modbus_POE_ETH_Relay_(B)) — Wiring, protocol specs, software tools
- [Original integration](https://github.com/icecoldfire/HomeAssistant-Waveshare-Relay) — Upstream project this is based on

---

## Standard Mode vs Extended Mode

The integration offers two operational modes, selectable during setup:

### Standard Mode (default)

Simple relay control and input monitoring. Perfect for basic on/off switching.

| Entity Type | Count (8ch) | Description |
|-------------|-------------|-------------|
| `switch` | 8 | Relay on/off control with state polling |
| `binary_sensor` | 8 | Digital input open/close detection |

### Extended Mode

Adds advanced features for power users, automation builders, and industrial applications.

| Entity Type | Count (8ch) | Description |
|-------------|-------------|-------------|
| `switch` | 8 | Relay on/off control with state polling |
| `binary_sensor` | 8 | Digital input open/close detection |
| `button` (pulse) | 8 | Pulse relay ON for a set duration, then auto-OFF |
| `number` (duration) | 8 | Configurable pulse duration per relay (0.1s - 3276s) |
| `select` (DI mode) | 8 | Per-channel DI control mode selector (4 modes) |
| `button` (master) | 3 | All Relays ON / All Relays OFF / Toggle All |
| `sensor` (diagnostic) | 2 | Firmware version + Modbus device address |

**Services** (registered in both modes):
- `waveshare_relay.toggle_relay` — Toggle a specific relay by channel
- `waveshare_relay.toggle_all` — Toggle all relays at once

---

## Digital Input (DI) Control Modes

Each digital input channel can be independently configured to one of four control modes. In Standard Mode, you can enable "DI Toggle Mode" to set all channels to Toggle mode. In Extended Mode, each channel gets its own mode selector in the UI.

| Mode | Value | Behavior |
|------|-------|----------|
| **Normal** | 0 | DI is read-only sensor. Relay is controlled only by commands (HA switches, automations, services). DI state is reported but does not affect the relay. |
| **Linkage** | 1 | Relay mirrors DI state in real-time. DI ON = relay ON, DI OFF = relay OFF. **Relay cannot be controlled by commands in this mode** — only by the physical input. |
| **Toggle** | 2 | Each pulse on the DI terminal toggles the corresponding relay. Press a button wired to DI1 and relay 1 flips. Relay can also still be controlled by commands. |
| **Edge Trigger** | 3 | Relay changes state once on each DI level change (rising or falling edge). Similar to Toggle but triggers on both press AND release. Relay can also still be controlled by commands. |

> **Important:** In **Linkage mode**, the relay does NOT respond to HA switch commands — it is controlled exclusively by the physical DI input. All other modes support both physical and command control.

### When to use each mode

| Use Case | Recommended Mode |
|----------|-----------------|
| HA-only control (no physical buttons) | **Normal** |
| Wall switch directly controls a light | **Linkage** |
| Push-button toggles a light on/off | **Toggle** |
| Motion sensor or door contact triggers relay | **Edge Trigger** |
| Hybrid: HA + physical buttons | **Toggle** or **Edge Trigger** |

---

## Relay Flash / Pulse

Extended Mode adds a **Pulse** button for each relay. When pressed:

1. The relay turns **ON**
2. It stays on for the configured **Pulse Duration** (set via the number slider)
3. It automatically turns **OFF**

This is handled entirely by the Waveshare hardware (Modbus flash-on command at address `0x0200+`), so the timing is precise and works even if HA loses connection.

**Use cases:** Garage door openers, door buzzers, irrigation valves, momentary triggers, timed ventilation.

The pulse duration is configurable per-relay from **0.1 seconds** to **3,276.7 seconds** (~54 minutes). The resolution is 100ms.

---

## Requirements

- Home Assistant 2025.1.0 or later
- Waveshare Modbus PoE ETH Relay board (8ch, 4ch, or 2ch)
- Device must be on the same network (or routable) from HA

## Device Configuration

Before adding the integration, configure your Waveshare relay board:

### 1. Access the Device Web Interface

Open a browser and navigate to the device IP (default: `http://192.168.1.200`). Default password: `admin` (or no password on some firmware versions — enter any value).

### 2. Network Settings

| Setting | Recommended Value |
|---------|------------------|
| Device IP | Set to your network (e.g., `192.168.10.97`) |
| Device Port | `4196` (default) |
| Work Mode | **TCP Server** |
| IP Mode | DHCP or Static |

### 3. Serial Settings (do not change from defaults)

| Setting | Value |
|---------|-------|
| Baud Rate | 115200 |
| Data Bits | 8 |
| Parity | None |
| Stop Bits | 1 |

> **Note:** The device port (default 4196) is the Modbus RTU-over-TCP port, NOT the standard Modbus TCP port 502. This integration communicates using raw Modbus RTU frames over the TCP socket. Do not change the serial settings — they must remain at the defaults for the internal relay controller to communicate.

### 4. Advanced Settings (Vircom software)

If using the Vircom configuration tool:
- Set **Transfer Protocol** to **"None"** (this means Modbus RTU — the default)
- Set **Modbus Gateway Type** to **"Multi-host non-storage"** (prevents the gateway from sending its own queries that interfere with HA)

## Installation

### Manual Installation

1. Copy the `waveshare_relay` folder to your Home Assistant `custom_components` directory:
   ```
   custom_components/
   └── waveshare_relay/
       ├── __init__.py
       ├── binary_sensor.py
       ├── button.py
       ├── config_flow.py
       ├── const.py
       ├── manifest.json
       ├── number.py
       ├── select.py
       ├── sensor.py
       ├── services.yaml
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
| DI Toggle Mode | OFF | Sets all DI channels to Toggle mode on startup |
| Extended Mode | OFF | Enables pulse buttons, DI mode selectors, master controls, diagnostics |

## Entities Created

### Standard Mode (8-channel board)

| Entity ID Pattern | Type | Description |
|-------------------|------|-------------|
| `switch.waveshare_relay_1` ... `_8` | Switch | Relay on/off control |
| `binary_sensor.waveshare_relay_input_1` ... `_8` | Binary Sensor | Digital input state |

### Extended Mode (adds to Standard)

| Entity ID Pattern | Type | Description |
|-------------------|------|-------------|
| `button.waveshare_relay_1_pulse` ... `_8_pulse` | Button | Pulse relay ON for set duration |
| `number.waveshare_relay_1_pulse_duration` ... `_8` | Number | Pulse duration slider (seconds) |
| `select.waveshare_relay_di_1_mode` ... `_8_mode` | Select | DI control mode per channel |
| `button.waveshare_relay_all_relays_on` | Button | Turn all relays ON |
| `button.waveshare_relay_all_relays_off` | Button | Turn all relays OFF |
| `button.waveshare_relay_toggle_all_relays` | Button | Toggle all relays |
| `sensor.waveshare_relay_firmware` | Sensor | Firmware version (diagnostic) |
| `sensor.waveshare_relay_modbus_address` | Sensor | Modbus device address (diagnostic) |

### Services

| Service | Description |
|---------|-------------|
| `waveshare_relay.toggle_relay` | Toggle a single relay (params: `ip_address`, `port`, `channel`) |
| `waveshare_relay.toggle_all` | Toggle all relays at once (params: `ip_address`, `port`) |

---

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

### Automation: Garage Door Pulse (Extended Mode)

```yaml
automation:
  - alias: "Garage Door Toggle"
    trigger:
      - platform: state
        entity_id: binary_sensor.garage_button
        to: "on"
    action:
      - service: button.press
        target:
          entity_id: button.waveshare_relay_1_pulse
```

### Automation: All Lights Off at Midnight (Extended Mode)

```yaml
automation:
  - alias: "All Lights Off at Midnight"
    trigger:
      - platform: time
        at: "00:00:00"
    action:
      - service: button.press
        target:
          entity_id: button.waveshare_relay_all_relays_off
```

### Automation: Toggle Relay via Service

```yaml
automation:
  - alias: "Toggle Kitchen Relay"
    trigger:
      - platform: state
        entity_id: binary_sensor.kitchen_motion
        to: "on"
    action:
      - service: waveshare_relay.toggle_relay
        data:
          ip_address: "192.168.10.97"
          port: 4196
          channel: 0
```

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

---

## Modbus Protocol Details

### Connection

| Property | Value |
|----------|-------|
| Protocol | Modbus RTU over TCP |
| Default Port | 4196 |
| Device ID | 1 |
| Baud Rate | 115200 (internal, do not change) |

### Register Map

| Address (hex) | Function | FC | Description |
|---------------|----------|----|-------------|
| `0x0000`-`0x0007` | Relay 1-8 | 0x01 (read), 0x05 (write) | ON: `0xFF00`, OFF: `0x0000`, Toggle: `0x5500` |
| `0x00FF` | All relays | 0x05 (write) | ON: `0xFF00`, OFF: `0x0000`, Toggle: `0x5500` |
| `0x0100`-`0x0107` | Relay 1-8 toggle | 0x05 (write) | `0xFF00` = toggle, `0x0000` = no change |
| `0x01FF` | All relays toggle | 0x05 (write) | `0xFF00` = toggle all |
| `0x0200`-`0x0207` | Relay 1-8 flash ON | 0x05 (write) | Value = interval in 100ms units (relay ON, then auto-OFF) |
| `0x0400`-`0x0407` | Relay 1-8 flash OFF | 0x05 (write) | Value = interval in 100ms units (relay OFF, then auto-ON) |
| `1x0000`-`1x0007` | Digital inputs 1-8 | 0x02 (read) | Input channel status |
| `4x1000`-`4x1007` | DI control modes 1-8 | 0x03 (read), 0x06 (write) | 0=Normal, 1=Linkage, 2=Toggle, 3=Edge |
| `4x4000` | Device address | 0x03 (read) | Modbus slave address |
| `4x8000` | Software version | 0x03 (read) | e.g., `0x0064` = 100 = V1.00 |

### Coil Values (FC 0x05)

| Value | Action |
|-------|--------|
| `0xFF00` | Turn relay ON |
| `0x0000` | Turn relay OFF |
| `0x5500` | Toggle relay state |

### Flash Timing

Flash ON/OFF interval = `value * 100ms`. Maximum value is `0x7FFF` (32,767 = ~54 minutes).

Example: `value = 0x000A` = 10 * 100ms = 1 second pulse.

---

## Troubleshooting

### Cannot connect to device
- Verify the device IP and port in the web interface (`http://<device-ip>`)
- Ensure "Work Mode" is set to **TCP Server**
- Check that port 4196 (or your configured port) is not blocked by firewall
- Try pinging the device: `ping 192.168.10.97`

### Relays not responding to commands
- Confirm Device ID is 1 (check register `0x4000` in Extended Mode diagnostics or via web interface)
- Check serial settings: 115200 baud, 8N1 (do not change from defaults)
- **If relay doesn't respond but returns a Modbus reply:** The channel may be in **Linkage mode**. Use Extended Mode's DI mode selector to switch it to Normal or Toggle mode.

### Digital inputs always show OFF
- Verify wiring: DI terminals need a signal (dry contact or voltage 5-36V) to trigger
- Check COM terminal wiring:
  - **COM not connected:** dry contact / passive input
  - **COM to V+:** NPN active input (low active, 5-30V)
  - **COM to GND:** PNP active input (high active)

### Pulse button doesn't work
- Ensure Extended Mode is enabled in the integration config
- Check the pulse duration slider is set to a value > 0
- The pulse is hardware-timed — even if HA disconnects, the relay will auto-revert

### Entity not appearing after setup
- Check Home Assistant logs for errors: **Settings > System > Logs**
- Ensure the integration loaded without import errors
- Try removing and re-adding the integration

## License

MIT
