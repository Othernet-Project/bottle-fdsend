=============
bottle-fdsend
=============

This package implements functions for constructing bottle's ``HTTPResponse``
objects from file handles. Unlike the ``bottle.static_file()`` function,
functions in this package allow for serving files constructed in memory, or
unpacked from compressed archives into memory.

Installation
============

To install bottle-fdsend, you can use pip or easy_install commands::

    pip install bottle-fdsend

    easy_install bottle-fdsend

Basic usage
===========

The function we will be using most of the time is the ``fdsend.send_file()`` 
function.  At it's simplest, we simply pass a file-like object to this
function and it will return a ``bottle.HTTPResponse`` object.

For example::

    from StringIO import StringIO
    from fdsend import send_file

    def my_request_handler():
        s = StringIO('foo')
        return send_file(s)

Because we are working with in-memory files and not physical files, however,
none of the common response headers are set if we don't supply additional
metadata about the file. In order to set Content-Type, Content-Length and
similar headers, we need to pass a few optional arguments.

Note that ``send_file()`` merely constructs a response object. We have to
return it in order to have bottle serve it. We also need to keep in mind that
the returned response object is a brand new one and anything we do to
``bottle.response`` is not reflected on it. If we need to set additional
headers and such, we must do so on the returned response object, not the
global ``bottle.response`` object.

Content type
============

There are two ways to set the Content-Type header. One is to pass the ctype
argument::

    def my_request_handler():
        ....
        return send_file(s, ctype='text/html')

Another method is to specify a filename with extension:

    def my_request_handler():
        ...
        return send_file(s, filename='foo.html')

If you pass both arguments, the ``ctype`` argument takes precedence when it
comes to Content-Type header.

Character set and encoding
==========================

When we set the Content-Type header by means of passing a filename, the content
type is automatically calculated based on file extension. In case of files
whose MIME type (content type) starts with 'test/' (e.g., 'text/html',
'text/plain', and so on), character set is appended to the Content-Type header.

For example, ``send_file(s, filename='foo.html')`` results in a Content-Type
header that looks like this::

    Content-Type: text/html; charset=UTF-8

The 'UTF-8' character set is the default. If our data is using a different
character set, we need to explicitly specify it. ::

    def my_request_handler():
        ...
        return send_file(s, filename='foo.html', charset='ascii')

With above snippet, we get a different Content-Type header::

    Content-Type: text/html; charset=ascii

Another header gets automatically added depending on file extension, and that
is the Content-Encoding header. This applies to compressed files. For example::

    def my_request_handler():
        ...
        return send_file(s, filename='foo.html.gz')

The above snippet generates the following headers:

    Content-Type: text/html; charset=UTF-8
    Content-Encoding: gzip
    
The Content-Encoding header cannot be set manually, but it can be omitted by
manually passing the ``ctype`` argument.

File size and byte serving
==========================

Because it would be wasteful to read from the file handle just to obtain the
file size, it is our responsibility to know in advance the size of our file and
tell ``send_file()`` what size it should use. This is done by using the aptly
named ``size`` parameter.

    def my_request_handler():
        ...
        return send_file(s, size=2000)

The size is in bytes, and when it is passed, two headers are added::

    Content-Length: 20000
    Accept-Range: bytes

The first header tells the client the size of the payload, and the second
header announces we are able to do byte serving_. Byte serving is especially
useful when browsers want to retrieve portions of the files (e.g., resume a
download, load files in stages, like in video players, PDF extensions, etc).

As programmers, we don't really need to do anything to take advantage of byte
serving techniques: ``send_file()`` takes care of it. However, we do need to
know the total size of the file and pass it.

Note that response when doing byte serving is 206, not 200.

File timestamp and 304 Not Modified responses
=============================================

If you want the Last-Modified header to be set, you must pass the timestamp
argument. The timestamp must be in seconds since Unix epoch. ::

    def my_request_handler():
        ...
        return send_file(s, timestamp=1429458831)

The above timestamp will generate the following Last-Modified header::

    Last-Modified: Sun, 19 Apr 2015 15:53:51 GMT

Passing the timestamp also causes ``send_file()`` to automatically return a
HTTP 304 Not Modified response when client includes a valid
``If-Modified-Since`` request header.

Content-Disposition
===================

When Content-Disposition header is set to a value of 'attachment', most modern
browsers will offer the user to download the file (by opening a download
dialog, for instance) instead of trying to display the contents in the browser
window. To set this header, we need to pass both the filename and the
``attachment`` argument::

    def my_request_handler():
        ...
        return send_file(s, filename='foo.html', attachment=True)

Byte serving wrappers
=====================

Lastly, we can control how the ranges are returned from the file-like object in 
byte serving. 

The simplest wrapper we can use is the bottle's own ``bottle._file_iter_range`` 
generator function. This wrapper allows us to iterate over the desired range
and return file data in chunks (1MB by default). 

While this works in most cases, it does not work for some types of file-like
objects, such as file handles for ZIP file contents using DEFLATE compression
which do not allow ``seek()`` to be called on them. (Not the mention the fact
that ``bottle._file_iter_range`` is not a public API and therefore subject to
change).

This package provides two alternatives. One is
``fdsend.rangewrapper.range_iter`` generator function and another is
``fdsend.rangewrapper.RangeWrapper`` class.

The generator function is similar to bottle's generator function, but
specifically designed to work around file-like objects that do not support
``seek()``.

The ``RangeWrapper`` is a bit different and it returns a file-like object that
has its own ``read()`` method which is restricted to the requested range.

The primary difference between the two is whether ``wsgi.file_wrapper`` feature
is used on not. This feature requires a file-like object to be passed in order
to be used.

The default wrapper is ``fdsend.rangewrapper.range_iter``.

It is also possible to write your own wrapper. The wrapper must be a callable
(function, class, etc) and must accept the following positional arguments:

- file handle
- offset (in bytes from the start of the file)
- length (size of the range in bytes)

The return value must be a valid WSGI response body (string, iterable,
file-like object).

Feature requests and bug reports
================================

Please report all feature requests and bugs to our `issue tracker`_.

.. _byte serving: https://en.wikipedia.org/wiki/Byte_serving
.. _issue tracker: https://github.com/Outernet-Project/bottle-fdsend/issues
