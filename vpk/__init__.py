import struct

__version__ = "0.1"
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

    files = {}
    vpk_path = ''

    def __init__(self, vpk_path, read_header_only=False):
        self.vpk_path = vpk_path

        self.read_header()

        if not read_header_only:
            self.read_index()

    def __repr__(self):
        headonly = ', read_header_only=True' if len(self.files) is 0 else ''
        return "%s('%s'%s)" % (self.__class__.__name__, self.vpk_path, headonly)

    def _read_sz(self, f):
        out = b""
        while True:
            c = f.read(1)
            if c in [b'\x00', b'']:
                break
            out += c

        return out.decode('ascii')

    def read_header(self):
        """
        Reads VPK's header
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
            elif self.version is 1:
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
            elif self.version is 2:
                (self.embed_chunk_length,
                 self.chunk_hashes_length,
                 self.self_hashes_length,
                 self.signature_length
                 ) = struct.unpack("4I", f.read(4*4))
                self.header_length += 4*7
            else:
                raise ValueError("Invalid header, or unsupported version")

    def read_file(self, fullpath):
        """
        Reads and returns the contents of a single file
        """
        if fullpath not in self.files:
            raise ValueError("File path not found")

        meta = self.files[fullpath]
        data = meta['preload']

        if meta['length']:
            with open(self.vpk_path.replace('dir', '%03d' % meta['archive_index'])) as f:
                f.seek(meta['offset'])
                data += f.read(meta['length'])

        return data

    def read_index(self):
        """
        Reads the index and populates VPK.files
        """
        self.files = {}
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
                    while True:
                        filename = self._read_sz(f)
                        if filename == b'':
                            break

                        fullpath = "{}/{}.{}".format(path, filename, ext)

                        (crc,
                         preload_length,
                         archive_index,
                         offset,
                         length,
                         _
                         ) = struct.unpack("IHHIIH", f.read(18))

                        preload = ''
                        if preload_length:
                            preload = f.read(preload_length)

                        self.files[fullpath] = {
                            'crc': crc,
                            'preload_length': preload_length,
                            'archive_index': archive_index,
                            'offset': offset,
                            'length': length,
                            'preload': preload
                        }
