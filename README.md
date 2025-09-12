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

1. **Dependencies:** aiotorrent is built to be extremely lite-weight, only 3 dependencies required for the core functionality:
 - [`fastbencode`](https://pypi.org/project/fastbencode/)
 - [`bitstring`](https://pypi.org/project/bitstring/)

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
# You can either pass the file path or a file-like object. aiotorrent will handle it internally.
from aiotorrent import Torrent
torrent = Torrent('path/to/file.torrent')

# To initialise the torrent, you need to call the init() coroutine.
await torrent.init()
```


## Getting peers via DHT
While it is not a requirement, it is highly recommended to do use DHT (Distributed Hash Table) for peer discovery, which in turn can lead to better file retrieval speeds. To let aiotorrent perform peer discovery via DHT, you can pass the `dht_enabled=True` parameter to the `init()` coroutine, as follows:

```python
await torrent.init(dht_enabled=True)
```

> [!NOTE]
> The current implementation of DHT is hardcoded to fetch a minimum of 100 peers

> [!CAUTION]
In some cases this can prevent the torrent from initializing when there are not enough peers available. This behavior will be fixed in a future release.

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


### Getting the download progress

Each torrent file inside `Torrent.files` has the following functions to get useful statistics about the download progress:

1. `get_bytes_downloaded()`: Returns the total number of bytes downloaded so far for a particular file. This also includes the number of bytes which may not be written to disk (ie the piece validation failed, and the piece was discarded).

2. `get_bytes_written()`: Returns the number of bytes written to disk for a particular file.

3. `get_download_progress(precision=2)`: Returns the download progress in percentage for a particular file. The precision parameter specifies the number of decimal places to round off the result to

```python
file = torrent.files[0]

print(f"Total bytes downloaded: {file.get_bytes_downloaded()} bytes")
# Output: Total bytes downloaded: 1048576 bytes

print(f"Download progress: {file.get_bytes_written()} / {file.size} bytes")
# Output: Download progress: 1048576 / 5242880 bytes

print(f"Download progress: {file.get_download_progress(precision=3)}%")
# Output: Download progress: 20.152%
```

# aiotorrent CLI
Starting from versions 0.9.0, aiotorrent ships with a cli which can be directly invoked from the terminal, if PYTHONPATH is set correctly. The usage is fairly simple, and self explanatory:

```bash
$  aiotorrent
usage: aiotorrent [-h] [-v] {download,stream,info} ...

aiotorrent CLI for downloading and streaming torrents.

positional arguments:
  {download,stream,info}
                        Available commands
    download            Download torrent files
    stream              Stream files over HTTP
    info                Parse and show torrent metadata

options:
  -h, --help            show this help message and exit
  -v, --verbose         Show verbose output. Use -vv, -vvv, etc for increased verbosity
```

# Contribution Guidelines
This project is open to contributions. Feel free to open issues on bug reports or feature requests.

Please ensure that you open an issue before submitting a pull request. Also refrain from making pull requests directly to the main branch.

<br>

_The above methods can take additional parameters to customize the behaviour of this library. [Read the documentation]() to know more._

