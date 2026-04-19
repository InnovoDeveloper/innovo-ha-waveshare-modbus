"""Constants for the Waveshare Relay integration."""

DOMAIN = "waveshare_relay"

# Config keys
CONF_ENABLE_INPUTS = "enable_inputs"
CONF_ENABLE_SWITCHES = "enable_switches"
CONF_NUM_CHANNELS = "num_channels"
CONF_DI_TOGGLE_MODE = "di_toggle_mode"
CONF_EXTENDED_MODE = "extended_mode"

# DI control modes (register 0x1000+)
DI_MODE_NORMAL = 0
DI_MODE_LINKAGE = 1
DI_MODE_TOGGLE = 2
DI_MODE_EDGE = 3

DI_MODE_OPTIONS = {
    "normal": DI_MODE_NORMAL,
    "linkage": DI_MODE_LINKAGE,
    "toggle": DI_MODE_TOGGLE,
    "edge_trigger": DI_MODE_EDGE,
}

DI_MODE_LABELS = {
    "normal": "Normal (command only)",
    "linkage": "Linkage (DI mirrors relay)",
    "toggle": "Toggle (DI pulse toggles relay)",
    "edge_trigger": "Edge Trigger (DI change toggles relay)",
}

# Modbus addresses
ADDR_RELAY_BASE = 0x0000        # FC 0x05: relay on/off/toggle
ADDR_RELAY_ALL = 0x00FF         # FC 0x05: all relays on/off/toggle
ADDR_TOGGLE_BASE = 0x0100       # FC 0x05: dedicated toggle
ADDR_TOGGLE_ALL = 0x01FF        # FC 0x05: toggle all
ADDR_FLASH_ON_BASE = 0x0200     # FC 0x05: flash on (value = interval * 100ms)
ADDR_FLASH_OFF_BASE = 0x0400    # FC 0x05: flash off (value = interval * 100ms)
ADDR_DI_BASE = 0x0000           # FC 0x02: read discrete inputs
ADDR_DI_MODE_BASE = 0x1000      # FC 0x03/0x06: read/write DI control mode
ADDR_DEVICE_ADDR = 0x4000       # FC 0x03: device address
ADDR_SOFTWARE_VER = 0x8000      # FC 0x03: software version
