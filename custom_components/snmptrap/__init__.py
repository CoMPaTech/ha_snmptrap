"""SNMP Trap Custom Component."""

import asyncio
import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType

DOMAIN = "snmptrap"
PORT = 162
PLATFORMS = ["sensor"]

_LOGGER = logging.getLogger(__name__)


def parse_trap(raw_bytes: bytes):
    """Parse SNMP trap BER structure enough to extract varbinds."""

    raw_buffer = raw_bytes.hex()

    # Best-effort raw string (may contain binary)
    try:
        raw_string = raw_bytes.decode("utf-8", errors="replace")
    except Exception:
        raw_string = raw_bytes.decode("latin-1", errors="replace")

    def read_length(buf, idx):
        length = buf[idx]
        idx += 1
        if length & 0x80:
            n = length & 0x7F
            length = int.from_bytes(buf[idx:idx+n], "big")
            idx += n
        return length, idx

    buf = raw_bytes
    idx = 0

    # SEQUENCE
    if buf[idx] != 0x30:
        return {"raw_buffer": raw_buffer, "raw_string": raw_string, "kv": {}, "lines": []}
    _, idx = read_length(buf, idx+1)

    # version
    if buf[idx] == 0x02:
        l, idx = read_length(buf, idx+1)
        idx += l

    # community
    if buf[idx] == 0x04:
        clen, idx = read_length(buf, idx+1)
        idx += clen

    # PDU type
    pdu_type = buf[idx]
    _, idx = read_length(buf, idx+1)

    # Skip request-id, error-status, error-index
    for _ in range(3):
        if buf[idx] == 0x02:
            l, idx = read_length(buf, idx+1)
            idx += l

    # VarBindList
    if buf[idx] != 0x30:
        return {"raw_buffer": raw_buffer, "raw_string": raw_string, "kv": {}, "lines": []}
    vbl_len, idx = read_length(buf, idx+1)

    kv = {}
    end = idx + vbl_len

    while idx < end:
        if buf[idx] != 0x30:
            break
        v_len, idx = read_length(buf, idx+1)
        v_end = idx + v_len

        # OID
        if buf[idx] == 0x06:
            oid_len, idx = read_length(buf, idx+1)
            oid_bytes = buf[idx:idx+oid_len]
            idx += oid_len

            oid = []
            if oid_len > 0:
                first = oid_bytes[0]
                oid.append(first // 40)
                oid.append(first % 40)
                val = 0
                for b in oid_bytes[1:]:
                    if b & 0x80:
                        val = (val << 7) | (b & 0x7F)
                    else:
                        val = (val << 7) | b
                        oid.append(val)
                        val = 0
            oid_str = ".".join(str(x) for x in oid)
        else:
            break

        # Value
        tag = buf[idx]
        val_len, idx = read_length(buf, idx+1)
        val_bytes = buf[idx:idx+val_len]
        idx += val_len

        if tag == 0x04:  # OCTET STRING
            try:
                val = val_bytes.decode("utf-8", errors="replace")
            except:
                val = val_bytes.decode("latin-1", errors="replace")

            # Normalize CR/LF
            val = val.replace("\r\n", "\n").replace("\r", "\n")

            # Split into lines
            lines = [line.strip() for line in val.split("\n") if line.strip()]

            # If multiline, store list; else store string
            val = lines if len(lines) > 1 else (lines[0] if lines else "")

        elif tag == 0x02:  # INTEGER
            val = int.from_bytes(val_bytes, "big")

        else:
            val = val_bytes.hex()

        kv[oid_str] = val
        idx = v_end

    # Build clean lines list
    clean_lines = []
    for v in kv.values():
        if isinstance(v, list):
            clean_lines.extend(v)
        else:
            clean_lines.append(v)

    # Derive semantic key/value pairs from lines
    text_kv = {}
    for line in clean_lines:
        parts = line.split()
        if len(parts) >= 2:
            key = parts[0]
            value = " ".join(parts[1:])
            text_kv[key] = value

    return {
        "raw_buffer": raw_buffer,
        "raw_string": raw_string,
        "kv": text_kv,      # <-- semantic KV (test2: bla, ...)
        "lines": clean_lines,
    }


async def async_setup(hass: HomeAssistant, config: ConfigType):
    return True


async def _start_listener(hass: HomeAssistant):
    """Start UDP listener once per hass instance."""
    if DOMAIN in hass.data and hass.data[DOMAIN].get("transport"):
        return

    transport = None

    class TrapProtocol(asyncio.DatagramProtocol):
        def datagram_received(self, data, addr):
            parsed = parse_trap(data)
            hass.bus.async_fire("snmptrap_event", parsed)
            hass.data[DOMAIN]["last_trap"] = parsed

    loop = asyncio.get_running_loop()
    try:
        transport, _ = await loop.create_datagram_endpoint(
            lambda: TrapProtocol(),
            local_addr=("0.0.0.0", PORT),
        )
        _LOGGER.info("SNMP trap listener started on UDP/%s", PORT)
    except OSError as err:
        _LOGGER.error("Failed to bind UDP/%s for snmptrap: %s", PORT, err)
        transport = None

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["transport"] = transport
    hass.data[DOMAIN].setdefault("last_trap", None)


async def _stop_listener(hass: HomeAssistant):
    data = hass.data.get(DOMAIN)
    if not data:
        return
    transport = data.get("transport")
    if transport:
        transport.close()
        data["transport"] = None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    await _start_listener(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    await _stop_listener(hass)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

