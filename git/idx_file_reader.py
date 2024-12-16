from __future__ import annotations

HASH_LEN = 20
CRC32_LEN = 4
OFFSET_32_LEN = 4
OFFSET_64_LEN = 8


def parse_git_idx(data: bytes):
    # File header - magic number = tOc, version = 2
    HEADER_END = 8
    header = data[:HEADER_END]
    assert header == b"\xfftOc\x00\x00\x00\x02"

    # 256 uint32 offsets in the fanout table
    FANOUT_END = HEADER_END + 256 * 4
    fanout = {}
    fanout_bytes = data[HEADER_END:FANOUT_END]
    for first_hash_byte in range(256):
        lsb_idx = first_hash_byte * 4
        uint_32_offset_bytes = fanout_bytes[lsb_idx : lsb_idx + 4]
        fanout[first_hash_byte] = int.from_bytes(uint_32_offset_bytes, byteorder="big")

    # Last fanout range gives us the number of hashes
    hash_no = fanout[255]

    # Hashes (sorted)
    HASHLIST_END = FANOUT_END + hash_no * HASH_LEN
    hash_bytes = data[FANOUT_END:HASHLIST_END]
    hashes: list[None | bytes] = [None] * hash_no
    for hash_idx, first_byte in enumerate(range(0, hash_no * HASH_LEN, HASH_LEN)):
        hash = hash_bytes[first_byte : first_byte + HASH_LEN]
        hashes[hash_idx] = hash

    # CRC-32 checksums
    CHECKSUMS_END = HASHLIST_END + hash_no * CRC32_LEN
    checksum_bytes = data[HASHLIST_END:CHECKSUMS_END]
    crc_32_checksums: list[None | bytes] = [None] * hash_no
    for checksum_idx, first_byte in enumerate(range(0, hash_no * CRC32_LEN, CRC32_LEN)):
        checksum = checksum_bytes[first_byte : first_byte + CRC32_LEN]
        crc_32_checksums[checksum_idx] = checksum

    # Offsets. 32 bit ones come first, if MSB is 1 then we need to replace it
    # with 64 bit one.
    offsets: list[None | int] = [None] * hash_no

    # 32-bit offsets
    OFFSETS_32_END = CHECKSUMS_END + hash_no * OFFSET_32_LEN
    offset_32_bytes = data[CHECKSUMS_END:OFFSETS_32_END]
    offset_64_bytes = data[OFFSETS_32_END:]
    for offset_idx, first_byte in enumerate(range(0, hash_no * OFFSET_32_LEN, OFFSET_32_LEN)):
        raw_offset: bytes = offset_32_bytes[first_byte : first_byte + OFFSET_32_LEN]
        offset = int.from_bytes(raw_offset, "big")

        # Check MSB to see if this is an extended offset
        if offset & (1 << 31):
            # Remove the MSB
            offset_64_idx = offset - (1<<31)
            # Index the list
            first_byte = offset_64_idx * OFFSET_64_LEN
            raw_offset = offset_64_bytes[first_byte : first_byte + OFFSET_64_LEN]
            offset = int.from_bytes(raw_offset, "big")

        offsets[offset_idx] = offset

    return (
        fanout,
        hashes,
        crc_32_checksums,
        offsets,
    )
