#!/usr/bin/env python3

"""
Dell PFS BIOS Assembler v0.1
Copyright (C) 2020 Vu Quang Trong

You will need Dell PFS BIOS Extractor v4.5.1
    at https://github.com/vuquangtrong/Dell-PFS-BIOS-Assembler
    to prepare BIOS entry raw files

To make Dell BIOS executable file, you will need
    * Model Information: hold model type, BIOS version
    * PFS Information: hold GUID of included BIOS entries
    * BIOS Entries: BIOS, EC, ME, etc.,

After making the output executable, Dell system will recognize its version as the version in Model Information.
If Model Information has version of 10, but BIOS entry is at version 9 actually, you can downgrade BIOS to version 9 eventually

To make downgrade BIOS:
    * extract current BIOS file, i.e. version 10
    * extract target BIOS file, i.e. version 9
    * use Model Information and PFS Information bin files from version 10
    * use BIOS and others file from version 9

Note:
    * You can downgrade BIOS and EC, but may not can downgrade Intel (CS)ME

"""

import os
import sys
import zlib
import ctypes
import struct
import argparse
import traceback

title = 'Dell PFS BIOS Assembler v0.1'

# Set ctypes Structure types
char = ctypes.c_char
uint8_t = ctypes.c_ubyte
uint16_t = ctypes.c_ushort
uint32_t = ctypes.c_uint
uint64_t = ctypes.c_uint64


class PFS_HDR(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('Tag', char * 8),  # 0x00
        ('HeaderVersion', uint32_t),  # 0x08
        ('PayloadSize', uint32_t),  # 0x0C
        # 0x10
    ]

    def pfs_print(self):
        print('\nPFS Header:\n')
        print('Tag            : %s' % self.Tag.decode('utf-8'))
        print('HeaderVersion  : %d' % self.HeaderVersion)
        print('PayloadSize    : 0x%X' % self.PayloadSize)


class PFS_FTR(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('PayloadSize', uint32_t),  # 0x00
        ('Checksum', uint32_t),  # 0x04 ~CRC32 w/ Vector 0
        ('Tag', char * 8),  # 0x08
        # 0x10
    ]

    def pfs_print(self):
        print('\nPFS Footer:\n')
        print('PayloadSize    : 0x%X' % self.PayloadSize)
        print('Checksum       : 0x%0.8X' % self.Checksum)
        print('Tag            : %s' % self.Tag.decode('utf-8'))


class PFS_ENTRY(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('GUID', uint32_t * 4),  # 0x00 Little Endian
        ('HeaderVersion', uint32_t),  # 0x10 1
        ('VersionType', uint8_t * 4),  # 0x14
        ('Version', uint16_t * 4),  # 0x18
        ('Reserved', uint64_t),  # 0x20
        ('DataSize', uint32_t),  # 0x28
        ('DataSigSize', uint32_t),  # 0x2C
        ('DataMetSize', uint32_t),  # 0x30
        ('DataMetSigSize', uint32_t),  # 0x34
        ('Unknown', uint32_t * 4),  # 0x38
        # 0x48
    ]

    def pfs_print(self):
        GUID = ''.join('%0.8X' % int.from_bytes(struct.pack('<I', val), 'little') for val in reversed(self.GUID))
        VersionType = ''.join(
            '%0.2X' % int.from_bytes(struct.pack('<I', val), 'little') for val in reversed(self.VersionType))
        Version = ''.join('%0.4X' % int.from_bytes(struct.pack('<I', val), 'little') for val in reversed(self.Version))
        Unknown = ''.join('%0.8X' % int.from_bytes(struct.pack('<I', val), 'little') for val in reversed(self.Unknown))

        print('\nPFS Entry:\n')
        print('GUID           : %s' % GUID)
        print('HeaderVersion  : %d' % self.HeaderVersion)
        print('VersionType    : %s' % VersionType)
        print('Version        : %s' % Version)
        print('Reserved       : 0x%X' % self.Reserved)
        print('DataSize       : 0x%X' % self.DataSize)
        print('DataSigSize    : 0x%X' % self.DataSigSize)
        print('DataMetSize    : 0x%X' % self.DataMetSize)
        print('DataMetSigSize : 0x%X' % self.DataMetSigSize)
        print('Unknown        : %s' % Unknown)


class PFS_ENTRY_R2(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('GUID', uint32_t * 4),  # 0x00 Little Endian
        ('HeaderVersion', uint32_t),  # 0x10 2
        ('VersionType', uint8_t * 4),  # 0x14
        ('Version', uint16_t * 4),  # 0x18
        ('Reserved', uint64_t),  # 0x20
        ('DataSize', uint32_t),  # 0x28
        ('DataSigSize', uint32_t),  # 0x2C
        ('DataMetSize', uint32_t),  # 0x30
        ('DataMetSigSize', uint32_t),  # 0x34
        ('Unknown', uint32_t * 8),  # 0x38
        # 0x58
    ]

    def pfs_print(self):
        GUID = ''.join('%0.8X' % int.from_bytes(struct.pack('<I', val), 'little') for val in reversed(self.GUID))
        VersionType = ''.join(
            '%0.2X' % int.from_bytes(struct.pack('<I', val), 'little') for val in reversed(self.VersionType))
        Version = ''.join('%0.4X' % int.from_bytes(struct.pack('<I', val), 'little') for val in reversed(self.Version))
        Unknown = ''.join('%0.8X' % int.from_bytes(struct.pack('<I', val), 'little') for val in reversed(self.Unknown))

        print('\nPFS Entry:\n')
        print('GUID           : %s' % GUID)
        print('HeaderVersion  : %d' % self.HeaderVersion)
        print('VersionType    : %s' % VersionType)
        print('Version        : %s' % Version)
        print('Reserved       : 0x%X' % self.Reserved)
        print('DataSize       : 0x%X' % self.DataSize)
        print('DataSigSize    : 0x%X' % self.DataSigSize)
        print('DataMetSize    : 0x%X' % self.DataMetSize)
        print('DataMetSigSize : 0x%X' % self.DataMetSigSize)
        print('Unknown        : %s' % Unknown)


class PFS_INFO(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('HeaderVersion', uint32_t),  # 0x00
        ('GUID', uint32_t * 4),  # 0x04 Little Endian
        ('Version', uint16_t * 4),  # 0x14
        ('VersionType', uint8_t * 4),  # 0x1C
        ('CharacterCount', uint16_t),  # 0x20 UTF-16 2-byte Characters
        # 0x22
    ]

    def pfs_print(self):
        GUID = ''.join('%0.8X' % int.from_bytes(struct.pack('<I', val), 'little') for val in reversed(self.GUID))
        Version = ''.join('%0.4X' % int.from_bytes(struct.pack('<I', val), 'little') for val in reversed(self.Version))
        VersionType = ''.join(
            '%0.2X' % int.from_bytes(struct.pack('<I', val), 'little') for val in reversed(self.VersionType))

        print('\nPFS Information:\n')
        print('HeaderVersion  : %d' % self.HeaderVersion)
        print('GUID           : %s' % GUID)
        print('Version        : %s' % Version)
        print('VersionType    : %s' % VersionType)
        print('CharacterCount : %d' % (self.CharacterCount * 2))


# Determine PFS Entry Version string via "Version" and "VersionType" fields
def get_version(version_fields, version_types):
    version = ''  # Initialize Version string

    # Each Version Type (1 byte) determines the type of each Version Value (2 bytes)
    # Version Type 'N' is Number, 'A' is Text and ' ' is Empty/Unused
    for idx in range(len(version_fields)):
        eol = '' if idx == len(version_fields) - 1 else '.'

        if version_types[idx] == 65:
            version += '%X%s' % (version_fields[idx], eol)  # 0x41 = ASCII
        elif version_types[idx] == 78:
            version += '%d%s' % (version_fields[idx], eol)  # 0x4E = Number
        elif version_types[idx] in (0, 32):
            version = version.strip('.')  # 0x00 or 0x20 = Unused
        else:
            version += '%X%s' % (version_fields[idx], eol)  # Unknown
            print('\n    Error: Unknown PFS Entry Version Type 0x%0.2X!' % version_types[idx])

    return version


# Get BIOS version from Model Information entry
def get_bios_version(entry_data):
    model_infos = entry_data.decode().split(";")
    version = "unknown"

    print("\nFound MODEL INFORMATION:")
    for info in model_infos:
        print("    %s" % info)
        if info.startswith("Version"):
            version = info.split("=")[1]

    return version


# Get PFS Entry Structure & Size via its Version
def get_pfs_entry(buffer, offset):
    pfs_entry_ver = int.from_bytes(buffer[offset + 0x10:offset + 0x14], 'little')  # PFS Entry Version

    if pfs_entry_ver == 1:
        return PFS_ENTRY, ctypes.sizeof(PFS_ENTRY)
    elif pfs_entry_ver == 2:
        return PFS_ENTRY_R2, ctypes.sizeof(PFS_ENTRY_R2)
    else:
        return PFS_ENTRY_R2, ctypes.sizeof(PFS_ENTRY_R2)


# Calculate Checksum XOR 8 of data
def chk_xor_8(data, init_value):
    value = init_value
    for byte in data: value = value ^ byte
    value = value ^ 0x0

    return value


# Process ctypes Structure Classes
# https://github.com/skochinsky/me-tools/blob/master/me_unpack.py by Igor Skochinsky
def get_struct(buffer, start_offset, class_name, param_list=None):
    if param_list is None: param_list = []

    structure = class_name(*param_list)  # Unpack parameter list
    struct_len = ctypes.sizeof(structure)
    struct_data = buffer[start_offset:start_offset + struct_len]
    fit_len = min(len(struct_data), struct_len)

    if (start_offset >= len(buffer)) or (fit_len < struct_len):
        print('\n    Error: Offset 0x%X out of bounds at %s, possibly incomplete image!' % (
        start_offset, class_name.__name__))

        input('\nPress enter to exit')

        sys.exit(1)

    ctypes.memmove(ctypes.addressof(structure), struct_data, fit_len)

    return structure


# Pause after any unexpected Python exception
# https://stackoverflow.com/a/781074 by Torsten Marek
def show_exception_and_exit(exc_type, exc_value, tb):
    if exc_type is KeyboardInterrupt:
        print('\n')
    else:
        print('\nError: %s crashed, please report the following:\n' % title)
        traceback.print_exception(exc_type, exc_value, tb)
        input('\nPress enter to exit')

    sys.exit(1)


# Dump struct to bytes
def struct_to_bytearray(struct_object):
    struct_len = ctypes.sizeof(struct_object)
    struct_data = bytearray(struct_len)
    struct_data_ptr = (ctypes.c_char * struct_len).from_buffer(struct_data)
    ctypes.memmove(struct_data_ptr, ctypes.addressof(struct_object), struct_len)
    return struct_data


# Set pause-able Python exception handler
sys.excepthook = show_exception_and_exit

# Show script title
print("\n" + title)

# Set argparse Arguments
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--folder', help='the path which includes necessary BIOS entry raw files')
args = parser.parse_args()

# Get ctypes Structure Sizes
pfs_header_size = ctypes.sizeof(PFS_HDR)
pfs_footer_size = ctypes.sizeof(PFS_FTR)
pfs_info_size = ctypes.sizeof(PFS_INFO)

# Check arg
input_path = os.path.abspath(args.folder if args.folder else ".")
print("Checking %s" % input_path)
if not os.path.isdir(input_path):
    print("    Error: the input folder does not exist")
    sys.exit(1)

# input files
all_files = [f for f in os.listdir(input_path) if os.path.isfile(os.path.join(input_path, f))]

# Parsing info
entries = [] # Store entry info, including valid flag, type, GUID, name, version, data
pfs_info = None # Buffer for PFS Information Entry Data
bios_version = 'unknown'

# scan for entries
for file in all_files:
    if not file.startswith("__"):
        print("\nScanning %s" % file)
        with open(os.path.join(input_path, file), "rb") as scanner:
            data = scanner.read()

            # read entry struct
            pfs_entry_struct, pfs_entry_size = get_pfs_entry(data, 0)
            pfs_entry = get_struct(data, 0, pfs_entry_struct)

            # Validate that a known PFS Entry Header Version was encountered
            if pfs_entry.HeaderVersion not in (1, 2):
                print('\n    Error: Unknown PFS Entry Header Version %d!' % pfs_entry.HeaderVersion)
                continue

            # Validate that the PFS Entry Reserved field is empty
            if pfs_entry.Reserved != 0:
                print('\n    Error: Detected non-empty PFS Entry Reserved field!')
                continue

            # Get PFS Entry Version string via "Version" and "VersionType" fields
            entry_version = get_version(pfs_entry.Version, pfs_entry.VersionType)

            # Get PFS Entry GUID in Big Endian format
            entry_guid = ''.join('%0.8X' % int.from_bytes(struct.pack('<I', val), 'little') for val in reversed(pfs_entry.GUID))

            # PFS Entry Data starts after the PFS Entry Structure
            entry_data_start = 0 + pfs_entry_size
            entry_data_end = entry_data_start + pfs_entry.DataSize
            entry_data = data[entry_data_start:entry_data_end]  # Store PFS Entry Data

            # Detect Entry Type
            entry_valid = False # this flag will be changed to True if entry is found in PFS INFORMATION
            entry_type = 'OTHER'  # Adjusted later if PFS Entry is Zlib, Chunks, PFS Info, Model Info

            # Get PFS Information from the PFS Entry with GUID E0717CE3A9BB25824B9F0DC8FD041960 or B033CB16EC9B45A14055F80E4D583FD3
            if entry_guid in ['E0717CE3A9BB25824B9F0DC8FD041960', 'B033CB16EC9B45A14055F80E4D583FD3']:
                entry_valid = True
                entry_type = 'PFS_INFO'

            # Get Model Information from the PFS Entry with GUID 6F1D619A22A6CB924FD4DA68233AE3FB
            elif entry_guid == '6F1D619A22A6CB924FD4DA68233AE3FB':
                entry_valid = True
                entry_type = 'MODEL_INFO'

            # Get Nested PFS from the PFS Entry with GUID 900FAE60437F3AB14055F456AC9FDA84
            elif entry_guid == '900FAE60437F3AB14055F456AC9FDA84':
                entry_type = 'NESTED_PFS'  # Nested PFS are usually zlib-compressed so it might change to 'ZLIB' later

            print("Found entry:")
            print("    Type = %s" % entry_type)
            print("    GUID = %s" % entry_guid)
            print("    Version = %s" % entry_version)

            # Give Names to special PFS Entries, not covered by PFS Information
            if entry_type == 'MODEL_INFO':
                file_name = 'Model Information'
                bios_version = get_bios_version(entry_data)
            elif entry_type == 'PFS_INFO':
                pfs_info = entry_data
                file_name = 'PFS Information'
            else:
                file_name = ''

            # Store entry info
            # Name will be insert later if GUID is found in PFS INFORMATION
            entries.append([entry_valid, entry_type, entry_guid, file_name, entry_version, data])


if pfs_info:
    print("\nFound PFS INFORMATION with below GUIDs")

    # Parse all PFS Information Entries/Descriptors
    info_start = 0  # Increasing PFS Information Entry starting offset
    while len(pfs_info[info_start:info_start + pfs_info_size]) == pfs_info_size:
        # Get PFS Information Structure values
        entry_info = get_struct(pfs_info, info_start, PFS_INFO)

        # Validate that a known PFS Information Header Version was encountered
        if entry_info.HeaderVersion != 1:
            print('\n    Error: Unknown PFS Information Header Version %d!' % entry_info.HeaderVersion)
            break  # Skip PFS Information Entries/Descriptors in case of assertion error

        # Get PFS Information GUID in Big Endian format to match each Info to the equivalent stored PFS Entry details
        entry_guid = ''.join('%0.8X' % int.from_bytes(struct.pack('<I', val), 'little') for val in reversed(entry_info.GUID))

        # The PFS Information Structure is not complete by itself. The size of the last field (Entry Name) is determined from CharacterCount
        # multiplied by 2 due to usage of UTF-16 2-byte Characters. Any Entry Name leading and/or trailing space/null characters are stripped
        entry_name = pfs_info[info_start + pfs_info_size:info_start + pfs_info_size + entry_info.CharacterCount * 2].decode('utf-16').strip()

        print("\n    Entry:")
        print("        GUID: %s" % entry_guid)
        print("        Name: %s" % entry_name)

        # Check if this GUID exits in Entry List
        for entry in entries:
            if entry[2] == entry_guid:
                entry[0] = True
                entry[3] = entry_name

        # The next PFS Information starts after the calculated Entry Name size
        # Two space/null characters seem to always exist after the Entry Name
        info_start += (pfs_info_size + entry_info.CharacterCount * 2 + 0x2)

print("\nImport matched GUIDs in PFS INFORMATION into BIOS payload section")

# import exe parts
with open(os.path.join(input_path, "__exe_begin.bin"), "rb") as importer:
    begin = importer.read()

with open(os.path.join(input_path, "__exe_end.bin"), "rb") as importer:
    end = importer.read()

# payload for uncompressed BIOS section
payload = bytearray()

# import valid
for entry in entries:
    if entry[0]:
        print("    Import %s %s %s" % (entry[2], entry[3], entry[4]))
        payload += bytearray(entry[5])

payload_len = len(payload)
payload_checksum = ~zlib.crc32(payload, 0) & 0xFFFFFFFF

# payload header
header = PFS_HDR()
header.Tag = b'PFS.HDR.'
header.HeaderVersion = 1
header.PayloadSize = payload_len

# payload footer
footer = PFS_FTR()
footer.PayloadSize = payload_len
footer.Checksum = payload_checksum
footer.Tag = b'PFS.FTR.'

# make BIOS section
uncompressed_data = struct_to_bytearray(header) + payload + struct_to_bytearray(footer)

# compress it
compressed_data = zlib.compress(uncompressed_data)
compressed_data_len = len(compressed_data)

# BIOS section header
header = bytearray(0x10)
header[:0x04] = compressed_data_len.to_bytes(4, 'little')
header[0x04: 0x0F] = bytearray(b'\xAA\xEE\xAA\x76\x1B\xEC\xBB\x20\xF1\xE6\x51')
header[0x0F] = chk_xor_8(header[:0x0F], 0x00)

# BIOS section footer
footer = bytearray(0x10)
footer[:0x04] = compressed_data_len.to_bytes(4, 'little')
footer[0x04: 0x0F] = bytearray(b'\xEE\xAA\xEE\x8F\x49\x1B\xE8\xAE\x14\x37\x90')
footer[0x0F] = chk_xor_8(footer[:0x0F], 0x00)

# merge them all
with open(os.path.join(input_path, "__output.exe"), "wb") as exporter:
    exporter.write(begin)
    exporter.write(header)
    exporter.write(compressed_data)
    exporter.write(footer)
    exporter.write(end)

print('Assembled Dell PFS BIOS image!')
