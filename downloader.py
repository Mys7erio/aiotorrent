import asyncio
import hashlib
from pathlib import Path

from piece import Piece
from core.file_utils import File, FileTree
from core.peers_manager import PeersManager


BLOCK_SIZE = 2 ** 14
# PIECES_PER_CYCLE = 5


class FilesDownloadManager:
	def __init__(self, torrent_info: dict, active_peers: list):
		# Extract torrent size and piece size values from torrent info
		piece_size = torrent_info['piece_len']
		torrent_size = torrent_info['size']

		# Create a directory with the same name as torrent name to download files to
		self.directory = torrent_info['name']
		Path(self.directory).mkdir(exist_ok=True)

		# divmod returns a tuple which is the quotient and remainder
		total_pieces, last_piece = divmod(torrent_size, piece_size)
		total_blocks, last_block = divmod(piece_size, BLOCK_SIZE)
		
		# Increment total number of pieces if last piece exists
		if last_piece: total_pieces += 1
		if last_block: total_blocks += 1

		# Since we're taking into account zero based piece index
		total_pieces -= 1

		piece_info = {
			'total_pieces': total_pieces,
			'total_blocks': total_blocks,
			'last_piece': last_piece,
			'last_block': last_block
		}

		self.piece_info = piece_info
		self.piece_hashmap = torrent_info['piece_hashmap']
		self.file_tree = FileTree(torrent_info)

		[print(f"{key}:{val}") for key, val in piece_info.items()]
		self.active_peers = active_peers


	async def get_file(self, file: File):
		piece_nums = [piece_num for piece_num in range(file.start_piece, file.end_piece + 1)]
		peers_manager = PeersManager(self.active_peers)

		while piece_nums:
			task_list = list()
			
			# for _ in range(PIECES_PER_CYCLE):
			while piece_nums and peers_manager.peers_available(piece_nums[0]):
				# if not piece_nums:
				# 	break
				piece_num = piece_nums.pop(0)
				piece = Piece(piece_num, self.piece_info, peers_manager)
				task_list.append(asyncio.create_task(piece.download()))

			pieces = await asyncio.gather(*task_list)

			# For every piece, if piece hash does not match, prepend piece num back to piece_nums.
			for piece in pieces:
				piece_hash = hashlib.sha1(piece.data).digest()

				if piece_hash != self.piece_hashmap[piece.piece_num]:
					print(f"Piece Hash Does Not Match for {piece}")
					piece_nums.insert(0, piece_num)
					# continue
					# Discard all pieces in the list if piece hash does not match
					# TODO: Find a better approach to handle piece hash mismatch
					break

				if file.start_piece == piece.piece_num:
					piece.data = piece.data[file.start_byte:]

				if file.end_piece == piece.piece_num:
					piece.data = piece.data[:file.end_byte]

				yield piece
		print(f"File {file} downloaded")


