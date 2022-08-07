import asyncio

from core.block import Block
from core.response_parser import PeerResponseParser as Parser
from core.response_handler import PeerResponseHandler as Handler
from core.message_generator import MessageGenerator as Generator


BLOCK_SIZE = 2 ** 14
BLOCKS_PER_PEER = 8


class Piece:
	def __init__(self, piece_num, piece_info, active_peers):
		"""
		piece_num: int
			Zero based piece index to be fetched from peers

		total_blocks: int
			total number of blocks in a single piece

		active_peers: asyncio.Queue
			Peers which are active and have completed handshake
		"""
		self.data = bytes()
		self.blocks = dict()
		# self.block_offsets = set()
		self.piece_num = piece_num
		self.active_peers = active_peers

		self._is_last_piece = False
		# self._last_offset = 0
		self.total_blocks = piece_info['total_blocks']

		# If piece_num matches the num of total pieces then it's the last piece.
		if piece_num == piece_info['total_pieces']:
			self._is_last_piece = True
			self.total_blocks, self._last_offset = divmod(piece_info['last_piece'], BLOCK_SIZE)
			# Since last block of last piece will have to be requested with
			# second last block of last piece.
			self.total_blocks -= 1


	def __repr__(self):
		return (f"Piece #{self.piece_num}")



	async def fetch_block(self, block_offsets: list):
		"""
		This function fetches a block from a peer. It returns
		either an Block object or a None Object.
	
		block_offset: int
			Zero based block offset which should be a multiple of
			BLOCK_SIZE. If there are 10 blocks in piece #0, block
			offset for block num 8 would be (8 * BLOCK_SIZE) = 131702
		"""
		requests = bytes()
		Peer = await self.active_peers.get()

		for offset in block_offsets:
			block_num = int(offset / BLOCK_SIZE)
			print(f"Requesting Block #{self.piece_num}-{block_num} from {Peer}")
			request_message = Generator.gen_request(self.piece_num, offset)

			# Last block of last piece will be requested with second last block.
			if self._is_last_piece and block_num == self.total_blocks:
				request_message = Generator.gen_request(
					self.piece_num,
					block_offset,
					BLOCK_SIZE=(BLOCK_SIZE + self._last_offset)
				)
			requests += request_message

		response = await Peer.send_message(requests, timeout=5)
		if not response: return None

		try:
			artifacts = Parser(response).parse()
			blocks = await Handler(artifacts, Peer=Peer).handle()
			[print(f"Got {block} from {Peer}") for block in blocks]
			return blocks # Return here does not prevent execution of finally block
		except TypeError as E:
			print(f"Fetch Block: {E}")
			return None
		finally:
			await self.active_peers.put(Peer)
			self.active_peers.task_done()


	def is_piece_complete(self) -> bool:
		for block_num in range(self.total_blocks):
			if not block_num in self.blocks:
				return False
		return True


	def gen_offsets(self) -> set:
		blocks = set()
		for block_num in range(self.total_blocks):
			if not block_num in self.blocks:
				block_offset = block_num * BLOCK_SIZE
				blocks.add(block_offset)
		return blocks


	async def download(self):
		task_list = list()
		# EMPTY_BLOCK_THRESHOLD = 3

		while not self.is_piece_complete():
			block_offsets = self.gen_offsets()
			for _ in range(self.active_peers.qsize()):
				try:
					offsets = {block_offsets.pop() for _ in range(BLOCKS_PER_PEER)}
					block_offsets.difference_update(offsets)
				except KeyError:
					# Blocks to be downloaded is less than BLOCKS_PER_PEER
					# A single peer can download all blocks now
					offsets = self.gen_offsets()
				finally:
					task_list.append(asyncio.create_task(self.fetch_block(offsets)))

			# Execute all tasks in parallel
			results = await asyncio.gather(*task_list)

			# Remove NoneType objects and merge inner lists to outerlists
			results = [result for result in results if result]
			results = sum(results, [])

			# In case of successful retrieval of block, add block to self.blocks
			for block in results:
				if block.data:
					self.blocks.update({block.num: block})

		# Concatenate all the block values
		for block_num in range(self.total_blocks):
			self.data += self.blocks[block_num].data
