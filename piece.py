import asyncio

from core.response_parser import PeerResponseParser as Parser
from core.response_handler import PeerResponseHandler as Handler
from core.message_generator import MessageGenerator as Generator


BLOCK_SIZE = 2 ** 14


class Block:
	def __init__(self, piece_num, offset, data):
		self.piece_num = piece_num
		self.offset = offset
		self.data = data
		self.num = int(offset / BLOCK_SIZE)


	def __repr__(self):
		return (f"Block #{self.piece_num}-{self.num}")



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
		self.block_offsets = set()
		self.piece_num = piece_num
		self.active_peers = active_peers

		self._is_last_piece = False
		self._last_offset = 0
		self.total_blocks = piece_info['total_blocks']

		# If piece_num matches the num of total pieces then it's the last piece.
		if piece_num == piece_info['total_pieces']:
			self._is_last_piece = True
			self.total_blocks, self._last_offset = divmod(piece_info['last_piece'], BLOCK_SIZE)

		# Add block offsets to block_offsets set
		for block_num in range(self.total_blocks):
			self.block_offsets.add(
				(block_num * BLOCK_SIZE)
			)


	def __repr__(self):
		return (f"Piece #{self.piece_num}")



	async def get_block(self, block_offset):
		"""
		This function fetches a block from a peer. It returns
		either an Block object or a None Object.
	
		block_offset: int
			Zero based block offset which should be a multiple of
			BLOCK_SIZE. If there are 10 blocks in piece #0, block
			offset for block num 8 would be (8 * BLOCK_SIZE) = 131702
		"""
		piece_num = self.piece_num
		block_num = int(block_offset / BLOCK_SIZE)
		Peer = await self.active_peers.get()

		request_message = Generator.gen_request(self.piece_num, block_offset)

		if self._is_last_piece and block_num == 7:
			request_message = Generator.gen_request(
				self.piece_num,
				block_offset,
				BLOCK_SIZE=(BLOCK_SIZE + self._last_offset)
			)

		response = await Peer.send_message(request_message)
		
		# If empty response, add block_offset back to unavailable blocks
		if not response:
			self.block_offsets.add(block_offset)
			return None

		try:
			artifacts = Parser(response).parse()
			response = await Handler(artifacts, Peer=Peer).handle()
			index, offset, data = response
			block = Block(index, offset, data)
			return block # Return here does not prevent execution of finally block
		except TypeError as E:
			self.block_offsets.add(block_offset)
			return None
		finally:
			await self.active_peers.put(Peer)
			self.active_peers.task_done()


	async def get_piece(self):
		task_list = list()
		while self.block_offsets:
			while not self.active_peers.empty() and self.block_offsets:
				offset = self.block_offsets.pop()
				task_list.append(
					asyncio.create_task(
						self.get_block(offset)
					)
				)
			# Execute all tasks in parallel
			results = await asyncio.gather(*task_list)

			# Remove NoneType objects from the list
			results = [result for result in results if result]

			for block in results:
				# In case of successful retrieval of block, add block to
				# self.blocks and remove block_offset from self.block_offsets
				if block.data:
					self.blocks.update({block.num: block})
					self.block_offsets.discard(block.offset)

		# Concatenate all the block values
		for block_num in range(self.total_blocks):
			self.data += self.blocks[block_num].data