"""Pure-Python PCAP and PCAPNG file parser.

No external libraries (such as libpcap or scapy) are required.
Runs natively across Windows, Linux, and macOS.
"""

from __future__ import annotations

import io
import socket
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO, List, Tuple


@dataclass
class ParsedPacket:
    """Dissected packet representation."""
    packet_number: int
    timestamp: float
    link_type: int = 1
    src_mac: str = ""
    dst_mac: str = ""
    ip_version: int = 4
    src_ip: str = ""
    dst_ip: str = ""
    protocol: str = "OTHER"
    src_port: int = 0
    dst_port: int = 0
    tcp_flags: dict[str, bool] = field(default_factory=dict)
    payload: bytes = b""
    length: int = 0
    summary: str = ""


# Link layer type constants
LINKTYPE_NULL = 0
LINKTYPE_ETHERNET = 1
LINKTYPE_RAW = 12
LINKTYPE_RAW_ALT = 101
LINKTYPE_LINUX_SLL = 113
LINKTYPE_LINUX_SLL2 = 276

PCAPNG_MAGIC = 0x0A0D0D0A


class PCAPParseException(Exception):
    """Raised when parsing fails."""


def _format_mac(raw: bytes) -> str:
    return ":".join(f"{b:02x}" for b in raw)


def _parse_dns_query_name(payload: bytes) -> str:
    """Extract domain name from standard DNS question payload."""
    if len(payload) < 12:
        return ""
    idx = 12
    labels: list[str] = []
    try:
        while idx < len(payload):
            length = payload[idx]
            if length == 0:
                break
            if length >= 192:  # pointer compression
                idx += 2
                break
            idx += 1
            if idx + length > len(payload):
                break
            label = payload[idx : idx + length].decode("ascii", errors="replace")
            labels.append(label)
            idx += length
        return ".".join(labels)
    except Exception:
        return ""


def parse_packet_data(raw_data: bytes, link_type: int, pkt_num: int, timestamp: float) -> ParsedPacket:
    """Dissect raw packet bytes based on link-layer type."""
    pkt = ParsedPacket(
        packet_number=pkt_num,
        timestamp=timestamp,
        link_type=link_type,
        length=len(raw_data),
    )

    offset = 0
    ethertype = 0

    if link_type == LINKTYPE_ETHERNET:
        if len(raw_data) < 14:
            return pkt
        pkt.dst_mac = _format_mac(raw_data[0:6])
        pkt.src_mac = _format_mac(raw_data[6:12])
        ethertype = struct.unpack("!H", raw_data[12:14])[0]
        offset = 14
        # Handle 802.1Q VLAN tag
        if ethertype == 0x8100 and len(raw_data) >= 18:
            ethertype = struct.unpack("!H", raw_data[16:18])[0]
            offset = 18

    elif link_type == LINKTYPE_LINUX_SLL:
        if len(raw_data) < 16:
            return pkt
        ethertype = struct.unpack("!H", raw_data[14:16])[0]
        offset = 16

    elif link_type == LINKTYPE_LINUX_SLL2:
        if len(raw_data) < 20:
            return pkt
        ethertype = struct.unpack("!H", raw_data[0:2])[0]
        offset = 20

    elif link_type in (LINKTYPE_RAW, LINKTYPE_RAW_ALT):
        if len(raw_data) < 1:
            return pkt
        ip_ver = raw_data[0] >> 4
        ethertype = 0x0800 if ip_ver == 4 else (0x86DD if ip_ver == 6 else 0)
        offset = 0

    else:
        # Default fallback: try treating as Ethernet or Raw IP
        if len(raw_data) >= 14 and raw_data[12:14] in (b"\x08\x00", b"\x86\xdd", b"\x08\x06"):
            ethertype = struct.unpack("!H", raw_data[12:14])[0]
            offset = 14
        elif len(raw_data) >= 20 and (raw_data[0] >> 4) in (4, 6):
            ip_ver = raw_data[0] >> 4
            ethertype = 0x0800 if ip_ver == 4 else 0x86DD
            offset = 0

    # Parse IP / ARP
    ip_proto = 0
    transport_offset = offset

    if ethertype == 0x0800:  # IPv4
        pkt.ip_version = 4
        if len(raw_data) < offset + 20:
            return pkt
        ver_ihl = raw_data[offset]
        ihl = (ver_ihl & 0x0F) * 4
        ip_proto = raw_data[offset + 9]
        pkt.src_ip = socket.inet_ntoa(raw_data[offset + 12 : offset + 16])
        pkt.dst_ip = socket.inet_ntoa(raw_data[offset + 16 : offset + 20])
        transport_offset = offset + ihl

    elif ethertype == 0x86DD:  # IPv6
        pkt.ip_version = 6
        if len(raw_data) < offset + 40:
            return pkt
        ip_proto = raw_data[offset + 6]
        try:
            pkt.src_ip = socket.inet_ntop(socket.AF_INET6, raw_data[offset + 8 : offset + 24])
            pkt.dst_ip = socket.inet_ntop(socket.AF_INET6, raw_data[offset + 24 : offset + 40])
        except Exception:
            pkt.src_ip = "IPv6"
            pkt.dst_ip = "IPv6"
        transport_offset = offset + 40

    elif ethertype == 0x0806:  # ARP
        pkt.protocol = "ARP"
        pkt.summary = "ARP request/reply"
        return pkt

    # Parse Transport Layer (TCP, UDP, ICMP)
    if ip_proto == 6:  # TCP
        pkt.protocol = "TCP"
        if len(raw_data) >= transport_offset + 20:
            src_port, dst_port = struct.unpack("!HH", raw_data[transport_offset : transport_offset + 4])
            pkt.src_port = src_port
            pkt.dst_port = dst_port
            data_offset = ((raw_data[transport_offset + 12] >> 4) & 0x0F) * 4
            flags_byte = raw_data[transport_offset + 13]
            pkt.tcp_flags = {
                "FIN": bool(flags_byte & 0x01),
                "SYN": bool(flags_byte & 0x02),
                "RST": bool(flags_byte & 0x04),
                "PSH": bool(flags_byte & 0x08),
                "ACK": bool(flags_byte & 0x10),
                "URG": bool(flags_byte & 0x20),
            }
            payload_start = transport_offset + data_offset
            pkt.payload = raw_data[payload_start:]
            pkt.summary = f"TCP {pkt.src_ip}:{pkt.src_port} -> {pkt.dst_ip}:{pkt.dst_port}"

    elif ip_proto == 17:  # UDP
        pkt.protocol = "UDP"
        if len(raw_data) >= transport_offset + 8:
            src_port, dst_port = struct.unpack("!HH", raw_data[transport_offset : transport_offset + 4])
            pkt.src_port = src_port
            pkt.dst_port = dst_port
            pkt.payload = raw_data[transport_offset + 8 :]
            pkt.summary = f"UDP {pkt.src_ip}:{pkt.src_port} -> {pkt.dst_ip}:{pkt.dst_port}"

    elif ip_proto == 1:  # ICMP
        pkt.protocol = "ICMP"
        pkt.summary = f"ICMP {pkt.src_ip} -> {pkt.dst_ip}"

    # Application protocol enrichment
    if pkt.payload:
        ports = {pkt.src_port, pkt.dst_port}
        if 80 in ports or 8080 in ports:
            if b"HTTP/" in pkt.payload or b"GET " in pkt.payload or b"POST " in pkt.payload:
                pkt.protocol = "HTTP"
        elif 21 in ports:
            pkt.protocol = "FTP"
        elif 23 in ports:
            pkt.protocol = "TELNET"
        elif 53 in ports:
            pkt.protocol = "DNS"
            qname = _parse_dns_query_name(pkt.payload)
            if qname:
                pkt.summary = f"DNS Query: {qname}"
        elif 5355 in ports:
            pkt.protocol = "LLMNR"
            qname = _parse_dns_query_name(pkt.payload)
            if qname:
                pkt.summary = f"LLMNR Query: {qname}"
        elif 137 in ports:
            pkt.protocol = "NETBIOS"
        elif 443 in ports or 8443 in ports:
            if len(pkt.payload) >= 5 and pkt.payload[0] in (20, 21, 22, 23):
                pkt.protocol = "TLS"

    return pkt


def parse_pcap_stream(stream: BinaryIO, max_packets: int = 1000) -> list[ParsedPacket]:
    """Parse standard PCAP file format from a binary stream."""
    global_hdr = stream.read(24)
    if len(global_hdr) < 24:
        raise PCAPParseException("File too short for PCAP global header")

    magic = struct.unpack("<I", global_hdr[:4])[0]

    is_little = True
    is_nano = False

    if magic == 0xA1B2C3D4:
        is_little = False
        is_nano = False
    elif magic == 0xD4C3B2A1:
        is_little = True
        is_nano = False
    elif magic == 0xA1B23C4D:
        is_little = False
        is_nano = True
    elif magic == 0x4D3CB2A1:
        is_little = True
        is_nano = True
    else:
        raise PCAPParseException(f"Unrecognized PCAP magic number: 0x{magic:08x}")

    endian = "<" if is_little else ">"
    network_link = struct.unpack(f"{endian}I", global_hdr[20:24])[0]

    packets: list[ParsedPacket] = []
    pkt_num = 1

    while pkt_num <= max_packets:
        hdr = stream.read(16)
        if len(hdr) < 16:
            break

        ts_sec, ts_usec, incl_len, _orig_len = struct.unpack(f"{endian}IIII", hdr)
        pkt_bytes = stream.read(incl_len)
        if len(pkt_bytes) < incl_len:
            break

        timestamp = float(ts_sec) + (float(ts_usec) / (1e9 if is_nano else 1e6))
        pkt = parse_packet_data(pkt_bytes, network_link, pkt_num, timestamp)
        packets.append(pkt)
        pkt_num += 1

    return packets


def parse_pcapng_stream(stream: BinaryIO, max_packets: int = 1000) -> list[ParsedPacket]:
    """Parse PCAPNG format blocks from a binary stream.

    Malformed blocks are ignored instead of being treated as valid packets so that
    a truncated or adversarial capture cannot cause bogus packet data to be parsed.
    """
    packets: list[ParsedPacket] = []
    pkt_num = 1
    link_type = LINKTYPE_ETHERNET

    endian = "<"  # default little endian for PCAPNG

    while pkt_num <= max_packets:
        hdr = stream.read(8)
        if len(hdr) < 8:
            break

        block_type, block_len = struct.unpack(f"{endian}II", hdr)

        if block_len < 12:
            # A valid PCAPNG block includes its own 8-byte header and at least 4 bytes of payload.
            break

        # Detect Section Header Block magic to determine endianness
        if block_type == 0x0A0D0D0A:
            body_start = stream.read(4)
            if body_start == b"\x1a\x2b\x3c\x4d":
                endian = ">"
            else:
                endian = "<"
            remaining = block_len - 12
            if remaining > 0:
                stream.read(remaining)
            continue

        # Interface Description Block (block type 1)
        if block_type == 0x00000001:
            body = stream.read(max(0, block_len - 8))
            if len(body) >= 2:
                link_type = struct.unpack(f"{endian}H", body[:2])[0]
            continue

        # Enhanced Packet Block (block type 6)
        if block_type == 0x00000006:
            # 8 bytes already read (type, len)
            # Body: Interface ID (4), ts_high (4), ts_low (4), cap_len (4), orig_len (4)
            body_len = block_len - 8
            if body_len < 20:
                break
            epb_hdr = stream.read(20)
            if len(epb_hdr) < 20:
                break
            _if_id, ts_high, ts_low, cap_len, _orig_len = struct.unpack(f"{endian}IIIII", epb_hdr)
            if cap_len > body_len - 20:
                break
            ts = ((ts_high << 32) | ts_low) / 1e6
            pkt_data = stream.read(cap_len)

            if len(pkt_data) < cap_len:
                break

            # Pad to 4-byte boundary
            pad = (4 - (cap_len % 4)) % 4
            trailing = block_len - (8 + 20 + cap_len + pad)
            if pad > 0:
                stream.read(pad)
            if trailing > 0:
                stream.read(trailing)

            pkt = parse_packet_data(pkt_data, link_type, pkt_num, ts)
            packets.append(pkt)
            pkt_num += 1
            continue

        # Simple Packet Block (block type 3)
        if block_type == 0x00000003:
            if block_len < 16:
                break
            spb_hdr = stream.read(4)
            if len(spb_hdr) < 4:
                break
            orig_len = struct.unpack(f"{endian}I", spb_hdr)[0]
            payload_len = max(0, block_len - 16)
            cap_len = min(orig_len, payload_len)
            pkt_data = stream.read(cap_len)
            if len(pkt_data) < cap_len:
                break
            pad = (4 - (cap_len % 4)) % 4
            trailing = block_len - (8 + 4 + cap_len + pad)
            if pad > 0:
                stream.read(pad)
            if trailing > 0:
                stream.read(trailing)

            pkt = parse_packet_data(pkt_data, link_type, pkt_num, 0.0)
            packets.append(pkt)
            pkt_num += 1
            continue

        # Skip other block types
        skip = block_len - 8
        if skip > 0:
            stream.read(skip)

    return packets


def parse_pcap_file(file_path: str | Path, max_packets: int = 1000) -> list[ParsedPacket]:
    """Inspect and parse a .pcap or .pcapng file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Packet capture file not found: {path}")

    with open(path, "rb") as fh:
        magic_check = fh.read(4)
        fh.seek(0)
        if len(magic_check) >= 4 and struct.unpack("<I", magic_check)[0] == PCAPNG_MAGIC:
            return parse_pcapng_stream(fh, max_packets=max_packets)
        return parse_pcap_stream(fh, max_packets=max_packets)


def create_sample_pcap_bytes(packets_data: list[Tuple[bytes, float]]) -> bytes:
    """Helper to synthesize standard PCAP bytes for testing."""
    buf = io.BytesIO()
    # Write global header (24 bytes): Little-endian microsecond pcap
    buf.write(struct.pack("<IHHiIII", 0xD4C3B2A1, 2, 4, 0, 0, 65535, LINKTYPE_ETHERNET))
    for raw_pkt, ts in packets_data:
        sec = int(ts)
        usec = int((ts - sec) * 1e6)
        incl_len = len(raw_pkt)
        buf.write(struct.pack("<IIII", sec, usec, incl_len, incl_len))
        buf.write(raw_pkt)
    return buf.getvalue()
