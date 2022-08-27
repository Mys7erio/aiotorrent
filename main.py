#!/usr/bin/python

import asyncio

from torrent import Torrent


async def main():
	print("*"*64)
	torrent = Torrent('utils/big-buck-bunny.torrent')
	await torrent.init()

	await torrent.download(torrent.files[1])


asyncio.run(main())
print("*"*64)
