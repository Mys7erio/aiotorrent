#!/usr/bin/python

import asyncio

from torrent import Torrent


async def main():
	print("*"*64)
	torrent = Torrent('utils/big-buck-bunny.torrent')
	await torrent.init()

	for file in torrent.files:
		await torrent.download(file)


asyncio.run(main())
print("*"*64)
