#!/usr/bin/python

import asyncio
import icecream

from torrent import Torrent


icecream.install()

async def main():
	print("*"*64)
	torrent = Torrent('utils/big-buck-bunny.torrent')
	await torrent.init()

	for file in torrent.files:
		await torrent.download(file)


asyncio.run(main())
print("*"*64)
