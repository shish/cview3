"""
Iterable ZIP archive genrator.

Derived directly from zipfile.py
"""
import struct, os, time, sys
import binascii

try:
    import zlib # We may need its compression method
except ImportError:
    zlib = None

__all__ = ["ZIP_STORED", "ZIP_DEFLATED", "ZipStream"]


ZIP64_LIMIT= (1 << 31) - 1

# constants for Zip file compression methods
ZIP_STORED = 0
ZIP_DEFLATED = 8
# Other ZIP compression methods not supported

# Here are some struct module formats for reading headers
structEndArchive = "<4s4H2lH"     # 9 items, end of archive, 22 bytes
stringEndArchive = "PK\005\006"   # magic number for end of archive record
structCentralDir = "<4s4B4HlLL5HLl"# 19 items, central directory, 46 bytes
stringCentralDir = "PK\001\002"   # magic number for central directory
structFileHeader = "<4s2B4HlLL2H"  # 12 items, file header record, 30 bytes
stringFileHeader = "PK\003\004"   # magic number for file header
structEndArchive64Locator = "<4slql" # 4 items, locate Zip64 header, 20 bytes
stringEndArchive64Locator = "PK\x06\x07" # magic token for locator header
structEndArchive64 = "<4sqhhllqqqq" # 10 items, end of archive (Zip64), 56 bytes
stringEndArchive64 = "PK\x06\x06" # magic token for Zip64 header
stringDataDescriptor = "PK\x07\x08" # magic number for data descriptor

# indexes of entries in the central directory structure
_CD_SIGNATURE = 0
_CD_CREATE_VERSION = 1
_CD_CREATE_SYSTEM = 2
_CD_EXTRACT_VERSION = 3
_CD_EXTRACT_SYSTEM = 4                  # is this meaningful?
_CD_FLAG_BITS = 5
_CD_COMPRESS_TYPE = 6
_CD_TIME = 7
_CD_DATE = 8
_CD_CRC = 9
_CD_COMPRESSED_SIZE = 10
_CD_UNCOMPRESSED_SIZE = 11
_CD_FILENAME_LENGTH = 12
_CD_EXTRA_FIELD_LENGTH = 13
_CD_COMMENT_LENGTH = 14
_CD_DISK_NUMBER_START = 15
_CD_INTERNAL_FILE_ATTRIBUTES = 16
_CD_EXTERNAL_FILE_ATTRIBUTES = 17
_CD_LOCAL_HEADER_OFFSET = 18

# indexes of entries in the local file header structure
_FH_SIGNATURE = 0
_FH_EXTRACT_VERSION = 1
_FH_EXTRACT_SYSTEM = 2                  # is this meaningful?
_FH_GENERAL_PURPOSE_FLAG_BITS = 3
_FH_COMPRESSION_METHOD = 4
_FH_LAST_MOD_TIME = 5
_FH_LAST_MOD_DATE = 6
_FH_CRC = 7
_FH_COMPRESSED_SIZE = 8
_FH_UNCOMPRESSED_SIZE = 9
_FH_FILENAME_LENGTH = 10
_FH_EXTRA_FIELD_LENGTH = 11


class ZipInfo (object):
    """Class with attributes describing each file in the ZIP archive."""

    __slots__ = (
            'orig_filename',
            'filename',
            'date_time',
            'compress_type',
            'comment',
            'extra',
            'create_system',
            'create_version',
            'extract_version',
            'reserved',
            'flag_bits',
            'volume',
            'internal_attr',
            'external_attr',
            'header_offset',
            'CRC',
            'compress_size',
            'file_size',
        )

    def __init__(self, filename="NoName", date_time=(1980,1,1,0,0,0)):
        self.orig_filename = filename   # Original file name in archive

        # Terminate the file name at the first null byte.  Null bytes in file
        # names are used as tricks by viruses in archives.
        null_byte = filename.find(chr(0))
        if null_byte >= 0:
            filename = filename[0:null_byte]
        # This is used to ensure paths in generated ZIP files always use
        # forward slashes as the directory separator, as required by the
        # ZIP format specification.
        if os.sep != "/" and os.sep in filename:
            filename = filename.replace(os.sep, "/")

        self.filename = filename        # Normalized file name
        self.date_time = date_time      # year, month, day, hour, min, sec
        # Standard values:
        self.compress_type = ZIP_STORED # Type of compression for the file
        self.comment = ""               # Comment for each file
        self.extra = ""                 # ZIP extra data
        if sys.platform == 'win32':
            self.create_system = 0          # System which created ZIP archive
        else:
            # Assume everything else is unix-y
            self.create_system = 3          # System which created ZIP archive
        self.create_version = 20        # Version which created ZIP archive
        self.extract_version = 20       # Version needed to extract archive
        self.reserved = 0               # Must be zero
        self.flag_bits = 0x08           # ZIP flag bits, bit 3 indicates presence of data descriptor
        self.volume = 0                 # Volume number of file header
        self.internal_attr = 0          # Internal attributes
        self.external_attr = 0          # External file attributes
        # Other attributes are set by class ZipFile:
        # header_offset         Byte offset to the file header
        # CRC                   CRC-32 of the uncompressed file
        # compress_size         Size of the compressed file
        # file_size             Size of the uncompressed file

    def DataDescriptor(self):
        if self.compress_size > ZIP64_LIMIT or self.file_size > ZIP64_LIMIT:
            fmt = "<4slQQ"
        else:
            fmt = "<4slLL"
        return struct.pack(fmt, stringDataDescriptor, self.CRC, self.compress_size, self.file_size)

    def FileHeader(self):
        """Return the per-file header as a string."""
        dt = self.date_time
        dosdate = (dt[0] - 1980) << 9 | dt[1] << 5 | dt[2]
        dostime = dt[3] << 11 | dt[4] << 5 | (dt[5] // 2)
        if self.flag_bits & 0x08:
            # Set these to zero because we write them after the file data
            CRC = compress_size = file_size = 0
        else:
            CRC = self.CRC
            compress_size = self.compress_size
            file_size = self.file_size

        extra = self.extra

        if file_size > ZIP64_LIMIT or compress_size > ZIP64_LIMIT:
            # File is larger than what fits into a 4 byte integer,
            # fall back to the ZIP64 extension
            fmt = '<hhqq'
            extra = extra + struct.pack(fmt,
                    1, struct.calcsize(fmt)-4, file_size, compress_size)
            file_size = 0xffffffff # -1
            compress_size = 0xffffffff # -1
            self.extract_version = max(45, self.extract_version)
            self.create_version = max(45, self.extract_version)

        header = struct.pack(structFileHeader, stringFileHeader,
                 self.extract_version, self.reserved, self.flag_bits,
                 self.compress_type, dostime, dosdate, CRC,
                 compress_size, file_size,
                 len(self.filename), len(extra))
        return header + self.filename + extra



class ZipStream:
    """
    """

    def __init__(self, path, arc_path='', compression=ZIP_DEFLATED):
        if compression == ZIP_STORED:
            pass
        elif compression == ZIP_DEFLATED:
            if not zlib:
                raise RuntimeError,\
                      "Compression requires the (missing) zlib module"
        else:
            raise RuntimeError, "That compression method is not supported"

        self.filelist = []              # List of ZipInfo instances for archive
        self.compression = compression  # Method of compression
        self.path = path                # source path
        self.arc_path = arc_path        # top level path in archive
        self.data_ptr = 0               # Keep track of location inside archive

    def __iter__(self):
        for data in self.zip_path(self.path, self.arc_path):
            yield data

        yield self.archive_footer()

    def update_data_ptr(self, data):
        """As data is added to the archive, update a pointer so we can determine
        the location of various structures as they are generated.

        data -- data to be added to archive

        Returns data
        """
        self.data_ptr += len(data)
        return data

    def zip_path(self, path, archive_dir_name):
        """Recursively generate data to add directory tree or file pointed to by
        path to the archive. Results in archive containing

        archive_dir_name/basename(path)
        archive_dir_name/basename(path)/*
        archive_dir_name/basename(path)/*/*
        .
        .
        .
        

        path -- path to file or directory
        archive_dir_name -- name of containing directory in archive
        """
        if os.path.isdir(path):
            dir_name = os.path.basename(path)
            for name in os.listdir(path):
                r_path = os.path.join(path, name)
                r_archive_dir_name = os.path.join(archive_dir_name, dir_name)
                for data in self.zip_path(r_path, r_archive_dir_name):
                    yield data
        else:
            archive_path = os.path.join(archive_dir_name, os.path.basename(path))
            for data in self.zip_file(path, archive_path):
                yield data


    def zip_file(self, filename, arcname=None, compress_type=None):
        """Generates data to add file at 'filename' to an archive.

        filename -- path to file to add to arcive
        arcname -- path of file inside the archive
        compress_type -- unused in ZipStream, just use self.compression


        This function generates the data corresponding to the fields:

        [local file header n]
        [file data n]
        [data descriptor n]

        as described in section V. of the PKZIP Application Note:
        http://www.pkware.com/business_and_developers/developer/appnote/
        """
        st = os.stat(filename)
        mtime = time.localtime(st.st_mtime)
        date_time = mtime[0:6]
        # Create ZipInfo instance to store file information
        if arcname is None:
            arcname = filename
        arcname = os.path.normpath(os.path.splitdrive(arcname)[1])
        while arcname[0] in (os.sep, os.altsep):
            arcname = arcname[1:]
        zinfo = ZipInfo(arcname, date_time)
        zinfo.external_attr = (st[0] & 0xFFFF) << 16L      # Unix attributes
        if compress_type is None:
            zinfo.compress_type = self.compression
        else:
            zinfo.compress_type = compress_type

        zinfo.file_size = st.st_size
        zinfo.header_offset = self.data_ptr    # Start of header bytes

        fp = open(filename, "rb")
        zinfo.CRC = CRC = 0
        zinfo.compress_size = compress_size = 0
        zinfo.file_size = file_size = 0
        yield self.update_data_ptr(zinfo.FileHeader())
        if zinfo.compress_type == ZIP_DEFLATED:
            cmpr = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION,
                 zlib.DEFLATED, -15)
        else:
            cmpr = None
        while 1:
            buf = fp.read(1024 * 8)
            if not buf:
                break
            file_size = file_size + len(buf)
            CRC = binascii.crc32(buf, CRC)
            if cmpr:
                buf = cmpr.compress(buf)
                compress_size = compress_size + len(buf)
            yield self.update_data_ptr(buf)
        fp.close()
        if cmpr:
            buf = cmpr.flush()
            compress_size = compress_size + len(buf)
            yield self.update_data_ptr(buf)
            zinfo.compress_size = compress_size
        else:
            zinfo.compress_size = file_size
        zinfo.CRC = CRC
        zinfo.file_size = file_size
        yield self.update_data_ptr(zinfo.DataDescriptor())
        self.filelist.append(zinfo)


    def archive_footer(self):
        """Returns data to finish off an archive based on the files already
        added via zip_file(...).  The data returned corresponds to the fields:

        [archive decryption header] 
        [archive extra data record] 
        [central directory]
        [zip64 end of central directory record]
        [zip64 end of central directory locator] 
        [end of central directory record]

        as described in section V. of the PKZIP Application Note:
        http://www.pkware.com/business_and_developers/developer/appnote/
        """
        data = []
        count = 0
        pos1 = self.data_ptr
        for zinfo in self.filelist:         # write central directory
            count = count + 1
            dt = zinfo.date_time
            dosdate = (dt[0] - 1980) << 9 | dt[1] << 5 | dt[2]
            dostime = dt[3] << 11 | dt[4] << 5 | (dt[5] // 2)
            extra = []
            if zinfo.file_size > ZIP64_LIMIT or zinfo.compress_size > ZIP64_LIMIT:
                extra.append(zinfo.file_size)
                extra.append(zinfo.compress_size)
                file_size = 0xffffffff #-1
                compress_size = 0xffffffff #-1
            else:
                file_size = zinfo.file_size
                compress_size = zinfo.compress_size

            if zinfo.header_offset > ZIP64_LIMIT:
                extra.append(zinfo.header_offset)
                header_offset = -1  # struct "l" format:  32 one bits
            else:
                header_offset = zinfo.header_offset

            extra_data = zinfo.extra
            if extra:
                # Append a ZIP64 field to the extra's
                extra_data = struct.pack('<hh' + 'q'*len(extra),1, 8*len(extra), *extra) + extra_data
                extract_version = max(45, zinfo.extract_version)
                create_version = max(45, zinfo.create_version)
            else:
                extract_version = zinfo.extract_version
                create_version = zinfo.create_version

            centdir = struct.pack(structCentralDir,
                                  stringCentralDir, create_version,
                                  zinfo.create_system, extract_version, zinfo.reserved,
                                  zinfo.flag_bits, zinfo.compress_type, dostime, dosdate,
                                  zinfo.CRC, compress_size, file_size,
                                  len(zinfo.filename), len(extra_data), len(zinfo.comment),
                                  0, zinfo.internal_attr, zinfo.external_attr,
                                  header_offset)
            
            data.append( self.update_data_ptr(centdir))
            data.append( self.update_data_ptr(zinfo.filename))
            data.append( self.update_data_ptr(extra_data))
            data.append( self.update_data_ptr(zinfo.comment))

        pos2 = self.data_ptr
        # Write end-of-zip-archive record
        if pos1 > ZIP64_LIMIT:
            # Need to write the ZIP64 end-of-archive records
            zip64endrec = struct.pack(structEndArchive64, stringEndArchive64,
                                      44, 45, 45, 0, 0, count, count, pos2 - pos1, pos1)
            data.append( self.update_data_ptr(zip64endrec))

            zip64locrec = struct.pack(structEndArchive64Locator,
                                      stringEndArchive64Locator, 0, pos2, 1)
            data.append( self.update_data_ptr(zip64locrec))

            # XXX Why is `pos3` computed next?  It's never referenced.
            pos3 = self.data_ptr
            endrec = struct.pack(structEndArchive, stringEndArchive,
                                 0, 0, count, count, pos2 - pos1, -1, 0)
            data.append( self.update_data_ptr(endrec))

        else:
            endrec = struct.pack(structEndArchive, stringEndArchive,
                                 0, 0, count, count, pos2 - pos1, pos1, 0)
            data.append( self.update_data_ptr(endrec))

        return ''.join(data)


if __name__ == "__main__":
    zipfile = sys.argv[1]
    path = sys.argv[2]

    zf = open(zipfile, 'wb')

    for data in ZipStream(path):
        zf.write(data)

    zf.close()

