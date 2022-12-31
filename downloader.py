import asyncio
import hashlib
from pathlib import Path

from piece import Piece
from core.file_utils import File, FileTree
from core.peers_manager import PeersManager


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
		self.peers_man = PeersManager(active_peers)

		[print(f"{key}:{val}") for key, val in piece_info.items()]

		# Will be populated when get_file() is called
		self.download_list = []


	def init_downloader(self, file: File) -> None:
		self.download_list = [piece_num for piece_num in range(file.start_piece, file.end_piece + 1)]


	def file_downloaded(self) -> None:
		'''
		Returns true if all the pieces have been downloaded, false otherwise
		'''
		return False if self.download_list else True


	async def get_file(self, file: File) -> Piece:
		self.init_downloader(file)
		task_list = list()

		while True:
			# Break loop if file downloaded
			if self.file_downloaded(): break

			batch_size = min(self.peers_man.pool_size(), len(self.download_list))
			# print(f"Using Batch Size Of: {batch_size}")

			for _ in range(batch_size):
				# Have to call this twice :/
				if not self.file_downloaded():
					piece_num = self.download_list.pop(0)
					piece = Piece(piece_num, self.piece_info, self.peers_man)
					task = asyncio.create_task(piece.download())
					task_list.append(task)

			try:
				pieces = await asyncio.gather(*task_list)
				task_list.clear()
			except Exception as E:
				print(E)

			# For every piece, if piece hash does not match, create a download
			# task of that piece and append it to tasklist.
			for piece in pieces:
				piece_hash = hashlib.sha1(piece.data).digest()
				if piece_hash != self.piece_hashmap[piece.piece_num]:
					print(f"Piece Hash Does Not Match for {piece}")
					piece = Piece(piece_num, self.piece_info, self.peers_man)
					task = asyncio.create_task(piece.download())
					task_list.insert(0, task)
					continue

				if file.start_piece == piece.piece_num:
					piece.data = piece.data[file.start_byte:]

				if file.end_piece == piece.piece_num:
					piece.data = piece.data[:file.end_byte]

				yield piece
		print(f"File {file} downloaded")


