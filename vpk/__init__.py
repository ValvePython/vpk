import struct
from binascii import crc32
from io import FileIO

__version__ = "0.9"
__author__ = "Rossen Georgiev"


class VPK:
    """
    Wrapper for reading Valve's VPK files
    """

    def __init__(self, vpk_path, read_header_only=False):
        # header
        self.signature = 0
        self.version = 0
        self.tree_length = 0
        self.header_length = 0

        self.tree = {}
        self.file_count = 0
        self.vpk_path = vpk_path

        self.read_header()

        if not read_header_only:
            self.read_index()

    def __repr__(self):
        headonly = ', read_header_only=True' if len(self) == 0 else ''
        return "%s('%s'%s)" % (self.__class__.__name__, self.vpk_path, headonly)

    def __iter__(self):
        def dir_list_generator(tree):
            for k in tree:
                if 'crc32' in tree[k]:
                    yield k
                else:
                    for line in dir_list_generator(tree[k]):
                        yield "%s/%s" % (k, line)

        return dir_list_generator(self.tree)

    def items(self):
        def dir_list_generator(tree):
            for path in tree:
                if 'crc32' in tree[path]:
                    yield path, tree[path]
                else:
                    for filename, meta in dir_list_generator(tree[path]):
                        yield "%s/%s" % (path, filename), meta

        return dir_list_generator(self.tree)

    def __len__(self):
        return self.file_count

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def _read_sz(self, f):
        buf = b''

        for chunk in iter(lambda: f.read(64), b''):
            pos = chunk.find(b'\x00')
            if pos > -1:
                buf += chunk[:pos]
                f.seek(f.tell() - (len(chunk) - (pos + 1)))
                break

            buf += chunk

        return buf.decode('ascii')

    def __getitem__(self, key):
        """
        Returns VPKFile instance
        """
        return self.get_file(key)

    def get_file(self, path):
        """
        Returns VPKFile instance for the given path
        """
        node = self.get_file_meta(path)
        return VPKFile(self.vpk_path, filepath=path, **node)

    def get_file_meta(self, path):
        node = self.tree
        for level in path.split('/'):
            try:
                node = node[level]
            except KeyError:
                raise KeyError("Path doesn't exist")

        if 'crc32' not in node or isinstance(node['crc32'], dict):
            raise KeyError("Path doesn't lead to a file")

        return node

    def read_header(self):
        """
        Reads VPK file header from the file
        """
        with open(self.vpk_path, 'rb') as f:
            (self.signature,
             self.version,
             self.tree_length
             ) = struct.unpack("3I", f.read(3*4))

            # original format - headerless
            if self.signature != 0x55aa1234:
                self.signature = 0
                self.version = 0
                self.tree_length = 0
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
            else:
                raise ValueError("Invalid header, or unsupported version")

    def read_index(self):
        """
        Reads the index and populates the directory tree
        """

        self.tree = {}
        self.file_count = 0
        with open(self.vpk_path, 'rb') as f:
            f.seek(self.header_length)

            while True:
                if self.version > 0 and f.tell() > self.tree_length + self.header_length:
                    raise ValueError("Error parsing index (out of bounds)")

                ext = self._read_sz(f)
                if ext == '':
                    break

                while True:
                    path = self._read_sz(f)
                    if path == '':
                        break

                    root = self.tree
                    if path != ' ':
                        path = path.split('/')
                        for folder in path:
                            try:
                                root = root[folder]
                            except KeyError:
                                root[folder] = root = {}

                    while True:
                        name = self._read_sz(f)
                        if name == '':
                            break

                        self.file_count += 1

                        x = root["{0}.{1}".format(name, ext)] = {
                            'preload': b''
                            }

                        (x['crc32'],
                         x['preload_length'],
                         x['archive_index'],
                         x['archive_offset'],
                         x['file_length'],
                         term,
                         ) = struct.unpack("IHHIIH", f.read(18))

                        if term != 0xffff:
                            raise ValueError("Error while parsing index")

                        if x['archive_index'] == 0x7fff:
                            x['archive_offset'] += self.header_length + self.tree_length

                        if x['preload_length']:
                            x['preload'] = f.read(x['preload_length'])


class VPKFile(FileIO):
    """
    Wrapper class for files with VPK

    Should act like a regular file object. No garantees
    """

    def __init__(self, vpk_path, **kw):
        self.vpk_path = vpk_path
        self.vpk_meta = kw

        for k, v in kw.items():
            setattr(self, k, v)

        if self.vpk_meta['preload'] != b'':
            self.vpk_meta['preload'] = '...'

        # total file length
        self.length = self.preload_length + self.file_length
        # offset of entire file
        self.offset = 0

        if self.file_length == 0:
            self.vpk_path = None
            return

        super(VPKFile, self).__init__(vpk_path.replace("dir.", "%03d." % self.archive_index), 'rb')
        super(VPKFile, self).seek(self.archive_offset)

    def save(self, path):
        """
        Save the file to the specified path
        """
        # remember and restore file position
        pos = self.tell()
        self.seek(0)

        with open(path, 'wb') as output:
            output.truncate(self.length)
            for chunk in iter(lambda: self.read(1024), b''):
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
        for chunk in iter(lambda: self.read(1024), b''):
            checksum = crc32(chunk, checksum)

        # restore file pointer
        self.seek(pos)

        return self.crc32 == checksum & 0xffffffff

    def __repr__(self):
        return "%s(%s, %s)" % (
            self.__class__.__name__,
            repr(self.name) if self.file_length > 0 else None,
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
        super(VPKFile, self).close()

    def tell(self):
        return self.offset

    def seek(self, offset):
        if offset < 0:
            raise IOError("Invalid argument")

        self.offset = offset
        if self.file_length > 0:
            super(VPKFile, self).seek(self.archive_offset + max(offset - self.preload_length, 0))

    def readlines(self):
        return [line for line in self]

    def readline(self, a=False):
        buf = b''

        for chunk in iter(lambda: self.read(256), b''):
            pos = chunk.find(b'\n')
            if pos > -1:
                pos += 1  # include \n
                buf += chunk[:pos]
                self.seek(self.offset - (len(chunk) - pos))
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
            data += super(VPKFile, self).read(left if length == -1 else min(left, length))
            self.offset += left if length == -1 else min(left, length)

        return data

    def write(self, seq):
        raise NotImplementedError("write method is not supported")
