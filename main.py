#!/usr/bin/python

import asyncio
import icecream

from torrent import Torrent


icecream.install()

async def main():
	print("*"*64)
	torrent = Torrent('utils/big-buck-bunny.torrent')

	torrent.contact_trackers()
	torrent.contact_peers()

	# asyncio.run(torrent.init(), debug=True)
	# asyncio.run(torrent.download(), debug=True)
	await torrent.init()
	await torrent.download()
	breakpoint()


asyncio.run(main())
print("*"*64)
