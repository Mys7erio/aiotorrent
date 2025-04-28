import asyncio
import argparse
import logging

from aiotorrent.aiotorrent import Torrent

"""
    aiotorrent download <path/to/file.torrent> <save_location<optional>>
    aiotorrent stream <path/to/file.torrent>
"""

LOG_LEVELS = {
    0: logging.NOTSET,
    1: logging.CRITICAL,
    2: logging.ERROR,
    3: logging.WARN,
    4: logging.INFO,
    5: logging.DEBUG,
}


async def download_torrent(torrent_file_loc, save_loc=None):
    # TODO: Add parameter for save location
    # TODO: Add parameter for download strategy
    torrent = Torrent(torrent_file_loc)
    await torrent.init(dht_enabled = True)
    for file in torrent.files:
        await torrent.download(file)


async def stream_torrent(torrent_file_loc, host="127.0.0.0", port=8080):
    torrent = Torrent(torrent_file_loc)
    await torrent.init(dht_enabled = True)
    for file in torrent.files:
        await torrent.stream(file, host=host, port=port)


def print_torrent_info(torrent_file_loc, format="json", verbose=False):
    torrent = Torrent(torrent_file_loc)
    info = torrent.get_torrent_info(format=format, verbose=verbose)
    print(info)



# ================================ Create parsers here ================================
def create_download_parser(subparsers):
    download_parser = subparsers.add_parser(
        "download",
        help="Download torrent files"
    )
    download_parser.add_argument(
        "torrent_path",
        help="Path to the .torrent file"
    )
    download_parser.add_argument(
        "save_location",
        nargs="?", # This makes the argument optional (0 or 1 argument)
        default=".", 
        help="(Optional) Save downloaded files to location (defaults to current directory)"
    )
    
    return download_parser

def create_stream_parser(subparsers):
    stream_parser = subparsers.add_parser(
        "stream",
        help="Stream files over HTTP"
    )
    stream_parser.add_argument(
        "torrent_path",
        help="Path to the .torrent file"
    )
    # Add opional arguments for host and port
    stream_parser.add_argument(
        "--host",
        "-H", # Short form
        default="localhost", # Default value if not provided
        help="Host address for streaming (defaults to localhost)"
    )
    stream_parser.add_argument(
        "--port",
        "-p", # Short form
        type=int,
        default=8080, # Default value if not provided
        help="Port for streaming (defaults to 8080)"
    )

    return stream_parser


def create_info_parser(subparsers):
    info_parser = subparsers.add_parser(
        "info",
        help="Parse and show torrent metadata"
    )
    info_parser.add_argument(
        "torrent_path",
        help="Path to the .torrent file"
    )
    info_parser.add_argument(
        "--format",
        "-f",
        default="json",
        help="Format to print the torrent metadata. Defaults to json"
    )

    return info_parser


# ================================ Main parser ================================
async def main_parser():
    """Sets up and parses the arguments, then calls the appropriate function."""
    parser = argparse.ArgumentParser(
        description="aiotorrent CLI for downloading and streaming torrents."
    )
    # Add the verbosity argument here
    parser.add_argument(
        '-v', '--verbose',
        action='count',
        default=0,  # Default verbosity is 0 if no -v is given
        help='Show verbose output. Use -vv, -vvv, etc for increased verbosity'
    )

    # Create subparsers for the different commands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands"
    )

    download_parser = create_download_parser(subparsers)
    stream_parser = create_stream_parser(subparsers)
    info_parser = create_info_parser(subparsers)

    download_parser.set_defaults(func=download_torrent)
    stream_parser.set_defaults(func=stream_torrent)
    info_parser.set_defaults(func=print_torrent_info)
    args = parser.parse_args()

    # Check if verbosity flag is set, if not it is set to 0
    # If set, ensure the verbosity doesn't exceed level 5 (DEBUG)
    verbosity = min(5, args.verbose) if args.verbose else 0
    log_level = LOG_LEVELS[verbosity]

    logging.basicConfig(level=log_level, handlers=[
        logging.StreamHandler(),
    ])


    if hasattr(args, 'func'):
        if args.command == 'download':
            await args.func(args.torrent_path, args.save_location)
        elif args.command == 'stream':
            await args.func(args.torrent_path, args.host, args.port)
        elif args.command == 'info':
            args.func(args.torrent_path, args.format, args.verbose)
    else:
        parser.print_help()


def main():
    asyncio.run(main_parser())


if __name__ == "__main__":
    main()