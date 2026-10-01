#!/usr/bin/env python3
"""Verify that a v2 -> v3 upgrade copied the full original payload unchanged."""
import hashlib
import json
from pathlib import Path
import struct
import sys


def payload_info(path, expected_magic, header_bytes):
    with Path(path).open("rb") as source:
        header = source.read(header_bytes)
    if header[:8] != expected_magic:
        raise ValueError("unexpected NInfer container version")
    metadata_bytes = struct.unpack_from("<Q", header, 8)[0]
    start = (header_bytes + metadata_bytes + 4095) // 4096 * 4096
    return start, Path(path).stat().st_size - start


def hash_range(path, start, length):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        source.seek(start)
        remaining = length
        while remaining:
            chunk = source.read(min(8 * 1024 * 1024, remaining))
            if not chunk:
                raise ValueError("payload ended early")
            digest.update(chunk)
            remaining -= len(chunk)
    return digest.hexdigest()


old, new = sys.argv[1:]
old_start, length = payload_info(old, b"NINFER\0\2", 16)
new_start, new_length = payload_info(new, b"NINFER\0\3", 32)
if new_length < length:
    raise ValueError("new container is shorter than original payload")
a, b = hash_range(old, old_start, length), hash_range(new, new_start, length)
print(json.dumps({"old_payload_offset": old_start, "new_payload_offset": new_start,
                  "verified_bytes": length, "v2_payload_sha256": a,
                  "v3_original_payload_sha256": b, "unchanged": a == b}, indent=2))
sys.exit(0 if a == b else 1)
