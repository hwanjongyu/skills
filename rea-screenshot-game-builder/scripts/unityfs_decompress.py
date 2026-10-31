#!/usr/bin/env python3
"""
UnityFS LZ4 Pure-Python Bundle Stream Decompressor
Part of rea-screenshot-game-builder skill.

Decompresses raw LZ4-compressed blocks from UnityFS Addressables bundles without
requiring external binary tools or proprietary C-extensions.
"""

import argparse
import sys
import os
import struct


def lz4_decompress(src: bytes, uncompressed_size: int) -> bytes:
    """Pure-Python LZ4 block decompressor."""
    out = bytearray()
    i = 0
    n = len(src)
    while i < n and len(out) < uncompressed_size:
        token = src[i]
        i += 1
        lit_len = token >> 4
        if lit_len == 15:
            while i < n:
                b = src[i]
                i += 1
                lit_len += b
                if b != 255:
                    break
        out.extend(src[i:i + lit_len])
        i += lit_len
        if i >= n or len(out) >= uncompressed_size:
            break
        if i + 2 > n:
            break
        offset = src[i] | (src[i + 1] << 8)
        i += 2
        match_len = (token & 0x0F) + 4
        if (token & 0x0F) == 15:
            while i < n:
                b = src[i]
                i += 1
                match_len += b
                if b != 255:
                    break
        start = len(out) - offset
        if start < 0:
            break
        for j in range(match_len):
            out.append(out[start + j])
    return bytes(out)


def unpack_unityfs_header(filepath: str):
    """Parses UnityFS bundle header and decompresses block index."""
    with open(filepath, "rb") as f:
        magic = f.read(7)
        if magic != b"UnityFS":
            raise ValueError(f"Invalid file signature: {magic!r}. Expected b'UnityFS'")

        f.seek(0)
        data = f.read()

    # Find UnityFS string null terminator
    null_idx = data.find(b"\x00")
    if null_idx == -1:
        raise ValueError("Malformed UnityFS signature")

    pos = null_idx + 1
    # Version (int32 big-endian)
    version = struct.unpack(">I", data[pos:pos + 4])[0]
    pos += 4

    # Player version string (null-terminated)
    pv_end = data.find(b"\x00", pos)
    player_version = data[pos:pv_end].decode("ascii", errors="replace")
    pos = pv_end + 1

    # Engine version string (null-terminated)
    ev_end = data.find(b"\x00", pos)
    engine_version = data[pos:ev_end].decode("ascii", errors="replace")
    pos = ev_end + 1

    file_size = struct.unpack(">Q", data[pos:pos + 8])[0]
    pos += 8
    ci_size = struct.unpack(">I", data[pos:pos + 4])[0]
    pos += 4
    ui_size = struct.unpack(">I", data[pos:pos + 4])[0]
    pos += 4
    flags = struct.unpack(">I", data[pos:pos + 4])[0]
    pos += 4

    print(f"[UnityFS Bundle Info]")
    print(f"  - Version:        {version}")
    print(f"  - Engine Version: {engine_version} (Player: {player_version})")
    print(f"  - Total Size:     {file_size} bytes")
    print(f"  - Compressed Index Size:   {ci_size} bytes")
    print(f"  - Uncompressed Index Size: {ui_size} bytes")
    print(f"  - Flags:          0x{flags:08x}")

    compression_type = flags & 0x3F
    compressed_block = data[pos:pos + ci_size]

    if compression_type == 3:  # LZ4
        print("[INFO] Index is LZ4 compressed. Decompressing...")
        decompressed_index = lz4_decompress(compressed_block, ui_size)
        print(f"[SUCCESS] Decompressed {len(decompressed_index)} bytes of metadata index.")
        return decompressed_index
    elif compression_type == 0:  # Uncompressed
        print("[INFO] Index is uncompressed.")
        return compressed_block
    else:
        print(f"[WARN] Compression type {compression_type} not natively handled by pure LZ4 decoder.")
        return compressed_block


def main():
    parser = argparse.ArgumentParser(
        description="Inspect and extract metadata from UnityFS bundles using pure Python LZ4 decoder."
    )
    parser.add_argument("bundle", help="Path to UnityFS bundle file (.bundle)")
    parser.add_argument("-o", "--output", help="Optional path to save decompressed block data")
    args = parser.parse_args()

    if not os.path.exists(args.bundle):
        print(f"[ERROR] Bundle not found: {args.bundle}", file=sys.stderr)
        sys.exit(1)

    try:
        index_data = unpack_unityfs_header(args.bundle)
        if args.output and index_data:
            with open(args.output, "wb") as f:
                f.write(index_data)
            print(f"[SUCCESS] Saved extracted block to: {args.output}")
    except Exception as e:
        print(f"[ERROR] Bundle decompression error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
