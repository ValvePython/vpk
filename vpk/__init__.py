import struct
from binascii import crc32

__version__ = "0.2"
__author__ = "Rossen Georgiev"


class VPK:
    """
    Wrapper for reading Valve's VPK files
    """

    # header
    signature = 0
    version = 0
    tree_length = 0
    header_length = 0

    tree = {}
    file_count = 0
    vpk_path = ''

    def __init__(self, vpk_path, read_header_only=False):
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

    def _read_sz(self, f):
        out = b""
        while True:
            c = f.read(1)
            if c in [b'\x00', b'']:
                break
            out += c

        return out.decode('ascii')

    def get_file(self, path):
        """
        Returns VPKFile instance for the given path
        """

        node = self.tree
        for level in path.split('/'):
            try:
                node = node[level]
            except KeyError:
                raise ValueError("Path doesn't exist")

        assert 'crc32' in node, "Path doesn't lead to a single file"

        return VPKFile(self.vpk_path, filepath=path, **node)

    def read_header(self):
        """
        Reads VPK file header from the file
        """
        with open(self.vpk_path, 'r') as f:
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
        with open(self.vpk_path, 'r') as f:
            f.seek(self.header_length)

            while True:
                ext = self._read_sz(f)
                if ext == b'':
                    break

                while True:
                    path = self._read_sz(f)
                    if path == b'':
                        break

                    root = self.tree
                    path = path.split('/')
                    for folder in path:
                        try:
                            root = root[folder]
                        except KeyError:
                            root[folder] = root = {}

                    while True:
                        name = self._read_sz(f)
                        if name == b'':
                            break

                        self.file_count += 1

                        x = root["{}.{}".format(name, ext)] = {
                            'payload': b''
                            }

                        (x['crc32'],
                         x['preload_length'],
                         x['archive_index'],
                         x['offset'],
                         x['length'],
                         _
                         ) = struct.unpack("IHHIIH", f.read(18))

                        if x['preload_length']:
                            x['preload'] = f.read(x['preload_length'])


class VPKFile(file):
    """
    Wrapper class for files with VPK

    Should act like a regular file object. No garantees
    """

    def __init__(self, vpk_path, **kw):
        self.vpk_path = vpk_path
        self.vpk_meta = kw
        self.readbuffer = b''

        for k, v in kw.items():
            setattr(self, k, v)

        super(VPKFile, self).__init__(vpk_path.replace("dir.", "%03d." % self.archive_index), 'rb')
        super(VPKFile, self).seek(self.offset)

    def verify(self):
        """
        Returns True if the file contents match with the CRC32 attribute

        note: reset
        """

        # remember and restore file position
        pos = self.tell()
        self.seek(0)
        data = self.read()
        self.seek(pos)

        return self.crc32 == crc32(data) & 0xffffffff

    def __repr__(self):
        return "%s(%s, %s)" % (
            self.__class__.__name__,
            repr(self.name),
            ', '.join(["%s=%s" % (k, repr(v)) for k, v in self.vpk_meta.items()])
            )

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def __iter__(self):
        return self

    def next(self):
        while True:
            chunk = self.read(512, next_read=True)
            self.readbuffer += chunk

            # the readbuffer is only empty when we've reached EOF
            if b'' == self.readbuffer:
                raise StopIteration

            # produce another line
            pos = self.readbuffer.find('\n')
            if pos > -1:
                line = self.readbuffer[:pos+1]
                self.readbuffer = self.readbuffer[pos+1:]
                return line

            # we've reached EOF, produce whats left in the readbuffer
            if b'' == chunk:
                line = self.readbuffer
                self.readbuffer = b''
                return line

    def close(self):
        super(VPKFile, self).close()

    def tell(self):
        return super(VPKFile, self).tell() - self.offset

    def seek(self, offset):
        if offset < 0:
            raise IOError("Invalid argument")

        super(VPKFile, self).seek(self.offset + offset)

    def read(self, length=-1, next_read=False):
        if not next_read and self.readbuffer != b'':
            raise ValueError("Mixing iteration and read methods would lose data")

        if super(VPKFile, self).tell() >= self.offset + self.length:
            return b''
        else:
            left = self.offset + self.length - super(VPKFile, self).tell()
            return super(VPKFile, self).read(left if length == -1 else min(left, length))

    def write(self, seq):
        raise NotImplementedError("write method is not supported")
