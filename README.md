<h1 align="center"><b>Aiotorrent</b></h1>
Aiotorrent is an asynchronous, ultra-lightweight torrent library written in pure Python with support for unique features such as serving of files over HTTP without downloading to disk & more.    

<br>
A comprehensive list of features supported by aiotorrent as of now are:

  - Complete asyncio support
  - Connecting to various types of torrent trackers (HTTP & UDP)
  - Specifying an appropriate piece download strategy (default and sequential downloading)
  - Downloading files to disk
  - Serving files over HTTP without saving them to disk

<br>

> [!NOTE]
> This library is still in active development and many additional features such as downloading files from a magnet link, resuming torrent downloads, etc are yet to (but soon will) be implemented.

<br />

# Requirements

_Tested on `Python 3.11` but it should work on `Python ^3.9` versions just fine._

1. **Dependencies:** The only 2 dependencies which are needed for aiotorrent to work are [`fast-bencode`](https://pypi.org/project/fast-bencode/) and [`bitstring`](https://pypi.org/project/bitstring/).

2. **Streaming dependencies:** built-in support for streaming files over HTTP. To use this feature, you need to install extra streaming dependencies.

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

```python
# Import the Torrent class and pass a torrent file to it:
from aiotorrent import Torrent
torrent = Torrent('path/to/file.torrent')

# To initialise the torrent, you need to call the init() coroutine.
await torrent.init()
```

## Downloading & Streaming

Torrent files are stored inside `Torrent.files` as a list. We can access them by sub-scripting the `Torrent.files` attribute, like as follows:

### Example to download and stream files

```python
# To download the third file
await torrent.download(torrent.files[2])
```

Similarly, to serve a torrent file over HTTP, you can call the `stream()` coroutine, as follows:

```python
# To stream the second file, etc
await torrent.stream(torrent.files[1])
```

This starts up a [`uvicorn`](https://github.com/encode/uvicorn) server on `localhost:8080` which uses [`starlette`](https://github.com/encode/starlette) behind the scenes as the ASGI framework to stream files over http.


### Piece downloading strategy
You can also change how pieces of a particular file are being downloaded. Currently, this library offers two download strategies:
  - *Default*: This strategy is used when the `strategy` parameter is not specified to the `Torrent.download()` function. It downloads file pieces in a pseudo-sequential manner. For instance, it will start fetching pieces in order, but **it may or may not yield the pieces in order**.

  - *Sequential*: This strategy is straight forward, and it **always yields pieces in a sequential manner**.
  
  > [!IMPORTANT]
  > The `stream()` coroutine always uses the SEQUENTIAL download strategy, and this behaviour cannot be changed.


```python
from aiotorrent import DownloadStrategy
from aiotorrent import Torrent

torrent = Torrent("path/to/file.torrent")
file = torrent.files[1]

# The download strategies available are: DownloadStrategy.DEFAULT and DownloadStrategy.SEQUENTIAL
await torrent.download(file, strategy=DownloadStrategy.SEQUENTIAL)
```

<br>

_The above methods can take additional parameters to customize the behaviour of this library. [Read the documentation]() to know more._

