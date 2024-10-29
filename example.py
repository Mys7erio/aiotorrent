#!/usr/bin/python

import sys
import asyncio
import logging
from datetime import datetime as dt

from aiotorrent import Torrent
from aiotorrent import DownloadStrategy


formatted_date = dt.now().strftime("%Y-%m-%d_%H-%M-%S")
stream_handler = logging.StreamHandler()

# Uncomment line number 14 and 18 to save logs to file
# file_handler = logging.FileHandler(f"utils/logs/{formatted_date}.log")

logging.basicConfig(level=logging.INFO, handlers=[
	stream_handler,
	# file_handler,
])


async def main():
	print("*"*64)
	try:
		torrent_file = sys.argv[1]
	except:
		print("[x] No torrent file supplied")
		sys.exit(1)

	torrent = Torrent(torrent_file)
	sub, video, poster = torrent.files

	start = dt.now()
	print(f"Started Execution at: {start}")

	await torrent.init()
	for file in torrent.files:
		await torrent.download(file, strategy=DownloadStrategy.SEQUENTIAL)

	end = dt.now()
	elapsed = end - start
	print(f"Execution completed in: {elapsed}")


async def stream_test():
	torrent = Torrent(r'utils\big-buck-bunny.torrent')
	sub, video, poster = torrent.files
	await torrent.init()
	await torrent.stream(video)


if __name__ == "__main__":
	asyncio.run(main())

