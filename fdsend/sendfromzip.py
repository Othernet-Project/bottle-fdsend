"""
sendfromzip.py: functions from sending content from ZIP file as response

Copyright 2015, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import os
import zipfile

from .sendfile import send_file
from .rangewrapper import range_iter


def get_zip_range_iter(zfile):
    """ Return an iterator generator that closes the ZIP file

    This function is a wrapper around ``fdsend.rangewrapper.range_iter`` which
    allows not only the extracted file's handle to be closed, but also the
    handle for the containing ZIP file itself.
    """
    def zip_range_iter(fd, offset, length):
        for chunk in range_iter(fd, offset, length):
            yield chunk
        zfile.close()
    return zip_range_iter


def send_from_zip(zippath, path, ctype=None, attachment=False):
    """ Returns a response that serves ZIP file content

    This function takes a path to a ZIP file and path of a file within the ZIP
    file and constructs a ``bottle.HTTPResponse`` object that serves the
    extracted content.

    The ``zippath`` argument points to the ZIP file, and ``path`` ponts to the
    path of the file archived file. Content type is derived from the filename,
    and can be overridden by passing an alternative content type using
    ``ctype`` argument.

    The ``attachment`` argument can be used to set the Content-Disposition
    header.

    Note that the modification date for the file being served is actually a
    modification time of the ZIP file itself.

    Other metadata are derived from the ``zipfile.ZipInfo`` object for the
    given path.

    This is a wrapper around ``fdsend.sendfile.send_file()`` function.
    """
    z = zipfile.ZipFile(zippath)
    fd = z.open(path)
    zinfo = z.getinfo(path)
    filename = os.path.basename(zinfo.filename)
    timestamp = os.stat(zippath).st_mtime
    size = zinfo.file_size
    return send_file(fd, filename=filename, size=size, timestamp=timestamp,
                     ctype=ctype, attachment=attachment,
                     wrapper=get_zip_range_iter(z))
