import queue
import asyncio

from core.response_parser import PeerResponseParser as Parser
from core.message_generator import MessageGenerator as Generator


BLOCK_SIZE = 2 ** 14


class Block:
	def __init__(self, piece_num, offset, data):
		self.piece_num = piece_num
		self.offset = offset
		self.data = data
		self.num = int(offset / BLOCK_SIZE)

		# Sometimes peers send previously unfinished responses (handshake/bitfield)
		if self.data: print(f"Got {self}")


	def __repr__(self):
		return (f"Block #{self.piece_num}-{self.num}")



class Piece:
	def __init__(self, piece_num, total_blocks, active_peers):
		self.data = bytes()
		self.blocks = dict()
		self.piece_num = piece_num
		self.active_peers = active_peers
		self.total_blocks = total_blocks
		

	def __repr__(self):
		return (f"Piece #{self.piece_num}")


	@staticmethod
	def gen_block_offsets(total_blocks):
		block_offsets = list()
		for piece_num in range(total_blocks):
			offset = piece_num * BLOCK_SIZE
			if not offset in self.blocks:
				block_offsets.append(block)
		return block_offsets


	async def get_block(self, piece_num, block_offset):
		index = self.piece_num
		offset = block_offset
		data = bytes()
		block_num = int(block_offset / BLOCK_SIZE)

		piece_info = {
			'index': index,
			'offset': offset,
			'block_len': BLOCK_SIZE
		}

		peer = await self.active_peers.get()
		print(f"Requesting {piece_num=} {block_num=} from {peer}")

		try:
			request_message = Generator.gen_request(piece_num, block_offset)
			response = await peer.send_message(request_message)
			if response:
				index, offset, data = Parser.parse_piece(response)
				if index > self.total_blocks: breakpoint()
		except TypeError:
			breakpoint()
		finally:
			block = Block(index, offset, data)
			await self.active_peers.put(peer)
			self.active_peers.task_done()

		return block


	async def get_piece(self):
		task_list = list()
		block_offsets = list()

		# Collect all block offsets in a set
		block_offsets = [(block_num * BLOCK_SIZE) for block_num in range(0, self.total_blocks)]
		while block_offsets:
			while not self.active_peers.empty() and block_offsets:
				offset = block_offsets.pop(0)
				task_list.append(
					asyncio.create_task(
						self.get_block(self.piece_num, offset)
					)
				)
			# Execute all tasks in parallel
			results = await asyncio.gather(*task_list)

			for block in results:
				# In case of empty or invalid block, add offset back to queue
				if not block.data: # or block.num > self.total_blocks:
					if not block.offset in block_offsets:
						block_offsets.append(block.offset)
				else:
					# In case of successful retrieval of block, add it to blocks
					self.blocks.update({block.num: block})
					if block.offset in block_offsets:
						block_offsets.remove(block.offset)

		breakpoint()
		# Concatenate all the block values
		for block_num in range(self.total_blocks):
			self.data += self.blocks[block_num].data

		return self.data