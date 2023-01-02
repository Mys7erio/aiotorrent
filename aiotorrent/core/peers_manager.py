import asyncio


class PeersManager:
	def __init__(self, peer_list):
		self.peers = asyncio.Queue()
		[self.peers.put_nowait(peer) for peer in peer_list]


	def peers_avail(self) -> bool:
		'''Checks if peer queue is not empty'''
		return not self.peers.empty()


	def pool_size(self) -> int:
		return self.peers.qsize()


	async def dispatch(self):
		peer = await self.peers.get()
		return peer


	async def retrieve(self, peer):
		self.peers.task_done()
		await self.peers.put(peer)

