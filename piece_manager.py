import asyncio
import hashlib

from piece import Piece
from core.response_parser import PeerResponseParser as Parser
from core.message_generator import MessageGenerator as Generator


BLOCK_SIZE = 2 ** 14

class PieceManager:
	def __init__(self, torrent_size, piece_size, piece_hashmap, active_peers):
		self.piece_hashmap = piece_hashmap
		self.piece_size = piece_size

		# divmod returns a tuple which is the quotient and remainder
		self.total_pieces, self.last_piece = divmod(torrent_size, piece_size)
		self.total_blocks, self.last_block = divmod(piece_size, BLOCK_SIZE)
		
		# increment total number of pieces if last piece exists
		if self.last_piece: self.total_pieces += 1
		if self.last_block: self.total_blocks += 1

		self.active_peers = asyncio.Queue()
		[self.active_peers.put_nowait(peer) for peer in active_peers]

	async def get_all_pieces(self):
		piece1 = await Piece(0, self.total_blocks, self.active_peers).get_piece()
		piece_hash = hashlib.sha1(piece1).digest()
		breakpoint()
		if piece_hash == self.piece_hashmap[0]:
			self.write_piece_to_disk(piece, 'testfile')
			print(f"Wrote piece 0 to disk")
		else:
			print(f"Piece Hash Does Not Match")



	def write_piece_to_disk(self, piece, filename):
		with open(filename, 'ab') as file:
			file.write(piece)


