"""Modbus RTU-over-TCP utilities for Waveshare Relay boards."""

import socket
import struct
import logging
import threading
import time

_LOGGER = logging.getLogger(__name__)

# Thread lock to serialize Modbus access (one TCP connection at a time)
_modbus_lock = threading.Lock()


def _crc16(data: bytes) -> bytes:
    """Calculate Modbus CRC16."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return struct.pack("<H", crc)


def _send_rtu(ip_address: str, port: int, request: bytes, timeout: float = 5.0) -> bytes | None:
    """Send a raw Modbus RTU frame over TCP and return the response."""
    frame = request + _crc16(request)
    with _modbus_lock:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                sock.connect((ip_address, port))
                sock.sendall(frame)
                response = sock.recv(256)
                _LOGGER.debug("TX: %s  RX: %s", frame.hex(), response.hex())
                return response
        except Exception as e:
            _LOGGER.error("Modbus RTU error (%s:%d): %s", ip_address, port, e)
            return None


# ── Coil reads (FC 0x01) ──────────────────────────────────

def read_coils(ip_address: str, port: int, start: int = 0, count: int = 8, device_id: int = 1) -> list[bool] | None:
    """Read coil status (FC 0x01) — relay output states."""
    request = struct.pack(">BBHH", device_id, 0x01, start, count)
    resp = _send_rtu(ip_address, port, request)
    if resp is None or len(resp) < 4 or resp[1] & 0x80:
        return None
    byte_count = resp[2]
    bits = []
    for b in range(byte_count):
        for bit in range(8):
            if len(bits) < count:
                bits.append(bool(resp[3 + b] & (1 << bit)))
    return bits


# ── Discrete input reads (FC 0x02) ────────────────────────

def read_discrete_inputs(ip_address: str, port: int, start: int = 0, count: int = 8, device_id: int = 1) -> list[bool] | None:
    """Read discrete inputs (FC 0x02) — digital input states."""
    request = struct.pack(">BBHH", device_id, 0x02, start, count)
    resp = _send_rtu(ip_address, port, request)
    if resp is None or len(resp) < 4 or resp[1] & 0x80:
        return None
    byte_count = resp[2]
    bits = []
    for b in range(byte_count):
        for bit in range(8):
            if len(bits) < count:
                bits.append(bool(resp[3 + b] & (1 << bit)))
    return bits


# ── Single coil writes (FC 0x05) ──────────────────────────

def write_single_coil(ip_address: str, port: int, address: int, value: bool, device_id: int = 1) -> bool:
    """Write single coil (FC 0x05) — turn relay ON (0xFF00) or OFF (0x0000)."""
    coil_value = 0xFF00 if value else 0x0000
    request = struct.pack(">BBHH", device_id, 0x05, address, coil_value)
    resp = _send_rtu(ip_address, port, request)
    if resp is None or len(resp) < 4:
        return False
    return resp[1] == 0x05


def write_coil_raw(ip_address: str, port: int, address: int, value: int, device_id: int = 1) -> bool:
    """Write single coil with raw value (FC 0x05) — for toggle (0x5500), flash, etc."""
    request = struct.pack(">BBHH", device_id, 0x05, address, value)
    resp = _send_rtu(ip_address, port, request)
    if resp is None or len(resp) < 4:
        return False
    return resp[1] == 0x05


def toggle_relay(ip_address: str, port: int, channel: int, device_id: int = 1) -> bool:
    """Toggle a single relay using dedicated toggle address (0x0100+)."""
    return write_coil_raw(ip_address, port, 0x0100 + channel, 0xFF00, device_id)


def toggle_all_relays(ip_address: str, port: int, device_id: int = 1) -> bool:
    """Toggle all relays at once (address 0x01FF)."""
    return write_coil_raw(ip_address, port, 0x01FF, 0xFF00, device_id)


def control_all_relays(ip_address: str, port: int, value: bool, device_id: int = 1) -> bool:
    """Turn all relays ON or OFF (address 0x00FF)."""
    coil_value = 0xFF00 if value else 0x0000
    return write_coil_raw(ip_address, port, 0x00FF, coil_value, device_id)


def flash_relay_on(ip_address: str, port: int, channel: int, duration_ms: int, device_id: int = 1) -> bool:
    """Flash relay ON for duration then auto-OFF (address 0x0200+, value = duration/100ms)."""
    interval = min(duration_ms // 100, 0x7FFF)
    if interval < 1:
        interval = 1
    return write_coil_raw(ip_address, port, 0x0200 + channel, interval, device_id)


def flash_relay_off(ip_address: str, port: int, channel: int, duration_ms: int, device_id: int = 1) -> bool:
    """Flash relay OFF for duration then auto-ON (address 0x0400+, value = duration/100ms)."""
    interval = min(duration_ms // 100, 0x7FFF)
    if interval < 1:
        interval = 1
    return write_coil_raw(ip_address, port, 0x0400 + channel, interval, device_id)


# ── Register reads/writes (FC 0x03/0x06) ──────────────────

def write_single_register(ip_address: str, port: int, address: int, value: int, device_id: int = 1) -> bool:
    """Write single holding register (FC 0x06)."""
    request = struct.pack(">BBHH", device_id, 0x06, address, value)
    resp = _send_rtu(ip_address, port, request)
    if resp is None or len(resp) < 4:
        return False
    return resp[1] == 0x06


def read_holding_register(ip_address: str, port: int, address: int, device_id: int = 1) -> int | None:
    """Read a single holding register (FC 0x03)."""
    request = struct.pack(">BBHH", device_id, 0x03, address, 1)
    resp = _send_rtu(ip_address, port, request)
    if resp is None or len(resp) < 5 or resp[1] & 0x80:
        return None
    return struct.unpack(">H", resp[3:5])[0]


def read_holding_registers(ip_address: str, port: int, address: int, count: int, device_id: int = 1) -> list[int] | None:
    """Read multiple holding registers (FC 0x03)."""
    request = struct.pack(">BBHH", device_id, 0x03, address, count)
    resp = _send_rtu(ip_address, port, request)
    if resp is None or len(resp) < 3 + count * 2 or resp[1] & 0x80:
        return None
    values = []
    for i in range(count):
        values.append(struct.unpack(">H", resp[3 + i * 2 : 5 + i * 2])[0])
    return values


# ── Device info ────────────────────────────────────────────

def read_device_address(ip_address: str, port: int) -> int | None:
    """Read Waveshare device address (register 0x4000)."""
    return read_holding_register(ip_address, port, 0x4000)


def read_software_version(ip_address: str, port: int) -> str | None:
    """Read Waveshare firmware version (register 0x8000)."""
    val = read_holding_register(ip_address, port, 0x8000)
    if val is not None:
        return f"V{val / 100:.2f}"
    return None


# ── DI control modes ──────────────────────────────────────

def read_di_mode(ip_address: str, port: int, channel: int, device_id: int = 1) -> int | None:
    """Read DI control mode for a channel (register 0x1000+)."""
    return read_holding_register(ip_address, port, 0x1000 + channel, device_id)


def read_all_di_modes(ip_address: str, port: int, num_channels: int = 8, device_id: int = 1) -> list[int] | None:
    """Read all DI control modes."""
    return read_holding_registers(ip_address, port, 0x1000, num_channels, device_id)


def set_di_mode(ip_address: str, port: int, channel: int, mode: int, device_id: int = 1) -> bool:
    """Set DI control mode for a single channel (register 0x1000+)."""
    return write_single_register(ip_address, port, 0x1000 + channel, mode, device_id)


def set_di_toggle_mode(ip_address: str, port: int, num_channels: int = 8, device_id: int = 1) -> bool:
    """Set all digital inputs to toggle mode (register 0x1000+ = 2)."""
    success = True
    for ch in range(num_channels):
        if not write_single_register(ip_address, port, 0x1000 + ch, 2, device_id):
            _LOGGER.error("Failed to set DI toggle mode for channel %d", ch)
            success = False
    return success


def ensure_di_modes(ip_address: str, port: int, mode: int, num_channels: int = 8,
                    device_id: int = 1, attempts: int = 3) -> list[int] | None:
    """Rewrite any DI channel whose mode is not `mode`, verifying each write.

    Returns the channels that were rewritten, or None if the board did not answer
    the read. A write only counts once a read-back confirms it, because the board
    can time out mid-sequence and leave channels in normal mode.
    """
    current = read_all_di_modes(ip_address, port, num_channels, device_id)
    if current is None:
        return None
    fixed = []
    for ch, value in enumerate(current):
        if value == mode:
            continue
        for _ in range(attempts):
            if (write_single_register(ip_address, port, 0x1000 + ch, mode, device_id)
                    and read_di_mode(ip_address, port, ch, device_id) == mode):
                fixed.append(ch)
                break
            time.sleep(0.3)
        else:
            _LOGGER.error("Failed to set DI mode %d for channel %d after %d attempts",
                          mode, ch, attempts)
    return fixed
