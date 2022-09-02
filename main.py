#!/usr/bin/python

import asyncio

from torrent import Torrent


async def main():
	print("*"*64)
	torrent = Torrent('utils/big-buck-bunny.torrent')
	sub, video, poster = torrent.files

	await torrent.init()
	await torrent.download(sub)
	await torrent.download(poster)
	await torrent.download(video)
	breakpoint()


asyncio.run(main())

