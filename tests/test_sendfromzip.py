"""
test_sendfromzip.py: tests for fdsend.sendfromzip module

Copyright 2015, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

try:
    from unittest import mock
except ImportError:
    import mock

import fdsend.sendfromzip as mod

MOD = mod.__name__


@mock.patch(MOD + '.range_iter')
def test_zip_range_iter(range_iter):
    """
    Given a closable object, and a file descriptor, when get_zip_range_iter()
    is called with the closable object, it returns an iterator that closes the
    closable object afer returning all chunks from the file descriptor.
    """
    zfile = mock.Mock()
    fd = mock.Mock()
    range_iter.return_value = [1, 2, 3]
    ziter = mod.get_zip_range_iter(zfile)
    ret = list(ziter(fd, 10, 20))
    assert ret == range_iter.return_value
    assert zfile.close.called


@mock.patch(MOD + '.os.stat')
@mock.patch(MOD + '.zipfile.ZipFile', autospec=True)
@mock.patch(MOD + '.send_file')
@mock.patch(MOD + '.get_zip_range_iter')
def test_send_from_zip(get_zip_range_iter, send_file, ZipFile, stat):
    """
    Given path to ZIP file and path of one of the archived files, when
    send_from_zip() is called, it calls send_file() with file descriptor
    matching the archived file, and its metadta.
    """
    fd = mock.Mock()
    zinfo = mock.Mock()
    ZipFile.return_value.open.return_value = fd
    ZipFile.return_value.getinfo.return_value = zinfo
    zinfo.filename = 'foo/bar/baz.html'
    zinfo.file_size = 1024
    stat.return_value.st_mtime = 142945883
    ret = mod.send_from_zip('foo.zip', 'foo/bar/baz.html', ctype='text/html',
                            attachment=True)
    send_file.assert_called_once_with(
        fd, filename='baz.html', size=1024, timestamp=142945883,
        ctype='text/html', attachment=True,
        wrapper=get_zip_range_iter.return_value)
    assert ret == send_file.return_value
