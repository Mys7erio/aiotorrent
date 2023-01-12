<h1 align="center"><b>Aiotorrent</b></h1>
Aiotorrent is an asynchronous, ultra-lightweight torrent library written in pure Python with support for features such as downloading files to disk, streaming of files over HTTP & more.

<br />  

# Requirements
_Tested on `Python 3.11` but it should work on `Python ^3.9` versions just fine._

1. **Dependencies:** The only 2 dependencies which are needed for aiotorrent to work are [`modern-bencode`](https://pypi.org/project/modern-bencode/) and [`bitstring`](https://pypi.org/project/bitstring/).

1. **Streaming dependencies:**  built-in support for streaming files over HTTP. To use this feature, you need to install some extra streaming dependencies.

<br />

# Installation
Install aiotorrent from PyPI using:
```
$ pip install aiotorrent
```
In order to use the streaming feature, you can install the dependencies using:
```
$ pip install aiotorrent[stream-support]
```

<br />


# Quickstart
### Initialisation
------------------
You need to import the Torrent class and pass a torrent file to it:
```
from aiotorrent import Torrent
torrent = Torrent('path/to/torrent')

# To initialise the torrent, you need to call the init() coroutine.
await torrent.init()

```

<!-- ### Files
---------
Files are stored as `File` objects in a list and can be accessed `Torrent.files`.

You can also use the `show_files()` method on the torrent object to show files inside this torrent,:
```
torrent.show_files()
```
_Thereon, optionally, you can store the files into individual variables using list unpacking. The following demo uses a torrent file which has 3 files_:
```
file0, file1, file2 = torrent.files
```

<br /> -->

### Downloading & Streaming
---------------------------
Files can be accessed from the `files` attribute of the torrent class which stores all the `File` objects as a list.
To download a file, you can call the `download()` coroutine and pass in a `File` object:
```
# To download file2
await torrent.download(torrent.files[2])
```

Similarly, to stream a torrent file, you can call the `stream()` coroutine, as follows:
```
await torrent.stream(torrent.files[2])
```
This starts up a [`uvicorn`](https://github.com/encode/uvicorn) server on `localhost:8080` which uses [`starlette`](https://github.com/encode/starlette) behind the scenes as the ASGI framework to stream files over http.

<br />

_The above methods can take additional parameters to customize the behaviour of this library. [Read the documentation]() to know more._

<br />
<br />

# TODO
- Test compatiability on older versions of Python.
- Add documentation for all the classes in the library.
- Add support for HTTP trackers (And later,  WSS trackers).