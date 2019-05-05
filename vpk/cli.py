#!/usr/bin/env python
"""
vpk - command line utility for working with Valve Pak files
"""

from __future__ import print_function
import re
import sys
from fnmatch import fnmatch
import argparse
from binascii import hexlify
import os

import vpk

def make_argparser():
    parser = argparse.ArgumentParser(description='Manage Valve Pak files')

    parser.add_argument('--version', action='version', version='%(prog)s ' + str(vpk.__version__))

    info = parser.add_argument_group('Main')
    info.add_argument('file', type=str, help='Input VPK file')

    excl = info.add_mutually_exclusive_group()
    excl.add_argument('-l', '--list', dest='list', action='store_true', help='List file paths')
    excl.add_argument('-la', dest='listall', action='store_true', help='List file paths, crc, size')
    excl.add_argument('-t', '--test', action='store_true', help='Verify contents')
    excl.add_argument('-c', '--create', metavar='DIR', type=str, help='Create VPK file from directory')
    excl.add_argument('-p', '--pipe', dest='pipe_output', action='store_true', help='Write file contents to stdout')
    excl.add_argument('-x', '--extract', dest='out_location', type=str, help='Exctract files to directory')

    info.add_argument('-nd', '--no-directories', dest='makedir', action='store_false', help="Don't create directries during extraction")
    info.add_argument('-pe', '--path-encoding', dest='path_enc', default='utf-8', metavar='ENC', type=str, help='File paths encoding')

    filtr = parser.add_argument_group('Filters')
    fexcl = filtr.add_mutually_exclusive_group()
    fexcl.add_argument('-f', '--filter', metavar="WILDCARD", type=str, help='Wildcard filter for file paths')
    fexcl.add_argument('-re', '--regex', type=str, help='Regular expression filter for file paths')
    fexcl.add_argument('-name', dest='filter_name', metavar="WILDCARD", type=str, help='Filename wildcard filter')

    return parser


def print_header(pak):
    num_files = len(pak)

    print("% 20s"%"VPK File:", pak.vpk_path)
    print("% 20s"%"Version:", pak.version)
    print("% 20s"%"Size:", "{:,}".format(os.path.getsize(pak.vpk_path)))

    if pak.version > 0:
        print("% 20s"%"Header size:", "{:,}".format(pak.header_length))
        print("% 20s"%"Index size:", "{:,}".format(pak.tree_length))

    if pak.version == 2:
        treesum, chunksum, filesum = pak.calculate_checksums()

        treesum_hex = hexlify(pak.tree_checksum).decode('ascii')
        chunksum_hex = hexlify(pak.chunk_hashes_checksum).decode('ascii')
        filesum_hex = hexlify(pak.file_checksum).decode('ascii')

        print("% 20s"%"Embedded chunk size:", "{:,}".format(pak.embed_chunk_length))
        print("% 20s"%"Tree MD5:", treesum_hex, "(OK)" if pak.tree_checksum == treesum else "MISMATCH!")
        print("% 20s"%"Chunk hashes MD5:", chunksum_hex, "(OK)" if pak.chunk_hashes_checksum == chunksum else "MISMATCH!")
        print("% 20s"%"File MD5:", filesum_hex, "(OK)" if pak.file_checksum == filesum else "MISMATCH!")
        print("% 20s"%"Has signature:", "Yes" if pak.signature_length else "No")

    print("% 20s"%"Number of files:", "{:,}".format(num_files))


def make_filter_func(wildcard=None, name_wildcard=None, regex=None):
    path_filter = None

    if wildcard:
        def path_filter(path):
            return fnmatch(path, wildcard)
    elif name_wildcard:
        def path_filter(path):
            return fnmatch(os.path.split(path)[1], name_wildcard)
    elif regex:
        def path_filter(path):
            return not not re.search(regex, path)

    return path_filter


def print_file_list(pak, match_filter=None, include_details=False):
    for path, metadata in pak.read_index_iter():
        if match_filter and not match_filter(path):
            continue

        crc = metadata[1]
        file_size = metadata[5]

        if include_details:
            print("%s CRC:%08x Size:%s" % (path, crc, file_size))
        else:
            print(path)


def print_verifcation(pak):
    for path, metadata in pak.read_index_iter():
        with pak.get_vpkfile_instance(path, metadata) as vpkfile:
            ok = vpkfile.verify()

            if not ok:
                print("%s: FAILED" % path)


def mktree(path):
    path, filename = os.path.split(path)

    if not path:
        return

    if not os.path.isdir(path):
        os.makedirs(path)


def extract_files(pak, match_filter, outdir, makedir=False):
    outdir = os.path.relpath(outdir)

    for path, metadata in pak.read_index_iter():
        if match_filter and not match_filter(path):
            continue

        with pak.get_vpkfile_instance(path, metadata) as vpkfile:
            if makedir:
                outpath = os.path.join(outdir, path)
            else:
                outpath = os.path.join(outdir, os.path.split(path)[1])

            mktree(outpath)

            vpkfile.save(outpath)

            print(outpath)


def pipe_files(pak, match_filter):
    for filepath in pak:
        if match_filter and not match_filter(filepath):
            continue

        vfp = pak.get_file(filepath)

        try:
            _out = sys.stdout.buffer
        except AttributeError:
            _out = sys.stdout

        for chunk in iter(lambda: vfp.read(8192), b''):
            _out.write(chunk)


def create_vpk(args):
    if not os.path.exists(args.create):
        raise IOError("path doesn't exist: %s" % repr(args.create))
    if not os.path.isdir(args.create):
        raise IOError("not a directory: %s" % repr(args.create))

    vpk.new(args.create, path_enc=args.path_enc).save(args.file)


def main():
    parser = make_argparser()
    args = parser.parse_args()

    if not sys.argv or not args.file:
        parser.print_help()
        return

    if args.file == '-':
        print("Reading from/writing to a pipe is not supported")
        return

    try:
        if args.create:
            create_vpk(args.create, args.file)
            return

        pak = vpk.open(args.file, path_enc=args.path_enc)

        path_filter = make_filter_func(args.filter, args.filter_name, args.regex)

        if args.list or args.listall:
            print_file_list(pak, path_filter, args.listall)
        elif args.pipe_output:
            pipe_files(pak, path_filter)
        elif args.test:
            print_verifcation(pak)
        elif args.out_location:
            extract_files(pak, path_filter, args.out_location, args.makedir)
        else:
            print_header(pak)

    except ValueError as e:
        print("Error:", str(e))
    except IOError as e:
        print("IOError:", str(e))
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
