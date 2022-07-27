import asyncio
import hashlib
from pathlib import Path

from piece import Piece
from core.file_utils import FileTree, File
from core.response_parser import PeerResponseParser as Parser
from core.message_generator import MessageGenerator as Generator


BLOCK_SIZE = 2 ** 14

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

		ic(self.piece_info)
		self.active_peers = asyncio.Queue()
		[self.active_peers.put_nowait(peer) for peer in active_peers]


	# async def get_all_pieces(self):
	# 	filename = f"file-{int(time())}.data"
	# 	filepath = f"utils/temp/{filename}"

	# 	piece_nums = {piece_num for piece_num in range(30, 100)}
	# 	while piece_nums:
	# 		piece_num = piece_nums.pop()
	# 		piece = Piece(piece_num, self.piece_info, self.active_peers)
	# 		await piece.get_piece()
	# 		piece_hash = hashlib.sha1(piece.data).digest()

	# 		if piece_hash == self.piece_hashmap[piece_num]:
	# 			self.write_piece_to_disk(piece.data, filepath)
	# 			print(f"Wrote {piece} to file {filepath}")
	# 		else:
	# 			print(f"Piece Hash Does Not Match for {piece}")
	# 			piece_nums.add(piece_num)


	async def get_file(self, file: File):
		piece_nums = [piece_num for piece_num in range(file.start_piece, file.end_piece + 1)]

		while piece_nums:
			piece_num = piece_nums.pop(0)
			piece = Piece(piece_num, self.piece_info, self.active_peers)
			await piece.get_piece()
			piece_hash = hashlib.sha1(piece.data).digest()

			# If piece hash does not match, prepend piece num back to piece_nums.
			# Python doesn't have a prepend function, improvised with the insert func.
			if piece_hash != self.piece_hashmap[piece_num]:
				print(f"Piece Hash Does Not Match for {piece}")
				piece_nums.insert(0, piece_num)
				continue

			if file.start_piece == piece_num:
				piece.data = piece.data[file.start_byte:]

			if file.end_piece == piece_num:
				piece.data = piece.data[:file.end_byte]

			self.write_piece_to_disk(piece, file)
		print(f"File {file} downloaded")


	def write_piece_to_disk(self, piece: Piece, file: File):
		# Filepath is file name prepended by directory name
		filepath = f"{self.directory}/{file.name}"

		with open(filepath, 'ab') as file:
			file.write(piece.data)

		print(f"Wrote {piece} to {file.name}")


