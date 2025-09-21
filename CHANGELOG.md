# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).



## [0.9.2] - 2025-09-21

### Changed
- [FIX] Import error in HTTPTracker class caused by old bencode dependency
- [FIX] Trivial: Fixed wrong type annotation in `trackers.py` [issue #19]


## [0.9.1] - 2025-09-12

### Added

### Changed
- [FIX] Optimised peer fetching speeds via DHT
- [FIX] import error from bencoding module caused the program to crash 
- [FIX] Fixed installation failures on Python3.13 due to stale incompatible dependency [replaced [fast-bencode](https://github.com/synodriver/fast-bencode) with [fastbencode](https://github.com/breezy-team/fastbencode)]

### Minor Changes
- [FIX] Fixed type error in `downloader.py` in `FilesDownloadManager.file_downloaded` method

## [v0.9.0] - 2025-06-22

### Added
- Added support for peer discovery via DHT crawling
- Added aiotorrent cli script for torrent operations (get file info, download, and stream)

### Changed
- [CHANGED] Change the final package name from aiotorrent to python-aiotorrent

### Minor Changes
 - [FIX] Handle single torrent files correctly [`aiotorrent/core/file_utils.py`]
 - [FIX] Improperly handled logging statement which crashed the program is not handled correctly [`aiotorrent/core/response_handler.py`]


## [v0.8.3] - 2024-12-24

### Added
- Support for http and https trackers

### Changed
- [CHANGED] Change the final package name from aiotorrent to python-aiotorrent

### Minor Changes
 - [FIX] Handle single torrent files correctly [`aiotorrent/core/file_utils.py`]
 - [FIX] Improperly handled logging statement which crashed the program is not handled correctly [`aiotorrent/core/response_handler.py`]


> [!WARNING]
> **AI Generated Changelog Below**

## 05af089 - 2024-11-04
### Added
- Workflow file to auto-publish builds to PyPI


## 7cbb794 - 2024-10-29
### Changed
- Merge pull request #6 from Mys7erio/rolling
- Merge branch rolling to main


## 35ccb51 - 2024-10-27
### Added
- Convenience functions for:
    - Getting bytes written to a file
    - Getting bytes downloaded for a file
    - Wrapper function for displaying download progress in %


## 02e02c0 - 2024-07-26
### Changed
 - Improvements to the Torrent.download() coroutine
 - Minor changes to SequentialPieceDispatcher

## 6d2db3c - 2024-07-25
### Added
 - New downloading mechanism which downloads pieces in a strictly sequential manner

## f4f9d5a - 2024-01-01
### Added
 - Implemented feature for dynamic pipelining (dynamically increases/decreases blocks requested based on peer reliability)

## ab89b6f - 2023-12-30
### Minor Changes
 - [FIX] Fixed bug which did not put the piece back in queue after piece validation failed (downloader.py)
 - [FIX] Fixed bug where a while loop was running unnecessarily (piece.py)

## c146a03 - 2023-12-28
### Changed
 - Made procedure for getting peers from trackers asynchronous

## 62fffb4 - 2023-12-24
### Changed
 - Using logging module instead of print to facilitate logging
 - Minor refactors and code cleanup

## 0d6c4c3 - 2023-12-18
### Changed
 - Merge rolling into main - Using queues to download pieces parallelly

## fb07b64 - 2023-12-18
### Added
 - Implemented queues to download pieces parallelly in downloader.py

## 67b0425 - 2023-12-01
### Changed
 - Updated dependencies requirements and versions
 - Fixed errors in example.py file (#4)

## 2504bdc - 2023-12-01
### Changed
 - Updated dependency versions
 - Fixed example.py file

## 458a6a8 - 2023-12-01
### Changed
 - Updated pyproject.toml to reflect changes about latest dependencies
 - Fixed error in example.py

## b96145c - 2023-11-30
### Changed
 - Merge pull request #3 from Mys7erio/rolling
 - Changed library used for parsing bencoded data

## cc6a07d - 2023-11-30
### Changed
 - Changed library used for parsing bencoded data (fast-bencode instead of modern-bencode)
 - Updated the README to reflect these changes
 - Modified the example file to be more user friendly

## d858f36 - 2023-01-20
### Added
 - Create LICENSE

## 0b064d7 - 2023-01-12
### Changed
 - Updated README

### 28ac31a - 2023-01-07
## Added
 - Readme.md

## Changed
 - Modified torrent class

## 116ab35 - 2023-01-05
### Changed
 - aiotorrent now raises a ModuleNotFoundError when streaming dependencies are not installed

## 8e0bb1f - 2023-01-04
### Changed
 - Added poetry.lock file to .gitignore

## 5cc5685 - 2023-01-04
### Changed
 - Modified pyproject.toml

## bf0a5ba - 2023-01-02
### Changed
 - Made Changes To Convert This Repo Into A Library
 - Renamed main.py to example.py
 - Renamed torrent.py to aiotorrent.py
 - Removed requirements-dev.txt
 - Used poetry to create scaffolding for the package
 - Moved all files to ./aiotorrent/
 - Files README.md, pyproject.toml, aiotorrent/init.py, tests/init.py added by poetry.
 - Changed example.py to use absolute path instead of relative part.
 - Changed All Relative Imports To Absolute Imports

## a5b38fc - 2022-12-31
### Changed
 - Merge pull request #2 from Mys7erio/rolling
 - Enabled Support For Streaming Files Over HTTP

## 62ab3eb - 2022-12-31
### Added
 - Enabled Support For Streaming Files Over HTTP

### Changed
 - Bug which caused loss of peers has been fixed (See piece.py for changes).
 - Minor changes & corrections.

## 06a1ecd - 2022-12-27
### Added
 - Added the stream function in torrent class which is a wip.

### Changed
 - Made Changes To Peer Dispatch And Retrieval Mechanism (Optimised download speeds)
 - Peers are now stored in an async queue in PeersManager.
 - Rewrote the PeersManager class to adapt to the above mentioned change.
 - Made necessary changes in Piece.download() to adapt to the above mentioned changes
 - Fixed bug in PeerResponseParser. Earlier it did not parse Keep-Alive messages.
 - Added init_downloader() and file_downloaded() functions to FilesDownloadManager.
 - Added type annotations to piece.py file.
 - Minor changes in syntax.

## ad4ef12 - 2022-11-22
### Changed
 - Optimised Piece Downloading Mechanism (Utilises all available peers with the next piece)
 - Removed the busy attribute from Peer class.
 - Tweaked peer selection and dispatching to adjust to the above changes in PeersManager.
 - Added peers_available function to PeersManager.
 - Disabled / Commented out blacklist and hailmary functions in PeersManager.
 - Added update_piece_info function to update which pieces a particular peer has.
 - If a peer is not available for a piece, the Piece.download() task will sleep for 1s.
 - Main now shows elapsed time.

## f3a9e5c - 2022-09-08
### Changed
 - Removed redundant statement in downloader.py

## 22460ad - 2022-09-02
### Changed
 - Merge branch 'main' into rolling

## 11307b1 - 2022-09-02
### Added
 - New PieceWriter class

### Changed
 - Made Changes To Allow For Streaming Of Files
 - FilesDownloadManager now yields pieces instead of directly saving to disk
 - Deleted block.py and peers_manager.py
 - Shifted Block and PieceWriter classes to core/util.py and PeersManger to peer.py
 - Removed unused imports

## d922954 - 2022-08-31
### Added
 - PieceWriter class

### Changed
 - Made changes to Piece downloading and piece writing logic
 - FilesDownloadManager now yields pieces instead of directly saving to disk
 - Shifted Block and PieceWriter classes to core/util.py
 - Removed unused imports

## 5b5dcfb - 2022-08-29
### Changed
 - Optimised The Execution Speed Of The Application (Pipelining multiple blocks)
 - Added PeersManager class
 - Added parameter to specify timeouts in Peer.send_message()
 - Peers now raise BrokenPipeError if peer is not active and send_message() is called
 - Piece class now returns self instead of self.data
 - IOError is now raised in Piece class if a peer sends an empty block
 - Response_handler now returns Block instead of a tuple
 - Removed icecream as a dependancy and ic() calls have been replaced with print statements
 - The FileTree object now inherits from list making it functional as an iterator as well as making it subscriptable
 - The files will now get downloaded in a directory with the same name as the torrent name
 - The FilesDownloadManager().save_to_disk() function now takes a Piece and File object instead of bytes() and str()

## d2a8517 - 2022-08-27
### Changed
 - The application now downloads multiple pieces simultaneously
 - Added PeersManager class
 - Fixed bug (again) which prevented the last piece of the torrent from being downloaded
 - Peers now raise BrokenPipeError if peer is not active and send_message() is called
 - IOError is now raised in Piece class if a peer sends an empty block
 - Modified Piece.gen_offsets() to adjust to changes mentioned in ^ 2nd point
 - "If-else" is now being used instead of exception handling to check for empty set while downloading blocks in a piece
 - Piece class now returns self instead of self.data
 - Added piece_size attribute to Piece class
 - Renamed Piece.fetch_block() to Piece.fetch_blocks()

## 88faba2 - 2022-08-07
### Added
 - Ability to request multiple blocks at once from peers

### Changed
 - Added parameter to specify timeouts in Peer.send_message()
 - Adapted response_handler and response_parser to adapt to the above change
 - Renamed get_block() to fetch_block() and get_piece() to download() in piece.py

## d82d2c9 - 2022-07-28
### Changed
 - Fixed hard-coded value of last block in piece.py
 - Shifted Block class to core/block.py
 - response_handler now returns Block instead of a tuple
 - removed import of struct module in peer.py

## 5af517f - 2022-07-27
### Changed
 - Response parser now does not clutter screen (prints only first 16 bytes of response for unknown message id)

## 3f2b0eb - 2022-07-27
### Changed
 - Removed ic() calls which were not removed in the previous commit

## 757a718 - 2022-07-27
### Changed
 - Removed icecream as a dependancy
 - Replaced all ic() calls with print statements
 - Minimized number of print statements while downloading pieces
 - Removed PieceError from util.py file since it was not being used

## b4d42a0 - 2022-07-27
### Changed
 - Fixed bug which paused the execution of the whole program if the response parser encountered an unknown message id
 - The FileTree object now inherits from list making it functional as an iterator as well as making it subscriptable
 - The files will now get downloaded in a directory with the same name as the torrent name
 - The FilesDownloadManager().save_to_disk() function now takes a Piece and File object instead of bytes() and str()
 - Minor changes in FileTree, Torrent classes and main.py to fix the errors caused by changes made to FileTree class

## d7959e6 - 2022-07-26
## Changed
 - Fixed bug which stopped the last piece from being downloaded
 - Fixed bug which crashed the program if a "single-file" torrent was provided
 - The contact_peers() function has been renamed to get_peers()
 - The _contact_trackers() and _get_peers() function get called implicitly in Torrent.init()

## 6798933 - 2022-07-25
### Added
 - New file core.file_utils with FileTree and File classes

### Changed
 - Renamed piece_manager to downloader
 - The piece_manager file has been renamed to downloader
 - The PieceManager class has been renamed to FilesDownloadManager
 - Minor changes in the Torrent API
 - Torrent objects will now contain a FileTree object
 - The download function of the Torrent class now takes a File object


## 1a90b0f - 2022-07-23
### Changed
 - Major changes to response parsing and response handling logic (Can now fetch and validate pieces)

## e3aca2d - 2022-07-18
### Added
 - First commit with files (partially working work-in-progress)

## dc393e1 - 2022-07-18
### Added
 - Initial commit

