"""
test_rangewrapper.py: tests for the fdsend.rangewapper module

Copyright 2015, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import io

try:
    from unittest import mock
except:
    import mock

import pytest

import fdsend.rangewrapper as mod

MOD = mod.__name__


def test_emulate_seek():
    """
    Given a file descriptor and offset, it reads the file in chunks of 8KB (by
    default) until it reaches the offset.
    """
    fd = mock.Mock()
    offset = 24576  # 24 KB, or 3 chunks of 8 KB (default chunk size)
    mod.emulate_seek(fd, offset)
    fd.read.assert_has_calls([
        mock.call(8192),
        mock.call(8192),
        mock.call(8192),
    ])


def test_emulate_seek_last_remainder():
    """
    Given a file descriptor and offset that isn't a whole multiple of default
    chunk size (8KB), last chunk read is smaller than the default chunk size.
    """
    fd = mock.Mock()
    offset = 24580  # 24 KB + 4 bytes
    mod.emulate_seek(fd, offset)
    fd.read.assert_has_calls([
        mock.call(8192),
        mock.call(8192),
        mock.call(8192),
        mock.call(4),
    ])


def test_emulate_custom_chunk_size():
    """
    Given a custom chunk size, it reads in chunks of specified size.
    """
    fd = mock.Mock()
    offset = 20
    mod.emulate_seek(fd, offset, chunk=10)
    fd.read.asert_has_calls([
        mock.call(10),
        mock.call(10),
    ])


def test_emulate_no_chunking():
    """
    Given chunk size of None, it reads entire offset at once.
    """
    fd = mock.Mock()
    offset = 20
    mod.emulate_seek(fd, offset, chunk=None)
    fd.read.asert_called_once_with(20)


def test_emulate_zero_chunking():
    """
    Given chunk size of 0, it reads entire offset at once.
    """
    fd = mock.Mock()
    offset = 20
    mod.emulate_seek(fd, offset, chunk=0)
    fd.read.asert_called_once_with(20)


def test_force_seek():
    """
    Given a file descriptor, it calls seek() on it with specified offset.
    """
    fd = mock.Mock()
    mod.force_seek(fd, 100)
    fd.seek.assert_called_once_with(100)


@mock.patch(MOD + '.emulate_seek')
def test_force_seek_emulation(emulate_seek):
    """
    Given a file descriptor that does not have seek() method, emulate_seek() is
    used as fallback
    """
    fd = mock.Mock()
    del fd.seek
    mod.force_seek(fd, 100)
    emulate_seek.assert_called_once_with(fd, 100, mod.CHUNK)


@mock.patch(MOD + '.emulate_seek')
def test_force_seek_with_unsupported_seek(emulate_seek):
    """
    Given a file descriptor whose seek method raises UnsupportedOperation
    exception, emulate_seek() is used as fallback.
    """
    fd = mock.Mock()
    fd.seek.side_effect = io.UnsupportedOperation
    mod.force_seek(fd, 100)
    emulate_seek.assert_called_once_with(fd, 100, mod.CHUNK)


def test_range_iter():
    """
    Given a file descript, offset, and length, retruns an iterator that reads
    from the descriptor in chunks of 8 KB (by default).
    """
    fd = mock.Mock()
    offset = 20
    length = 24576  # 3 chunks of 8 KB
    calls = []
    for chunk in mod.range_iter(fd, offset, length):
        calls.append(mock.call(8192))
        fd.read.assert_has_calls(calls)
        assert chunk == fd.read.return_value
    fd.seek.assert_called_once_with(offset)


def test_range_iter_closes_fd():
    """
    Given a file descriptor, when range_iter iteration finishes, the file
    handle is closed.
    """
    fd = mock.Mock()
    list(mod.range_iter(fd, 20, 30))
    assert fd.close.called


def test_range_iter_interruption():
    """
    Given a descriptor that exhausts reads before desired length is reached,
    iteration should stop as soon as file descriptor is exhausted.
    """
    fd = mock.Mock()
    fd.read.side_effect = ['chunk', 'chunk', '']  # exhausted after 2 reads
    length = 3 * mod.CHUNK  # should read 3 chunks
    ret = list(mod.range_iter(fd, 0, length))
    assert len(ret) == 2


def test_range_iter_support_fd_with_no_seek():
    """
    Given a descriptor that does not support seek(), it is able to return the
    correct number of chunks reguardless.
    """
    fd = mock.Mock()
    fd.seek.side_effect = io.UnsupportedOperation
    length = 3 * mod.CHUNK
    ret = list(mod.range_iter(fd, 20, length))
    assert len(ret) == 3
    del fd.seek
    ret = list(mod.range_iter(fd, 20, length))
    assert len(ret) == 3


def test_range_wrapper():
    """
    Given a file descriptor, offset, and length, returns a file-like object
    that provides read() and close() methods.
    """
    fd = mock.Mock()
    offset = length = 20
    ret = mod.RangeWrapper(fd, offset, length)
    assert hasattr(ret, 'read')
    assert hasattr(ret.read, '__call__')
    assert hasattr(ret, 'close')
    assert hasattr(ret.close, '__call__')


@mock.patch(MOD + '.force_seek')
def test_range_wrapper_seeks(force_seek):
    """
    Given a file descriptor, it adjust the offset of the read to specified
    offset using force_seek().
    """
    fd = mock.Mock()
    offset = length = 20
    mod.RangeWrapper(fd, offset, length)
    force_seek.assert_called_once_with(fd, offset, mod.RangeWrapper.chunk)


def test_range_wrapper_close():
    """
    Given file descriptor, when close() method is called, it closes the file
    descriptor itself and clears the reference to file descriptor.
    """
    fd = mock.Mock()
    offset = length = 20
    ret = mod.RangeWrapper(fd, offset, length)
    assert ret.fd is fd
    ret.close()
    assert ret.fd is None
    assert fd.close.called


def test_range_wrapper_close_fails_silently():
    """
    Given file descriptor with no close() method, when close() method is
    called, it fails silently.
    """
    fd = mock.Mock()
    del fd.close
    offset = length = 20
    ret = mod.RangeWrapper(fd, offset, length)
    ret.close()
    assert ret.fd is None


def test_range_wrapper_read_on_closed_descriptor():
    """
    Given closed file descriptor, when read() method is invoked, ValueError is
    raised.
    """
    fd = mock.Mock()
    offset = length = 20
    ret = mod.RangeWrapper(fd, offset, length)
    ret.close()
    with pytest.raises(ValueError):
        ret.read()


def test_range_wrapper_read_without_size():
    """
    Given file descriptor and length, when read() method is invoked without
    arguments, the file descriptor's read() method is invoked with ``length``
    as argument and data read from descriptor is returned.
    """
    fd = mock.Mock()
    offset = length = 20
    ret = mod.RangeWrapper(fd, offset, length)
    data = ret.read()
    fd.read.assert_called_once_with(length)
    assert data == fd.read.return_value


def test_range_wrapper_read_with_size():
    """
    Given file descriptor and length, when calling read() with size that is
    less than length, the descriptor's read() method is called with the
    specified size.
    """
    fd = mock.Mock()
    offset = length = 20
    ret = mod.RangeWrapper(fd, offset, length)
    ret.read(10)
    fd.read.assert_called_once_with(10)


def test_range_wrapper_multiple_reads():
    """
    Given file descriptor and length, when calling read() multiple times with
    size that is less than length, file descriptor's read() method is invoked
    multiple times until sum of all sizes is larger than length and read()
    method returns empty string once that limit is reached.
    """
    fd = mock.Mock()
    offset = length = 20
    ret = mod.RangeWrapper(fd, offset, length)
    data = ret.read(10)
    assert data == fd.read.return_value
    data = ret.read(10)
    assert data == fd.read.return_value
    data = ret.read(10)
    assert data == ''
    data = ret.read(10)
    assert data == ''
    fd.read.assert_has_calls([
        mock.call(10),
        mock.call(10)
    ])
