#!/usr/bin/python

import asyncio
from datetime import datetime as dt

from torrent import Torrent


async def main():
	print("*"*64)
	torrent = Torrent('utils/big-buck-bunny.torrent')
	sub, video, poster = torrent.files

	start = dt.now()
	print(f"Started Execution at: {start}")

	await torrent.init()
	await torrent.download(sub)
	await torrent.download(video)
	await torrent.download(poster)

	end = dt.now()
	elapsed = end - start
	print(f"Execution completed in: {elapsed}")
	breakpoint()


async def stream_test():
	torrent = Torrent('utils/big-buck-bunny.torrent')
	sub, video, poster = torrent.files
	await torrent.init()
	await torrent.stream(video)


asyncio.run(main())

