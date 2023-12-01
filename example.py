#!/usr/bin/python

import sys
import asyncio
from datetime import datetime as dt

from aiotorrent.aiotorrent import Torrent


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
	await torrent.download(sub)
	await torrent.download(poster)
	await torrent.download(video)

	end = dt.now()
	elapsed = end - start
	print(f"Execution completed in: {elapsed}")
	breakpoint()


async def stream_test():
	torrent = Torrent(r'aiotorrent\utils\big-buck-bunny.torrent')
	sub, video, poster = torrent.files
	await torrent.init()
	await torrent.stream(video)


if __name__ == "__main__":
	asyncio.run(main())

