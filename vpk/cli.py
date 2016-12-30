#!/usr/bin/env python
"""
vpk - command line utility for working with Valve Pak files
"""

from __future__ import print_function
import re
import sys
from fnmatch import fnmatch
import argparse
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
    excl.add_argument('-x', '--extract', dest='out_location', type=str, help='Exctract files to directory')
    info.add_argument('-nd', '--no-directories', dest='makedir', action='store_false', help="Don't create directries during extraction")
    excl.add_argument('-t', '--test', action='store_true', help='Verify contents')
    excl.add_argument('-c', '--create', metavar='DIR', type=str, help='Create VPK file from directory')

    filtr = parser.add_argument_group('Filters')
    fexcl = filtr.add_mutually_exclusive_group()
    fexcl.add_argument('-f', '--filter', metavar="WILDCARD", type=str, help='Wildcard filter for file paths')
    fexcl.add_argument('-re', '--regex', type=str, help='Regular expression filter for file paths')
    fexcl.add_argument('-name', dest='filter_name', metavar="WILDCARD", type=str, help='Filename wildcard filter')

    return parser


def print_header(pak):
    num_files = len(pak)

    print("VPK File:", pak.vpk_path)
    print("Version:", pak.version)
    print("Size: {:,}".format(os.path.getsize(pak.vpk_path)))

    if pak.version > 0:
        print("Header size: {:,}".format(pak.header_length))
        print("Index size: {:,}".format(pak.tree_length))

    print("Number of files: {:,}".format(num_files))


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
        with pak.make_vpkfile(path, metadata) as vpkfile:
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

        with pak.make_vpkfile(path, metadata) as vpkfile:
            if makedir:
                outpath = os.path.join(outdir, path)
            else:
                outpath = os.path.join(outdir, os.path.split(path)[1])

            mktree(outpath)

            vpkfile.save(outpath)

            print(outpath)


def create_vpk(directory, outpath):
    if not os.path.exists(directory):
        raise IOError("path doesn't exist: %s" % repr(directory))
    if not os.path.isdir(directory):
        raise IOError("not a directory: %s" % repr(directory))

    vpk.new(directory).save(outpath)


def main():
    parser = make_argparser()
    args = parser.parse_args()

    if not sys.argv or not args.file:
        parser.print_help()
        return

    try:
        if args.create:
            create_vpk(args.create, args.file)
            return

        pak = vpk.open(args.file)

        path_filter = make_filter_func(args.filter, args.filter_name, args.regex)

        if args.list or args.listall:
            print_file_list(pak, path_filter, args.listall)
        elif args.test:
            print_verifcation(pak)
        elif args.out_location:
            extract_files(pak, path_filter, args.out_location, args.makedir)
        else:
            print_header(pak)

    except IOError as e:
        print("IOError:", str(e))
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
