import asyncio
import logging
from pathlib import Path

from aiotorrent.piece import Piece
from aiotorrent.core.util import BLOCK_SIZE
from aiotorrent.core.file_utils import File, FileTree
from aiotorrent.core.util import SequentialPieceDispatcher

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


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

		peer_def = 10   # Peer default priority
		self.peer_queue = asyncio.PriorityQueue()
		for peer in active_peers:
			self.peer_queue.put_nowait((peer_def, peer))

		# Queue for storing pieces for a file
		self.file_pieces = asyncio.PriorityQueue()
		


	def create_pieces_queue(self, file: File) -> None:
		piece_def = 3   # Default piece priority
		for piece_num in range(file.start_piece, file.end_piece + 1):
			self.file_pieces.put_nowait((piece_def, piece_num))


	def file_downloaded(self) -> bool:
		'''
		Returns true if all the pieces have been downloaded, false otherwise
		'''
		return True if self.file_pieces.empty() else False


	async def get_file(self, file: File) -> Piece:
		self.create_pieces_queue(file)
		task_list = list()

		while not self.file_downloaded():
			prio_piece, num = await self.file_pieces.get()
			piece = Piece(num, prio_piece, self.piece_info)
			task = asyncio.create_task(piece.download(self.peer_queue))
			task_list.append(task)

		for task in asyncio.as_completed(task_list):
			piece = await task

			if not Piece.is_valid(piece, self.piece_hashmap):
				self.file_pieces.put_nowait((1, piece.num))
				continue

			if file.start_piece == piece.num:
				piece.data = piece.data[file.start_byte:]

			if file.end_piece == piece.num:
				piece.data = piece.data[:file.end_byte]

			file._set_bytes_written(file.get_bytes_written() + len(piece.data))
			yield piece

		logger.info(f"File {file} downloaded")


	async def get_file_sequential(self, file: File, piece_len) -> Piece:
		task_list = []
		dispatch_manager = SequentialPieceDispatcher(file, piece_len)

		self.create_pieces_queue(file)
		max_concurrent_pieces = 10
		sema = asyncio.Semaphore(max_concurrent_pieces)

		while not self.file_downloaded():
			async with sema:
				await sema.acquire()
				prio_piece, num = await self.file_pieces.get()
				piece = Piece(num, prio_piece, self.piece_info)
				# Passing semaphore so that piece can release it when it finishes fetching
				# all the blocks for itself
				task = asyncio.create_task(piece.download(self.peer_queue, _semaphore=sema))
				task_list.append(task)

				for task in task_list:
					if not task.done():
						break
					else:
						task_list.remove(task)
						piece = task.result()
						file._set_bytes_downloaded(file.get_bytes_downloaded() + len(piece.data))
						# yield piece
	
						if not Piece.is_valid(piece, self.piece_hashmap):
							self.file_pieces.put_nowait((1, piece.num))
							continue

						if file.start_piece == piece.num:
							piece.data = piece.data[file.start_byte:]

						if file.end_piece == piece.num:
							piece.data = piece.data[:file.end_byte]
							
						await dispatch_manager.put(piece)
						async for piece in dispatch_manager.dispatch():
							file._set_bytes_written(file.get_bytes_written() + len(piece.data))
							yield piece

		async for piece in dispatch_manager.drain():
			file._set_bytes_written(file.get_bytes_written() + len(piece.data))
			yield piece
