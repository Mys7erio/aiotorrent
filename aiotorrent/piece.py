import asyncio
import hashlib
import logging

from aiotorrent.core.util import Block
from aiotorrent.core.response_parser import PeerResponseParser as Parser
from aiotorrent.core.response_handler import PeerResponseHandler as Handler
from aiotorrent.core.message_generator import MessageGenerator as Generator

from aiotorrent.core.util import BLOCK_SIZE, BLOCKS_PER_CYCLE, MIN_BLOCKS_PER_CYCLE


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

#TODO: Update class paramater documentation
#TODO: Rename peers_man to peer_queue
#TODO: Use consistent naming convention for other variables
class Piece:
	def __init__(self, num: int, priority: int, piece_info: dict[str, int]):
		"""
		num: int
			Zero based piece index to be fetched from peers

		piece_info: dict
			dictionary containing information regarding pieces

		peers_man: PeersManager
			Object of PeersManager
		"""
		self.data = bytes()
		self.blocks = dict()
		self.num = num
		self.priority = priority

		self._is_last_piece = False
		self.total_blocks = piece_info['total_blocks']
		self.piece_size = self.total_blocks * BLOCK_SIZE

		# If num matches the num of total pieces then it's the last piece.
		if self.num == piece_info['total_pieces']:
			self._is_last_piece = True
			self.total_blocks, self._last_offset = divmod(piece_info['last_piece'], BLOCK_SIZE)
			self.piece_size = (self.total_blocks * BLOCK_SIZE) + self._last_offset


	def __repr__(self):
		return (f"Piece #{self.num}")


	async def fetch_blocks(self, block_offsets: list[int], peer) -> list[Block]:
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
			logger.debug(f"Requesting Block #{self.num}-{block_num} from {peer}")
			request_message = Generator.gen_request(self.num, offset)

			# Last block of last piece will be requested with second last block.
			is_last_block = True if block_num == (self.total_blocks - 1) else False

			if self._is_last_piece and is_last_block:
				request_message = Generator.gen_request(self.num, offset, BLOCK_SIZE + self._last_offset)

			requests += request_message

		response = await peer.send_message(requests, timeout=5)

		# If peer sends empty block, update the piece_info of peer
		# by setting it to false and raise IOError
		if not response:
			peer.update_piece_info(self.num, False)
			raise IOError(f"{peer} Sent Empty Blocks")

		try:
			artifacts = Parser(response).parse()
			blocks = await Handler(artifacts, Peer=peer).handle()
			for block in blocks:
				logger.debug(f"Got {block} from {peer}")

			return blocks
		
		except TypeError as E:
			logging.info(f"Requesting Blocks for {self} from {peer} Returned None")
			logging.warning(E)
			self.adjust_blocks_per_cycle(-1)
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


	@staticmethod
	def is_valid(piece, piece_hashmap):
		#TODO: make this an instance method so that every piece can validate it's own data
		piece_hash = hashlib.sha1(piece.data).digest()

		if piece_hash != piece_hashmap[piece.num]:
			logging.warning(f"Piece Hash Does Not Match for {piece}")
			return False
			
		return True


	def adjust_blocks_per_cycle(self, value: int = 1):
		"""
		Increments / Decrements BLOCKS_PER_CYCLE by `value`
		"""
		global BLOCKS_PER_CYCLE
		BLOCKS_PER_CYCLE += value

		# Ensure BLOCKS_PER_CYCLE is always greater than MIN_BLOCKS_PER_CYCLE
		BLOCKS_PER_CYCLE = max(BLOCKS_PER_CYCLE, MIN_BLOCKS_PER_CYCLE)

		# Ensure BLOCKS_PER_CYCLE is always less than total_blocks in a piece
		BLOCKS_PER_CYCLE = min(BLOCKS_PER_CYCLE, self.total_blocks)


	async def download(self, peers_man, _semaphore = None) -> 'Piece':
		priority, peer = await peers_man.get()

		while not self.is_piece_complete():
			task_list = list()
			block_offsets = self.gen_offsets()

			# If number of block offsets to be downloaded is less than BLOCKS_PER_CYCLE,
			# all blocks can be downloaded in a single cycle.
			if len(block_offsets) >= BLOCKS_PER_CYCLE:
				offsets = {block_offsets.pop() for _ in range(BLOCKS_PER_CYCLE)}
				block_offsets.difference_update(offsets)
			else:
				offsets = self.gen_offsets()

			blocks = self.fetch_blocks(offsets, peer)
			task = asyncio.create_task(blocks)
			task_list.append(task)

			try:
				# Get results and increment BLOCKS_PER_CYCLE if successful
				results = await asyncio.gather(*task_list)
				self.adjust_blocks_per_cycle(1)

			except (BrokenPipeError, IOError):
				# If BrokenPipe or IOError recieved then we need to reduce the peers priority
				current_priority, current_peer = priority, peer
				priority, peer = await peers_man.get()
				await peers_man.put((current_priority + 1, current_peer))
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

		await peers_man.put((priority - 1, peer))
		# Release semaphore so that the next task can begin
		if _semaphore is not None:
			_semaphore.release()
		return self
