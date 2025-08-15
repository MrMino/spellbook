#!/usr/bin/env python
from pathlib import Path
from collections import namedtuple
import difflib
import time
import sys
import binascii
import marshal
import dis
import struct


PycData = namedtuple('PycData', ['magic', 'flags', 'timestamp', 'size', 'code', 'filename'])


def pyc_info(path: Path) -> PycData:
    data = path.read_bytes()
    magic = data[:4]
    flags = data[4:8]
    assert flags == b'\x00\x00\x00\x00', "Unsupported flags in .pyc file"
    timestamp = data[8:12]
    size = data[12:16]
    code = marshal.loads(data[16:])

    return PycData(
        magic=binascii.hexlify(magic).decode('utf-8'),
        flags=flags,
        timestamp=time.asctime(time.localtime(struct.unpack('I', timestamp)[0])),
        size=struct.unpack('I', size),
        code=code,
        filename=path.name,
    )


def view_pyc(pyc: PycData):
    print(f'Magic: {pyc.magic}')
    print(f'Timestamp: {pyc.timestamp}')
    print(f'Size: {pyc.size[0]} bytes')
    print('Code Object:')
    dis.dis(pyc.code)


ANSII_RED = '\033[91m'
ANSII_RESET = '\033[0m'

def diff_pyc(left: PycData, right: PycData):
    if left.magic != right.magic:
        print(f'{ANSII_RED}Magic: {left.magic} <> {right.magic}{ANSII_RESET}')
    else:
        print(f"Magic: {left.magic} (identical)")

    if left.flags != right.flags:
        print(f'{ANSII_RED}Flags: {left.flags} <> {right.flags}{ANSII_RESET}')
    else:
        print(f"Flags: {left.flags} (identical)")

    if left.timestamp != right.timestamp:
        print(f'{ANSII_RED}Timestamp: {left.timestamp} <> {right.timestamp}{ANSII_RESET}')
    else:
        print(f"Timestamp: {left.timestamp} (identical)")

    if left.size != right.size:
        print(f'{ANSII_RED}Size: {left.size[0]} <> {right.size[0]} bytes{ANSII_RESET}')
    else:
        print(f"Size: {left.size[0]} bytes (identical)")

    if left.code != right.code:
        left_dis = dis.Bytecode(left.code).dis()
        right_dis = dis.Bytecode(right.code).dis()

        diff = difflib.unified_diff(
            left_dis.splitlines(),
            right_dis.splitlines(),
            fromfile=left.filename,
            tofile=right.filename,
            lineterm=''
        )
        print(f'{ANSII_RED}Code differences:{ANSII_RESET}')
        for line in diff:
            print(line)
    else:
        print("Code identical:")
        dis.dis(left.code)


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) == 1:
        pyc = pyc_info(Path(args[0]))
    elif len(args) == 2:
        left_pyc = pyc_info(Path(args[0]))
        right_pyc = pyc_info(Path(args[1]))
        diff_pyc(left_pyc, right_pyc)
    else:
        print('Usage: python pycdiff.py <pyc_file1> [<pyc_file2>]')
        sys.exit(1)
