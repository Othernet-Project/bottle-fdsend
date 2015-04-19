"""
test_sendfile.py: tests for fdsend.sendfile module

Copyright 2015, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import time
import pytest

try:
    from unittest import mock
except ImportError:
    import mock

import fdsend.sendfile as mod

MOD = mod.__name__


def test_format_ts():
    """
    Given timestamp, format_ts() returns a timestamp according to standards.
    """
    timestamp = 1429458831
    assert mod.format_ts(timestamp) == 'Sun, 19 Apr 2015 15:53:51 GMT'


@mock.patch(MOD + '.time.gmtime')
def test_format_ts_with_no_args(gmtime):
    """
    Given no timestamp, format_ts() returns a timestamp for current time and
    date.
    """
    tstruct = time.struct_time((2015, 1, 1, 0, 0, 0, 0, 0, 0))
    gmtime.return_value = tstruct  # making gmtime deterministic
    assert mod.format_ts() == 'Mon, 01 Jan 2015 00:00:00 GMT'


def test_send_file_with_wrong_object():
    """
    Given an object that has no 'read' attribute, when calling send_file(),
    ValueError is raised.
    """
    fd = mock.Mock()
    del fd.read
    with pytest.raises(ValueError):
        mod.send_file(fd, 'foo.txt')


@mock.patch(MOD + '.request')
@mock.patch(MOD + '.HTTPResponse')
def test_send_file_mime(HTTPResponse, *ignored):
    """
    Given a file descriptor and filename, mime type is automatically guessed
    and appropriate Content-Type header is set.
    """
    fd = mock.Mock()
    mod.send_file(fd, 'foo.pdf')
    expected_headers = {
        'Content-Type': 'application/pdf'
    }
    HTTPResponse.assert_called_once_with(fd, status=200, **expected_headers)


@mock.patch(MOD + '.request')
@mock.patch(MOD + '.HTTPResponse')
def test_send_file_mime_text(HTTPResponse, *ignored):
    """
    Given a filename that matches a text type, appropriate charset is added to
    the Content-Type header.
    """
    fd = mock.Mock()
    mod.send_file(fd, 'foo.html')
    expected_headers = {
        'Content-Type': 'text/html; charset=UTF-8'
    }
    HTTPResponse.assert_called_once_with(fd, status=200, **expected_headers)


@mock.patch(MOD + '.request')
@mock.patch(MOD + '.HTTPResponse')
def test_send_file_custom_encoding(HTTPResponse, *ignored):
    """
    Given a filename that matches a text type, when send_file() is called with
    specific encoding, the encoding is added to the Content-Type header.
    """
    fd = mock.Mock()
    mod.send_file(fd, 'foo.html', charset='ascii')
    expected_headers = {
        'Content-Type': 'text/html; charset=ascii'
    }
    HTTPResponse.assert_called_once_with(fd, status=200, **expected_headers)


@mock.patch(MOD + '.request')
@mock.patch(MOD + '.HTTPResponse')
def test_send_file_enctype(HTTPResponse, *ignored):
    """
    Given a filename with .gz extension, when send_file() is called, it
    should set Content-Encoding header.
    """
    fd = mock.Mock()
    mod.send_file(fd, 'foo.tar.gz')
    expected_headers = {
        'Content-Type': 'application/x-tar',
        'Content-Encoding': 'gzip',
    }
    HTTPResponse.assert_called_once_with(fd, status=200, **expected_headers)


@mock.patch(MOD + '.request')
@mock.patch(MOD + '.HTTPResponse')
def test_no_content_type(HTTPResponse, *ignored):
    """
    Given a filename with unknown content type, no Content-Type header is set.
    """
    fd = mock.Mock()
    mod.send_file(fd, 'foo')
    HTTPResponse.assert_called_once_with(fd, status=200)


@mock.patch(MOD + '.request')
@mock.patch(MOD + '.HTTPResponse')
def test_no_content_type_but_has_enc(HTTPResponse, *ignored):
    """
    Given a filename for which only encoding can be calculated, no Content-Type
    header is set.
    """
    fd = mock.Mock()
    mod.send_file(fd, 'foo.gz')
    expected_headers = {
        'Content-Encoding': 'gzip',
    }
    HTTPResponse.assert_called_once_with(fd, status=200, **expected_headers)


@mock.patch(MOD + '.request')
@mock.patch(MOD + '.HTTPResponse')
def test_send_with_size(HTTPResponse, request):
    """
    Given a size, it should set both Content-Length and Accept-Ranges headers.
    """
    fd = mock.Mock()
    request.environ.get.return_value = None
    mod.send_file(fd, 'foo', 200)
    expected_headers = {
        'Content-Length': 200,
        'Accept-Ranges': 'bytes',
    }
    HTTPResponse.assert_called_once_with(fd, status=200, **expected_headers)


@mock.patch(MOD + '.request')
@mock.patch(MOD + '.HTTPResponse')
def test_send_with_timestamp(HTTPResponse, request):
    """
    Given a timestamp, it should set Last-Modified header.
    """
    fd = mock.Mock()
    request.environ.get.return_value = None
    mod.send_file(fd, 'foo', timestamp=1429458831)
    expected_headers = {
        'Last-Modified': 'Sun, 19 Apr 2015 15:53:51 GMT'
    }
    HTTPResponse.assert_called_once_with(fd, status=200, **expected_headers)


@mock.patch(MOD + '.parse_date')
@mock.patch(MOD + '.time.gmtime')
@mock.patch(MOD + '.request')
@mock.patch(MOD + '.HTTPResponse')
def test_if_modified_since(HTTPResponse, request, getmtime, parse_date):
    """
    Given timestamp and If-Modified-Since request header and timestamp that is
    older than the header value, when calling send_file(), HTTP 304 response is
    created instead of the regular response.  A Date header should be set to
    current timestamp.
    """
    fd = mock.Mock()
    timestamp = 1428841333
    modsince = 'Sat, 24 Apr 2015 12:22:14 GMT'
    parse_date.return_value = 1428841334
    getmtime.return_value = time.struct_time((
        2015, 4, 19, 16, 48, 12, 6, 0, 0))
    request.environ.get.return_value = modsince
    mod.send_file(fd, 'foo', timestamp=timestamp)
    expected_headers = {
        'Last-Modified': 'Sun, 19 Apr 2015 16:48:12 GMT',
        'Date': 'Sun, 19 Apr 2015 16:48:12 GMT',
    }
    HTTPResponse.assert_called_once_with(status=304, **expected_headers)


@mock.patch(MOD + '.parse_date')
@mock.patch(MOD + '.time.gmtime')
@mock.patch(MOD + '.request')
@mock.patch(MOD + '.HTTPResponse')
def test_if_modified_since_stale(HTTPResponse, request, getmtime, parse_date):
    """
    Given timestamp and If-Modified-Since request header and timestamp that is
    newer than the header value, when calling send_file(), HTTP 304 response is
    created instead of the regular response.  A Date header should be set to
    current timestamp.
    """
    fd = mock.Mock()
    timestamp = 1428841335
    modsince = 'Sat, 24 Apr 2015 12:22:14 GMT'
    parse_date.return_value = 1428841334
    getmtime.return_value = time.struct_time((
        2015, 4, 19, 16, 48, 12, 6, 0, 0))
    request.environ.get.return_value = modsince
    mod.send_file(fd, 'foo', timestamp=timestamp)
    expected_headers = {
        'Last-Modified': 'Sun, 19 Apr 2015 16:48:12 GMT',
    }
    HTTPResponse.assert_called_once_with(fd, status=200, **expected_headers)


@mock.patch(MOD + '.request')
@mock.patch(MOD + '.HTTPResponse')
def test_head(HTTPResponse, request):
    """
    Given request method is HEAD, emtpy string is returned as body instead of
    the file descriptor.
    """
    fd = mock.Mock()
    request.method = 'HEAD'
    mod.send_file(fd, 'foo')
    HTTPResponse.assert_called_once_with('', status=200)


@mock.patch(MOD + '.parse_range_header')
@mock.patch(MOD + '.request')
@mock.patch(MOD + '.HTTPError')
def test_wrong_range(HTTPError, request, parse_range_header):
    """
    Given size and invalid Range request header, HTTP 416 error should be
    returned.
    """
    fd = mock.Mock()
    parse_range_header.return_value = []
    mod.send_file(fd, 'foo', size=200)
    HTTPError.assert_called_once_with(416, 'Request Range Not Satisfiable')


@mock.patch(MOD + '.parse_range_header')
@mock.patch(MOD + '.request')
@mock.patch(MOD + '.HTTPResponse')
def test_range_wrapper(HTTPResponse, request, parse_range_header):
    """
    Given size and valid Range request header, file descriptor is wrapped, and
    Content-Range and Content-Length headers are set, with 206 status code.
    """
    fd = mock.Mock()
    wrapper = mock.Mock()
    parse_range_header.return_value = ((20, 300),)
    mod.send_file(fd, 'foo', size=400, wrapper=wrapper)
    expected_headers = {
        'Accept-Ranges': 'bytes',
        'Content-Length': '280',
        'Content-Range': 'bytes 20-299/400',
    }
    wrapper.assert_called_once_with(fd, offset=20, length=280)
    HTTPResponse.assert_called_once_with(
        wrapper.return_value, status=206, **expected_headers)
