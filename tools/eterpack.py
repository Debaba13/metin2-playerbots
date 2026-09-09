#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EterPack (.eix/.epk) reader and writer for the r40250 client.

The client keeps its scripts in pack/root.epk and reads them through an index,
root.eix, that is one LZO object encrypted with the index key; every file in
the .epk is its own LZO object, encrypted with the data key when its type says
so. Nothing on a player's machine can add a file to such an archive except a
GUI packer, which is why the client-side half of a feature (the F9 GM panel,
say) used to be "repack root.epk by hand". This does it from a script:

    python tools/eterpack.py list   <pack/root>
    python tools/eterpack.py extract <pack/root> <outdir>
    python tools/eterpack.py repack  <pack/root> <outpack/root> <dir-with-replacements>

`repack` rewrites the archive with every file of the original, taking a file
from <dir> instead when one of the same name is there (a new name is appended).
Types are kept per file; a new file gets the type of the majority. Needs
python-lzo (apt liblzo2-dev + pip python-lzo; the docker python image does).

Keys are the stock r40250 ones (EterPack.cpp). A client with its own keys
fails the index check loudly - the fourcc of the decrypted index is tested -
rather than writing garbage.
"""
import os
import struct
import sys
import zlib

import lzo

INDEX_KEY = (45129401, 92367215, 681285731, 1710201)
DATA_KEY = (78952482, 527348324, 1632463, 486575)
DELTA = 0x9E3779B9
MASK = 0xFFFFFFFF
ENTRY = 192
FOURCC_LZO = b'MCOZ'
FOURCC_INDEX = b'EPKD'


def xtea_decrypt_block(v0, v1, k):
    s = (DELTA * 32) & MASK
    for _ in range(32):
        v1 = (v1 - ((((v0 << 4) ^ (v0 >> 5)) + v0) ^ (s + k[(s >> 11) & 3]))) & MASK
        s = (s - DELTA) & MASK
        v0 = (v0 - ((((v1 << 4) ^ (v1 >> 5)) + v1) ^ (s + k[s & 3]))) & MASK
    return v0, v1


def xtea_encrypt_block(v0, v1, k):
    s = 0
    for _ in range(32):
        v0 = (v0 + ((((v1 << 4) ^ (v1 >> 5)) + v1) ^ (s + k[s & 3]))) & MASK
        s = (s + DELTA) & MASK
        v1 = (v1 + ((((v0 << 4) ^ (v0 >> 5)) + v0) ^ (s + k[(s >> 11) & 3]))) & MASK
    return v0, v1


def xtea(data, key, encrypt):
    out = bytearray(len(data))
    f = xtea_encrypt_block if encrypt else xtea_decrypt_block
    for i in range(0, len(data) - 7, 8):
        v0, v1 = struct.unpack_from('<II', data, i)
        a, b = f(v0, v1, key)
        struct.pack_into('<II', out, i, a, b)
    tail = len(data) % 8
    if tail:
        out[-tail:] = data[-tail:]
    return bytes(out)


def lzo_unpack(blob, key):
    """One CLZObject: fourcc, encrypted size, compressed size, real size, data."""
    fourcc, enc, comp, real = struct.unpack_from('<4sIII', blob, 0)
    if fourcc != FOURCC_LZO:
        raise ValueError('not an LZO object: %r' % fourcc)
    # The encrypted region is the fourcc again and then the LZO stream, padded
    # to the cipher's eight bytes; an unencrypted object carries the stream
    # straight after the header.
    if key:
        body = xtea(blob[16:16 + enc], key, False)
        if body[:4] != FOURCC_LZO:
            raise ValueError('wrong key: decrypted fourcc %r' % body[:4])
        return lzo.decompress(body[4:4 + comp], False, real)
    if blob[16:20] != FOURCC_LZO:
        raise ValueError('unencrypted object without its inner fourcc')
    return lzo.decompress(blob[20:20 + comp], False, real)


def lzo_pack(data, key):
    comp = lzo.compress(data, 9, False)
    enc = 0
    body = FOURCC_LZO + comp
    if key:
        body += bytes((-len(body)) % 8)
        enc = len(body)
        body = xtea(body, key, True)
    return struct.pack('<4sIII', FOURCC_LZO, enc, len(comp), len(data)) + body


def read_index(path_eix):
    raw = open(path_eix, 'rb').read()
    index = lzo_unpack(raw, INDEX_KEY)
    fourcc, version, count = struct.unpack_from('<4sII', index, 0)
    if fourcc != FOURCC_INDEX:
        raise ValueError('index fourcc %r: not a stock-key archive' % fourcc)
    entries = []
    for i in range(count):
        off = 12 + i * ENTRY
        (idx, name, crc, disk, real, size, pos, typ) = struct.unpack_from('<I161s3xIIIIIB3x', index, off)
        entries.append({'id': idx, 'name': name.split(b'\0', 1)[0].decode('latin-1'), 'crc': crc,
                        'disk': disk, 'real': real, 'size': size, 'pos': pos, 'type': typ})
    return version, entries


# COMPRESSED_TYPE_COMPRESS (1) is an LZO object, plain in this client and under
# a pack key in others; the first file decides and the writer uses the same.
TYPE1_KEY = [None]


def read_file(epk, e):
    blob = epk[e['pos']:e['pos'] + e['disk']]
    if e['type'] == 0:
        return blob
    if e['type'] == 1:
        if TYPE1_KEY[0] is None:
            for key in (None, INDEX_KEY, DATA_KEY):
                try:
                    data = lzo_unpack(blob, key)
                    TYPE1_KEY[0] = key
                    return data
                except Exception:
                    continue
            raise ValueError('file %s: no stock key opens a type-1 object' % e['name'])
        return lzo_unpack(blob, TYPE1_KEY[0])
    if e['type'] == 2:
        return lzo_unpack(blob, DATA_KEY)
    raise ValueError('file %s has type %d (not lzo/raw); refusing' % (e['name'], e['type']))


def write_pack(path_base, version, files):
    """files: list of (name, data, type). Writes <base>.eix and <base>.epk."""
    epk = bytearray()
    entries = []
    for i, (name, data, typ) in enumerate(files):
        if typ == 0:
            blob = data
        elif typ == 1:
            blob = lzo_pack(data, TYPE1_KEY[0])
        elif typ == 2:
            blob = lzo_pack(data, DATA_KEY)
        else:
            raise ValueError('type %d' % typ)
        # The client maps data_size bytes at data_position, and the stock
        # packer lays every file at a 128-byte boundary with data_size the
        # on-disk size rounded up to 128 and the archive padded to match; a
        # data_size larger than what is left in the file - the real size of
        # a compressed last file, say - maps past the end and the client dies
        # without a word at login. (Only the fourth DWORD, `size`, is
        # uninitialised garbage in the stock index; it gets the real size.)
        pos = len(epk)
        epk += blob
        padded = (len(blob) + 127) // 128 * 128
        epk += bytes(padded - len(blob))
        nm = name.encode('latin-1')
        entries.append(struct.pack('<I161s3xIIIIIB3x', i, nm, zlib.crc32(nm.lower()) & MASK,
                                   len(blob), padded, len(data), pos, typ))
    index = struct.pack('<4sII', FOURCC_INDEX, version, len(files)) + b''.join(entries)
    open(path_base + '.epk', 'wb').write(bytes(epk))
    open(path_base + '.eix', 'wb').write(lzo_pack(index, INDEX_KEY))


def main():
    cmd = sys.argv[1]
    base = sys.argv[2]
    version, entries = read_index(base + '.eix')
    if cmd == 'list':
        print('version', version, 'files', len(entries))
        for e in entries:
            print('%3d type=%d size=%7d disk=%7d %s' % (e['id'], e['type'], e['real'], e['disk'], e['name']))
        return
    epk = open(base + '.epk', 'rb').read()
    if cmd == 'extract':
        out = sys.argv[3]
        os.makedirs(out, exist_ok=True)
        for e in entries:
            data = read_file(epk, e)
            p = os.path.join(out, e['name'].replace('\\', '/'))
            os.makedirs(os.path.dirname(p) or out, exist_ok=True)
            open(p, 'wb').write(data)
        print('extracted', len(entries), 'files to', out)
        return
    if cmd == 'repack':
        out_base, repl = sys.argv[3], sys.argv[4]
        replacements = {}
        for root, _, names in os.walk(repl):
            for n in names:
                rel = os.path.relpath(os.path.join(root, n), repl).replace('\\', '/')
                replacements[rel.lower()] = open(os.path.join(root, n), 'rb').read()
        types = [e['type'] for e in entries]
        default_type = max(set(types), key=types.count)
        files = []
        seen = set()
        for e in entries:
            key = e['name'].replace('\\', '/').lower()
            data = replacements.pop(key, None)
            if data is None:
                data = read_file(epk, e)
            else:
                seen.add(key)
                print('replaced', e['name'], len(data))
            files.append((e['name'], data, e['type'] if e['type'] in (0, 1, 2) else default_type))
        for key, data in sorted(replacements.items()):
            print('added', key, len(data))
            files.append((key, data, default_type))
        write_pack(out_base, version, files)
        print('wrote', out_base + '.eix/.epk', 'files', len(files))
        return
    raise SystemExit('usage: list|extract|repack')


if __name__ == '__main__':
    main()
