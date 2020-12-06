import struct
from binascii import crc32
from hashlib import md5
from io import open as fopen
import os
import sys

__version__ = "1.3.3"
__author__ = "Rossen Georgiev"


def open(*args, **kwargs):
    """
    Returns a VPK instance for specified path. Same arguments
    """
    return VPK(*args, **kwargs)


def new(*args, **kwargs):
    """
    Returns a NewVPK instance for the specific path. Same arguments
    """
    return NewVPK(*args, **kwargs)


class NewVPK(object):
    def __init__(self, path, path_enc='utf-8'):
        self.path_enc = path_enc

        self.signature = 0x55aa1234
        self.version = 1
        self.tree_length = 0
        self.header_length = 4*3

        self.tree = {}
        self.path = ''
        self.file_count = 0

        self.read_dir(path)

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self.path)

    def read_dir(self, path):
        """
        Reads the given path into the tree
        """
        self.tree = {}
        self.file_count = 0
        self.path = path

        for root, _, filelist in os.walk(path):
            rel = root[len(path):].lstrip('/\\')

            # empty rel, means file is in root dir
            if not rel:
                rel = ' '

            for filename in filelist:
                filename = filename.split('.')
                if len(filename) <= 1:
                    raise RuntimeError("Files without an extension are not supported: {0}".format(
                                       repr(os.path.join(root, '.'.join(filename))),
                                       ))

                ext = filename[-1]
                filename = '.'.join(filename[:-1])

                if ext not in self.tree:
                    self.tree[ext] = {}
                if rel not in self.tree[ext]:
                    self.tree[ext][rel] = []

                self.tree[ext][rel].append(filename)
                self.file_count += 1

        self.tree_length = self.calculate_tree_length()


    def calculate_tree_length(self):
        """
        Walks the tree and calculate the tree length
        """
        tree_length = 0

        for ext in self.tree:
            tree_length += len(ext) + 2

            for relpath in self.tree[ext]:
                tree_length += len(relpath) + 2

                for filename in self.tree[ext][relpath]:
                    tree_length += len(filename) + 1 + 18

        return tree_length + 1


    def save(self, vpk_output_path):
        """
        Saves the VPK at the given path
        """
        with fopen(vpk_output_path, 'wb') as f:
            # write VPK1 header
            f.write(struct.pack("3I", self.signature,
                                      self.version,
                                      self.tree_length))

            self.header_length = f.tell()

            data_offset = self.header_length + self.tree_length

            # write file tree
            for ext in self.tree:
                f.write(ext.encode(self.path_enc) + b"\x00")

                for relpath in self.tree[ext]:
                    norm_relpath = '/'.join(relpath.split(os.path.sep))
                    f.write(norm_relpath.encode(self.path_enc) + b"\x00")

                    for filename in self.tree[ext][relpath]:
                        f.write(filename.encode(self.path_enc) + b'\x00')

                        # append file data
                        metadata_offset = f.tell()
                        file_offset = data_offset
                        real_filename = filename if not ext else (filename + '.' + ext)
                        checksum = 0
                        f.seek(data_offset)

                        with fopen(os.path.join(self.path,
                                                '' if relpath == ' ' else relpath,
                                                real_filename
                                                ),
                                   'rb') as pakfile:
                            for chunk in iter(lambda: pakfile.read(8192), b''):
                                checksum = crc32(chunk, checksum)
                                f.write(chunk)

                        data_offset = f.tell()
                        file_length = f.tell() - file_offset
                        f.seek(metadata_offset)

                        # metadata

                        # crc32
                        # preload_length
                        # archive_index
                        # archive_offset
                        # file_length
                        # suffix
                        f.write(struct.pack("IHHIIH", checksum & 0xFFffFFff,
                                                      0,
                                                      0x7fff,
                                                      file_offset - self.tree_length - self.header_length,
                                                      file_length,
                                                      0xffff
                                                      ))


                    # next relpath
                    f.write(b"\x00")
                # next ext
                f.write(b"\x00")
            # end of file tree
            f.write(b"\x00")


    def save_and_open(self, path):
        """
        Saves the VPK file and returns VPK instance of it
        """
        self.save(path)
        return VPK(path)


def _read_cstring(f, encoding='utf-8'):
    buf = b''

    for chunk in iter(lambda: f.read(64), b''):
        pos = chunk.find(b'\x00')
        if pos > -1:
            buf += chunk[:pos]
            f.seek(f.tell() - (len(chunk) - (pos + 1)))
            break

        buf += chunk

    return buf.decode(encoding) if encoding else buf

class VPK(object):
    """
    Wrapper for reading Valve's Pak files
    """
    signature = 0
    version = 0
    tree_length = 0
    header_length = 0

    def __init__(self, vpk_path, read_header_only=True, path_enc='utf-8', fopen=fopen):
        self.path_enc = path_enc
        self.fopen = fopen

        # header
        self.tree = None
        self.vpk_path = vpk_path

        self.read_header()

        if not read_header_only:
            self.read_index()

    def __repr__(self):
        headonly = ', read_header_only=True' if len(self) == 0 else ''
        return "%s('%s'%s)" % (self.__class__.__name__, self.vpk_path, headonly)

    def __iter__(self):
        if self.tree is None:
            def path_generator():
                for path, meta in self.read_index_iter():
                    yield path

            return iter(path_generator())
        else:
            return iter(self.tree)

    def items(self):
        if self.tree is None:
            tree = self.read_index_iter()

            return tree if sys.version_info >= (3,) else list(tree)
        else:
            return self.tree.items()

    def __len__(self):
        if self.tree is None:
            length = 0
            for _ in self.read_index_iter():
                length += 1

            return length
        else:
            return len(self.tree)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def __getitem__(self, key):
        """
        Returns VPKFile instance
        """
        return self.get_file(key)

    def get_file(self, path):
        """
        Returns VPKFile instance for the given path
        """
        metadata = self.get_file_meta(path)
        return self.get_vpkfile_instance(path, metadata)

    def get_file_meta(self, path):
        """
        Returns metadata for given file path
        """
        if self.tree is None:
            self.read_index()

        if path not in self.tree:
            raise KeyError("Path doesn't exist")

        return self._make_meta_dict(self.tree[path])

    def get_vpkfile_instance(self, path, metadata):
        if isinstance(metadata, tuple):
            metadata = self._make_meta_dict(metadata)
        return VPKFile(self._make_vpkfile_path(metadata), filepath=path, fopen=self.fopen, **metadata)

    def _make_vpkfile_path(self, metadata):
        path = self.vpk_path

        if metadata['archive_index'] != 0x7fff:
            path = path.replace('english','').replace("dir.", "%03d." % metadata['archive_index'])

        return path

    def _make_meta_dict(self, metadata):
        return dict(zip(['preload',
                         'crc32',
                         'preload_length',
                         'archive_index',
                         'archive_offset',
                         'file_length',
                         ], metadata))

    def read_header(self):
        """
        Reads VPK file header from the file
        """
        with self.fopen(self.vpk_path, 'rb') as f:
            (self.signature,
             self.version,
             self.tree_length
             ) = struct.unpack("3I", f.read(3*4))

            # original format - headerless
            if self.signature != 0x55aa1234:
                raise ValueError("File is not VPK (invalid magic)")
            # v1
            elif self.version == 1:
                self.header_length += 4*3
            # v2 with extended header
            #
            # according to http://forum.xentax.com/viewtopic.php?f=10&t=11208
            # struct VPKDirHeader_t
            # {
            #    int32 m_nHeaderMarker;
            #    int32 m_nVersion;
            #    int32 m_nDirectorySize;
            #    int32 m_nEmbeddedChunkSize;
            #    int32 m_nChunkHashesSize;
            #    int32 m_nSelfHashesSize;
            #    int32 m_nSignatureSize;
            # }
            elif self.version == 2:
                (self.embed_chunk_length,
                 self.chunk_hashes_length,
                 self.self_hashes_length,
                 self.signature_length
                 ) = struct.unpack("4I", f.read(4*4))
                self.header_length += 4*7

                f.seek(self.tree_length + self.embed_chunk_length + self.chunk_hashes_length, 1)

                assert self.self_hashes_length == 48, "Self hashes section size mismatch"

                (self.tree_checksum,
                 self.chunk_hashes_checksum,
                 self.file_checksum,
                 ) = struct.unpack("16s16s16s", f.read(16*3))
            else:
                raise ValueError("Invalid header, or unsupported version")

    def calculate_checksums(self):
        assert self.version == 2, "Checksum only work for VPK version 2"

        tree_checksum = md5()
        chunk_hashes_checksum = md5()
        file_checksum = md5()

        def chunk_reader(length, chunk_size=2**14):
            limit = f.tell() + length

            while f.tell() < limit:
                yield f.read(min(chunk_size, limit - f.tell()))

        with self.fopen(self.vpk_path, 'rb') as f:
            file_checksum.update(f.read(self.header_length))

            for chunk in chunk_reader(self.tree_length):
                file_checksum.update(chunk)
                tree_checksum.update(chunk)

            for chunk in chunk_reader(self.embed_chunk_length):
                file_checksum.update(chunk)

            for chunk in chunk_reader(self.chunk_hashes_length):
                file_checksum.update(chunk)
                chunk_hashes_checksum.update(chunk)

            file_checksum.update(f.read(16*2))

        return tree_checksum.digest(), chunk_hashes_checksum.digest(), file_checksum.digest()

    def read_index(self):
        """
        Reads the index and populates the directory tree
        """
        if not isinstance(self.tree, dict):
            self.tree = dict()

        self.tree.clear()

        for path, metadata in self.read_index_iter():
            self.tree[path] = metadata

    def read_index_iter(self):
        """Generator function that reads the file index from the vpk file

        yeilds (file_path, metadata)
        """
        _sblank, _sempty, _sdot, _ssep = ((' ', '', '.', '/')
                                          if self.path_enc else
                                          (b' ', b'', b'.', b'/'))

        with self.fopen(self.vpk_path, 'rb') as f:
            f.seek(self.header_length)

            while True:
                if self.version > 0 and f.tell() > self.tree_length + self.header_length:
                    raise ValueError("Error parsing index (out of bounds)")

                ext = _read_cstring(f, self.path_enc)
                if not ext:
                    break

                while True:
                    path = _read_cstring(f, self.path_enc)
                    if not path:
                        break
                    if path != _sblank:
                        path = path + _ssep
                    else:
                        path = _sempty

                    while True:
                        name = _read_cstring(f, self.path_enc)
                        if not name:
                            break

                        (crc32,
                         preload_length,
                         archive_index,
                         archive_offset,
                         file_length,
                         suffix,
                         ) = metadata = list(struct.unpack("IHHIIH", f.read(18)))

                        if suffix != 0xffff:
                            raise ValueError("Error while parsing index")

                        if archive_index == 0x7fff:
                            metadata[3] = self.header_length + self.tree_length + archive_offset

                        metadata = (f.read(preload_length),) + tuple(metadata[:-1])

                        yield path + name + _sdot + ext, metadata


class VPKFile(object):
    """
    File-like object for files inside VPK
    """
    _fp = None
    _vpk_path = None

    def __init__(self, vpk_path, fopen=fopen, **kw):
        self.vpk_path = vpk_path
        self.fopen = fopen
        self.vpk_meta = kw

        for k, v in kw.items():
            setattr(self, k, v)

        if self.vpk_meta['preload'] != b'':
            self.vpk_meta['preload'] = '...'

        # total file length
        self.length = self.preload_length + self.file_length
        # offset of entire file
        self.offset = 0

        if vpk_path:
            self._fp = self.fopen(vpk_path, 'rb')
            self._fp.seek(self.archive_offset)

    def save(self, path):
        """
        Save the file to the specified path
        """
        # remember and restore file position
        pos = self.tell()
        self.seek(0)

        with fopen(path, 'wb') as output:
            output.truncate(self.length)
            for chunk in iter(lambda: self.read(8192), b''):
                output.write(chunk)

        self.seek(pos)

    def verify(self):
        """
        Returns True if the file contents match with the CRC32 attribute

        note: reset
        """

        # remember file pointer
        pos = self.tell()
        self.seek(0)

        checksum = 0
        for chunk in iter(lambda: self.read(8192), b''):
            checksum = crc32(chunk, checksum)

        # restore file pointer
        self.seek(pos)

        return self.crc32 == checksum & 0xffffffff

    def __repr__(self):
        return "%s(%s, %s)" % (
            self.__class__.__name__,
            repr(self.vpk_path) if self.file_length > 0 else None,
            ', '.join(["%s=%s" % (k, repr(v)) for k, v in self.vpk_meta.items()])
            )

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        line = self.readline()
        if line == b'':
            raise StopIteration
        return line

    def close(self):
        if self._fp:
            self._fp.close()

    def tell(self):
        return self.offset

    def seek(self, offset, whence=0):
        if whence == 0:
            if offset < 0:
                raise IOError("Invalid argument")
        elif whence == 1:
            offset = self.offset + offset
        elif whence == 2:
            offset = self.length + offset
        else:
            raise ValueError("Invalid value for whence")

        self.offset = offset = min(max(offset, 0), self.length)
        self._fp.seek(self.archive_offset + max(offset - self.preload_length, 0))

    def readlines(self):
        return [line for line in self]

    def readline(self, a=False):
        buf = b''

        for chunk in iter(lambda: self.read(256), b''):
            pos = chunk.find(b'\n')
            if pos > -1:
                pos += 1  # include \n
                buf += chunk[:pos]
                self.seek(-(len(chunk) - pos), 1)
                break

            buf += chunk

        return buf

    def read(self, length=-1):
        if length == 0 or self.offset >= self.length:
            return b''

        data = b''

        if self.offset <= self.preload_length:
            data += self.preload[self.offset:self.offset+length if length > -1 else None]
            self.offset += len(data)
            if length > 0:
                length = max(length - len(data), 0)

        if self.file_length > 0 and self.offset >= self.preload_length:
            left = self.file_length - (self.offset - self.preload_length)
            data += self._fp.read(left if length == -1 else min(left, length))
            self.offset += left if length == -1 else min(left, length)

        return data

    def write(self, seq):
        raise NotImplementedError("write method is not supported")
