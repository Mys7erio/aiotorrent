# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added CHANGELOG.md
- Added file `aiotorrent/core/cli.py`
- Added aiotorrent script to `pyproject.toml`
- Added function `_get_peers_dht()` to `Torrent` class
- Added function `get_torrent_info()` to `Torrent` class
- Added class `SimpleDHTCrawler` at `aiotorrent/DHTv4.py`


### Changed

- [FIX] Trackers are now marked as active when a successful connection is made
- [CHANGED] Added new parameter `dht_enabled` to `Torrent.init()` function



### Minor Changes
 - The logger now does not log the names of files inside the torrent (aiotorrent/aiotorrent.py)
