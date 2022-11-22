import asyncio

from core.response_parser import PeerResponseParser as Parser
from core.response_handler import PeerResponseHandler as Handler
from core.message_generator import MessageGenerator as Generator


BLOCK_SIZE = 2 ** 14
BLOCKS_PER_CYCLE = 8


class Piece:
	def __init__(self, piece_num, piece_info, peers_manager):
		"""
		piece_num: int
			Zero based piece index to be fetched from peers

		piece_info: dict
			dictionary containing information regarding pieces

		peers_manager: PeersManager
			Object of PeersManager
		"""
		self.data = bytes()
		self.blocks = dict()
		self.piece_num = piece_num
		self.peers_manager = peers_manager

		self._is_last_piece = False
		self.total_blocks = piece_info['total_blocks']
		self.piece_size = self.total_blocks * BLOCK_SIZE

		# If piece_num matches the num of total pieces then it's the last piece.
		if piece_num == piece_info['total_pieces']:
			self._is_last_piece = True
			self.total_blocks, self._last_offset = divmod(piece_info['last_piece'], BLOCK_SIZE)
			self.piece_size = (self.total_blocks * BLOCK_SIZE) + self._last_offset


	def __repr__(self):
		return (f"Piece #{self.piece_num}")


	async def fetch_blocks(self, block_offsets, peer):
		"""
		This function fetches a block from a peer. It returns
		either an Block object or a None Object.
	
		block_offsets: list[int]
			Zero based block offsets which should be a multiple of
			BLOCK_SIZE. If there are 10 blocks in piece #0, block
			offset for block num 8 would be (8 * BLOCK_SIZE) = 131702
		"""
		requests = bytes()

		for offset in block_offsets:
			block_num = int(offset / BLOCK_SIZE)
			# print(f"Requesting Block #{self.piece_num}-{block_num} from {peer}")
			request_message = Generator.gen_request(self.piece_num, offset)

			# Last block of last piece will be requested with second last block.
			is_last_block = True if block_num == (self.total_blocks-1) else False

			if self._is_last_piece and is_last_block:
				request_message = Generator.gen_request(
					self.piece_num,
					offset,
					BLOCK_SIZE=(BLOCK_SIZE + self._last_offset)
				)

			requests += request_message

		response = await peer.send_message(requests, timeout=5)

		if not response:
			# If peer sends empty block, update the piece_info of peer
			# by setting it to false and raise IOError
			peer.update_piece_info(self.piece_num, False)
			raise IOError(f"{peer} Sent Empty Blocks")

		try:
			artifacts = Parser(response).parse()
			blocks = await Handler(artifacts, Peer=peer).handle()
			# [print(f"Got {block} from {peer}") for block in blocks]
			return blocks # Return here does not prevent execution of finally block
		except TypeError as E:
			print(f"Fetch Block: {E}")
			return None


	def is_piece_complete(self) -> bool:
		for block_num in range(self.total_blocks):
			if not block_num in self.blocks:
				return False
		return True


	def gen_offsets(self) -> set:
		blocks = set()
		total_blocks = self.total_blocks
		if self._is_last_piece: total_blocks += 1
		for block_num in range(self.total_blocks):
			if not block_num in self.blocks:
				block_offset = block_num * BLOCK_SIZE
				blocks.add(block_offset)
		return blocks


	async def download(self):
		peer = self.peers_manager.dispatch(self.piece_num)

		while not self.is_piece_complete():
			task_list = list()
			block_offsets = self.gen_offsets()

			# If len(block_offsets) is less than BLOCKS_PER_CYCLE, all blocks
			# can be downloaded in a single cycle.
			if len(block_offsets) >= BLOCKS_PER_CYCLE:
				offsets = {block_offsets.pop() for _ in range(BLOCKS_PER_CYCLE)}
				block_offsets.difference_update(offsets)
			else:
				offsets = self.gen_offsets()

			task_list.append(asyncio.create_task(self.fetch_blocks(offsets, peer)))

			try:
			# Execute all tasks in parallel
				results = await asyncio.gather(*task_list)

			# In case of empty block / broken pipe, get a new peer if available
			# or continuously wait for 1s untill a peer is available
			except (BrokenPipeError, IOError):
				while not self.peers_manager.peers_available(self.piece_num):
					await asyncio.sleep(1)
				else:
					self.peers_manager.retrieve(peer)
					peer = self.peers_manager.dispatch(self.piece_num)
					continue

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

		self.peers_manager.retrieve(peer)
		return self
